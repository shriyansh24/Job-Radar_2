"""Saved search alert worker.

Checks saved searches with alert_enabled=True, runs the search query,
and creates notifications for new matching jobs.
"""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.notifications.models import Notification
from app.settings.models import SavedSearch

logger = structlog.get_logger()


async def check_saved_search_alerts() -> None:
    """Check all enabled saved searches for new job matches and create notifications."""
    async with async_session_factory() as db:
        query = select(SavedSearch).where(SavedSearch.alert_enabled == True)  # noqa: E712
        result = await db.scalars(query)
        searches = list(result.all())

        if not searches:
            return

        logger.info("alert_worker.checking", search_count=len(searches))

        for search in searches:
            try:
                await _check_single_alert(db, search)
            except Exception as exc:
                logger.error(
                    "alert_worker.search_failed",
                    search_id=str(search.id),
                    error=str(exc),
                )

        await db.commit()


async def _check_single_alert(db: AsyncSession, search: SavedSearch) -> None:
    """Check a single saved search for new results since last check."""
    from app.jobs.models import Job

    filters_dict = search.filters or {}
    q = filters_dict.get("q", "")

    # Build a basic query based on saved filters
    job_query = select(Job).where(Job.is_active == True)  # noqa: E712

    if search.user_id:
        job_query = job_query.where(Job.user_id == search.user_id)

    if q:
        job_query = job_query.where(Job.title.ilike(f"%{q}%"))

    # Only check jobs since last alert check
    if search.last_checked_at:
        job_query = job_query.where(Job.created_at > search.last_checked_at)

    job_query = job_query.limit(20)
    result = await db.scalars(job_query)
    new_jobs = list(result.all())

    # Update last_checked_at
    now = datetime.now(timezone.utc)
    await db.execute(
        update(SavedSearch).where(SavedSearch.id == search.id).values(last_checked_at=now)
    )

    if new_jobs and search.user_id:
        notif = Notification(
            user_id=search.user_id,
            title=f"New jobs for '{search.name}'",
            body=f"{len(new_jobs)} new job(s) match your saved search '{search.name}'.",
            notification_type="alert",
            link=f"/jobs?q={q}" if q else "/jobs",
        )
        db.add(notif)
        logger.info(
            "alert_worker.new_matches",
            search=search.name,
            count=len(new_jobs),
        )
