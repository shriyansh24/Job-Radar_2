"""Tests for Module 2 Search Expansion Engine: Core engine logic.

Covers AST building, source translation, deduplication, rule matching,
strictness levels, and edge cases.
"""

import re

import pytest

from backend.phase7a.constants import QueryStrictness, SourceType
from backend.phase7a.id_utils import compute_template_id
from backend.phase7a.m2_engine import ExpansionResult, SearchExpansionEngine
from backend.phase7a.m2_rules import DefaultRule, SENIORITY_PREFIXES


@pytest.fixture
def engine():
    """Create a SearchExpansionEngine with default rules."""
    return SearchExpansionEngine()


@pytest.fixture
def empty_engine():
    """Create a SearchExpansionEngine with no rules."""
    return SearchExpansionEngine(
        synonym_rules=[],
        seniority_prefixes=[""],
        skill_rules=[],
    )


@pytest.fixture
def custom_engine():
    """Create a SearchExpansionEngine with custom rules for testing."""
    synonym_rules = [
        DefaultRule(
            rule_type="synonym",
            input_pattern="Test Job",
            output_variants=["Test Position", "Test Role"],
            priority=10,
        ),
    ]
    skill_rules = [
        DefaultRule(
            rule_type="skill",
            input_pattern="TestSkill",
            output_variants=["Skill A", "Skill B"],
            priority=30,
        ),
    ]
    return SearchExpansionEngine(
        synonym_rules=synonym_rules,
        seniority_prefixes=["", "Senior"],
        skill_rules=skill_rules,
    )


# --- expand() tests ---

class TestExpand:
    """Tests for the expand() method."""

    def test_returns_expansion_result(self, engine):
        result = engine.expand("ML Engineer")
        assert isinstance(result, ExpansionResult)

    def test_template_id_deterministic(self, engine):
        r1 = engine.expand("ML Engineer")
        r2 = engine.expand("ML Engineer")
        assert r1.template_id == r2.template_id

    def test_template_id_matches_compute(self, engine):
        result = engine.expand("ML Engineer")
        assert result.template_id == compute_template_id("ML Engineer")

    def test_intent_preserved(self, engine):
        result = engine.expand("ML Engineer")
        assert result.intent == "ML Engineer"

    def test_strictness_preserved(self, engine):
        result = engine.expand("ML Engineer", strictness="strict")
        assert result.strictness == "strict"

    def test_expansion_ast_has_schema(self, engine):
        result = engine.expand("ML Engineer")
        assert result.expansion_ast["$schema"] == "query_ast_v1"

    def test_expansion_ast_has_children(self, engine):
        result = engine.expand("ML Engineer")
        assert len(result.expansion_ast["children"]) > 0

    def test_source_translations_generated(self, engine):
        result = engine.expand("ML Engineer")
        assert len(result.source_translations) > 0

    def test_specific_sources(self, engine):
        result = engine.expand("ML Engineer", sources=["serpapi", "greenhouse"])
        assert set(result.source_translations.keys()) == {"serpapi", "greenhouse"}

    def test_all_sources_default(self, engine):
        result = engine.expand("ML Engineer")
        expected_sources = {s.value for s in SourceType}
        assert set(result.source_translations.keys()) == expected_sources

    def test_estimated_variants_positive(self, engine):
        result = engine.expand("ML Engineer")
        assert result.estimated_variants > 0

    def test_empty_intent_raises(self, engine):
        with pytest.raises(ValueError, match="empty"):
            engine.expand("")

    def test_whitespace_intent_raises(self, engine):
        with pytest.raises(ValueError, match="empty"):
            engine.expand("   ")

    def test_invalid_strictness_raises(self, engine):
        with pytest.raises(ValueError, match="Invalid strictness"):
            engine.expand("ML Engineer", strictness="invalid")

    def test_intent_normalized(self, engine):
        r1 = engine.expand("  ML   Engineer  ")
        assert r1.intent == "ML Engineer"

    def test_unknown_intent_still_works(self, engine):
        """An intent with no matching synonym rules should still produce results."""
        result = engine.expand("Quantum Computing Researcher")
        assert result.estimated_variants > 0
        assert result.expansion_ast["children"][0]["value"] == "Quantum Computing Researcher"


# --- build_ast() tests ---

class TestBuildAST:
    """Tests for the build_ast() method."""

    def test_ast_structure(self, engine):
        rules = engine.get_matching_rules("ML Engineer")
        ast = engine.build_ast("ML Engineer", rules, "balanced")
        assert ast["$schema"] == "query_ast_v1"
        assert ast["type"] == "OR"
        assert isinstance(ast["children"], list)
        assert isinstance(ast["seniority_variants"], list)
        assert isinstance(ast["exclude"], list)

    def test_includes_original_intent(self, engine):
        rules = engine.get_matching_rules("ML Engineer")
        ast = engine.build_ast("ML Engineer", rules, "balanced")
        values = [c["value"] for c in ast["children"]]
        assert "ML Engineer" in values

    def test_includes_synonyms(self, engine):
        rules = engine.get_matching_rules("ML Engineer")
        ast = engine.build_ast("ML Engineer", rules, "balanced")
        values = [c["value"] for c in ast["children"]]
        assert "Machine Learning Engineer" in values
        assert "Applied Scientist" in values
        assert "AI Engineer" in values

    def test_strict_no_seniority(self, engine):
        rules = engine.get_matching_rules("ML Engineer")
        ast = engine.build_ast("ML Engineer", rules, "strict")
        assert ast["seniority_variants"] == [""]

    def test_balanced_has_seniority(self, engine):
        rules = engine.get_matching_rules("ML Engineer")
        ast = engine.build_ast("ML Engineer", rules, "balanced")
        assert "Senior" in ast["seniority_variants"]
        assert "Staff" in ast["seniority_variants"]

    def test_broad_has_seniority(self, engine):
        rules = engine.get_matching_rules("ML Engineer")
        ast = engine.build_ast("ML Engineer", rules, "broad")
        assert "Senior" in ast["seniority_variants"]

    def test_broad_includes_skill_expansions(self, engine):
        """Broad mode on 'ML Engineer' should include ML skill expansions."""
        rules = engine.get_matching_rules("ML Engineer")
        ast = engine.build_ast("ML Engineer", rules, "broad")
        values = [c["value"] for c in ast["children"]]
        # The "ML" keyword in "ML Engineer" should trigger ML skill expansions
        assert any(
            c.get("optional", False) for c in ast["children"]
        ), "Broad mode should have optional skill terms"

    def test_excludes_intern(self, engine):
        rules = engine.get_matching_rules("ML Engineer")
        ast = engine.build_ast("ML Engineer", rules, "balanced")
        assert "intern" in ast["exclude"]
        assert "internship" in ast["exclude"]

    def test_no_duplicate_children(self, engine):
        rules = engine.get_matching_rules("ML Engineer")
        ast = engine.build_ast("ML Engineer", rules, "balanced")
        values = [c["value"].lower() for c in ast["children"]]
        assert len(values) == len(set(values)), "Children should not contain duplicates"

    def test_unknown_intent_produces_single_term(self, empty_engine):
        """An unknown intent with no rules should produce a single term."""
        ast = empty_engine.build_ast("Unknown Job Title", [], "balanced")
        assert len(ast["children"]) == 1
        assert ast["children"][0]["value"] == "Unknown Job Title"


# --- translate_for_source() tests ---

class TestTranslateForSource:
    """Tests for the translate_for_source() method."""

    def test_serpapi_quoted_or(self, engine):
        ast = {
            "type": "OR",
            "children": [
                {"type": "term", "value": "ML Engineer"},
                {"type": "term", "value": "AI Engineer"},
            ],
            "seniority_variants": [""],
            "exclude": [],
        }
        result = engine.translate_for_source(ast, "serpapi")
        assert '"ML Engineer"' in result
        assert '"AI Engineer"' in result
        assert " OR " in result

    def test_greenhouse_single_term(self, engine):
        ast = {
            "type": "OR",
            "children": [
                {"type": "term", "value": "Machine Learning Engineer"},
                {"type": "term", "value": "ML Engineer"},
            ],
            "seniority_variants": [""],
            "exclude": [],
        }
        result = engine.translate_for_source(ast, "greenhouse")
        # Greenhouse strips common suffixes like "Engineer"
        assert result == "Machine Learning"

    def test_greenhouse_preserves_when_no_suffix(self, engine):
        ast = {
            "type": "OR",
            "children": [
                {"type": "term", "value": "Data Science"},
            ],
            "seniority_variants": [""],
            "exclude": [],
        }
        result = engine.translate_for_source(ast, "greenhouse")
        assert result == "Data Science"

    def test_lever_quoted_or(self, engine):
        ast = {
            "type": "OR",
            "children": [
                {"type": "term", "value": "ML Engineer"},
                {"type": "term", "value": "AI Engineer"},
            ],
            "seniority_variants": [""],
            "exclude": [],
        }
        result = engine.translate_for_source(ast, "lever")
        assert '"ML Engineer"' in result
        assert " OR " in result

    def test_jobspy_unquoted_or(self, engine):
        ast = {
            "type": "OR",
            "children": [
                {"type": "term", "value": "ML Engineer"},
                {"type": "term", "value": "AI Engineer"},
            ],
            "seniority_variants": [""],
            "exclude": [],
        }
        result = engine.translate_for_source(ast, "jobspy")
        assert "ML Engineer OR AI Engineer" == result

    def test_ashby_quoted_or(self, engine):
        ast = {
            "type": "OR",
            "children": [
                {"type": "term", "value": "ML Engineer"},
            ],
            "seniority_variants": [""],
            "exclude": [],
        }
        result = engine.translate_for_source(ast, "ashby")
        assert result == '"ML Engineer"'

    def test_unknown_source_default(self, engine):
        ast = {
            "type": "OR",
            "children": [
                {"type": "term", "value": "ML Engineer"},
                {"type": "term", "value": "AI Engineer"},
            ],
            "seniority_variants": [""],
            "exclude": [],
        }
        result = engine.translate_for_source(ast, "some_unknown_source")
        assert "ML Engineer" in result
        assert "AI Engineer" in result

    def test_skips_optional_terms(self, engine):
        ast = {
            "type": "OR",
            "children": [
                {"type": "term", "value": "ML Engineer"},
                {"type": "term", "value": "Python", "optional": True},
            ],
            "seniority_variants": [""],
            "exclude": [],
        }
        result = engine.translate_for_source(ast, "serpapi")
        assert '"ML Engineer"' in result
        assert "Python" not in result

    def test_empty_children_returns_empty(self, engine):
        ast = {
            "type": "OR",
            "children": [],
            "seniority_variants": [""],
            "exclude": [],
        }
        result = engine.translate_for_source(ast, "serpapi")
        assert result == ""


# --- deduplicate_variants() tests ---

class TestDeduplicateVariants:
    """Tests for the deduplicate_variants() method."""

    def test_removes_exact_duplicates(self, engine):
        result = engine.deduplicate_variants(["ML Engineer", "ML Engineer"])
        assert result == ["ML Engineer"]

    def test_case_insensitive(self, engine):
        result = engine.deduplicate_variants(["ML Engineer", "ml engineer", "ML ENGINEER"])
        assert len(result) == 1
        assert result[0] == "ML Engineer"  # First occurrence preserved

    def test_preserves_order(self, engine):
        result = engine.deduplicate_variants(["B", "A", "C"])
        assert result == ["B", "A", "C"]

    def test_strips_whitespace(self, engine):
        result = engine.deduplicate_variants(["  ML Engineer  ", "ML Engineer"])
        assert result == ["ML Engineer"]

    def test_removes_empty_strings(self, engine):
        result = engine.deduplicate_variants(["", "ML Engineer", "  ", "AI Engineer"])
        assert result == ["ML Engineer", "AI Engineer"]

    def test_empty_input(self, engine):
        result = engine.deduplicate_variants([])
        assert result == []


# --- get_matching_rules() tests ---

class TestGetMatchingRules:
    """Tests for the get_matching_rules() method."""

    def test_ml_engineer_matches(self, engine):
        rules = engine.get_matching_rules("ML Engineer")
        types = [r.rule_type for r in rules]
        assert "synonym" in types
        assert "seniority" in types  # Wildcard matches

    def test_case_insensitive(self, engine):
        rules_lower = engine.get_matching_rules("ml engineer")
        rules_upper = engine.get_matching_rules("ML Engineer")
        assert len(rules_lower) == len(rules_upper)

    def test_wildcard_always_matches(self, engine):
        rules = engine.get_matching_rules("Some Unknown Job")
        seniority_rules = [r for r in rules if r.rule_type == "seniority"]
        assert len(seniority_rules) > 0, "Wildcard seniority rule should match any intent"

    def test_no_synonym_match_for_unknown(self, engine):
        rules = engine.get_matching_rules("Quantum Computing Researcher")
        synonym_rules = [r for r in rules if r.rule_type == "synonym"]
        assert len(synonym_rules) == 0

    def test_sorted_by_priority(self, engine):
        rules = engine.get_matching_rules("ML Engineer")
        priorities = [r.priority for r in rules]
        assert priorities == sorted(priorities)


# --- preview_expansion() tests ---

class TestPreviewExpansion:
    """Tests for the preview_expansion() method."""

    def test_returns_list(self, engine):
        result = engine.preview_expansion("ML Engineer")
        assert isinstance(result, list)

    def test_includes_original(self, engine):
        result = engine.preview_expansion("ML Engineer", strictness="strict")
        assert "ML Engineer" in result

    def test_includes_synonyms(self, engine):
        result = engine.preview_expansion("ML Engineer", strictness="strict")
        assert "Machine Learning Engineer" in result

    def test_strict_no_seniority_prefix(self, engine):
        result = engine.preview_expansion("ML Engineer", strictness="strict")
        senior_variants = [v for v in result if v.startswith("Senior ")]
        assert len(senior_variants) == 0

    def test_balanced_has_seniority_prefix(self, engine):
        result = engine.preview_expansion("ML Engineer", strictness="balanced")
        senior_variants = [v for v in result if v.startswith("Senior ")]
        assert len(senior_variants) > 0

    def test_broad_more_than_balanced(self, engine):
        balanced = engine.preview_expansion("ML Engineer", strictness="balanced")
        broad = engine.preview_expansion("ML Engineer", strictness="broad")
        assert len(broad) >= len(balanced)

    def test_no_duplicates(self, engine):
        result = engine.preview_expansion("ML Engineer", strictness="broad")
        lowered = [v.lower() for v in result]
        assert len(lowered) == len(set(lowered)), "Preview should not contain duplicates"

    def test_empty_intent_returns_empty(self, engine):
        result = engine.preview_expansion("")
        assert result == []

    def test_whitespace_intent_returns_empty(self, engine):
        result = engine.preview_expansion("   ")
        assert result == []

    def test_excludes_intern_variants(self, engine):
        """Intern/internship should be excluded from all variants."""
        result = engine.preview_expansion("ML Engineer", strictness="broad")
        for variant in result:
            assert "intern" not in variant.lower() or "internship" not in variant.lower()

    def test_unknown_intent_returns_intent(self, engine):
        result = engine.preview_expansion("Quantum Computing Researcher", strictness="strict")
        assert "Quantum Computing Researcher" in result


# --- Strictness level tests ---

class TestStrictnessLevels:
    """Tests verifying behavior differences across strictness levels."""

    def test_strict_minimal_expansion(self, engine):
        """Strict: original intent + direct synonyms only, no seniority."""
        result = engine.expand("ML Engineer", strictness="strict")
        ast = result.expansion_ast
        # Should have synonyms but no seniority
        assert ast["seniority_variants"] == [""]
        # Should not have optional skill terms
        optional = [c for c in ast["children"] if c.get("optional", False)]
        assert len(optional) == 0

    def test_balanced_adds_seniority(self, engine):
        """Balanced: synonyms + seniority variants."""
        result = engine.expand("ML Engineer", strictness="balanced")
        ast = result.expansion_ast
        assert "Senior" in ast["seniority_variants"]
        assert "Staff" in ast["seniority_variants"]

    def test_broad_adds_skills(self, engine):
        """Broad: synonyms + seniority + skill expansions."""
        result = engine.expand("ML Engineer", strictness="broad")
        ast = result.expansion_ast
        optional = [c for c in ast["children"] if c.get("optional", False)]
        assert len(optional) > 0, "Broad mode should include optional skill terms"

    def test_variant_count_increases_with_strictness(self, engine):
        strict = engine.expand("ML Engineer", strictness="strict")
        balanced = engine.expand("ML Engineer", strictness="balanced")
        broad = engine.expand("ML Engineer", strictness="broad")
        assert strict.estimated_variants <= balanced.estimated_variants
        assert balanced.estimated_variants <= broad.estimated_variants


# --- Edge cases ---

class TestEdgeCases:
    """Edge case tests for the engine."""

    def test_special_chars_in_intent(self, engine):
        """Intent with special characters should not crash."""
        result = engine.expand("C++ Developer")
        assert result.intent == "C++ Developer"
        assert result.estimated_variants > 0

    def test_very_long_intent(self, engine):
        """Very long intent strings should not crash."""
        long_intent = "A" * 500
        result = engine.expand(long_intent)
        assert result.intent == long_intent
        assert result.estimated_variants > 0

    def test_intent_with_numbers(self, engine):
        result = engine.expand("Web3 Developer")
        assert result.intent == "Web3 Developer"

    def test_single_word_intent(self, engine):
        result = engine.expand("Engineer")
        assert result.estimated_variants > 0

    def test_custom_sources_empty(self, engine):
        result = engine.expand("ML Engineer", sources=[])
        assert result.source_translations == {}

    def test_custom_engine_works(self, custom_engine):
        result = custom_engine.expand("Test Job", strictness="balanced")
        ast = result.expansion_ast
        values = [c["value"] for c in ast["children"]]
        assert "Test Job" in values
        assert "Test Position" in values
        assert "Test Role" in values

    def test_no_rules_still_returns_original(self, empty_engine):
        result = empty_engine.expand("Anything Goes")
        assert result.estimated_variants >= 1
        values = [c["value"] for c in result.expansion_ast["children"]]
        assert "Anything Goes" in values

    def test_unicode_intent(self, engine):
        result = engine.expand("Entwickler")
        assert result.intent == "Entwickler"

    def test_multiple_spaces_normalized(self, engine):
        r1 = engine.expand("ML  Engineer")
        r2 = engine.expand("ML Engineer")
        assert r1.template_id == r2.template_id

    def test_leading_trailing_whitespace(self, engine):
        r1 = engine.expand("  ML Engineer  ")
        r2 = engine.expand("ML Engineer")
        assert r1.template_id == r2.template_id

    def test_all_sources_disabled_still_expands(self, engine):
        """Even with no sources, expansion should still produce an AST."""
        result = engine.expand("ML Engineer", sources=[])
        assert result.expansion_ast is not None
        assert result.estimated_variants > 0
        assert result.source_translations == {}


class TestCustomEngineConfigurations:
    """Tests for custom engine configurations."""

    def test_custom_seniority_prefixes(self):
        engine = SearchExpansionEngine(seniority_prefixes=["", "Junior", "Intern"])
        result = engine.preview_expansion("Developer", strictness="balanced")
        assert "Junior Developer" in result
        # Note: "Intern Developer" would be filtered by exclude
        # since "intern" is in the exclude list

    def test_empty_synonym_rules(self):
        engine = SearchExpansionEngine(synonym_rules=[])
        result = engine.expand("ML Engineer", strictness="strict")
        # Should still have the original intent
        values = [c["value"] for c in result.expansion_ast["children"]]
        assert "ML Engineer" in values
        # But no synonyms
        assert "Machine Learning Engineer" not in values

    def test_empty_skill_rules(self):
        engine = SearchExpansionEngine(skill_rules=[])
        result = engine.expand("ML Engineer", strictness="broad")
        # Should have synonyms and seniority but no skill expansions
        optional = [c for c in result.expansion_ast["children"] if c.get("optional", False)]
        assert len(optional) == 0
