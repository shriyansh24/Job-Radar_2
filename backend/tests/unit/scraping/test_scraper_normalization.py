from __future__ import annotations

import pytest

from app.config import Settings
from app.scraping.port import ScrapedJob
from app.scraping.scrapers.base import BaseScraper


class ConcreteScraper(BaseScraper):
    """Concrete subclass for testing base class methods."""

    @property
    def source_name(self) -> str:
        return "test"

    async def fetch_jobs(
        self, query: str, location: str | None = None, limit: int = 50
    ) -> list[ScrapedJob]:
        return []

    async def health_check(self) -> bool:
        return True


@pytest.fixture
def scraper():
    settings = Settings(
        database_url="sqlite+aiosqlite:///test.db",
        serpapi_api_key="",
        theirstack_api_key="",
        apify_api_key="",
    )
    return ConcreteScraper(settings)


class TestNormalizeRemoteType:
    def test_remote_keywords(self, scraper):
        assert scraper._normalize_remote_type("Remote") == "remote"
        assert scraper._normalize_remote_type("Work from home") == "remote"
        assert scraper._normalize_remote_type("WFH") == "remote"
        assert scraper._normalize_remote_type("Anywhere") == "remote"

    def test_hybrid(self, scraper):
        assert scraper._normalize_remote_type("Hybrid - NYC") == "hybrid"

    def test_onsite(self, scraper):
        assert scraper._normalize_remote_type("New York, NY") == "onsite"
        assert scraper._normalize_remote_type("San Francisco Office") == "onsite"

    def test_none(self, scraper):
        assert scraper._normalize_remote_type(None) is None
        assert scraper._normalize_remote_type("") is None


class TestNormalizeExperience:
    def test_entry_level(self, scraper):
        assert scraper._normalize_experience("Entry Level") == "entry"
        assert scraper._normalize_experience("Junior Developer") == "entry"
        assert scraper._normalize_experience("Associate Engineer") == "entry"
        assert scraper._normalize_experience("Internship") == "entry"

    def test_mid_level(self, scraper):
        assert scraper._normalize_experience("Mid-Level") == "mid"
        assert scraper._normalize_experience("Intermediate") == "mid"

    def test_senior_level(self, scraper):
        assert scraper._normalize_experience("Senior Engineer") == "senior"
        assert scraper._normalize_experience("Sr. Developer") == "senior"

    def test_lead_level(self, scraper):
        assert scraper._normalize_experience("Lead Engineer") == "lead"
        assert scraper._normalize_experience("Principal Engineer") == "lead"
        assert scraper._normalize_experience("Staff Engineer") == "lead"

    def test_executive(self, scraper):
        assert scraper._normalize_experience("Director of Engineering") == "executive"
        assert scraper._normalize_experience("VP Engineering") == "executive"
        assert scraper._normalize_experience("Chief Technology Officer") == "executive"

    def test_default_mid(self, scraper):
        assert scraper._normalize_experience("Full-time") == "mid"

    def test_none(self, scraper):
        assert scraper._normalize_experience(None) is None


class TestExtractSalary:
    def test_k_range(self, scraper):
        sal_min, sal_max, period = scraper._extract_salary("$120k-$150k")
        assert sal_min == 120000
        assert sal_max == 150000
        assert period == "annual"

    def test_full_range(self, scraper):
        sal_min, sal_max, period = scraper._extract_salary("$120,000 - $150,000")
        assert sal_min == 120000
        assert sal_max == 150000
        assert period == "annual"

    def test_hourly(self, scraper):
        sal_min, sal_max, period = scraper._extract_salary("$50/hr")
        assert sal_min == 50
        assert sal_max is None
        assert period == "hourly"

    def test_per_hour(self, scraper):
        sal_min, sal_max, period = scraper._extract_salary("$75 per hour")
        assert sal_min == 75
        assert period == "hourly"

    def test_none(self, scraper):
        sal_min, sal_max, period = scraper._extract_salary(None)
        assert sal_min is None
        assert sal_max is None
        assert period is None

    def test_no_salary(self, scraper):
        sal_min, sal_max, period = scraper._extract_salary(
            "Great company with competitive compensation"
        )
        assert sal_min is None
