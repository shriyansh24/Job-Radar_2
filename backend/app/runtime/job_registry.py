from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import structlog
from arq.worker import Retry

from app.runtime.job_lifecycle import run_with_lifecycle
from app.workers.alert_worker import check_saved_search_alerts
from app.workers.auto_apply_worker import run_auto_apply_batch
from app.workers.digest_worker import run_daily_digest
from app.workers.enrichment_worker import (
    run_embedding_batch,
    run_enrichment_batch,
    run_tfidf_scoring,
)
from app.workers.gmail_worker import run_gmail_sync
from app.workers.maintenance_worker import run_cleanup, run_source_health_check
from app.workers.phase7a_worker import (
    run_followup_reminders,
    run_staleness_sweep,
)
from app.workers.phase7a_worker import (
    run_source_health_checks as run_phase7a_source_health,
)
from app.workers.scraping_worker import (
    run_scheduled_scrape,
    run_target_batch_job,
)

logger = structlog.get_logger()
__all__ = ["Retry"]

SCRAPING_QUEUE = "arq:queue:scraping"
ANALYSIS_QUEUE = "arq:queue:analysis"
OPS_QUEUE = "arq:queue:ops"
QueueName = str
WorkerJob = Callable[..., Awaitable[None]]


@dataclass(frozen=True)
class RegisteredJob:
    name: str
    queue_name: QueueName
    runner: WorkerJob
    timeout_seconds: int
    max_tries: int


async def increment_worker_counter(
    redis: Any,
    *,
    role: str,
    counter_name: str,
    health_interval_seconds: int,
) -> int | None:
    from app.runtime.worker_metrics import increment_worker_counter as _increment_worker_counter

    return await _increment_worker_counter(
        redis,
        role=role,
        counter_name=counter_name,
        health_interval_seconds=health_interval_seconds,
    )


async def _run_with_lifecycle(
    *,
    job_name: str,
    queue_name: str,
    ctx: dict[str, Any] | None,
    callback: Callable[[], Awaitable[None]],
) -> None:
    await run_with_lifecycle(
        job_name=job_name,
        queue_name=queue_name,
        ctx=ctx,
        callback=callback,
        logger=logger,
        registered_jobs=REGISTERED_JOBS,
        increment_worker_counter=increment_worker_counter,
    )


async def _run_scheduled_scrape(ctx: dict[str, Any]) -> None:
    await _run_with_lifecycle(
        job_name="scheduled_scrape",
        queue_name=SCRAPING_QUEUE,
        ctx=ctx,
        callback=lambda: run_scheduled_scrape(ctx=ctx),
    )


async def _run_target_batch_career_page(ctx: dict[str, Any]) -> None:
    await _run_with_lifecycle(
        job_name="target_batch_career_page",
        queue_name=SCRAPING_QUEUE,
        ctx=ctx,
        callback=lambda: run_target_batch_job(
            source_kind="career_page",
            batch_size=50,
            ctx=ctx,
        ),
    )


async def _run_target_batch_watchlist(ctx: dict[str, Any]) -> None:
    await _run_with_lifecycle(
        job_name="target_batch_watchlist",
        queue_name=SCRAPING_QUEUE,
        ctx=ctx,
        callback=lambda: run_target_batch_job(
            source_kind="watchlist",
            batch_size=25,
            ctx=ctx,
        ),
    )


async def _run_enrichment_batch(
    ctx: dict[str, Any],
    user_id: str | None = None,
) -> None:
    await _run_with_lifecycle(
        job_name="enrichment_batch",
        queue_name=ANALYSIS_QUEUE,
        ctx=ctx,
        callback=lambda: run_enrichment_batch(ctx=ctx, user_id=user_id),
    )


async def _run_embedding_batch(ctx: dict[str, Any]) -> None:
    await _run_with_lifecycle(
        job_name="embedding_batch",
        queue_name=ANALYSIS_QUEUE,
        ctx=ctx,
        callback=lambda: run_embedding_batch(ctx=ctx),
    )


async def _run_tfidf_scoring(ctx: dict[str, Any]) -> None:
    await _run_with_lifecycle(
        job_name="tfidf_scoring",
        queue_name=ANALYSIS_QUEUE,
        ctx=ctx,
        callback=lambda: run_tfidf_scoring(ctx=ctx),
    )


async def _run_cleanup(ctx: dict[str, Any]) -> None:
    await _run_with_lifecycle(
        job_name="cleanup",
        queue_name=OPS_QUEUE,
        ctx=ctx,
        callback=lambda: run_cleanup(ctx=ctx),
    )


async def _run_source_health_check(ctx: dict[str, Any]) -> None:
    await _run_with_lifecycle(
        job_name="source_health",
        queue_name=OPS_QUEUE,
        ctx=ctx,
        callback=lambda: run_source_health_check(ctx=ctx),
    )


async def _run_auto_apply_batch(ctx: dict[str, Any]) -> None:
    await _run_with_lifecycle(
        job_name="auto_apply_batch",
        queue_name=OPS_QUEUE,
        ctx=ctx,
        callback=lambda: run_auto_apply_batch(ctx=ctx),
    )


async def _run_saved_search_alerts(ctx: dict[str, Any]) -> None:
    await _run_with_lifecycle(
        job_name="saved_search_alerts",
        queue_name=OPS_QUEUE,
        ctx=ctx,
        callback=check_saved_search_alerts,
    )


async def _run_staleness_sweep(ctx: dict[str, Any]) -> None:
    await _run_with_lifecycle(
        job_name="staleness_sweep",
        queue_name=OPS_QUEUE,
        ctx=ctx,
        callback=run_staleness_sweep,
    )


async def _run_phase7a_source_health(ctx: dict[str, Any]) -> None:
    await _run_with_lifecycle(
        job_name="phase7a_source_health",
        queue_name=OPS_QUEUE,
        ctx=ctx,
        callback=run_phase7a_source_health,
    )


async def _run_followup_reminders(ctx: dict[str, Any]) -> None:
    await _run_with_lifecycle(
        job_name="followup_reminders",
        queue_name=OPS_QUEUE,
        ctx=ctx,
        callback=run_followup_reminders,
    )


async def _run_daily_digest(ctx: dict[str, Any]) -> None:
    await _run_with_lifecycle(
        job_name="daily_digest",
        queue_name=OPS_QUEUE,
        ctx=ctx,
        callback=lambda: run_daily_digest(ctx=ctx),
    )


async def _run_gmail_sync(ctx: dict[str, Any]) -> None:
    await _run_with_lifecycle(
        job_name="gmail_sync",
        queue_name=OPS_QUEUE,
        ctx=ctx,
        callback=lambda: run_gmail_sync(ctx=ctx),
    )


REGISTERED_JOBS: dict[str, RegisteredJob] = {
    "scheduled_scrape": RegisteredJob(
        name="scheduled_scrape",
        queue_name=SCRAPING_QUEUE,
        runner=_run_scheduled_scrape,
        timeout_seconds=1800,
        max_tries=2,
    ),
    "target_batch_career_page": RegisteredJob(
        name="target_batch_career_page",
        queue_name=SCRAPING_QUEUE,
        runner=_run_target_batch_career_page,
        timeout_seconds=1800,
        max_tries=2,
    ),
    "target_batch_watchlist": RegisteredJob(
        name="target_batch_watchlist",
        queue_name=SCRAPING_QUEUE,
        runner=_run_target_batch_watchlist,
        timeout_seconds=1800,
        max_tries=2,
    ),
    "enrichment_batch": RegisteredJob(
        name="enrichment_batch",
        queue_name=ANALYSIS_QUEUE,
        runner=_run_enrichment_batch,
        timeout_seconds=1800,
        max_tries=3,
    ),
    "embedding_batch": RegisteredJob(
        name="embedding_batch",
        queue_name=ANALYSIS_QUEUE,
        runner=_run_embedding_batch,
        timeout_seconds=1800,
        max_tries=3,
    ),
    "tfidf_scoring": RegisteredJob(
        name="tfidf_scoring",
        queue_name=ANALYSIS_QUEUE,
        runner=_run_tfidf_scoring,
        timeout_seconds=1800,
        max_tries=2,
    ),
    "cleanup": RegisteredJob(
        name="cleanup",
        queue_name=OPS_QUEUE,
        runner=_run_cleanup,
        timeout_seconds=900,
        max_tries=2,
    ),
    "source_health": RegisteredJob(
        name="source_health",
        queue_name=OPS_QUEUE,
        runner=_run_source_health_check,
        timeout_seconds=900,
        max_tries=2,
    ),
    "auto_apply_batch": RegisteredJob(
        name="auto_apply_batch",
        queue_name=OPS_QUEUE,
        runner=_run_auto_apply_batch,
        timeout_seconds=3600,
        max_tries=1,
    ),
    "saved_search_alerts": RegisteredJob(
        name="saved_search_alerts",
        queue_name=OPS_QUEUE,
        runner=_run_saved_search_alerts,
        timeout_seconds=900,
        max_tries=2,
    ),
    "staleness_sweep": RegisteredJob(
        name="staleness_sweep",
        queue_name=OPS_QUEUE,
        runner=_run_staleness_sweep,
        timeout_seconds=900,
        max_tries=2,
    ),
    "phase7a_source_health": RegisteredJob(
        name="phase7a_source_health",
        queue_name=OPS_QUEUE,
        runner=_run_phase7a_source_health,
        timeout_seconds=900,
        max_tries=2,
    ),
    "followup_reminders": RegisteredJob(
        name="followup_reminders",
        queue_name=OPS_QUEUE,
        runner=_run_followup_reminders,
        timeout_seconds=900,
        max_tries=2,
    ),
    "daily_digest": RegisteredJob(
        name="daily_digest",
        queue_name=OPS_QUEUE,
        runner=_run_daily_digest,
        timeout_seconds=1800,
        max_tries=2,
    ),
    "gmail_sync": RegisteredJob(
        name="gmail_sync",
        queue_name=OPS_QUEUE,
        runner=_run_gmail_sync,
        timeout_seconds=1800,
        max_tries=2,
    ),
}


def get_registered_job(job_name: str) -> RegisteredJob:
    try:
        return REGISTERED_JOBS[job_name]
    except KeyError as exc:
        raise ValueError(f"Unknown worker job '{job_name}'") from exc


def get_registered_job_ids() -> list[str]:
    return sorted(REGISTERED_JOBS)


def get_registered_jobs(*, queue_name: str | None = None) -> list[RegisteredJob]:
    jobs = sorted(REGISTERED_JOBS.values(), key=lambda job: job.name)
    if queue_name is None:
        return jobs
    return [job for job in jobs if job.queue_name == queue_name]


def get_queue_names() -> list[str]:
    return sorted({job.queue_name for job in REGISTERED_JOBS.values()})
