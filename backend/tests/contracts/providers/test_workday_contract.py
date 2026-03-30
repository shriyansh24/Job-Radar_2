"""Contract tests for the Workday ATS parser.

Loads fixture data, runs it through WorkdayScraper._parse_response,
and validates that all outputs conform to ScrapedJob interface requirements.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

import pytest

from app.scraping.port import ScrapedJob
from app.scraping.scrapers.workday import WorkdayScraper

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "workday"
BASE_URL = "https://microsoft.wd5.myworkdayjobs.com"

# Valid enum values for ScrapedJob fields
VALID_REMOTE_TYPES = {None, "remote", "hybrid", "onsite"}
VALID_EXPERIENCE_LEVELS = {None, "entry", "mid", "senior", "lead", "executive"}
VALID_SALARY_PERIODS = {None, "annual", "hourly", "monthly"}


def load_fixture() -> dict:
    """Load the Workday XHR fixture file."""
    with open(FIXTURES / "microsoft_xhr.json") as f:
        return json.load(f)


def load_expected() -> list[dict]:
    """Load expected jobs for comparison."""
    path = FIXTURES / "expected_jobs.json"
    if not path.exists():
        pytest.skip("No expected_jobs.json found")
    with open(path) as f:
        return json.load(f)


def create_scraper() -> WorkdayScraper:
    """Create a WorkdayScraper instance bypassing __init__."""
    return WorkdayScraper.__new__(WorkdayScraper)


def parse_fixture() -> list[ScrapedJob]:
    """Parse the Workday fixture through the actual parser."""
    data = load_fixture()
    scraper = create_scraper()
    return scraper._parse_response(data, BASE_URL)


def _is_valid_url(url: str | None) -> bool:
    """Check that a URL is well-formed (has scheme and netloc)."""
    if url is None:
        return True
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)


class TestWorkdayFixtureStructure:
    """Verify the raw fixture data has the expected structure."""

    def test_fixture_loads(self):
        data = load_fixture()
        assert "jobPostings" in data
        assert "total" in data

    def test_fixture_has_postings(self):
        data = load_fixture()
        assert len(data["jobPostings"]) > 0

    def test_total_matches_posting_count(self):
        data = load_fixture()
        assert data["total"] == len(data["jobPostings"])

    def test_all_postings_have_title(self):
        data = load_fixture()
        for posting in data["jobPostings"]:
            assert "title" in posting and posting["title"], "Posting missing title"

    def test_all_postings_have_external_path(self):
        data = load_fixture()
        for posting in data["jobPostings"]:
            assert "externalPath" in posting and posting["externalPath"], (
                f"Posting missing externalPath: {posting.get('title', 'unknown')}"
            )


class TestWorkdayExpectedJobs:
    """Verify expected_jobs.json has required contract fields."""

    def test_expected_jobs_have_required_fields(self):
        expected = load_expected()
        for job in expected:
            assert "title" in job, f"Expected job missing title: {job}"
            assert "company_name" in job, f"Expected job missing company_name: {job}"
            assert "source" in job, f"Expected job missing source: {job}"

    def test_expected_jobs_source_is_workday(self):
        expected = load_expected()
        for job in expected:
            assert job["source"] == "workday", f"Expected job has wrong source: {job['source']}"

    def test_expected_jobs_match_fixture_count(self):
        data = load_fixture()
        expected = load_expected()
        assert len(expected) == len(data["jobPostings"]), (
            f"Expected {len(expected)} jobs but fixture has {len(data['jobPostings'])} postings"
        )


class TestWorkdayParserContract:
    """Run the actual parser on fixture data and validate ScrapedJob output."""

    def test_parser_produces_jobs(self):
        jobs = parse_fixture()
        assert len(jobs) > 0

    def test_parser_job_count_matches_fixture(self):
        data = load_fixture()
        jobs = parse_fixture()
        assert len(jobs) == len(data["jobPostings"])

    def test_parser_extracts_correct_jobs(self):
        """Run Workday parser on fixture and verify output matches expected."""
        jobs = parse_fixture()
        expected = load_expected()

        assert len(jobs) == len(expected)
        for job, exp in zip(jobs, expected):
            assert job.title == exp["title"], (
                f"Title mismatch: parsed={job.title}, expected={exp['title']}"
            )
            assert job.source == "workday"

    def test_all_jobs_have_title(self):
        jobs = parse_fixture()
        for job in jobs:
            assert job.title, "Job has empty title"

    def test_all_jobs_have_company_name(self):
        jobs = parse_fixture()
        for job in jobs:
            assert job.company_name, f"Job missing company_name: {job.title}"

    def test_all_jobs_have_source(self):
        jobs = parse_fixture()
        for job in jobs:
            assert job.source == "workday", f"Job has wrong source: {job.source}"

    def test_all_jobs_have_source_url(self):
        jobs = parse_fixture()
        for job in jobs:
            assert job.source_url, f"Job missing source_url: {job.title}"

    def test_no_malformed_urls(self):
        jobs = parse_fixture()
        for job in jobs:
            assert _is_valid_url(job.source_url), f"Malformed source_url: {job.source_url}"
            assert _is_valid_url(job.company_logo_url), (
                f"Malformed company_logo_url: {job.company_logo_url}"
            )

    def test_source_urls_contain_base_url(self):
        """Workday source URLs should start with the base URL."""
        jobs = parse_fixture()
        for job in jobs:
            assert job.source_url.startswith(BASE_URL), (
                f"source_url does not start with base URL: {job.source_url}"
            )

    def test_valid_remote_type_enum(self):
        jobs = parse_fixture()
        for job in jobs:
            assert job.remote_type in VALID_REMOTE_TYPES, f"Invalid remote_type: {job.remote_type}"

    def test_valid_experience_level_enum(self):
        jobs = parse_fixture()
        for job in jobs:
            assert job.experience_level in VALID_EXPERIENCE_LEVELS, (
                f"Invalid experience_level: {job.experience_level}"
            )

    def test_valid_salary_period_enum(self):
        jobs = parse_fixture()
        for job in jobs:
            assert job.salary_period in VALID_SALARY_PERIODS, (
                f"Invalid salary_period: {job.salary_period}"
            )

    def test_salary_consistency(self):
        """If salary_min and salary_max both present, min <= max."""
        jobs = parse_fixture()
        for job in jobs:
            if job.salary_min is not None and job.salary_max is not None:
                assert job.salary_min <= job.salary_max, (
                    f"salary_min ({job.salary_min}) > salary_max ({job.salary_max}) "
                    f"for job: {job.title}"
                )

    def test_company_name_extracted_from_url(self):
        """Company name should be extracted from the base URL tenant."""
        jobs = parse_fixture()
        for job in jobs:
            assert job.company_name == "microsoft", (
                f"Expected company 'microsoft' but got '{job.company_name}'"
            )

    def test_location_populated(self):
        """All fixture jobs should have a location."""
        jobs = parse_fixture()
        for job in jobs:
            assert job.location, f"Job missing location: {job.title}"

    def test_expected_job_titles_match(self):
        """All expected job titles should appear in parsed output."""
        jobs = parse_fixture()
        expected = load_expected()

        parsed_titles = [j.title for j in jobs]
        expected_titles = [e["title"] for e in expected]
        assert parsed_titles == expected_titles, (
            f"Title order mismatch: parsed={parsed_titles}, expected={expected_titles}"
        )

    def test_expected_job_locations_match(self):
        """Parsed job locations should match expected locations."""
        jobs = parse_fixture()
        expected = load_expected()

        for job, exp in zip(jobs, expected):
            if "location" in exp:
                assert job.location == exp["location"], (
                    f"Location mismatch for {job.title}: "
                    f"parsed={job.location}, expected={exp['location']}"
                )
