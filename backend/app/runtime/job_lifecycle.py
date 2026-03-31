from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any, cast

from arq.worker import Retry

from app.runtime.job_context import resolve_queue_correlation_id

IncrementWorkerCounter = Callable[..., Awaitable[int | None]]
WorkerCallback = Callable[[], Awaitable[None]]


def build_job_log_fields(
    ctx: dict[str, Any],
    *,
    queue_name: str,
    registered_jobs: Mapping[str, Any],
) -> dict[str, Any]:
    job_try = int(ctx.get("job_try") or 1)
    queue_job_id = ctx.get("job_id")
    registered_job = registered_jobs.get(str(ctx.get("job_name", "")))
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


def retry_delay_seconds(job_try: int) -> int:
    return int(min(30 * (2 ** max(job_try - 1, 0)), 300))


async def run_with_lifecycle(
    *,
    job_name: str,
    queue_name: str,
    ctx: dict[str, Any] | None,
    callback: WorkerCallback,
    logger: Any,
    registered_jobs: Mapping[str, Any],
    increment_worker_counter: IncrementWorkerCounter,
) -> None:
    context = {"job_name": job_name, **dict(ctx or {})}
    log_fields = build_job_log_fields(
        context,
        queue_name=queue_name,
        registered_jobs=registered_jobs,
    )
    log_fields["queue_correlation_id"] = await resolve_queue_correlation_id(
        context,
        logger=logger,
    )
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
            retry_in_seconds = retry_delay_seconds(log_fields["job_try"])
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
