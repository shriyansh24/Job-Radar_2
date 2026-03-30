"""Saved search alert worker.

Checks saved searches with alert_enabled=True, runs the search query,
and creates notifications for new matching jobs.
"""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.settings.alerts import check_saved_search_alert, record_saved_search_alert_failure
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
    try:
        await check_saved_search_alert(db, search)
    except Exception as exc:
        search.last_checked_at = datetime.now(timezone.utc)
        record_saved_search_alert_failure(search, exc)
        raise
