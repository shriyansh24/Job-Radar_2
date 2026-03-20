from __future__ import annotations

import structlog

from app.config import Settings
from app.database import async_session_factory
from app.scraping.scrapers.career_page import CareerPageScraper
from app.scraping.service import ScrapingService

logger = structlog.get_logger()


async def run_scheduled_scrape(ctx: dict | None = None) -> None:
    """Background job: run all configured scrapers for each saved search query."""
    settings = Settings()
    async with async_session_factory() as db:
        service = ScrapingService(db, settings)

        # Get user's search queries from profile
        try:
            from sqlalchemy import select

            from app.profile.models import UserProfile

            profile = await db.scalar(select(UserProfile).limit(1))
            if not profile or not profile.search_queries:
                logger.info("no_search_queries_configured")
                return

            for query_config in profile.search_queries:
                query = query_config.get("query", "")
                location = query_config.get("location")
                if query:
                    result = await service.run_scrape(
                        query=query,
                        location=location,
                        user_id=profile.user_id,
                    )
                    logger.info(
                        "scheduled_scrape_done",
                        query=query,
                        found=result.jobs_found,
                        new=result.jobs_new,
                    )
        except Exception as e:
            logger.error("scheduled_scrape_failed", error=str(e))
        finally:
            await service.close()


async def run_career_page_scrape(ctx: dict | None = None) -> None:
    """Background job: scrape configured career page targets."""
    settings = Settings()
    async with async_session_factory() as db:
        try:
            from datetime import UTC, datetime

            from sqlalchemy import select

            from app.scraping.models import ScrapeTarget

            targets = (
                await db.scalars(
                    select(ScrapeTarget).where(
                        ScrapeTarget.source_kind == "career_page",
                        ScrapeTarget.enabled == True,  # noqa: E712
                    )
                )
            ).all()

            scraper = CareerPageScraper(settings)

            for target in targets:
                try:
                    jobs = await scraper.fetch_jobs(target.url)
                    target.last_success_at = datetime.now(UTC)
                    target.consecutive_failures = 0
                    logger.info(
                        "career_page_scraped", url=target.url, jobs=len(jobs)
                    )
                except Exception as e:
                    target.consecutive_failures += 1
                    target.last_failure_at = datetime.now(UTC)
                    logger.error(
                        "career_page_scrape_failed", url=target.url, error=str(e)
                    )

            await db.commit()
            await scraper.close()
        except Exception as e:
            logger.error("career_page_worker_failed", error=str(e))
