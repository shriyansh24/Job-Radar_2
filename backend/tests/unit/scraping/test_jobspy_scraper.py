"""Unit tests for JobSpyScraper."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.scraping.scrapers.jobspy import JobSpyScraper


def _make_scraper() -> JobSpyScraper:
    settings = MagicMock()
    return JobSpyScraper(settings=settings)


class _DictRow:
    """Pandas-like row that supports both row.get(key) and row[key]."""

    def __init__(self, data: dict):
        self._data = data

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def __getitem__(self, key: str):
        return self._data[key]


def _make_df_row(**kwargs) -> dict:
    """Create a mock DataFrame row with required fields."""
    defaults = {
        "title": "Software Engineer",
        "company": "TechCo",
        "site": "indeed",
        "job_url": "https://indeed.com/job/123",
        "location": "San Francisco, CA",
        "is_remote": "False",
        "description": "Build great software.",
        "job_type": "fulltime",
        "min_amount": None,
        "max_amount": None,
        "interval": None,
    }
    defaults.update(kwargs)
    # Return an object that supports both row.get("key") and row["key"]
    return _DictRow(defaults)


class _MockDataFrame:
    """Minimal pandas-like DataFrame mock."""

    def __init__(self, rows: list[SimpleNamespace]):
        self._rows = rows

    def iterrows(self):
        for i, row in enumerate(self._rows):
            yield i, row

    def __getitem__(self, key: str):
        return [getattr(r, key) for r in self._rows]

    def __len__(self):
        return len(self._rows)


class TestFetchJobs:
    @pytest.mark.asyncio
    async def test_jobspy_not_installed_returns_empty(self):
        scraper = _make_scraper()
        with patch.dict("sys.modules", {"jobspy": None}):
            result = await scraper.fetch_jobs("python developer")
        assert result == []

    @pytest.mark.asyncio
    async def test_scrape_jobs_exception_returns_empty(self):
        scraper = _make_scraper()
        mock_module = MagicMock()
        mock_module.scrape_jobs.side_effect = RuntimeError("Network error")
        with patch.dict("sys.modules", {"jobspy": mock_module}):
            result = await scraper.fetch_jobs("python developer")
        assert result == []

    @pytest.mark.asyncio
    async def test_maps_fields_correctly(self):
        scraper = _make_scraper()
        row = _make_df_row(
            title="Backend Engineer",
            company="Acme Corp",
            site="linkedin",
            job_url="https://linkedin.com/jobs/abc",
            location="Remote",
            is_remote="True",
            description="Great role.",
            job_type="fulltime",
            min_amount=100000,
            max_amount=150000,
            interval="yearly",
        )
        df = _MockDataFrame([row])

        mock_module = MagicMock()
        mock_module.scrape_jobs.return_value = df

        with patch.dict("sys.modules", {"jobspy": mock_module}):
            result = await scraper.fetch_jobs("backend engineer")

        assert len(result) == 1
        job = result[0]
        assert job.title == "Backend Engineer"
        assert job.company_name == "Acme Corp"
        assert job.source == "jobspy_linkedin"
        assert job.source_url == "https://linkedin.com/jobs/abc"
        assert job.salary_min == 100000.0
        assert job.salary_max == 150000.0
        assert job.salary_period == "yearly"

    @pytest.mark.asyncio
    async def test_empty_result_returns_empty_list(self):
        scraper = _make_scraper()
        df = _MockDataFrame([])
        mock_module = MagicMock()
        mock_module.scrape_jobs.return_value = df

        with patch.dict("sys.modules", {"jobspy": mock_module}):
            result = await scraper.fetch_jobs("no results query")

        assert result == []

    @pytest.mark.asyncio
    async def test_limit_respected(self):
        scraper = _make_scraper()
        rows = [_make_df_row(title=f"Job {i}", job_url=f"https://co.com/{i}") for i in range(20)]
        df = _MockDataFrame(rows)
        mock_module = MagicMock()
        mock_module.scrape_jobs.return_value = df

        with patch.dict("sys.modules", {"jobspy": mock_module}):
            result = await scraper.fetch_jobs("developer", limit=5)

        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_passes_location_to_scrape_jobs(self):
        scraper = _make_scraper()
        df = _MockDataFrame([])
        mock_module = MagicMock()
        mock_module.scrape_jobs.return_value = df

        with patch.dict("sys.modules", {"jobspy": mock_module}):
            await scraper.fetch_jobs("python dev", location="Austin, TX", limit=10)

        call_kwargs = mock_module.scrape_jobs.call_args
        assert call_kwargs.kwargs.get("location") == "Austin, TX" or \
               "Austin, TX" in str(call_kwargs)


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_returns_true_when_jobspy_installed(self):
        scraper = _make_scraper()
        mock_module = MagicMock()
        with patch.dict("sys.modules", {"jobspy": mock_module}):
            result = await scraper.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_jobspy_not_installed(self):
        scraper = _make_scraper()
        with patch.dict("sys.modules", {"jobspy": None}):
            result = await scraper.health_check()
        assert result is False


class TestSourceName:
    def test_source_name_is_jobspy(self):
        scraper = _make_scraper()
        assert scraper.source_name == "jobspy"
