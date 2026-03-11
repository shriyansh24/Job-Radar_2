"""Tests for Module 2 Search Expansion Engine: Default expansion rules.

Verifies the correctness of the default synonym, seniority, and skill rules
that are seeded into the database.
"""

from backend.phase7a.m2_rules import (
    DefaultRule,
    SENIORITY_PREFIXES,
    SENIORITY_RULES,
    SKILL_RULES,
    SYNONYM_RULES,
    get_all_default_rules,
    get_skill_map,
    get_synonym_map,
)


class TestDefaultRuleDataclass:
    """Tests for the DefaultRule frozen dataclass."""

    def test_frozen(self):
        rule = DefaultRule(
            rule_type="synonym",
            input_pattern="test",
            output_variants=["a", "b"],
            priority=10,
        )
        # Frozen dataclass should raise on assignment
        try:
            rule.rule_type = "other"
            assert False, "Should raise FrozenInstanceError"
        except AttributeError:
            pass  # Expected

    def test_default_priority(self):
        rule = DefaultRule(
            rule_type="synonym",
            input_pattern="test",
            output_variants=["a"],
        )
        assert rule.priority == 100

    def test_custom_priority(self):
        rule = DefaultRule(
            rule_type="synonym",
            input_pattern="test",
            output_variants=["a"],
            priority=10,
        )
        assert rule.priority == 10


class TestSynonymRules:
    """Tests for the built-in synonym rules."""

    def test_all_are_synonym_type(self):
        for rule in SYNONYM_RULES:
            assert rule.rule_type == "synonym"

    def test_all_have_priority_10(self):
        for rule in SYNONYM_RULES:
            assert rule.priority == 10

    def test_all_have_nonempty_variants(self):
        for rule in SYNONYM_RULES:
            assert len(rule.output_variants) > 0

    def test_ml_engineer_synonyms(self):
        ml_rules = [r for r in SYNONYM_RULES if r.input_pattern == "ML Engineer"]
        assert len(ml_rules) == 1
        variants = ml_rules[0].output_variants
        assert "Machine Learning Engineer" in variants
        assert "Applied Scientist" in variants
        assert "AI Engineer" in variants

    def test_backend_engineer_synonyms(self):
        rules = [r for r in SYNONYM_RULES if r.input_pattern == "Backend Engineer"]
        assert len(rules) == 1
        variants = rules[0].output_variants
        assert "Backend Developer" in variants
        assert "Server Engineer" in variants

    def test_frontend_engineer_synonyms(self):
        rules = [r for r in SYNONYM_RULES if r.input_pattern == "Frontend Engineer"]
        assert len(rules) == 1
        variants = rules[0].output_variants
        assert "Frontend Developer" in variants
        assert "UI Engineer" in variants

    def test_data_scientist_synonyms(self):
        rules = [r for r in SYNONYM_RULES if r.input_pattern == "Data Scientist"]
        assert len(rules) == 1
        variants = rules[0].output_variants
        assert "Analytics Engineer" in variants

    def test_devops_engineer_synonyms(self):
        rules = [r for r in SYNONYM_RULES if r.input_pattern == "DevOps Engineer"]
        assert len(rules) == 1
        variants = rules[0].output_variants
        assert "Site Reliability Engineer" in variants
        assert "SRE" in variants
        assert "Platform Engineer" in variants
        assert "Infrastructure Engineer" in variants

    def test_full_stack_synonyms(self):
        rules = [r for r in SYNONYM_RULES if r.input_pattern == "Full Stack"]
        assert len(rules) == 1
        variants = rules[0].output_variants
        assert "Fullstack" in variants
        assert "Full-Stack" in variants

    def test_no_duplicate_input_patterns(self):
        patterns = [r.input_pattern for r in SYNONYM_RULES]
        assert len(patterns) == len(set(patterns))


class TestSeniorityRules:
    """Tests for the built-in seniority rules."""

    def test_single_wildcard_rule(self):
        assert len(SENIORITY_RULES) == 1
        assert SENIORITY_RULES[0].input_pattern == "*"

    def test_priority_20(self):
        assert SENIORITY_RULES[0].priority == 20

    def test_seniority_prefixes_content(self):
        assert "" in SENIORITY_PREFIXES, "Empty prefix (no seniority) must be included"
        assert "Senior" in SENIORITY_PREFIXES
        assert "Staff" in SENIORITY_PREFIXES
        assert "Principal" in SENIORITY_PREFIXES
        assert "Lead" in SENIORITY_PREFIXES

    def test_empty_prefix_is_first(self):
        assert SENIORITY_PREFIXES[0] == "", "Empty prefix should be first"


class TestSkillRules:
    """Tests for the built-in skill rules."""

    def test_all_are_skill_type(self):
        for rule in SKILL_RULES:
            assert rule.rule_type == "skill"

    def test_all_have_priority_30(self):
        for rule in SKILL_RULES:
            assert rule.priority == 30

    def test_python_skills(self):
        rules = [r for r in SKILL_RULES if r.input_pattern == "Python"]
        assert len(rules) == 1
        variants = rules[0].output_variants
        assert "Python" in variants
        assert "Django" in variants
        assert "FastAPI" in variants
        assert "Flask" in variants

    def test_javascript_skills(self):
        rules = [r for r in SKILL_RULES if r.input_pattern == "JavaScript"]
        assert len(rules) == 1
        variants = rules[0].output_variants
        assert "TypeScript" in variants
        assert "React" in variants
        assert "Node.js" in variants

    def test_ml_skills(self):
        rules = [r for r in SKILL_RULES if r.input_pattern == "ML"]
        assert len(rules) == 1
        variants = rules[0].output_variants
        assert "Machine Learning" in variants
        assert "Deep Learning" in variants
        assert "NLP" in variants
        assert "Computer Vision" in variants


class TestGetAllDefaultRules:
    """Tests for get_all_default_rules()."""

    def test_returns_all_rules(self):
        all_rules = get_all_default_rules()
        expected_count = len(SYNONYM_RULES) + len(SENIORITY_RULES) + len(SKILL_RULES)
        assert len(all_rules) == expected_count

    def test_sorted_by_priority(self):
        all_rules = get_all_default_rules()
        priorities = [r.priority for r in all_rules]
        assert priorities == sorted(priorities), "Rules must be sorted by priority ascending"

    def test_synonyms_first(self):
        all_rules = get_all_default_rules()
        # Synonym rules (priority 10) should come first
        first_rule = all_rules[0]
        assert first_rule.priority == 10

    def test_skills_last(self):
        all_rules = get_all_default_rules()
        last_rule = all_rules[-1]
        assert last_rule.priority == 30


class TestGetSynonymMap:
    """Tests for get_synonym_map()."""

    def test_returns_dict(self):
        result = get_synonym_map()
        assert isinstance(result, dict)

    def test_keys_are_lowercase(self):
        result = get_synonym_map()
        for key in result.keys():
            assert key == key.lower()

    def test_ml_engineer_present(self):
        result = get_synonym_map()
        assert "ml engineer" in result
        assert "Machine Learning Engineer" in result["ml engineer"]

    def test_count_matches_rules(self):
        result = get_synonym_map()
        assert len(result) == len(SYNONYM_RULES)


class TestGetSkillMap:
    """Tests for get_skill_map()."""

    def test_returns_dict(self):
        result = get_skill_map()
        assert isinstance(result, dict)

    def test_keys_are_lowercase(self):
        result = get_skill_map()
        for key in result.keys():
            assert key == key.lower()

    def test_python_present(self):
        result = get_skill_map()
        assert "python" in result
        assert "Django" in result["python"]

    def test_count_matches_rules(self):
        result = get_skill_map()
        assert len(result) == len(SKILL_RULES)
