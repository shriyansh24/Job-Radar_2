"""Module 2 — Search Expansion Engine: Core engine logic.

The SearchExpansionEngine is deterministic and rule-based (V1).
It takes a user intent string and expands it into source-specific
query strings using synonym rules, seniority variants, and skill mappings.

No embedding-driven expansion. No LLM-generated expansion.
Per PHASE7A_LOCKED.md constraints.

Data flow:
    1. Input: user intent string + strictness level
    2. Normalize: strip, collapse whitespace
    3. Match rules: apply expansion_rules in priority order
    4. Build AST: construct AND/OR tree with variants
    5. Apply seniority: generate seniority prefix variants
    6. Deduplicate: remove equivalent variants
    7. Translate: convert AST to source-specific strings
    8. Output: source-query map + AST for logging
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from backend.phase7a.constants import QueryStrictness, SourceType
from backend.phase7a.id_utils import compute_template_id
from backend.phase7a.m2_rules import (
    SENIORITY_PREFIXES,
    DefaultRule,
    get_all_default_rules,
    get_skill_map,
    get_synonym_map,
)


# --- Result types ---

@dataclass
class ExpansionResult:
    """The output of a search expansion operation."""

    template_id: str
    intent: str
    expansion_ast: dict
    source_translations: dict[str, str]
    strictness: str
    estimated_variants: int


# --- Engine ---

class SearchExpansionEngine:
    """Rule-based search expansion engine (V1).

    Expands user intent strings into source-specific query strings
    using deterministic synonym, seniority, and skill rules.

    The engine operates entirely in-memory using the default rules
    loaded at instantiation. Database-persisted rules can be loaded
    via passing custom rules to the constructor.
    """

    def __init__(
        self,
        synonym_rules: Optional[list[DefaultRule]] = None,
        seniority_prefixes: Optional[list[str]] = None,
        skill_rules: Optional[list[DefaultRule]] = None,
    ):
        """Initialize the engine with expansion rules.

        Args:
            synonym_rules: Custom synonym rules. Defaults to built-in rules.
            seniority_prefixes: Custom seniority prefixes. Defaults to built-in.
            skill_rules: Custom skill rules. Defaults to built-in rules.
        """
        if synonym_rules is not None:
            self._synonym_map: dict[str, list[str]] = {
                r.input_pattern.lower(): r.output_variants
                for r in synonym_rules
            }
        else:
            self._synonym_map = get_synonym_map()

        self._seniority_prefixes: list[str] = (
            seniority_prefixes if seniority_prefixes is not None
            else list(SENIORITY_PREFIXES)
        )

        if skill_rules is not None:
            self._skill_map: dict[str, list[str]] = {
                r.input_pattern.lower(): r.output_variants
                for r in skill_rules
            }
        else:
            self._skill_map = get_skill_map()

    # --- Public API ---

    def expand(
        self,
        intent: str,
        strictness: str = "balanced",
        sources: Optional[list[str]] = None,
    ) -> ExpansionResult:
        """Expand a user intent into source-specific query strings.

        Args:
            intent: The user's search intent (e.g., "ML Engineer").
            strictness: Expansion breadth: strict|balanced|broad.
            sources: List of source types to generate translations for.
                     Defaults to all known sources.

        Returns:
            ExpansionResult with AST, source translations, and metadata.

        Raises:
            ValueError: If intent is empty or strictness is invalid.
        """
        intent = self._normalize_intent(intent)
        if not intent:
            raise ValueError("Intent must not be empty.")

        strictness_enum = self._validate_strictness(strictness)

        if sources is None:
            sources = [s.value for s in SourceType]

        rules = self.get_matching_rules(intent)
        ast = self.build_ast(intent, rules, strictness_enum.value)
        source_translations = {
            src: self.translate_for_source(ast, src)
            for src in sources
        }

        all_variants = self._collect_all_terms(ast)
        estimated_variants = len(all_variants)

        template_id = compute_template_id(intent)

        return ExpansionResult(
            template_id=template_id,
            intent=intent,
            expansion_ast=ast,
            source_translations=source_translations,
            strictness=strictness_enum.value,
            estimated_variants=estimated_variants,
        )

    def build_ast(
        self,
        intent: str,
        rules: list[DefaultRule],
        strictness: str,
    ) -> dict:
        """Build a query AST from an intent and matching rules.

        The AST is an AND/OR tree:
        - Top level is OR (any variant matches)
        - Each variant is a term node
        - Seniority variants are stored as metadata
        - Excludes are stored for filtering

        Args:
            intent: Normalized user intent.
            rules: Matching rules from get_matching_rules().
            strictness: strict|balanced|broad.

        Returns:
            Dict representing the query AST.
        """
        intent_lower = intent.lower()

        # Collect base variants: the intent itself + synonyms
        base_variants: list[str] = [intent]

        # Apply synonym rules (all strictness levels get synonyms)
        synonym_variants = self._synonym_map.get(intent_lower, [])
        for variant in synonym_variants:
            if variant.lower() != intent_lower:
                base_variants.append(variant)

        # Determine seniority variants based on strictness
        if strictness == QueryStrictness.STRICT.value:
            seniority_variants = [""]  # No seniority expansion in strict
        else:
            seniority_variants = list(self._seniority_prefixes)

        # Standard exclusions
        exclude = ["intern", "internship"]

        # Build children (term nodes), deduplicating by lowercase
        children = []
        seen_lower: set[str] = set()

        for variant in base_variants:
            vl = variant.strip().lower()
            if vl and vl not in seen_lower:
                seen_lower.add(vl)
                children.append({
                    "type": "term",
                    "value": variant.strip(),
                })

        # In broad mode, add skill expansions as optional terms
        if strictness == QueryStrictness.BROAD.value:
            skill_children = self._get_skill_expansions(intent_lower)
            for sc in skill_children:
                scl = sc.strip().lower()
                if scl and scl not in seen_lower:
                    seen_lower.add(scl)
                    children.append({
                        "type": "term",
                        "value": sc.strip(),
                        "optional": True,
                    })

        ast = {
            "$schema": "query_ast_v1",
            "type": "OR",
            "children": children,
            "seniority_variants": seniority_variants,
            "exclude": exclude,
        }

        return ast

    def translate_for_source(self, ast: dict, source_type: str) -> str:
        """Convert a query AST into a source-specific query string.

        Translation rules per source:
            serpapi (Google Jobs): Natural language with quoted OR
            greenhouse: Title filter string (simpler, single primary term)
            lever: Natural language search with quoted OR
            jobspy: search_term with unquoted OR operator
            ashby: Natural language search with quoted OR
            theirstack/apify: Natural language OR

        Args:
            ast: Query AST dict.
            source_type: Source type string (e.g., "serpapi").

        Returns:
            Source-specific query string.
        """
        terms = self._collect_required_terms(ast)
        if not terms:
            return ""

        source_lower = source_type.lower()

        if source_lower == SourceType.SERPAPI.value:
            return self._translate_serpapi(terms)
        elif source_lower == SourceType.GREENHOUSE.value:
            return self._translate_greenhouse(terms)
        elif source_lower == SourceType.LEVER.value:
            return self._translate_lever(terms)
        elif source_lower == SourceType.JOBSPY.value:
            return self._translate_jobspy(terms)
        elif source_lower == SourceType.ASHBY.value:
            return self._translate_ashby(terms)
        else:
            return self._translate_default(terms)

    def deduplicate_variants(self, variants: list[str]) -> list[str]:
        """Remove duplicate variants (case-insensitive).

        Preserves the first occurrence's casing.

        Args:
            variants: List of query variant strings.

        Returns:
            Deduplicated list preserving original order and casing.
        """
        seen: set[str] = set()
        result: list[str] = []
        for v in variants:
            v_stripped = v.strip()
            key = v_stripped.lower()
            if key and key not in seen:
                seen.add(key)
                result.append(v_stripped)
        return result

    def get_matching_rules(self, intent: str) -> list[DefaultRule]:
        """Find all expansion rules that match a given intent.

        Matching is case-insensitive exact match against input_pattern.
        The wildcard pattern "*" matches all intents (used for seniority rules).

        Args:
            intent: The normalized user intent.

        Returns:
            List of matching DefaultRule objects, sorted by priority (ascending).
        """
        intent_lower = intent.lower().strip()
        all_rules = get_all_default_rules()
        matched: list[DefaultRule] = []

        for rule in all_rules:
            pattern = rule.input_pattern.lower().strip()
            if pattern == "*" or pattern == intent_lower:
                matched.append(rule)

        return sorted(matched, key=lambda r: r.priority)

    def preview_expansion(
        self,
        intent: str,
        strictness: str = "balanced",
    ) -> list[str]:
        """Preview all expanded variants for an intent (flat list).

        This generates the full set of title variants including
        seniority prefixes, suitable for showing to the user before
        running actual queries.

        Args:
            intent: User's search intent.
            strictness: Expansion breadth.

        Returns:
            Flat, deduplicated list of all variant strings.
        """
        intent = self._normalize_intent(intent)
        if not intent:
            return []

        strictness_enum = self._validate_strictness(strictness)
        rules = self.get_matching_rules(intent)
        ast = self.build_ast(intent, rules, strictness_enum.value)

        return self._collect_all_terms(ast)

    # --- Private helpers ---

    @staticmethod
    def _normalize_intent(intent: str) -> str:
        """Normalize intent: strip, collapse whitespace."""
        if not intent:
            return ""
        result = intent.strip()
        result = re.sub(r"\s+", " ", result)
        return result

    @staticmethod
    def _validate_strictness(strictness: str) -> QueryStrictness:
        """Validate and return the strictness enum value.

        Raises:
            ValueError: If strictness is not a valid QueryStrictness value.
        """
        try:
            return QueryStrictness(strictness.lower())
        except ValueError:
            valid = [s.value for s in QueryStrictness]
            raise ValueError(
                f"Invalid strictness '{strictness}'. Must be one of: {valid}"
            )

    def _get_skill_expansions(self, intent_lower: str) -> list[str]:
        """Get skill-related expansions for broad mode.

        Checks if any skill keywords appear in the intent and
        returns their related technologies.
        """
        expansions: list[str] = []
        for skill_key, related in self._skill_map.items():
            if skill_key in intent_lower:
                expansions.extend(related)
        return expansions

    def _collect_required_terms(self, ast: dict) -> list[str]:
        """Extract all required (non-optional) term values from an AST."""
        terms: list[str] = []
        for child in ast.get("children", []):
            if child.get("type") == "term" and not child.get("optional", False):
                terms.append(child["value"])
            elif child.get("type") in ("AND", "OR"):
                terms.extend(self._collect_required_terms(child))
        return terms

    def _collect_all_terms(self, ast: dict) -> list[str]:
        """Collect all expanded variants including seniority prefixes.

        Returns a deduplicated flat list.
        """
        base_terms: list[str] = []
        for child in ast.get("children", []):
            if child.get("type") == "term":
                base_terms.append(child["value"])
            elif child.get("type") in ("AND", "OR"):
                base_terms.extend(self._collect_all_terms_recursive(child))

        seniority_variants = ast.get("seniority_variants", [""])
        exclude = {e.lower() for e in ast.get("exclude", [])}

        all_variants: list[str] = []
        for prefix in seniority_variants:
            for term in base_terms:
                if prefix:
                    variant = f"{prefix} {term}"
                else:
                    variant = term
                # Skip if it contains excluded terms
                if not any(exc in variant.lower() for exc in exclude):
                    all_variants.append(variant)

        return self.deduplicate_variants(all_variants)

    def _collect_all_terms_recursive(self, node: dict) -> list[str]:
        """Recursively collect term values from nested AST nodes."""
        terms: list[str] = []
        if node.get("type") == "term":
            terms.append(node["value"])
        for child in node.get("children", []):
            terms.extend(self._collect_all_terms_recursive(child))
        return terms

    # --- Source-specific translators ---

    def _translate_serpapi(self, terms: list[str]) -> str:
        """SerpApi (Google Jobs): Natural language with OR and quoted terms.

        Example: '"Machine Learning Engineer" OR "ML Engineer" OR "Applied Scientist"'
        """
        quoted = [f'"{t}"' for t in terms]
        return " OR ".join(quoted)

    def _translate_greenhouse(self, terms: list[str]) -> str:
        """Greenhouse: Single primary term, title filter string.

        Greenhouse API uses a simpler search. We extract the core concept
        from the first (primary) term and use that as the title filter.

        Example: "Machine Learning"
        """
        if not terms:
            return ""
        primary = terms[0]
        # Extract the core concept (before common suffixes)
        core = re.sub(
            r"\s+(Engineer|Developer|Scientist|Architect|Manager|Analyst)$",
            "",
            primary,
            flags=re.IGNORECASE,
        )
        return core if core else primary

    def _translate_lever(self, terms: list[str]) -> str:
        """Lever: Natural language search with OR.

        Example: '"ML Engineer" OR "Machine Learning Engineer"'
        """
        quoted = [f'"{t}"' for t in terms]
        return " OR ".join(quoted)

    def _translate_jobspy(self, terms: list[str]) -> str:
        """JobSpy: search_term with OR operator (unquoted).

        Example: "ML Engineer OR Machine Learning Engineer"
        """
        return " OR ".join(terms)

    def _translate_ashby(self, terms: list[str]) -> str:
        """Ashby: Natural language search with OR.

        Example: '"ML Engineer" OR "Machine Learning Engineer"'
        """
        quoted = [f'"{t}"' for t in terms]
        return " OR ".join(quoted)

    def _translate_default(self, terms: list[str]) -> str:
        """Default translation: OR-joined terms."""
        return " OR ".join(terms)
