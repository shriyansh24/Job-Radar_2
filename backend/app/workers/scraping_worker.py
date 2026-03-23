from __future__ import annotations

import uuid

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
                    logger.info("career_page_scraped", url=target.url, jobs=len(jobs))
                except Exception as e:
                    target.consecutive_failures += 1
                    target.last_failure_at = datetime.now(UTC)
                    logger.error("career_page_scrape_failed", url=target.url, error=str(e))

            await db.commit()
            await scraper.close()
        except Exception as e:
            logger.error("career_page_worker_failed", error=str(e))


async def run_target_batch_job(
    source_kind: str = "career_page",
    batch_size: int = 50,
    ctx: dict | None = None,
) -> None:
    """Background job: run the tier-based target pipeline for due targets.

    Selects targets that are due for scraping via ``select_due_targets()``,
    then runs them through ``ScrapingService.run_target_batch()``.

    Args:
        source_kind: Filter targets by source_kind (e.g. "career_page", "watchlist").
        batch_size: Maximum number of targets to process per tick.
        ctx: APScheduler job context (unused, present for signature compat).
    """
    settings = Settings()
    async with async_session_factory() as db:
        try:
            from sqlalchemy import select

            from app.scraping.control.scheduler import compute_next_run, select_due_targets
            from app.scraping.models import ScrapeTarget

            # 1. Load enabled, non-quarantined targets of the requested kind
            all_targets = (
                await db.scalars(
                    select(ScrapeTarget).where(
                        ScrapeTarget.source_kind == source_kind,
                        ScrapeTarget.enabled == True,  # noqa: E712
                        ScrapeTarget.quarantined == False,  # noqa: E712
                    )
                )
            ).all()

            due = select_due_targets(list(all_targets), batch_size=batch_size)
            if not due:
                logger.info("target_batch_no_due_targets", source_kind=source_kind)
                return

            # 2. Build adapter registry and a lightweight browser pool stub
            #    (BrowserPool is provided by Chunk 4; if unavailable, use a no-op)
            from app.scraping.execution.adapter_registry import build_default_registry

            adapter_registry = build_default_registry(settings)

            try:
                from app.scraping.execution.browser_pool import BrowserPool

                browser_pool = BrowserPool()
            except ImportError:
                browser_pool = _NoOpBrowserPool()

            # 3. Run the batch
            run_id = uuid.uuid4()
            service = ScrapingService(db, settings)
            try:
                results = await service.run_target_batch(
                    targets=due,
                    run_id=run_id,
                    adapter_registry=adapter_registry,
                    browser_pool=browser_pool,
                )

                # 4. Update target metadata based on per-target results
                succeeded_ids = results.get("succeeded_target_ids", set())
                for target in due:
                    target.next_scheduled_at = compute_next_run(
                        target,
                        success=(target.id in succeeded_ids),
                    )

                await db.commit()

                logger.info(
                    "target_batch_completed",
                    source_kind=source_kind,
                    run_id=str(run_id),
                    attempted=results["targets_attempted"],
                    succeeded=results["targets_succeeded"],
                    failed=results["targets_failed"],
                    jobs_found=results["jobs_found"],
                )
            finally:
                await service.close()

        except Exception as e:
            logger.error("target_batch_job_failed", source_kind=source_kind, error=str(e))


class _NoOpBrowserPool:
    """Stub browser pool used when the real BrowserPool (Chunk 4) is not available."""

    class _NoOpContext:
        async def __aenter__(self):
            return None

        async def __aexit__(self, *args):
            pass

    def acquire(self, tier: int, domain: str):
        return self._NoOpContext()
