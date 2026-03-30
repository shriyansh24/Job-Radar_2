from __future__ import annotations

from types import SimpleNamespace

from app.auto_apply.engine import RuleEngine


def make_job(**kwargs):
    """Create a mock job object for testing."""
    defaults = {
        "id": "job-1",
        "title": "Software Engineer",
        "company_name": "Acme Corp",
        "description_clean": "Build web applications with Python and React",
        "match_score": 85,
        "experience_level": "mid",
        "remote_type": "remote",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_rule(**kwargs):
    """Create a mock rule object for testing."""
    defaults = {
        "id": "rule-1",
        "priority": 0,
        "is_active": True,
        "min_match_score": None,
        "required_keywords": None,
        "excluded_keywords": None,
        "required_companies": None,
        "excluded_companies": None,
        "experience_levels": None,
        "remote_types": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestRuleEngine:
    """Test the rule engine matching logic."""

    def setup_method(self):
        self.engine = RuleEngine()

    def test_match_all_when_no_criteria(self) -> None:
        """A rule with no criteria matches all jobs."""
        jobs = [make_job()]
        rules = [make_rule()]
        matches = self.engine.match_jobs(jobs, rules)
        assert len(matches) == 1
        assert matches[0][0].id == "job-1"

    def test_no_rules_returns_empty(self) -> None:
        jobs = [make_job()]
        matches = self.engine.match_jobs(jobs, [])
        assert matches == []

    def test_no_jobs_returns_empty(self) -> None:
        rules = [make_rule()]
        matches = self.engine.match_jobs([], rules)
        assert matches == []

    def test_min_match_score_pass(self) -> None:
        jobs = [make_job(match_score=90)]
        rules = [make_rule(min_match_score=80)]
        matches = self.engine.match_jobs(jobs, rules)
        assert len(matches) == 1

    def test_min_match_score_fail(self) -> None:
        jobs = [make_job(match_score=50)]
        rules = [make_rule(min_match_score=80)]
        matches = self.engine.match_jobs(jobs, rules)
        assert len(matches) == 0

    def test_min_match_score_none_job(self) -> None:
        """Job with no score should fail min_match_score check."""
        jobs = [make_job(match_score=None)]
        rules = [make_rule(min_match_score=80)]
        matches = self.engine.match_jobs(jobs, rules)
        assert len(matches) == 0

    def test_required_keywords_match(self) -> None:
        jobs = [make_job(title="Senior Python Developer")]
        rules = [make_rule(required_keywords=["python", "java"])]
        matches = self.engine.match_jobs(jobs, rules)
        assert len(matches) == 1

    def test_required_keywords_no_match(self) -> None:
        jobs = [make_job(title="Marketing Manager", description_clean="marketing role")]
        rules = [make_rule(required_keywords=["python", "java"])]
        matches = self.engine.match_jobs(jobs, rules)
        assert len(matches) == 0

    def test_excluded_keywords_blocks(self) -> None:
        jobs = [make_job(title="Senior Engineer", description_clean="Must have 10 years")]
        rules = [make_rule(excluded_keywords=["senior"])]
        matches = self.engine.match_jobs(jobs, rules)
        assert len(matches) == 0

    def test_excluded_keywords_allows(self) -> None:
        jobs = [make_job(title="Junior Engineer")]
        rules = [make_rule(excluded_keywords=["senior", "staff"])]
        matches = self.engine.match_jobs(jobs, rules)
        assert len(matches) == 1

    def test_required_companies_match(self) -> None:
        jobs = [make_job(company_name="Google Inc")]
        rules = [make_rule(required_companies=["Google"])]
        matches = self.engine.match_jobs(jobs, rules)
        assert len(matches) == 1

    def test_required_companies_no_match(self) -> None:
        jobs = [make_job(company_name="Acme Corp")]
        rules = [make_rule(required_companies=["Google"])]
        matches = self.engine.match_jobs(jobs, rules)
        assert len(matches) == 0

    def test_excluded_companies_blocks(self) -> None:
        jobs = [make_job(company_name="Evil Corp")]
        rules = [make_rule(excluded_companies=["Evil"])]
        matches = self.engine.match_jobs(jobs, rules)
        assert len(matches) == 0

    def test_experience_levels_match(self) -> None:
        jobs = [make_job(experience_level="mid")]
        rules = [make_rule(experience_levels=["mid", "senior"])]
        matches = self.engine.match_jobs(jobs, rules)
        assert len(matches) == 1

    def test_experience_levels_no_match(self) -> None:
        jobs = [make_job(experience_level="junior")]
        rules = [make_rule(experience_levels=["mid", "senior"])]
        matches = self.engine.match_jobs(jobs, rules)
        assert len(matches) == 0

    def test_experience_levels_none_passes(self) -> None:
        """Job with no experience_level should pass experience filter."""
        jobs = [make_job(experience_level=None)]
        rules = [make_rule(experience_levels=["mid", "senior"])]
        matches = self.engine.match_jobs(jobs, rules)
        assert len(matches) == 1

    def test_remote_types_match(self) -> None:
        jobs = [make_job(remote_type="remote")]
        rules = [make_rule(remote_types=["remote", "hybrid"])]
        matches = self.engine.match_jobs(jobs, rules)
        assert len(matches) == 1

    def test_remote_types_no_match(self) -> None:
        jobs = [make_job(remote_type="onsite")]
        rules = [make_rule(remote_types=["remote", "hybrid"])]
        matches = self.engine.match_jobs(jobs, rules)
        assert len(matches) == 0

    def test_priority_ordering(self) -> None:
        """Highest priority rule should match first."""
        job = make_job(match_score=90)
        low = make_rule(id="low", priority=1, min_match_score=50)
        high = make_rule(id="high", priority=10, min_match_score=80)
        matches = self.engine.match_jobs([job], [low, high])
        assert len(matches) == 1
        assert matches[0][1].id == "high"

    def test_first_match_wins(self) -> None:
        """Only the first matching rule (by priority) is used per job."""
        job = make_job()
        rule1 = make_rule(id="r1", priority=10)
        rule2 = make_rule(id="r2", priority=5)
        matches = self.engine.match_jobs([job], [rule1, rule2])
        assert len(matches) == 1
        assert matches[0][1].id == "r1"

    def test_multiple_jobs_multiple_rules(self) -> None:
        """Each job gets matched to its best rule independently."""
        jobs = [
            make_job(id="j1", company_name="Google"),
            make_job(id="j2", company_name="Meta"),
        ]
        google_rule = make_rule(id="google", priority=5, required_companies=["Google"])
        catch_all = make_rule(id="catchall", priority=1)
        matches = self.engine.match_jobs(jobs, [catch_all, google_rule])
        assert len(matches) == 2
        match_map = {m[0].id: m[1].id for m in matches}
        assert match_map["j1"] == "google"
        assert match_map["j2"] == "catchall"

    def test_combined_criteria(self) -> None:
        """Test a rule with multiple criteria that all must pass."""
        job = make_job(
            match_score=90,
            title="Senior Python Developer",
            company_name="Google",
            experience_level="senior",
            remote_type="remote",
        )
        rule = make_rule(
            min_match_score=80,
            required_keywords=["python"],
            excluded_keywords=["junior"],
            required_companies=["Google"],
            experience_levels=["senior"],
            remote_types=["remote"],
        )
        matches = self.engine.match_jobs([job], [rule])
        assert len(matches) == 1

    def test_combined_criteria_one_fails(self) -> None:
        """If any single criterion fails, the whole rule fails."""
        job = make_job(
            match_score=90,
            title="Senior Python Developer",
            company_name="Google",
            experience_level="junior",  # Doesn't match
            remote_type="remote",
        )
        rule = make_rule(
            min_match_score=80,
            required_keywords=["python"],
            experience_levels=["senior"],
        )
        matches = self.engine.match_jobs([job], [rule])
        assert len(matches) == 0
