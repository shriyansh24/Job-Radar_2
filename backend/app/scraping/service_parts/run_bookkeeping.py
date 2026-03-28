from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


async def create_run_record(
    db: AsyncSession,
    *,
    sources: list[str],
    user_id: uuid.UUID | None,
) -> uuid.UUID | None:
    """Create a scraper_runs record. Returns None if model not available."""
    try:
        from app.scraping.models import ScraperRun

        run = ScraperRun(
            user_id=user_id,
            source=",".join(sources),
            status="running",
        )
        db.add(run)
        await db.flush()
        return cast(uuid.UUID | None, run.id)
    except Exception as exc:
        logger.debug("scraper_run_record_unavailable", error=str(exc))
        await db.rollback()
        return None


async def complete_run_record(
    db: AsyncSession,
    *,
    run_id: uuid.UUID | None,
    jobs_found: int,
    jobs_new: int,
    jobs_updated: int,
    errors: list[str],
    elapsed: float,
) -> None:
    if not run_id:
        return
    try:
        from app.scraping.models import ScraperRun

        run = await db.get(ScraperRun, run_id)
        if run:
            run.status = "completed" if not errors else "completed_with_errors"
            run.jobs_found = jobs_found
            run.jobs_new = jobs_new
            run.jobs_updated = jobs_updated
            run.error_message = "; ".join(errors) if errors else None
            run.completed_at = datetime.now(UTC)
            run.duration_seconds = Decimal(str(round(elapsed, 2)))
        await db.commit()
    except Exception as exc:
        logger.warning("scraper_run_record_update_failed", error=str(exc))
        await db.rollback()
