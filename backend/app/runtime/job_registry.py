from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, cast

import structlog
from arq.worker import Retry

from app.runtime.worker_metrics import increment_worker_counter
from app.workers.alert_worker import check_saved_search_alerts
from app.workers.auto_apply_worker import run_auto_apply_batch
from app.workers.digest_worker import run_daily_digest
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


def _job_log_fields(ctx: dict[str, Any], *, queue_name: str) -> dict[str, Any]:
    job_try = int(ctx.get("job_try") or 1)
    queue_job_id = ctx.get("job_id")
    registered_job = REGISTERED_JOBS.get(str(ctx.get("job_name", "")))
    max_tries = registered_job.max_tries if registered_job is not None else None
    retry_remaining = max(max_tries - job_try, 0) if max_tries is not None else None
    return {
        "job_id": queue_job_id,
        "queue_job_id": queue_job_id,
        "queue_correlation_id": queue_job_id,
        "job_try": job_try,
        "queue_name": queue_name,
        "job_max_tries": max_tries,
        "job_retryable": (max_tries or 0) > 1,
        "job_retry_remaining": retry_remaining,
    }


def _retry_delay_seconds(job_try: int) -> int:
    return int(min(30 * (2 ** max(job_try - 1, 0)), 300))


async def _run_with_lifecycle(
    *,
    job_name: str,
    queue_name: str,
    ctx: dict[str, Any] | None,
    callback: Callable[[], Awaitable[None]],
) -> None:
    context = {"job_name": job_name, **dict(ctx or {})}
    log_fields = _job_log_fields(context, queue_name=queue_name)
    redis = cast(Any, context.get("redis"))
    worker_role = str(context.get("worker_role", ""))
    health_interval_seconds = int(context.get("health_check_interval_seconds") or 15)
    logger.info("queue_job_started", job_name=job_name, **log_fields)
    try:
        await callback()
    except Retry as exc:
        await increment_worker_counter(
            redis,
            role=worker_role,
            counter_name="retry_scheduled_total",
            health_interval_seconds=health_interval_seconds,
        )
        logger.warning(
            "queue_job_retry_requested",
            job_name=job_name,
            retry_in_seconds=(exc.defer_score or 0) / 1000,
            **log_fields,
        )
        raise
    except Exception:
        if (
            log_fields["job_retryable"]
            and log_fields["job_max_tries"] is not None
            and log_fields["job_try"] < log_fields["job_max_tries"]
        ):
            retry_in_seconds = _retry_delay_seconds(log_fields["job_try"])
            await increment_worker_counter(
                redis,
                role=worker_role,
                counter_name="retry_scheduled_total",
                health_interval_seconds=health_interval_seconds,
            )
            logger.exception(
                "queue_job_retry_scheduled",
                job_name=job_name,
                retry_in_seconds=retry_in_seconds,
                **log_fields,
            )
            raise Retry(defer=retry_in_seconds)
        await increment_worker_counter(
            redis,
            role=worker_role,
            counter_name="queue_job_failed_total",
            health_interval_seconds=health_interval_seconds,
        )
        if bool(log_fields["job_retryable"]):
            await increment_worker_counter(
                redis,
                role=worker_role,
                counter_name="retry_exhausted_total",
                health_interval_seconds=health_interval_seconds,
            )
        logger.exception(
            "queue_job_failed",
            job_name=job_name,
            will_retry=False,
            retry_exhausted=bool(log_fields["job_retryable"]),
            **log_fields,
        )
        raise
    await increment_worker_counter(
        redis,
        role=worker_role,
        counter_name="queue_job_completed_total",
        health_interval_seconds=health_interval_seconds,
    )
    logger.info("queue_job_completed", job_name=job_name, **log_fields)


async def _run_scheduled_scrape(ctx: dict[str, Any]) -> None:
    await _run_with_lifecycle(
        job_name="scheduled_scrape",
        queue_name=SCRAPING_QUEUE,
        ctx=ctx,
        callback=lambda: run_scheduled_scrape(ctx=ctx),
    )


async def _run_career_page_scrape(ctx: dict[str, Any]) -> None:
    await _run_with_lifecycle(
        job_name="career_page_scrape",
        queue_name=SCRAPING_QUEUE,
        ctx=ctx,
        callback=lambda: run_career_page_scrape(ctx=ctx),
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


REGISTERED_JOBS: dict[str, RegisteredJob] = {
    "scheduled_scrape": RegisteredJob(
        name="scheduled_scrape",
        queue_name=SCRAPING_QUEUE,
        runner=_run_scheduled_scrape,
        timeout_seconds=1800,
        max_tries=2,
    ),
    "career_page_scrape": RegisteredJob(
        name="career_page_scrape",
        queue_name=SCRAPING_QUEUE,
        runner=_run_career_page_scrape,
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
