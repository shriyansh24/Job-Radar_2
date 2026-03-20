from __future__ import annotations

from datetime import UTC, datetime, timedelta

import structlog

from app.config import Settings
from app.database import async_session_factory

logger = structlog.get_logger()


async def run_cleanup(ctx: dict | None = None) -> None:
    """Remove old jobs, update source health."""
    async with async_session_factory() as db:
        try:
            from sqlalchemy import update

            from app.jobs.models import Job

            cutoff = datetime.now(UTC) - timedelta(days=90)
            result = await db.execute(
                update(Job)
                .where(Job.scraped_at < cutoff, Job.status == "new")
                .values(is_active=False)
            )
            await db.commit()
            logger.info("cleanup_completed", deactivated=result.rowcount)
        except Exception as e:
            logger.error("cleanup_failed", error=str(e))


async def run_source_health_check(ctx: dict | None = None) -> None:
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
    for name, scraper in scrapers.items():
        try:
            healthy = await scraper.health_check()
            logger.info(
                "source_health_check",
                source=name,
                healthy=healthy,
            )
        except Exception as e:
            logger.error(
                "source_health_check_failed",
                source=name,
                error=str(e),
            )
        finally:
            await scraper.close()
