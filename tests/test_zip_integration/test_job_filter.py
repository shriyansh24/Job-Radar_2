"""Test declarative job filter DSL."""
import pytest
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from backend.adapters.job_filter import JobFilter


@dataclass
class MockJob:
    title: str = "Software Engineer"
    title_normalized: str = "software engineer"
    description_plain: str = "Build web apps with Python and React"
    location: str = "San Francisco, CA"
    location_normalized: str = "san francisco, ca"
    remote_type: str = "hybrid"
    employment_type: str = "full_time"
    seniority_level: str = "mid"
    salary_min: float = 100000
    salary_max: float = 150000
    posted_at: datetime = None
    company: str = "Acme Corp"
    company_normalized: str = "acme corp"
    tech_stack: list = None
    match_score: float = 85

    def __post_init__(self):
        if self.tech_stack is None:
            self.tech_stack = ["Python", "React"]
        if self.posted_at is None:
            self.posted_at = datetime.utcnow()


# ---------------------------------------------------------------------------
# Keyword tests
# ---------------------------------------------------------------------------

class TestJobFilterKeywords:
    def test_include_keyword_passes(self):
        f = JobFilter(keywords_include=["python"])
        passes, reasons = f.evaluate(MockJob())
        assert passes

    def test_include_keyword_fails(self):
        f = JobFilter(keywords_include=["golang"])
        passes, reasons = f.evaluate(MockJob())
        assert not passes
        assert any("missing_keyword" in r for r in reasons)

    def test_exclude_keyword_blocks(self):
        f = JobFilter(keywords_exclude=["python"])
        passes, reasons = f.evaluate(MockJob())
        assert not passes

    def test_include_any_passes_with_one(self):
        f = JobFilter(keywords_include_any=["golang", "react"])
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_include_any_fails_when_none_match(self):
        f = JobFilter(keywords_include_any=["golang", "rust"])
        passes, reasons = f.evaluate(MockJob())
        assert not passes
        assert any("no_matching_keyword_any" in r for r in reasons)

    def test_include_all_keywords_must_all_be_present(self):
        f = JobFilter(keywords_include=["python", "react"])
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_include_fails_when_one_missing(self):
        f = JobFilter(keywords_include=["python", "golang"])
        passes, reasons = f.evaluate(MockJob())
        assert not passes
        assert any("missing_keyword" in r for r in reasons)

    def test_multiple_excludes_any_triggers(self):
        f = JobFilter(keywords_exclude=["java", "python"])
        passes, _ = f.evaluate(MockJob())
        assert not passes

    def test_exclude_not_present_passes(self):
        f = JobFilter(keywords_exclude=["golang"])
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_empty_filter_always_passes(self):
        f = JobFilter()
        passes, reasons = f.evaluate(MockJob())
        assert passes
        assert reasons == []

    def test_keyword_match_in_title(self):
        # "engineer" is in the title but not the description
        f = JobFilter(keywords_include=["engineer"])
        job = MockJob(description_plain="Build things.")
        passes, _ = f.evaluate(job)
        assert passes

    def test_keyword_word_boundary(self):
        # "go" should NOT match inside "golang"
        f = JobFilter(keywords_include=["go"])
        job = MockJob(description_plain="We use golang every day")
        passes, _ = f.evaluate(job)
        assert not passes

    def test_reason_contains_term(self):
        f = JobFilter(keywords_include=["haskell"])
        _, reasons = f.evaluate(MockJob())
        assert any("haskell" in r for r in reasons)


# ---------------------------------------------------------------------------
# Salary tests
# ---------------------------------------------------------------------------

class TestJobFilterSalary:
    def test_salary_min_passes(self):
        f = JobFilter(salary_min=90000)
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_salary_min_fails(self):
        f = JobFilter(salary_min=200000)
        passes, reasons = f.evaluate(MockJob())
        assert not passes
        assert any("salary_below_min" in r for r in reasons)

    def test_salary_max_passes(self):
        f = JobFilter(salary_max=200000)
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_salary_max_fails(self):
        f = JobFilter(salary_max=100000)
        passes, reasons = f.evaluate(MockJob())
        # salary_max of job is 150_000 which is > filter 100_000
        assert not passes
        assert any("salary_above_max" in r for r in reasons)

    def test_no_salary_data_permissive_by_default(self):
        f = JobFilter(salary_min=80000)
        job = MockJob(salary_min=None, salary_max=None)
        passes, _ = f.evaluate(job)
        assert passes  # no data → pass silently

    def test_require_salary_data_rejects_missing(self):
        f = JobFilter(salary_min=80000, require_salary_data=True)
        job = MockJob(salary_min=None, salary_max=None)
        passes, reasons = f.evaluate(job)
        assert not passes
        assert any("no_salary_data" in r for r in reasons)

    def test_salary_range_both_pass(self):
        f = JobFilter(salary_min=80000, salary_max=200000)
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_only_salary_min_on_job(self):
        # salary_max is None; salary_min is 120_000
        f = JobFilter(salary_min=100000)
        job = MockJob(salary_min=120000, salary_max=None)
        passes, _ = f.evaluate(job)
        assert passes


# ---------------------------------------------------------------------------
# Location tests
# ---------------------------------------------------------------------------

class TestJobFilterLocation:
    def test_location_match_passes(self):
        f = JobFilter(locations_include=["san francisco"])
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_location_mismatch_fails(self):
        f = JobFilter(locations_include=["new york"])
        passes, reasons = f.evaluate(MockJob())
        assert not passes
        assert any("location_mismatch" in r for r in reasons)

    def test_multiple_locations_any_match_passes(self):
        f = JobFilter(locations_include=["new york", "san francisco"])
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_empty_locations_passes(self):
        f = JobFilter(locations_include=[])
        passes, _ = f.evaluate(MockJob())
        assert passes


# ---------------------------------------------------------------------------
# Remote type tests
# ---------------------------------------------------------------------------

class TestJobFilterRemoteType:
    def test_remote_type_match_passes(self):
        f = JobFilter(remote_types=["hybrid"])
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_remote_type_mismatch_fails(self):
        f = JobFilter(remote_types=["remote"])
        passes, reasons = f.evaluate(MockJob())
        assert not passes
        assert any("remote_type_mismatch" in r for r in reasons)

    def test_multiple_remote_types_match(self):
        f = JobFilter(remote_types=["remote", "hybrid"])
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_remote_type_case_insensitive(self):
        f = JobFilter(remote_types=["HYBRID"])
        passes, _ = f.evaluate(MockJob())
        assert passes


# ---------------------------------------------------------------------------
# Employment type tests
# ---------------------------------------------------------------------------

class TestJobFilterEmploymentType:
    def test_employment_type_match_passes(self):
        f = JobFilter(employment_types=["full_time"])
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_employment_type_mismatch_fails(self):
        f = JobFilter(employment_types=["contract"])
        passes, reasons = f.evaluate(MockJob())
        assert not passes
        assert any("employment_type_mismatch" in r for r in reasons)


# ---------------------------------------------------------------------------
# Seniority tests
# ---------------------------------------------------------------------------

class TestJobFilterSeniority:
    def test_seniority_match_passes(self):
        f = JobFilter(seniority_levels=["mid"])
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_seniority_mismatch_fails(self):
        f = JobFilter(seniority_levels=["senior"])
        passes, reasons = f.evaluate(MockJob())
        assert not passes
        assert any("seniority_mismatch" in r for r in reasons)

    def test_multiple_seniority_levels(self):
        f = JobFilter(seniority_levels=["mid", "senior"])
        passes, _ = f.evaluate(MockJob())
        assert passes


# ---------------------------------------------------------------------------
# Tech stack tests
# ---------------------------------------------------------------------------

class TestJobFilterTechStack:
    def test_tech_all_passes(self):
        f = JobFilter(tech_stack_all=["Python"])
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_tech_all_fails(self):
        f = JobFilter(tech_stack_all=["Python", "Rust"])
        passes, reasons = f.evaluate(MockJob())
        assert not passes
        assert any("tech_stack_missing_required" in r for r in reasons)

    def test_tech_all_multiple_present(self):
        f = JobFilter(tech_stack_all=["Python", "React"])
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_tech_any_passes_with_one(self):
        f = JobFilter(tech_stack_any=["Python", "Rust"])
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_tech_any_fails_none_present(self):
        f = JobFilter(tech_stack_any=["Rust", "Zig"])
        passes, reasons = f.evaluate(MockJob())
        assert not passes
        assert any("tech_stack_no_match_any" in r for r in reasons)

    def test_tech_all_case_insensitive(self):
        f = JobFilter(tech_stack_all=["python"])
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_tech_stack_none_passes_all_checks(self):
        # Job has no tech_stack; filter with empty lists passes
        f = JobFilter()
        job = MockJob(tech_stack=None)
        passes, _ = f.evaluate(job)
        assert passes


# ---------------------------------------------------------------------------
# Company exclusion tests
# ---------------------------------------------------------------------------

class TestJobFilterCompanyExclude:
    def test_excluded_company_fails(self):
        f = JobFilter(companies_exclude=["acme"])
        passes, reasons = f.evaluate(MockJob())
        assert not passes
        assert any("company_excluded" in r for r in reasons)

    def test_non_excluded_company_passes(self):
        f = JobFilter(companies_exclude=["megacorp"])
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_company_exclusion_case_insensitive(self):
        f = JobFilter(companies_exclude=["ACME"])
        passes, _ = f.evaluate(MockJob())
        assert not passes


# ---------------------------------------------------------------------------
# Posted-within tests
# ---------------------------------------------------------------------------

class TestJobFilterPostedWithin:
    def test_recent_job_passes(self):
        f = JobFilter(posted_within_days=7)
        job = MockJob(posted_at=datetime.utcnow())
        passes, _ = f.evaluate(job)
        assert passes

    def test_old_job_fails(self):
        f = JobFilter(posted_within_days=7)
        old_dt = datetime.utcnow() - timedelta(days=30)
        job = MockJob(posted_at=old_dt)
        passes, reasons = f.evaluate(job)
        assert not passes
        assert any("posted_too_old" in r for r in reasons)

    def test_no_posted_at_passes_permissively(self):
        f = JobFilter(posted_within_days=7)
        job = MockJob(posted_at=None)
        passes, _ = f.evaluate(job)
        assert passes

    def test_timezone_aware_posted_at(self):
        f = JobFilter(posted_within_days=7)
        job = MockJob(posted_at=datetime.now(timezone.utc))
        passes, _ = f.evaluate(job)
        assert passes


# ---------------------------------------------------------------------------
# Match score tests
# ---------------------------------------------------------------------------

class TestJobFilterMatchScore:
    def test_score_above_min_passes(self):
        f = JobFilter(min_match_score=80)
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_score_below_min_fails(self):
        f = JobFilter(min_match_score=90)
        passes, reasons = f.evaluate(MockJob())
        assert not passes
        assert any("match_score_below_min" in r for r in reasons)

    def test_no_score_passes_permissively(self):
        f = JobFilter(min_match_score=80)
        job = MockJob(match_score=None)
        passes, _ = f.evaluate(job)
        assert passes


# ---------------------------------------------------------------------------
# from_dict tests
# ---------------------------------------------------------------------------

class TestJobFilterFromDict:
    def test_from_dict_creates_filter(self):
        f = JobFilter.from_dict({"keywords_include": ["python"], "salary_min": 100000})
        assert f.keywords_include == ["python"]
        assert f.salary_min == 100000

    def test_from_dict_empty(self):
        f = JobFilter.from_dict({})
        assert f.keywords_include == []

    def test_from_dict_unknown_keys_ignored(self):
        f = JobFilter.from_dict({"unknown_field": "value", "salary_min": 50000})
        assert f.salary_min == 50000

    def test_from_dict_all_supported_list_fields(self):
        f = JobFilter.from_dict({
            "keywords_include": ["python"],
            "keywords_exclude": ["php"],
            "keywords_include_any": ["react", "vue"],
            "tech_stack_all": ["python"],
            "tech_stack_any": ["react"],
            "locations_include": ["remote"],
            "remote_types": ["remote"],
            "employment_types": ["full_time"],
            "seniority_levels": ["mid"],
            "companies_exclude": ["badcorp"],
        })
        assert f.keywords_exclude == ["php"]
        assert f.tech_stack_all == ["python"]

    def test_from_dict_numeric_fields(self):
        f = JobFilter.from_dict({
            "salary_min": 80000,
            "salary_max": 200000,
            "min_match_score": 70,
            "posted_within_days": 14,
        })
        assert f.salary_max == 200000
        assert f.posted_within_days == 14


# ---------------------------------------------------------------------------
# filter_jobs tests
# ---------------------------------------------------------------------------

class TestFilterJobs:
    def test_filters_list(self):
        f = JobFilter(keywords_include=["python"])
        jobs = [
            MockJob(),
            MockJob(
                title="Go Developer",
                title_normalized="go developer",
                description_plain="Write Go code",
            ),
        ]
        result = f.filter_jobs(jobs)
        assert len(result) == 1

    def test_empty_list_returns_empty(self):
        f = JobFilter(keywords_include=["python"])
        assert f.filter_jobs([]) == []

    def test_all_pass(self):
        f = JobFilter()
        jobs = [MockJob(), MockJob()]
        assert len(f.filter_jobs(jobs)) == 2

    def test_none_pass(self):
        f = JobFilter(keywords_include=["cobol"])
        jobs = [MockJob(), MockJob()]
        assert f.filter_jobs(jobs) == []

    def test_multiple_criteria_combined(self):
        f = JobFilter(
            keywords_include=["python"],
            salary_min=90000,
            remote_types=["hybrid", "remote"],
            tech_stack_all=["Python"],
        )
        passes, reasons = f.evaluate(MockJob())
        assert passes
        assert reasons == []

    def test_combined_criteria_one_fails(self):
        f = JobFilter(
            keywords_include=["python"],
            salary_min=200000,  # will fail
        )
        passes, reasons = f.evaluate(MockJob())
        assert not passes
        assert any("salary_below_min" in r for r in reasons)

    def test_generator_input_accepted(self):
        f = JobFilter(keywords_include=["python"])
        gen = (MockJob() for _ in range(3))
        result = f.filter_jobs(gen)
        assert len(result) == 3
