from __future__ import annotations

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.workers.alert_worker import check_saved_search_alerts
from app.workers.auto_apply_worker import run_auto_apply_batch
from app.workers.enrichment_worker import (
    run_embedding_batch,
    run_enrichment_batch,
    run_tfidf_scoring,
)
from app.workers.maintenance_worker import run_cleanup, run_source_health_check
from app.workers.phase7a_worker import (
    run_followup_reminders,
    run_staleness_sweep,
)
from app.workers.phase7a_worker import (
    run_source_health_checks as run_phase7a_source_health,
)
from app.workers.scraping_worker import (
    run_career_page_scrape,
    run_scheduled_scrape,
    run_target_batch_job,
)

logger = structlog.get_logger()


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the background job scheduler."""
    scheduler = AsyncIOScheduler()

    # Scraping: every 6 hours
    scheduler.add_job(
        run_scheduled_scrape,
        IntervalTrigger(hours=6),
        id="scheduled_scrape",
        kwargs={"ctx": {}},
        replace_existing=True,
    )

    # Career pages: every 12 hours
    scheduler.add_job(
        run_career_page_scrape,
        IntervalTrigger(hours=12),
        id="career_page_scrape",
        kwargs={"ctx": {}},
        replace_existing=True,
    )

    # Enrichment: every 30 minutes
    scheduler.add_job(
        run_enrichment_batch,
        IntervalTrigger(minutes=30),
        id="enrichment_batch",
        kwargs={"ctx": {}},
        replace_existing=True,
    )

    # Embeddings: every hour
    scheduler.add_job(
        run_embedding_batch,
        IntervalTrigger(hours=1),
        id="embedding_batch",
        kwargs={"ctx": {}},
        replace_existing=True,
    )

    # TF-IDF: every 2 hours
    scheduler.add_job(
        run_tfidf_scoring,
        IntervalTrigger(hours=2),
        id="tfidf_scoring",
        kwargs={"ctx": {}},
        replace_existing=True,
    )

    # Cleanup: daily
    scheduler.add_job(
        run_cleanup,
        IntervalTrigger(days=1),
        id="cleanup",
        kwargs={"ctx": {}},
        replace_existing=True,
    )

    # Source health: every 4 hours
    scheduler.add_job(
        run_source_health_check,
        IntervalTrigger(hours=4),
        id="source_health",
        kwargs={"ctx": {}},
        replace_existing=True,
    )

    # Auto-apply: every 4 hours
    scheduler.add_job(
        run_auto_apply_batch,
        IntervalTrigger(hours=4),
        id="auto_apply_batch",
        kwargs={"ctx": {}},
        replace_existing=True,
    )

    # Saved search alerts: every 30 minutes
    scheduler.add_job(
        check_saved_search_alerts,
        IntervalTrigger(minutes=30),
        id="saved_search_alerts",
        replace_existing=True,
    )

    # Phase 7A: staleness sweep every 6 hours
    scheduler.add_job(
        run_staleness_sweep,
        IntervalTrigger(hours=6),
        id="staleness_sweep",
        replace_existing=True,
    )

    # Phase 7A: source health checks every 4 hours
    scheduler.add_job(
        run_phase7a_source_health,
        IntervalTrigger(hours=4),
        id="phase7a_source_health",
        replace_existing=True,
    )

    # Phase 7A: follow-up reminders every hour
    scheduler.add_job(
        run_followup_reminders,
        IntervalTrigger(hours=1),
        id="followup_reminders",
        replace_existing=True,
    )

    # Target-based pipeline: career page targets every 30 minutes
    scheduler.add_job(
        run_target_batch_job,
        IntervalTrigger(minutes=30),
        id="target_batch_career_page",
        kwargs={"source_kind": "career_page", "batch_size": 50},
        replace_existing=True,
    )

    # Target-based pipeline: watchlist targets every 2 hours
    scheduler.add_job(
        run_target_batch_job,
        IntervalTrigger(hours=2),
        id="target_batch_watchlist",
        kwargs={"source_kind": "watchlist", "batch_size": 25},
        replace_existing=True,
    )

    jobs = scheduler.get_jobs()
    logger.info(
        "scheduler_configured",
        job_count=len(jobs),
        job_ids=[job.id for job in jobs],
    )

    return scheduler
