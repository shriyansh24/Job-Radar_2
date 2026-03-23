"""Contract tests for the Lever ATS parser.

Loads fixture data, parses it using the same logic as LeverScraper,
and validates that all outputs conform to ScrapedJob interface requirements.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

import pytest

from app.scraping.port import ScrapedJob
from app.scraping.scrapers.lever import LeverScraper

FIXTURES = Path(__file__).parent.parent / "fixtures" / "lever"

# Valid enum values for ScrapedJob fields
VALID_REMOTE_TYPES = {None, "remote", "hybrid", "onsite"}
VALID_EXPERIENCE_LEVELS = {None, "entry", "mid", "senior", "lead", "executive"}
VALID_SALARY_PERIODS = {None, "annual", "hourly", "monthly"}


def load_fixture() -> list[dict]:
    """Load the Lever postings fixture file."""
    for f in FIXTURES.glob("*_postings.json"):
        with open(f) as fh:
            return json.load(fh)
    pytest.skip("No lever fixture found")


def load_expected() -> list[dict]:
    """Load expected jobs for comparison."""
    path = FIXTURES / "expected_jobs.json"
    if not path.exists():
        pytest.skip("No expected_jobs.json found")
    with open(path) as f:
        return json.load(f)


def parse_fixture_to_scraped_jobs(
    postings: list[dict], company_slug: str = "plaid"
) -> list[ScrapedJob]:
    """Parse Lever fixture data into ScrapedJob objects.

    Replicates the parsing logic from LeverScraper.fetch_jobs so
    contract tests can validate ScrapedJob output without async HTTP.
    """
    scraper = LeverScraper.__new__(LeverScraper)

    jobs: list[ScrapedJob] = []
    for item in postings:
        cats = item.get("categories", {})
        jobs.append(
            ScrapedJob(
                title=item.get("text", ""),
                company_name=company_slug,
                source="lever",
                source_url=item.get("hostedUrl"),
                location=cats.get("location", ""),
                remote_type=scraper._normalize_remote_type(cats.get("location", "")),
                description_raw=item.get("descriptionPlain", ""),
                experience_level=scraper._normalize_experience(cats.get("commitment")),
                job_type=cats.get("commitment"),
            )
        )
    return jobs


def _is_valid_url(url: str | None) -> bool:
    """Check that a URL is well-formed (has scheme and netloc)."""
    if url is None:
        return True
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)


class TestLeverFixtureStructure:
    """Verify the raw fixture data has the expected structure."""

    def test_fixture_loads(self):
        data = load_fixture()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_all_postings_have_text(self):
        data = load_fixture()
        for posting in data:
            assert "text" in posting and posting["text"], (
                f"Posting missing text: {posting.get('id', 'unknown')}"
            )

    def test_all_postings_have_categories(self):
        data = load_fixture()
        for posting in data:
            assert "categories" in posting, (
                f"Posting missing categories: {posting.get('text', 'unknown')}"
            )

    def test_all_postings_have_hosted_url(self):
        data = load_fixture()
        for posting in data:
            assert "hostedUrl" in posting and posting["hostedUrl"], (
                f"Posting missing hostedUrl: {posting.get('text', 'unknown')}"
            )

    def test_all_postings_have_id(self):
        data = load_fixture()
        for posting in data:
            assert "id" in posting and posting["id"], (
                f"Posting missing id: {posting.get('text', 'unknown')}"
            )


class TestLeverExpectedJobs:
    """Verify expected_jobs.json has required contract fields."""

    def test_expected_jobs_have_required_fields(self):
        expected = load_expected()
        for job in expected:
            assert "title" in job, f"Expected job missing title: {job}"
            assert "source" in job, f"Expected job missing source: {job}"

    def test_expected_jobs_source_is_lever(self):
        expected = load_expected()
        for job in expected:
            assert job["source"] == "lever", f"Expected job has wrong source: {job['source']}"

    def test_expected_jobs_have_urls(self):
        expected = load_expected()
        for job in expected:
            url = job.get("url") or job.get("source_url")
            assert url, f"Expected job missing URL: {job.get('title')}"
            assert _is_valid_url(url), f"Malformed URL: {url}"


class TestLeverParserContract:
    """Run the parser on fixture data and validate ScrapedJob output."""

    def test_parser_produces_jobs(self):
        postings = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(postings)
        assert len(jobs) > 0

    def test_parser_job_count_matches_fixture(self):
        postings = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(postings)
        assert len(jobs) == len(postings)

    def test_all_jobs_have_title(self):
        postings = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(postings)
        for job in jobs:
            assert job.title, "Job has empty title"

    def test_all_jobs_have_company_name(self):
        postings = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(postings)
        for job in jobs:
            assert job.company_name, f"Job missing company_name: {job.title}"

    def test_all_jobs_have_source(self):
        postings = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(postings)
        for job in jobs:
            assert job.source == "lever", f"Job has wrong source: {job.source}"

    def test_all_jobs_have_source_url(self):
        postings = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(postings)
        for job in jobs:
            assert job.source_url, f"Job missing source_url: {job.title}"

    def test_no_malformed_urls(self):
        postings = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(postings)
        for job in jobs:
            assert _is_valid_url(job.source_url), f"Malformed source_url: {job.source_url}"
            assert _is_valid_url(job.company_logo_url), (
                f"Malformed company_logo_url: {job.company_logo_url}"
            )

    def test_valid_remote_type_enum(self):
        postings = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(postings)
        for job in jobs:
            assert job.remote_type in VALID_REMOTE_TYPES, f"Invalid remote_type: {job.remote_type}"

    def test_valid_experience_level_enum(self):
        postings = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(postings)
        for job in jobs:
            assert job.experience_level in VALID_EXPERIENCE_LEVELS, (
                f"Invalid experience_level: {job.experience_level}"
            )

    def test_valid_salary_period_enum(self):
        postings = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(postings)
        for job in jobs:
            assert job.salary_period in VALID_SALARY_PERIODS, (
                f"Invalid salary_period: {job.salary_period}"
            )

    def test_salary_consistency(self):
        """If salary_min and salary_max both present, min <= max."""
        postings = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(postings)
        for job in jobs:
            if job.salary_min is not None and job.salary_max is not None:
                assert job.salary_min <= job.salary_max, (
                    f"salary_min ({job.salary_min}) > salary_max ({job.salary_max}) "
                    f"for job: {job.title}"
                )

    def test_matches_expected_jobs(self):
        """Parsed jobs should match expected_jobs.json on title and source."""
        postings = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(postings)
        expected = load_expected()

        parsed_by_url = {j.source_url: j for j in jobs}
        for exp in expected:
            exp_url = exp.get("url") or exp.get("source_url")
            assert exp_url in parsed_by_url, (
                f"Expected job URL not found in parsed output: {exp_url}"
            )

    def test_expected_job_titles_match(self):
        """Parsed job titles should match expected titles."""
        postings = load_fixture()
        jobs = parse_fixture_to_scraped_jobs(postings)
        expected = load_expected()

        parsed_by_url = {j.source_url: j for j in jobs}
        for exp in expected:
            exp_url = exp.get("url") or exp.get("source_url")
            if exp_url in parsed_by_url:
                parsed_job = parsed_by_url[exp_url]
                assert parsed_job.title == exp["title"], (
                    f"Title mismatch: parsed={parsed_job.title}, expected={exp['title']}"
                )

    def test_lever_salary_data_from_fixture(self):
        """Lever postings may include salaryRange; verify it parses correctly."""
        postings = load_fixture()
        for posting in postings:
            salary = posting.get("salaryRange")
            if salary:
                sal_min = salary.get("min")
                sal_max = salary.get("max")
                if sal_min is not None and sal_max is not None:
                    assert sal_min <= sal_max, (
                        f"Fixture salary_min ({sal_min}) > salary_max ({sal_max}) "
                        f"in posting: {posting.get('text')}"
                    )
