from __future__ import annotations

import hashlib
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
        seen_at = datetime.now(UTC)
        job_id = compute_job_id(scraped)
        scraped_fields = scraped_job_to_dict(scraped)
        content_hash = _compute_content_hash(scraped)
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
                setattr(existing, field_name, value)
            existing.scraped_at = seen_at
            existing.first_seen_at = existing.first_seen_at or seen_at
            existing.last_seen_at = seen_at
            existing.seen_count = (existing.seen_count or 0) + 1
            existing.disappeared_at = None
            if existing.content_hash != content_hash:
                existing.previous_hash = existing.content_hash
                existing.content_hash = content_hash
            updated_count += 1
        else:
            job = Job(
                id=job_id,
                user_id=user_id,
                first_seen_at=seen_at,
                last_seen_at=seen_at,
                disappeared_at=None,
                content_hash=content_hash,
                seen_count=1,
                **scraped_fields,
            )
            db.add(job)
            new_count += 1

    try:
        await db.flush()
    except Exception as exc:
        logger.error("persist_jobs_failed", error=str(exc))
        await db.rollback()
        raise

    return new_count, updated_count


def _compute_content_hash(job: ScrapedJob) -> str:
    """Track material content changes without including volatile scrape metadata."""
    content = (
        f"{job.title.strip().lower()}|"
        f"{job.company_name.strip().lower()}|"
        f"{(job.location or '').strip().lower()}|"
        f"{(job.description_raw or '').strip()[:1000]}"
    )
    return hashlib.sha256(content.encode()).hexdigest()
