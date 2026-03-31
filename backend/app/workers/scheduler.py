from __future__ import annotations

import structlog
from apscheduler.events import (
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_MISSED,
    JobExecutionEvent,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.runtime.job_registry import get_registered_job_ids
from app.runtime.queue import QueueDispatchResult, enqueue_registered_job

logger = structlog.get_logger()


def _log_job_event(event: JobExecutionEvent) -> None:
    if event.exception:
        logger.error(
            "scheduler_job_failed",
            job_id=event.job_id,
            scheduled_run_time=event.scheduled_run_time.isoformat()
            if event.scheduled_run_time
            else None,
            exception=str(event.exception),
        )
        return

    if event.code == EVENT_JOB_MISSED:
        logger.warning(
            "scheduler_job_missed",
            job_id=event.job_id,
            scheduled_run_time=event.scheduled_run_time.isoformat()
            if event.scheduled_run_time
            else None,
        )
        return

    logger.info(
        "scheduler_job_dispatched",
        job_id=event.job_id,
        scheduled_run_time=event.scheduled_run_time.isoformat()
        if event.scheduled_run_time
        else None,
        enqueued_job_id=event.retval.enqueued_job_id
        if isinstance(event.retval, QueueDispatchResult)
        else None,
        queue_job_id=event.retval.queue_job_id
        if isinstance(event.retval, QueueDispatchResult)
        else None,
        queue_correlation_id=event.retval.queue_correlation_id
        if isinstance(event.retval, QueueDispatchResult)
        else None,
        queue_name=(
            event.retval.queue_name if isinstance(event.retval, QueueDispatchResult) else None
        ),
        queue_depth_before=event.retval.queue_depth_before
        if isinstance(event.retval, QueueDispatchResult)
        else None,
        queue_depth_after=event.retval.queue_depth_after
        if isinstance(event.retval, QueueDispatchResult)
        else None,
        queue_pressure_before=event.retval.queue_pressure_before
        if isinstance(event.retval, QueueDispatchResult)
        else None,
        queue_pressure_after=event.retval.queue_pressure_after
        if isinstance(event.retval, QueueDispatchResult)
        else None,
        oldest_job_age_seconds_before=event.retval.oldest_job_age_seconds_before
        if isinstance(event.retval, QueueDispatchResult)
        else None,
        oldest_job_age_seconds_after=event.retval.oldest_job_age_seconds_after
        if isinstance(event.retval, QueueDispatchResult)
        else None,
        queue_alert_before=event.retval.queue_alert_before
        if isinstance(event.retval, QueueDispatchResult)
        else None,
        queue_alert_after=event.retval.queue_alert_after
        if isinstance(event.retval, QueueDispatchResult)
        else None,
    )


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the background job scheduler."""
    scheduler = AsyncIOScheduler()

    # Scraping: every 6 hours
    scheduler.add_job(
        enqueue_registered_job,
        IntervalTrigger(hours=6),
        id="scheduled_scrape",
        kwargs={"job_name": "scheduled_scrape"},
        replace_existing=True,
    )

    # Career pages: every 12 hours
    scheduler.add_job(
        enqueue_registered_job,
        IntervalTrigger(hours=12),
        id="career_page_scrape",
        kwargs={"job_name": "career_page_scrape"},
        replace_existing=True,
    )

    # Enrichment: every 30 minutes
    scheduler.add_job(
        enqueue_registered_job,
        IntervalTrigger(minutes=30),
        id="enrichment_batch",
        kwargs={"job_name": "enrichment_batch"},
        replace_existing=True,
    )

    # Embeddings: every hour
    scheduler.add_job(
        enqueue_registered_job,
        IntervalTrigger(hours=1),
        id="embedding_batch",
        kwargs={"job_name": "embedding_batch"},
        replace_existing=True,
    )

    # TF-IDF: every 2 hours
    scheduler.add_job(
        enqueue_registered_job,
        IntervalTrigger(hours=2),
        id="tfidf_scoring",
        kwargs={"job_name": "tfidf_scoring"},
        replace_existing=True,
    )

    # Cleanup: daily
    scheduler.add_job(
        enqueue_registered_job,
        IntervalTrigger(days=1),
        id="cleanup",
        kwargs={"job_name": "cleanup"},
        replace_existing=True,
    )

    # Daily digest: once per day
    scheduler.add_job(
        enqueue_registered_job,
        IntervalTrigger(days=1),
        id="daily_digest",
        kwargs={"job_name": "daily_digest"},
        replace_existing=True,
    )

    # Gmail sync: every 30 minutes
    scheduler.add_job(
        enqueue_registered_job,
        IntervalTrigger(minutes=30),
        id="gmail_sync",
        kwargs={"job_name": "gmail_sync"},
        replace_existing=True,
    )

    # Source health: every 4 hours
    scheduler.add_job(
        enqueue_registered_job,
        IntervalTrigger(hours=4),
        id="source_health",
        kwargs={"job_name": "source_health"},
        replace_existing=True,
    )

    # Auto-apply: every 4 hours
    scheduler.add_job(
        enqueue_registered_job,
        IntervalTrigger(hours=4),
        id="auto_apply_batch",
        kwargs={"job_name": "auto_apply_batch"},
        replace_existing=True,
    )

    # Saved search alerts: every 30 minutes
    scheduler.add_job(
        enqueue_registered_job,
        IntervalTrigger(minutes=30),
        id="saved_search_alerts",
        kwargs={"job_name": "saved_search_alerts"},
        replace_existing=True,
    )

    # Phase 7A: staleness sweep every 6 hours
    scheduler.add_job(
        enqueue_registered_job,
        IntervalTrigger(hours=6),
        id="staleness_sweep",
        kwargs={"job_name": "staleness_sweep"},
        replace_existing=True,
    )

    # Phase 7A: source health checks every 4 hours
    scheduler.add_job(
        enqueue_registered_job,
        IntervalTrigger(hours=4),
        id="phase7a_source_health",
        kwargs={"job_name": "phase7a_source_health"},
        replace_existing=True,
    )

    # Phase 7A: follow-up reminders every hour
    scheduler.add_job(
        enqueue_registered_job,
        IntervalTrigger(hours=1),
        id="followup_reminders",
        kwargs={"job_name": "followup_reminders"},
        replace_existing=True,
    )

    # Target-based pipeline: career page targets every 30 minutes
    scheduler.add_job(
        enqueue_registered_job,
        IntervalTrigger(minutes=30),
        id="target_batch_career_page",
        kwargs={"job_name": "target_batch_career_page"},
        replace_existing=True,
    )

    # Target-based pipeline: watchlist targets every 2 hours
    scheduler.add_job(
        enqueue_registered_job,
        IntervalTrigger(hours=2),
        id="target_batch_watchlist",
        kwargs={"job_name": "target_batch_watchlist"},
        replace_existing=True,
    )

    jobs = scheduler.get_jobs()
    scheduler.add_listener(_log_job_event, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED)
    logger.info(
        "scheduler_configured",
        job_count=len(jobs),
        job_ids=[job.id for job in jobs],
        worker_job_ids=get_registered_job_ids(),
        dispatch_mode="arq_enqueue",
    )

    return scheduler
