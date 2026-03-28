from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import structlog
from sqlalchemy.engine import CursorResult

from app.config import Settings
from app.database import async_session_factory

logger = structlog.get_logger()


async def run_cleanup(ctx: Mapping[str, Any] | None = None) -> None:
    """Remove old jobs, update source health."""
    async with async_session_factory() as db:
        try:
            from sqlalchemy import update

            from app.jobs.models import Job

            cutoff = datetime.now(UTC) - timedelta(days=90)
            result = cast(
                CursorResult[Any],
                await db.execute(
                update(Job)
                .where(Job.scraped_at < cutoff, Job.status == "new")
                .values(is_active=False)
                ),
            )
            await db.commit()
            logger.info("cleanup_completed", deactivated=result.rowcount)
        except Exception:
            logger.exception("cleanup_failed")
            raise


async def run_source_health_check(ctx: Mapping[str, Any] | None = None) -> None:
    """Check health of all scraper sources."""
    settings = Settings()
    from app.scraping.scrapers.ashby import AshbyScraper
    from app.scraping.scrapers.greenhouse import GreenhouseScraper
    from app.scraping.scrapers.lever import LeverScraper
    from app.scraping.scrapers.serpapi import SerpAPIScraper
    from app.scraping.scrapers.theirstack import TheirStackScraper

    scrapers = {
        "serpapi": SerpAPIScraper(settings),
        "greenhouse": GreenhouseScraper(settings),
        "lever": LeverScraper(settings),
        "ashby": AshbyScraper(settings),
        "theirstack": TheirStackScraper(settings),
    }
    failed_sources: list[str] = []
    for name, scraper in scrapers.items():
        try:
            healthy = await scraper.health_check()
            logger.info(
                "source_health_check",
                source=name,
                healthy=healthy,
            )
            if not healthy:
                failed_sources.append(name)
        except Exception:
            failed_sources.append(name)
            logger.exception(
                "source_health_check_failed",
                source=name,
            )
        finally:
            await scraper.close()
    if failed_sources:
        raise RuntimeError(
            "Source health checks failed for: " + ", ".join(sorted(failed_sources))
        )
