"""Contract tests for the Greenhouse ATS parser.

Loads fixture data, parses it using the same logic as GreenhouseScraper,
and validates that all outputs conform to ScrapedJob interface requirements.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pytest

from app.scraping.port import ScrapedJob
from app.scraping.scrapers.greenhouse import GreenhouseScraper

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "greenhouse"

# Valid enum values for ScrapedJob fields
VALID_REMOTE_TYPES = {None, "remote", "hybrid", "onsite"}
VALID_EXPERIENCE_LEVELS = {None, "entry", "mid", "senior", "lead", "executive"}
VALID_SALARY_PERIODS = {None, "annual", "hourly", "monthly"}


def load_fixture() -> dict:
    """Load the Greenhouse board fixture file."""
    fixture_path = next(FIXTURES.glob("*_board.json"), None)
    if fixture_path is None:
        pytest.skip("No greenhouse fixture found")
    with fixture_path.open() as fh:
        return json.load(fh)


def load_expected() -> list[dict]:
    """Load expected jobs for comparison."""
    path = FIXTURES / "expected_jobs.json"
    if not path.exists():
        pytest.skip("No expected_jobs.json found")
    with path.open() as f:
        return json.load(f)


def parse_fixture_to_scraped_jobs(data: dict, board_token: str = "gitlab") -> list[ScrapedJob]:
    """Parse Greenhouse fixture data into ScrapedJob objects.

    Replicates the parsing logic from GreenhouseScraper.fetch_jobs so
    contract tests can validate ScrapedJob output without async HTTP.
    """
    scraper = GreenhouseScraper.__new__(GreenhouseScraper)

    jobs: list[ScrapedJob] = []
    for item in data.get("jobs", []):
        loc = item.get("location", {}).get("name", "")

        posted_at = None
        if item.get("updated_at"):
            try:
                posted_at = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                posted_at = None

        # The fixture stores company_name at the top level; the real API
        # nests it under company.name.  Accept both formats.
        company = item.get("company", {}).get("name") or item.get("company_name") or board_token

        jobs.append(
            ScrapedJob(
                title=item.get("title", ""),
                company_name=company,
                source="greenhouse",
                source_url=item.get("absolute_url"),
                location=loc,
                remote_type=scraper._normalize_remote_type(loc),
                description_raw=item.get("content", ""),
                posted_at=posted_at,
            )
        )
    return jobs


def _is_valid_url(url: str | None) -> bool:
    """Check that a URL is well-formed (has scheme and netloc)."""
    if url is None:
        return True  # None is acceptable for optional URLs
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)


class TestGreenhouseFixtureStructure:
    """Verify the raw fixture data has the expected structure."""

    def test_fixture_loads(self):
        data = load_fixture()
        assert "jobs" in data
        assert len(data["jobs"]) > 0

    def test_all_jobs_have_title(self):
        data = load_fixture()
        for job in data["jobs"]:
            assert "title" in job and job["title"], (
                f"Job missing title: {job.get('id', 'unknown')}"
            )

    def test_all_jobs_have_location(self):
        data = load_fixture()
        for job in data["jobs"]:
            assert "location" in job, f"Job missing location key: {job.get('title', 'unknown')}"

    def test_all_jobs_have_absolute_url(self):
        data = load_fixture()
        for job in data["jobs"]:
            assert "absolute_url" in job and job["absolute_url"], (
                f"Job missing absolute_url: {job.get('title', 'unknown')}"
            )


class TestGreenhouseExpectedJobs:
    """Verify expected_jobs.json has required contract fields."""

    def test_expected_jobs_have_required_fields(self):
        expected = load_expected()
        for job in expected:
            assert "title" in job, f"Expected job missing title: {job}"
            assert "company_name" in job or "company" in job, (
                f"Expected job missing company: {job}"
            )
            assert "source" in job, f"Expected job missing source: {job}"

    def test_expected_jobs_source_is_greenhouse(self):
        expected = load_expected()
        for job in expected:
            assert job["source"] == "greenhouse", f"Expected job has wrong source: {job['source']}"

    def test_expected_jobs_have_urls(self):
        expected = load_expected()
        for job in expected:
            url = job.get("url") or job.get("source_url")
            assert url, f"Expected job missing URL: {job.get('title')}"
            assert _is_valid_url(url), f"Malformed URL: {url}"


class TestGreenhouseParserContract:
    """Run the parser on fixture data and validate ScrapedJob output."""

    def test_parser_produces_jobs(self):
        data = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(data)
        assert len(jobs) > 0

    def test_parser_job_count_matches_fixture(self):
        data = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(data)
        assert len(jobs) == len(data["jobs"])

    def test_all_jobs_have_title(self):
        data = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(data)
        for job in jobs:
            assert job.title, "Job has empty title"

    def test_all_jobs_have_company_name(self):
        data = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(data)
        for job in jobs:
            assert job.company_name, f"Job missing company_name: {job.title}"

    def test_all_jobs_have_source(self):
        data = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(data)
        for job in jobs:
            assert job.source == "greenhouse", f"Job has wrong source: {job.source}"

    def test_all_jobs_have_source_url(self):
        data = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(data)
        for job in jobs:
            assert job.source_url, f"Job missing source_url: {job.title}"

    def test_no_malformed_urls(self):
        data = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(data)
        for job in jobs:
            assert _is_valid_url(job.source_url), f"Malformed source_url: {job.source_url}"
            assert _is_valid_url(job.company_logo_url), (
                f"Malformed company_logo_url: {job.company_logo_url}"
            )

    def test_valid_remote_type_enum(self):
        data = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(data)
        for job in jobs:
            assert job.remote_type in VALID_REMOTE_TYPES, f"Invalid remote_type: {job.remote_type}"

    def test_valid_experience_level_enum(self):
        data = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(data)
        for job in jobs:
            assert job.experience_level in VALID_EXPERIENCE_LEVELS, (
                f"Invalid experience_level: {job.experience_level}"
            )

    def test_valid_salary_period_enum(self):
        data = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(data)
        for job in jobs:
            assert job.salary_period in VALID_SALARY_PERIODS, (
                f"Invalid salary_period: {job.salary_period}"
            )

    def test_salary_consistency(self):
        """If salary_min and salary_max both present, min <= max."""
        data = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(data)
        for job in jobs:
            if job.salary_min is not None and job.salary_max is not None:
                assert job.salary_min <= job.salary_max, (
                    f"salary_min ({job.salary_min}) > salary_max ({job.salary_max}) "
                    f"for job: {job.title}"
                )

    def test_matches_expected_jobs(self):
        """Parsed jobs should match expected_jobs.json on title and source."""
        data = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(data)
        expected = load_expected()

        # Build lookup by title for comparison
        parsed_titles = {j.title.strip() for j in jobs}
        for exp in expected:
            assert exp["title"] in parsed_titles, (
                f"Expected job title not found in parsed output: {exp['title']}"
            )

    def test_expected_job_urls_match(self):
        """Parsed job URLs should match expected URLs."""
        data = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(data)
        expected = load_expected()

        parsed_by_title = {j.title.strip(): j for j in jobs}
        for exp in expected:
            title = exp["title"]
            if title in parsed_by_title:
                parsed_job = parsed_by_title[title]
                exp_url = exp.get("url") or exp.get("source_url")
                if exp_url:
                    assert parsed_job.source_url == exp_url, (
                        f"URL mismatch for {title}: "
                        f"parsed={parsed_job.source_url}, expected={exp_url}"
                    )
