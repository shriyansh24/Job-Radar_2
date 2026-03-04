import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy import update

from backend.config import get_settings
from backend.database import async_session
from backend.models import Job, ScraperRun, UserProfile
from backend.scrapers.serpapi_scraper import SerpApiScraper
from backend.scrapers.greenhouse_scraper import GreenhouseScraper
from backend.scrapers.lever_scraper import LeverScraper
from backend.scrapers.ashby_scraper import AshbyScraper
from backend.scrapers.jobspy_scraper import JobSpyScraper
from backend.scrapers.theirstack_scraper import TheirStackScraper
from backend.enrichment.deduplicator import deduplicate_and_insert
from backend.enrichment.llm_enricher import run_enrichment_batch
from backend.enrichment.embedding import score_jobs_batch

logger = logging.getLogger(__name__)

# SSE event queue for broadcasting scraper events
sse_clients: list[asyncio.Queue] = []


def broadcast_sse(event: dict):
    for queue in sse_clients:
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            pass


SCRAPERS = {
    "serpapi": SerpApiScraper,
    "greenhouse": GreenhouseScraper,
    "lever": LeverScraper,
    "ashby": AshbyScraper,
    "jobspy": JobSpyScraper,
    "theirstack": TheirStackScraper,
}


async def _get_search_params() -> tuple[list[str], list[str], list[str]]:
    """Get search queries, locations, and company watchlist from user profile."""
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(UserProfile).where(UserProfile.id == 1)
        )
        profile = result.scalar_one_or_none()

    queries = ["AI Engineer", "ML Engineer", "Data Scientist"]
    locations = ["Remote", "New York, NY"]
    watchlist = []

    if profile:
        if profile.default_queries:
            queries = profile.default_queries
        if profile.default_locations:
            locations = profile.default_locations
        if profile.company_watchlist:
            watchlist = profile.company_watchlist

    return queries, locations, watchlist


async def run_scraper(source: str):
    """Run a specific scraper and store results."""
    logger.info(f"Starting scraper: {source}")

    async with async_session() as session:
        # Create scraper run record
        run = ScraperRun(source=source, status="running")
        session.add(run)
        await session.commit()
        run_id = run.id

    broadcast_sse({
        "event": "scraper_started",
        "source": source,
        "run_id": run_id,
    })

    queries, locations, watchlist = await _get_search_params()
    scraper_class = SCRAPERS.get(source)
    if not scraper_class:
        logger.error(f"Unknown scraper source: {source}")
        return

    scraper = scraper_class()
    jobs_found = 0
    jobs_new = 0
    jobs_updated = 0
    error_message = None

    try:
        all_raw_jobs = []

        # ATS scrapers use watchlist slugs
        if source in ("greenhouse", "lever", "ashby") and watchlist:
            for query in queries:
                for location in locations:
                    raw = await scraper.fetch_jobs(
                        query=query, location=location, limit=200, slugs=watchlist
                    )
                    all_raw_jobs.extend(raw)
        else:
            for query in queries:
                for location in locations:
                    raw = await scraper.fetch_jobs(
                        query=query, location=location, limit=200
                    )
                    all_raw_jobs.extend(raw)

        jobs_found = len(all_raw_jobs)

        broadcast_sse({
            "event": "job_found",
            "source": source,
            "count": jobs_found,
        })

        # Deduplicate and insert
        async with async_session() as session:
            for job_data in all_raw_jobs:
                is_new, job_id = await deduplicate_and_insert(job_data, session)
                if is_new:
                    jobs_new += 1
                else:
                    jobs_updated += 1

        broadcast_sse({
            "event": "scraper_progress",
            "source": source,
            "new": jobs_new,
            "existing": jobs_updated,
        })

    except Exception as e:
        error_message = str(e)
        logger.error(f"Scraper {source} failed: {e}")
        broadcast_sse({
            "event": "scraper_error",
            "source": source,
            "error": error_message,
        })

    # Update scraper run record
    async with async_session() as session:
        await session.execute(
            update(ScraperRun)
            .where(ScraperRun.id == run_id)
            .values(
                completed_at=datetime.utcnow(),
                jobs_found=jobs_found,
                jobs_new=jobs_new,
                jobs_updated=jobs_updated,
                error_message=error_message,
                status="completed" if not error_message else "failed",
            )
        )
        await session.commit()

    broadcast_sse({
        "event": "scraper_completed",
        "source": source,
        "found": jobs_found,
        "new": jobs_new,
        "existing": jobs_updated,
    })

    logger.info(
        f"Scraper {source} complete: {jobs_found} found, "
        f"{jobs_new} new, {jobs_updated} existing"
    )


async def run_all_scrapers():
    """Run all enabled scrapers sequentially."""
    for source in SCRAPERS:
        try:
            await run_scraper(source)
        except Exception as e:
            logger.error(f"Scraper {source} failed: {e}")


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the APScheduler."""
    jobstores = {
        "default": SQLAlchemyJobStore(url="sqlite:///./data/jobradar.db")
    }

    scheduler = AsyncIOScheduler(jobstores=jobstores)

    scheduler.add_job(
        run_scraper, "interval", hours=6,
        args=["serpapi"], id="serpapi_scrape", replace_existing=True
    )
    scheduler.add_job(
        run_scraper, "interval", hours=3,
        args=["greenhouse"], id="greenhouse_scrape", replace_existing=True
    )
    scheduler.add_job(
        run_scraper, "interval", hours=3,
        args=["lever"], id="lever_scrape", replace_existing=True
    )
    scheduler.add_job(
        run_scraper, "interval", hours=3,
        args=["ashby"], id="ashby_scrape", replace_existing=True
    )
    scheduler.add_job(
        run_scraper, "interval", hours=12,
        args=["jobspy"], id="jobspy_scrape", replace_existing=True
    )
    scheduler.add_job(
        run_enrichment_batch, "interval", minutes=15,
        id="enrichment_batch", replace_existing=True
    )
    scheduler.add_job(
        score_jobs_batch, "interval", minutes=20,
        id="scoring_batch", replace_existing=True
    )

    return scheduler
