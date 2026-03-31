from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import unquote, urlparse
from uuid import uuid4

import structlog
from arq.connections import ArqRedis, RedisSettings, create_pool

from app.config import settings
from app.runtime import job_context, queue_state

logger = structlog.get_logger()

_queue_pool: ArqRedis | None = None
_queue_pool_lock = asyncio.Lock()
JOB_METADATA_TTL_SECONDS = job_context.JOB_METADATA_TTL_SECONDS
VALID_QUEUE_PRESSURES = queue_state.VALID_QUEUE_PRESSURES
VALID_QUEUE_ALERTS = queue_state.VALID_QUEUE_ALERTS
_CORRELATION_ID_SANITIZER = re.compile(r"[^A-Za-z0-9_-]+")
SCRAPING_QUEUE = queue_state.SCRAPING_QUEUE
ANALYSIS_QUEUE = queue_state.ANALYSIS_QUEUE
OPS_QUEUE = queue_state.OPS_QUEUE
QUEUE_PRESSURE_THRESHOLDS = queue_state.QUEUE_PRESSURE_THRESHOLDS
QUEUE_ALERT_AGE_THRESHOLDS_SECONDS = queue_state.QUEUE_ALERT_AGE_THRESHOLDS_SECONDS
QueueSnapshot = queue_state.QueueSnapshot
classify_queue_pressure = queue_state.classify_queue_pressure
summarize_queue_pressures = queue_state.summarize_queue_pressures
classify_queue_alert = queue_state.classify_queue_alert
derive_overall_pressure = queue_state.derive_overall_pressure
derive_overall_alert = queue_state.derive_overall_alert


def _get_queue_names() -> list[str]:
    from app.runtime.job_registry import get_queue_names

    return get_queue_names()


def _get_registered_job(job_name: str) -> Any:
    from app.runtime.job_registry import get_registered_job

    return get_registered_job(job_name)


def _configured_worker_health_interval_seconds() -> int:
    from app.runtime.worker_metrics import configured_worker_health_interval_seconds

    return configured_worker_health_interval_seconds()


async def _sync_worker_queue_metrics_for_queue(
    redis: ArqRedis | None,
    *,
    snapshot: "QueueSnapshot",
    health_interval_seconds: int,
) -> None:
    from app.runtime.worker_metrics import sync_worker_queue_metrics_for_queue

    await sync_worker_queue_metrics_for_queue(
        redis,
        snapshot=snapshot,
        health_interval_seconds=health_interval_seconds,
    )


def configured_worker_health_interval_seconds() -> int:
    return _configured_worker_health_interval_seconds()


async def sync_worker_queue_metrics_for_queue(
    redis: ArqRedis | None,
    *,
    snapshot: "QueueSnapshot",
    health_interval_seconds: int,
) -> None:
    await _sync_worker_queue_metrics_for_queue(
        redis,
        snapshot=snapshot,
        health_interval_seconds=health_interval_seconds,
    )


def _current_unix_ms() -> int:
    return int(time.time() * 1000)


def _score_to_oldest_job_age_seconds(score: float | int | None) -> int:
    if score is None:
        return 0
    age_ms = max(_current_unix_ms() - int(score), 0)
    return age_ms // 1000


@dataclass(frozen=True)
class QueueDispatchResult:
    job_name: str
    queue_name: str
    enqueued_job_id: str | None
    queue_depth_before: int
    queue_depth_after: int
    queue_pressure_before: str
    queue_pressure_after: str
    queue_job_id: str | None = None
    queue_correlation_id: str | None = None
    oldest_job_age_seconds_before: int = 0
    oldest_job_age_seconds_after: int = 0
    queue_alert_before: str = "clear"
    queue_alert_after: str = "clear"


def build_redis_settings() -> RedisSettings:
    parsed = urlparse(settings.redis_url)
    if parsed.scheme not in {"redis", "rediss"} or not parsed.hostname:
        raise RuntimeError(
            "JR_REDIS_URL must use redis:// or rediss:// with an explicit host."
        )

    database = int((parsed.path or "/0").lstrip("/") or "0")
    ssl_enabled = settings.redis_use_tls or parsed.scheme == "rediss"

    return RedisSettings(
        host=parsed.hostname,
        port=parsed.port or 6379,
        database=database,
        username=unquote(parsed.username) if parsed.username else None,
        password=unquote(parsed.password) if parsed.password else None,
        ssl=ssl_enabled,
    )


async def startup_queue_pool() -> ArqRedis:
    global _queue_pool
    async with _queue_pool_lock:
        if _queue_pool is None:
            redis_settings = build_redis_settings()
            _queue_pool = await create_pool(redis_settings)
            await _queue_pool.ping()
            logger.info(
                "queue_pool_ready",
                redis_host=redis_settings.host,
                redis_port=redis_settings.port,
                redis_database=redis_settings.database,
                redis_tls=redis_settings.ssl,
                queue_names=_get_queue_names(),
            )
    return _queue_pool


async def get_queue_pool() -> ArqRedis:
    if _queue_pool is not None:
        return _queue_pool
    return await startup_queue_pool()


async def shutdown_queue_pool() -> None:
    global _queue_pool
    async with _queue_pool_lock:
        if _queue_pool is not None:
            await _queue_pool.close(close_connection_pool=True)
            _queue_pool = None
            logger.info("queue_pool_stopped")


async def get_queue_depths(queue_pool: ArqRedis | None = None) -> dict[str, int]:
    active_pool = queue_pool or await get_queue_pool()
    queue_names = _get_queue_names()
    queue_depths = await asyncio.gather(
        *(active_pool.zcard(queue_name) for queue_name in queue_names)
    )
    return dict(zip(queue_names, queue_depths, strict=True))


async def _get_oldest_queue_score(queue_name: str, queue_pool: ArqRedis) -> float | int | None:
    if not hasattr(queue_pool, "zrange"):
        return None
    entries = await cast(Any, queue_pool).zrange(queue_name, 0, 0, withscores=True)
    if not entries:
        return None
    raw_score = entries[0][1]
    if isinstance(raw_score, (int, float)):
        return raw_score
    try:
        return float(raw_score)
    except (TypeError, ValueError):
        return None


async def capture_queue_snapshot(
    queue_name: str,
    queue_pool: ArqRedis | None = None,
) -> QueueSnapshot:
    active_pool = queue_pool or await get_queue_pool()
    queue_depth = await active_pool.zcard(queue_name)
    queue_pressure = classify_queue_pressure(queue_name, queue_depth)
    oldest_job_age_seconds = _score_to_oldest_job_age_seconds(
        await _get_oldest_queue_score(queue_name, active_pool)
    )
    queue_alert = classify_queue_alert(
        queue_name,
        pressure=queue_pressure,
        oldest_job_age_seconds=oldest_job_age_seconds,
    )
    return QueueSnapshot(
        queue_name=queue_name,
        queue_depth=queue_depth,
        queue_pressure=queue_pressure,
        oldest_job_age_seconds=oldest_job_age_seconds,
        queue_alert=queue_alert,
    )


async def get_queue_snapshots(
    queue_pool: ArqRedis | None = None,
) -> dict[str, QueueSnapshot]:
    active_pool = queue_pool or await get_queue_pool()
    queue_names = _get_queue_names()
    snapshots = await asyncio.gather(
        *(capture_queue_snapshot(queue_name, active_pool) for queue_name in queue_names)
    )
    return {snapshot.queue_name: snapshot for snapshot in snapshots}


def sanitize_correlation_id(correlation_id: str | None) -> str | None:
    if correlation_id is None:
        return None
    normalized = _CORRELATION_ID_SANITIZER.sub("-", correlation_id).strip("-")
    if not normalized:
        return None
    return normalized[:96]


def build_job_metadata_key(job_id: str) -> str:
    return job_context.build_job_metadata_key(job_id)


async def enqueue_registered_job(
    job_name: str,
    correlation_id: str | None = None,
    **job_kwargs: object,
) -> QueueDispatchResult:
    job = _get_registered_job(job_name)
    queue_pool = await get_queue_pool()
    before_snapshot = await capture_queue_snapshot(job.queue_name, queue_pool)
    normalized_correlation_id = sanitize_correlation_id(correlation_id)
    requested_job_id = f"{job.name}-{uuid4().hex}"
    job_ref = await queue_pool.enqueue_job(
        job.name,
        _job_id=requested_job_id,
        _queue_name=job.queue_name,
    )
    if job_ref is None:
        logger.warning(
            "scheduler_job_enqueue_failed",
            job_name=job.name,
            queue_name=job.queue_name,
            queue_job_id=requested_job_id,
            queue_correlation_id=normalized_correlation_id,
            failure_reason="missing_job_reference",
        )
        raise RuntimeError(
            f"Queue enqueue for job '{job.name}' returned no job reference; treating as failure."
        )
    enqueued_job_id = getattr(job_ref, "job_id", None)
    if not isinstance(enqueued_job_id, str) or not enqueued_job_id.strip():
        logger.warning(
            "scheduler_job_enqueue_failed",
            job_name=job.name,
            queue_name=job.queue_name,
            queue_job_id=requested_job_id,
            queue_correlation_id=normalized_correlation_id,
            failure_reason="invalid_job_id",
        )
        raise RuntimeError(
            f"Queue enqueue for job '{job.name}' returned an invalid job id; treating as failure."
        )
    effective_queue_correlation_id = normalized_correlation_id or enqueued_job_id
    if job_context.build_job_metadata_payload(
        correlation_id=effective_queue_correlation_id,
        job_kwargs=job_kwargs,
    ):
        await job_context.store_job_metadata(
            queue_pool,
            job_id=enqueued_job_id,
            correlation_id=effective_queue_correlation_id,
            job_kwargs=job_kwargs,
        )
    after_snapshot = await capture_queue_snapshot(job.queue_name, queue_pool)
    await sync_worker_queue_metrics_for_queue(
        queue_pool,
        snapshot=after_snapshot,
        health_interval_seconds=configured_worker_health_interval_seconds(),
    )
    logger.info(
        "scheduler_job_enqueued",
        job_name=job.name,
        queue_name=job.queue_name,
        enqueued_job_id=enqueued_job_id,
        queue_job_id=enqueued_job_id,
        queue_correlation_id=effective_queue_correlation_id,
        queue_depth_before=before_snapshot.queue_depth,
        queue_depth_after=after_snapshot.queue_depth,
        queue_pressure_before=before_snapshot.queue_pressure,
        queue_pressure_after=after_snapshot.queue_pressure,
        oldest_job_age_seconds_before=before_snapshot.oldest_job_age_seconds,
        oldest_job_age_seconds_after=after_snapshot.oldest_job_age_seconds,
        queue_alert_before=before_snapshot.queue_alert,
        queue_alert_after=after_snapshot.queue_alert,
        job_max_tries=job.max_tries,
        job_timeout_seconds=job.timeout_seconds,
    )
    return QueueDispatchResult(
        job_name=job.name,
        queue_name=job.queue_name,
        enqueued_job_id=enqueued_job_id,
        queue_depth_before=before_snapshot.queue_depth,
        queue_depth_after=after_snapshot.queue_depth,
        queue_pressure_before=before_snapshot.queue_pressure,
        queue_pressure_after=after_snapshot.queue_pressure,
        queue_job_id=enqueued_job_id,
        queue_correlation_id=effective_queue_correlation_id,
        oldest_job_age_seconds_before=before_snapshot.oldest_job_age_seconds,
        oldest_job_age_seconds_after=after_snapshot.oldest_job_age_seconds,
        queue_alert_before=before_snapshot.queue_alert,
        queue_alert_after=after_snapshot.queue_alert,
    )
