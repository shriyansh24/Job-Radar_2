from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.config import Settings
from app.jobs.models import Job
from app.scraping.port import ScrapedJob, ScraperPort
from app.scraping.rate_limiter import CircuitBreaker, TokenBucketLimiter
from app.scraping.service import ScrapingService, compute_ats_composite_key


class FakeScraper(ScraperPort):
    """Mock scraper that returns predefined jobs."""

    def __init__(
        self,
        name: str,
        jobs: list[ScrapedJob] | None = None,
        *,
        fail: bool = False,
    ):
        self._name = name
        self._jobs = jobs or []
        self._fail = fail

    @property
    def source_name(self) -> str:
        return self._name

    async def fetch_jobs(
        self, query: str, location: str | None = None, limit: int = 50
    ) -> list[ScrapedJob]:
        if self._fail:
            raise RuntimeError(f"{self._name} exploded")
        return self._jobs

    async def health_check(self) -> bool:
        return not self._fail


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
    url: str | None = None,
    description: str | None = None,
    location: str | None = None,
    ats_provider: str | None = None,
    ats_job_id: str | None = None,
    company_domain: str | None = None,
) -> ScrapedJob:
    return ScrapedJob(
        title=title,
        company_name=company,
        source=source,
        source_url=url,
        description_raw=description,
        location=location,
        ats_provider=ats_provider,
        ats_job_id=ats_job_id,
        company_domain=company_domain,
    )


def _inject_scrapers(
    svc: ScrapingService,
    scrapers: dict[str, ScraperPort],
) -> None:
    """Replace real scrapers and create matching limiters/breakers."""
    svc._scrapers = scrapers
    svc._rate_limiters = {n: TokenBucketLimiter(rate=1.0, burst=5) for n in scrapers}
    svc._circuit_breakers = {n: CircuitBreaker() for n in scrapers}


def _stub_db(svc, persist_return=(0, 0)):
    """Return context managers that stub all DB operations."""
    return (
        patch.object(
            svc,
            "_persist_jobs",
            new_callable=AsyncMock,
            return_value=persist_return,
        ),
        patch.object(
            svc,
            "_create_run_record",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch.object(
            svc,
            "_complete_run_record",
            new_callable=AsyncMock,
        ),
    )


class TestScrapingServiceOrchestration:
    """Integration tests for full scraping pipeline with mock scrapers."""

    @pytest.mark.asyncio
    async def test_aggregates_from_multiple_sources(self):
        db = AsyncMock()
        svc = ScrapingService(db, _settings())
        _inject_scrapers(
            svc,
            {
                "alpha": FakeScraper("alpha", [_job(title="Alpha Job", source="alpha")]),
                "beta": FakeScraper("beta", [_job(title="Beta Job", source="beta")]),
            },
        )

        p1, p2, p3 = _stub_db(svc, persist_return=(2, 0))
        with p1, p2, p3:
            result = await svc.run_scrape(query="python")

        assert result.jobs_found == 2
        assert result.jobs_new == 2
        assert not result.errors

    @pytest.mark.asyncio
    async def test_failing_scraper_records_error(self):
        db = AsyncMock()
        svc = ScrapingService(db, _settings())
        _inject_scrapers(
            svc,
            {
                "good": FakeScraper("good", [_job(title="Good Job", source="good")]),
                "bad": FakeScraper("bad", fail=True),
            },
        )

        p1, p2, p3 = _stub_db(svc, persist_return=(1, 0))
        with p1, p2, p3:
            result = await svc.run_scrape(query="python")

        assert result.jobs_found == 1
        assert result.jobs_new == 1
        assert len(result.errors) == 1
        assert "bad" in result.errors[0]

    @pytest.mark.asyncio
    async def test_circuit_breaker_skips_open_source(self):
        db = AsyncMock()
        svc = ScrapingService(db, _settings())
        _inject_scrapers(
            svc,
            {
                "open_cb": FakeScraper(
                    "open_cb",
                    [_job(title="Unreachable", source="open_cb")],
                ),
            },
        )

        # Force circuit open
        cb = svc._circuit_breakers["open_cb"]
        for _ in range(cb.failure_threshold):
            cb.record_failure()

        p1, p2, p3 = _stub_db(svc)
        with p1, p2, p3:
            result = await svc.run_scrape(sources=["open_cb"], query="python")

        assert result.jobs_found == 0
        assert "circuit breaker open" in result.errors[0]

    @pytest.mark.asyncio
    async def test_dedup_removes_duplicates(self):
        db = AsyncMock()
        svc = ScrapingService(db, _settings())
        duplicate = _job(title="Dupe Job", company="SameCo", source="a")
        _inject_scrapers(
            svc,
            {
                "src1": FakeScraper("src1", [duplicate]),
                "src2": FakeScraper("src2", [duplicate]),
            },
        )

        persisted_count: list[int] = []

        async def mock_persist(jobs, user_id):
            persisted_count.append(len(jobs))
            return (len(jobs), 0)

        with (
            patch.object(svc, "_persist_jobs", side_effect=mock_persist),
            patch.object(
                svc,
                "_create_run_record",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch.object(
                svc,
                "_complete_run_record",
                new_callable=AsyncMock,
            ),
        ):
            result = await svc.run_scrape(query="python")

        assert result.jobs_found == 2  # Found 2 from scrapers
        assert persisted_count[0] == 1  # Only 1 after dedup

    @pytest.mark.asyncio
    async def test_event_callback_called(self):
        db = AsyncMock()
        svc = ScrapingService(db, _settings())
        _inject_scrapers(
            svc,
            {
                "evented": FakeScraper("evented", [_job(source="evented")]),
            },
        )

        callback = AsyncMock()

        p1, p2, p3 = _stub_db(svc, persist_return=(1, 0))
        with p1, p2, p3:
            await svc.run_scrape(query="python", event_callback=callback)

        callback.assert_called_once()
        event = callback.call_args[0][0]
        assert event["type"] == "scraper_progress"
        assert event["source"] == "evented"

    @pytest.mark.asyncio
    async def test_source_filter_respected(self):
        db = AsyncMock()
        svc = ScrapingService(db, _settings())
        _inject_scrapers(
            svc,
            {
                "wanted": FakeScraper("wanted", [_job(source="wanted")]),
                "unwanted": FakeScraper("unwanted", [_job(source="unwanted")]),
            },
        )

        p1, p2, p3 = _stub_db(svc, persist_return=(1, 0))
        with p1, p2, p3:
            result = await svc.run_scrape(sources=["wanted"], query="python")

        assert result.jobs_found == 1
        assert result.jobs_new == 1


class TestComputeJobId:
    def test_stable_id(self):
        job = _job(title="Dev", company="Co")
        id1 = ScrapingService._compute_job_id(job)
        id2 = ScrapingService._compute_job_id(job)
        assert id1 == id2
        assert len(id1) == 64

    def test_different_jobs_different_ids(self):
        j1 = _job(title="Frontend", company="A")
        j2 = _job(title="Backend", company="B")
        assert ScrapingService._compute_job_id(j1) != ScrapingService._compute_job_id(j2)


class TestScrapedToDict:
    def test_converts_all_fields(self):
        job = _job(title="Test", company="TestCo")
        d = ScrapingService._scraped_to_dict(job)
        assert d["title"] == "Test"
        assert d["company_name"] == "TestCo"
        assert d["source"] == "test"
        assert "scraped_at" in d


class TestScrapingPersistence:
    @pytest.mark.asyncio
    async def test_persist_jobs_updates_existing_row_by_ats_key(
        self, db_session
    ):
        svc = ScrapingService(db_session, _settings())
        first_seen_at = datetime.now(UTC) - timedelta(days=3)
        existing = Job(
            id=ScrapingService._compute_job_id(
                _job(
                    title="Platform Engineer",
                    company="Acme",
                    source="greenhouse",
                    location="Remote",
                )
            ),
            user_id=None,
            source="greenhouse",
            title="Platform Engineer",
            company_name="Acme",
            location="Remote",
            ats_provider="greenhouse",
            ats_job_id="job-123",
            ats_composite_key=compute_ats_composite_key(
                None, "greenhouse", "job-123"
            ),
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            freshness_score=0.7,
            content_hash="old-hash",
            seen_count=1,
        )
        db_session.add(existing)
        await db_session.commit()

        new_count, updated_count = await svc._persist_jobs(
            [
                _job(
                    title="Senior Platform Engineer",
                    company="Acme",
                    source="greenhouse",
                    location="Hybrid",
                    description="New description",
                    ats_provider="greenhouse",
                    ats_job_id="job-123",
                )
            ],
            user_id=None,
        )

        jobs = list((await db_session.scalars(select(Job))).all())
        assert (new_count, updated_count) == (0, 1)
        assert len(jobs) == 1
        assert jobs[0].id == existing.id
        assert jobs[0].title == "Senior Platform Engineer"
        assert jobs[0].location == "Hybrid"
        assert jobs[0].seen_count == 2
        assert jobs[0].first_seen_at == first_seen_at
        assert jobs[0].last_seen_at is not None
        assert jobs[0].last_seen_at > first_seen_at
        assert jobs[0].previous_hash == "old-hash"
        assert jobs[0].content_hash != "old-hash"
        assert jobs[0].freshness_score == pytest.approx(0.5)

    @pytest.mark.asyncio
    async def test_persist_jobs_initializes_freshness_fields(self, db_session):
        svc = ScrapingService(db_session, _settings())

        new_count, updated_count = await svc._persist_jobs(
            [
                _job(
                    title="Data Engineer",
                    company="Beta",
                    source="lever",
                    description="Build pipelines",
                )
            ],
            user_id=None,
        )

        job = (await db_session.scalars(select(Job))).one()
        assert (new_count, updated_count) == (1, 0)
        assert job.first_seen_at is not None
        assert job.last_seen_at is not None
        assert job.first_seen_at == job.last_seen_at
        assert job.freshness_score == pytest.approx(1.0)
        assert job.seen_count == 1
        assert job.content_hash is not None
