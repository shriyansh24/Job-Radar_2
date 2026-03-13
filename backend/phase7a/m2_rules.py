"""Module 2 — Search Expansion Engine: Default expansion rules.

These rules are seeded into the expansion_rules table on first migration.
They provide deterministic, rule-based query expansion without any
embedding or LLM involvement (per PHASE7A_LOCKED.md constraints).

Rule types:
    synonym   (priority 10) — Direct title/role synonyms.
    seniority (priority 20) — Seniority prefix variants applied to all intents.
    skill     (priority 30) — Skill-to-related-skill mappings.

Rules are matched by case-insensitive exact match or wildcard ("*")
against the user's intent string.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DefaultRule:
    """A default expansion rule to seed into the database."""

    rule_type: str
    input_pattern: str
    output_variants: list[str]
    priority: int = 100


# --- Synonym rules (priority 10) ---
# These map common job title abbreviations and alternatives to their variants.

SYNONYM_RULES: list[DefaultRule] = [
    DefaultRule(
        rule_type="synonym",
        input_pattern="ML Engineer",
        output_variants=[
            "Machine Learning Engineer",
            "Applied Scientist",
            "AI Engineer",
        ],
        priority=10,
    ),
    DefaultRule(
        rule_type="synonym",
        input_pattern="Backend Engineer",
        output_variants=[
            "Backend Developer",
            "Server Engineer",
            "Server-side Developer",
        ],
        priority=10,
    ),
    DefaultRule(
        rule_type="synonym",
        input_pattern="Frontend Engineer",
        output_variants=[
            "Frontend Developer",
            "UI Engineer",
            "Web Developer",
        ],
        priority=10,
    ),
    DefaultRule(
        rule_type="synonym",
        input_pattern="Data Scientist",
        output_variants=[
            "Data Science",
            "Analytics Engineer",
            "Applied Data Scientist",
        ],
        priority=10,
    ),
    DefaultRule(
        rule_type="synonym",
        input_pattern="DevOps Engineer",
        output_variants=[
            "Site Reliability Engineer",
            "SRE",
            "Platform Engineer",
            "Infrastructure Engineer",
        ],
        priority=10,
    ),
    DefaultRule(
        rule_type="synonym",
        input_pattern="Full Stack",
        output_variants=[
            "Fullstack",
            "Full-Stack",
        ],
        priority=10,
    ),
]


# --- Seniority rules (priority 20) ---
# These define prefix variants applied to intents.
# The engine applies these prefixes to the base intent and its synonyms.

SENIORITY_PREFIXES: list[str] = [
    "",           # No prefix (original title)
    "Senior",
    "Staff",
    "Principal",
    "Lead",
]

# Stored as a single seniority rule for the engine to reference.
SENIORITY_RULES: list[DefaultRule] = [
    DefaultRule(
        rule_type="seniority",
        input_pattern="*",  # Applies to all intents
        output_variants=SENIORITY_PREFIXES,
        priority=20,
    ),
]


# --- Skill rules (priority 30) ---
# These map skill keywords to related technologies/frameworks.

SKILL_RULES: list[DefaultRule] = [
    DefaultRule(
        rule_type="skill",
        input_pattern="Python",
        output_variants=[
            "Python",
            "Django",
            "FastAPI",
            "Flask",
        ],
        priority=30,
    ),
    DefaultRule(
        rule_type="skill",
        input_pattern="JavaScript",
        output_variants=[
            "JavaScript",
            "TypeScript",
            "React",
            "Node.js",
        ],
        priority=30,
    ),
    DefaultRule(
        rule_type="skill",
        input_pattern="ML",
        output_variants=[
            "Machine Learning",
            "Deep Learning",
            "NLP",
            "Computer Vision",
        ],
        priority=30,
    ),
]


def get_all_default_rules() -> list[DefaultRule]:
    """Return all default rules to be seeded into the database.

    Returns rules in priority order (lower priority number = higher precedence).
    """
    all_rules = SYNONYM_RULES + SENIORITY_RULES + SKILL_RULES
    return sorted(all_rules, key=lambda r: r.priority)


def get_synonym_map() -> dict[str, list[str]]:
    """Return a lookup dict of input_pattern (lowered) -> output_variants.

    This is used by the engine for fast synonym resolution without
    hitting the database on every expansion.
    """
    return {
        rule.input_pattern.lower(): rule.output_variants
        for rule in SYNONYM_RULES
    }


def get_skill_map() -> dict[str, list[str]]:
    """Return a lookup dict of skill keyword (lowered) -> related skills.

    Used by the engine for broad-mode skill expansion.
    """
    return {
        rule.input_pattern.lower(): rule.output_variants
        for rule in SKILL_RULES
    }
