from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.config import Settings
from app.jobs.models import Job
from app.scraping.deduplication import compute_ats_composite_key
from app.scraping.port import ScrapedJob
from app.scraping.service import ScrapingService


def _settings() -> Settings:
    return Settings(
        database_url="sqlite+aiosqlite:///test.db",
        serpapi_api_key="",
        theirstack_api_key="",
        apify_api_key="",
    )


def _greenhouse_job(*, title: str, location: str | None = None) -> ScrapedJob:
    return ScrapedJob(
        title=title,
        company_name="Acme",
        source="greenhouse",
        source_url="https://boards.greenhouse.io/acme/jobs/12345",
        company_domain="example.com",
        location=location,
        ats_provider="greenhouse",
        ats_job_id="12345",
    )


async def test_persist_jobs_updates_existing_row_by_ats_composite_key(db_session):
    service = ScrapingService(db_session, _settings())

    initial_job = _greenhouse_job(title="Software Engineer", location="Austin, TX")
    changed_job = _greenhouse_job(title="Senior Software Engineer", location="Remote")

    first_new, first_updated = await service._persist_jobs([initial_job], user_id=None)
    second_new, second_updated = await service._persist_jobs([changed_job], user_id=None)

    jobs = (await db_session.scalars(select(Job))).all()

    assert first_new == 1
    assert first_updated == 0
    assert second_new == 0
    assert second_updated == 1
    assert len(jobs) == 1
    assert jobs[0].title == "Senior Software Engineer"
    assert jobs[0].location == "Remote"
    assert jobs[0].ats_provider == "greenhouse"
    assert jobs[0].ats_job_id == "12345"
    assert jobs[0].ats_composite_key is not None


async def test_persist_jobs_tracks_lifecycle_fields_for_existing_jobs(db_session):
    service = ScrapingService(db_session, _settings())
    first_seen_at = datetime.now(UTC) - timedelta(days=3)

    existing = Job(
        id=ScrapingService._compute_job_id(
            _greenhouse_job(title="Software Engineer", location="Austin, TX")
        ),
        user_id=None,
        source="greenhouse",
        title="Software Engineer",
        company_name="Acme",
        location="Austin, TX",
        company_domain="example.com",
        ats_provider="greenhouse",
        ats_job_id="12345",
        ats_composite_key=compute_ats_composite_key("example.com", "greenhouse", "12345"),
        first_seen_at=first_seen_at,
        last_seen_at=first_seen_at,
        content_hash="old-hash",
        seen_count=1,
        disappeared_at=first_seen_at,
    )
    db_session.add(existing)
    await db_session.commit()

    changed_job = ScrapedJob(
        title="Senior Software Engineer",
        company_name="Acme",
        source="greenhouse",
        source_url="https://boards.greenhouse.io/acme/jobs/12345",
        company_domain="example.com",
        location="Remote",
        description_raw="Updated responsibilities",
        ats_provider="greenhouse",
        ats_job_id="12345",
    )

    new_count, updated_count = await service._persist_jobs([changed_job], user_id=None)
    job = (await db_session.scalars(select(Job))).one()

    assert (new_count, updated_count) == (0, 1)
    assert job.title == "Senior Software Engineer"
    assert job.location == "Remote"
    assert job.first_seen_at == first_seen_at
    assert job.last_seen_at is not None
    assert job.last_seen_at > first_seen_at
    assert job.scraped_at == job.last_seen_at
    assert job.seen_count == 2
    assert job.disappeared_at is None
    assert job.previous_hash == "old-hash"
    assert job.content_hash is not None
    assert job.content_hash != "old-hash"


async def test_persist_jobs_initializes_lifecycle_fields_for_new_jobs(db_session):
    service = ScrapingService(db_session, _settings())
    new_job = ScrapedJob(
        title="Data Engineer",
        company_name="Beta",
        source="lever",
        description_raw="Build pipelines",
    )

    new_count, updated_count = await service._persist_jobs([new_job], user_id=None)
    job = (await db_session.scalars(select(Job))).one()

    assert (new_count, updated_count) == (1, 0)
    assert job.first_seen_at is not None
    assert job.last_seen_at is not None
    assert job.first_seen_at == job.last_seen_at
    assert job.scraped_at == job.last_seen_at
    assert job.seen_count == 1
    assert job.content_hash is not None
    assert job.previous_hash is None
