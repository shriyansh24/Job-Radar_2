from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.scraping.port import ScrapedJob
from app.scraping.service_parts.identity import compute_job_id, scraped_job_to_dict

logger = structlog.get_logger()


async def persist_jobs(
    db: AsyncSession,
    jobs: list[ScrapedJob],
    user_id: uuid.UUID | None,
) -> tuple[int, int]:
    """Save scraped jobs to DB. Returns (new_count, updated_count)."""
    new_count = 0
    updated_count = 0

    try:
        from app.jobs.models import Job
    except ImportError:
        logger.warning("job_model_not_available", hint="Phase 3A not complete")
        return 0, 0

    for scraped in jobs:
        job_id = compute_job_id(scraped)
        scraped_fields = scraped_job_to_dict(scraped)
        ats_composite_key = scraped_fields.get("ats_composite_key")
        existing = None
        if ats_composite_key:
            existing = await db.scalar(
                select(Job).where(Job.ats_composite_key == ats_composite_key)
            )
        if existing is None:
            existing = await db.get(Job, job_id)

        if existing:
            for field_name, value in scraped_fields.items():
                if field_name == "scraped_at":
                    continue
                setattr(existing, field_name, value)
            existing.scraped_at = datetime.now(UTC)
            updated_count += 1
        else:
            job = Job(
                id=job_id,
                user_id=user_id,
                **scraped_fields,
            )
            db.add(job)
            new_count += 1

    try:
        await db.commit()
    except Exception as exc:
        logger.error("persist_jobs_failed", error=str(exc))
        await db.rollback()

    return new_count, updated_count
