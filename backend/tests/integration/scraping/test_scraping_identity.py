from __future__ import annotations

from sqlalchemy import select

from app.config import Settings
from app.jobs.models import Job
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
