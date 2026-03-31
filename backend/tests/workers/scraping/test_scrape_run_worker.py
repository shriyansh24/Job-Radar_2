from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config import Settings
from app.scraping.port import ScrapedJob, ScraperPort
from app.scraping.rate_limiter import CircuitBreaker, TokenBucketLimiter
from app.scraping.service import ScrapingService


class SlowScraper(ScraperPort):
    def __init__(
        self,
        name: str,
        jobs: list[ScrapedJob] | None = None,
        delay: float = 0.0,
    ):
        self._name = name
        self._jobs = jobs or []
        self._delay = delay

    @property
    def source_name(self) -> str:
        return self._name

    async def fetch_jobs(
        self, query: str, location: str | None = None, limit: int = 50
    ) -> list[ScrapedJob]:
        if self._delay:
            await asyncio.sleep(self._delay)
        return self._jobs

    async def health_check(self) -> bool:
        return True


def _settings() -> Settings:
    return Settings(
        database_url="sqlite+aiosqlite:///test.db",
        serpapi_api_key="",
        theirstack_api_key="",
        apify_api_key="",
    )


def _job(
    title: str = "Software Engineer",
    company: str = "Acme Inc",
    source: str = "test",
) -> ScrapedJob:
    return ScrapedJob(title=title, company_name=company, source=source)


def _service_with_scraper(scraper: ScraperPort) -> ScrapingService:
    svc = ScrapingService.__new__(ScrapingService)
    svc.db = MagicMock()
    svc.db.commit = AsyncMock(return_value=None)
    svc.settings = _settings()
    svc._scrapers = {scraper.source_name: scraper}
    svc._rate_limiters = {scraper.source_name: TokenBucketLimiter(rate=1.0, burst=5)}
    svc._circuit_breakers = {scraper.source_name: CircuitBreaker()}
    svc._create_run_record = AsyncMock(return_value=None)
    svc._persist_jobs = AsyncMock(return_value=(0, 0))
    svc._complete_run_record = AsyncMock(return_value=None)
    return svc


@pytest.mark.asyncio
async def test_run_scrape_times_out_slow_source():
    svc = _service_with_scraper(SlowScraper("slow", [_job()], delay=0.05))
    svc.SOURCE_FETCH_TIMEOUT_S = 0.01

    result = await svc.run_scrape(query="python")

    assert result.jobs_found == 0
    assert result.errors and result.errors[0].startswith("slow:")


@pytest.mark.asyncio
async def test_run_scrape_event_callback_failure_is_non_fatal():
    svc = _service_with_scraper(SlowScraper("fast", [_job(source="fast")]))
    callback = AsyncMock(side_effect=RuntimeError("callback failed"))

    result = await svc.run_scrape(query="python", event_callback=callback)

    assert result.jobs_found == 1
    assert result.errors == []
    callback.assert_awaited_once()
