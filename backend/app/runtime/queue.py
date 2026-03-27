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
from app.runtime.job_registry import (
    ANALYSIS_QUEUE,
    OPS_QUEUE,
    SCRAPING_QUEUE,
    get_queue_names,
    get_registered_job,
)

logger = structlog.get_logger()

_queue_pool: ArqRedis | None = None
_queue_pool_lock = asyncio.Lock()
VALID_QUEUE_PRESSURES = frozenset({"nominal", "elevated", "saturated"})
VALID_QUEUE_ALERTS = frozenset({"clear", "watch", "backlog", "stalled"})
_CORRELATION_ID_SANITIZER = re.compile(r"[^A-Za-z0-9_-]+")

QUEUE_PRESSURE_THRESHOLDS: dict[str, tuple[int, int]] = {
    SCRAPING_QUEUE: (10, 25),
    ANALYSIS_QUEUE: (20, 50),
    OPS_QUEUE: (5, 15),
}

QUEUE_ALERT_AGE_THRESHOLDS_SECONDS: dict[str, tuple[int, int]] = {
    SCRAPING_QUEUE: (300, 1200),
    ANALYSIS_QUEUE: (180, 900),
    OPS_QUEUE: (120, 600),
}


@dataclass(frozen=True)
class QueueSnapshot:
    queue_name: str
    queue_depth: int
    queue_pressure: str
    oldest_job_age_seconds: int
    queue_alert: str


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
                queue_names=get_queue_names(),
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
    queue_names = get_queue_names()
    queue_depths = await asyncio.gather(
        *(active_pool.zcard(queue_name) for queue_name in queue_names)
    )
    return dict(zip(queue_names, queue_depths, strict=True))


def classify_queue_pressure(queue_name: str, depth: int) -> str:
    elevated_threshold, saturated_threshold = QUEUE_PRESSURE_THRESHOLDS.get(queue_name, (10, 25))
    if depth >= saturated_threshold:
        return "saturated"
    if depth >= elevated_threshold:
        return "elevated"
    return "nominal"


def summarize_queue_pressures(queue_depths: dict[str, int]) -> dict[str, str]:
    return {
        queue_name: classify_queue_pressure(queue_name, depth)
        for queue_name, depth in queue_depths.items()
    }


def classify_queue_alert(queue_name: str, *, pressure: str, oldest_job_age_seconds: int) -> str:
    watch_age_seconds, stalled_age_seconds = QUEUE_ALERT_AGE_THRESHOLDS_SECONDS.get(
        queue_name, (180, 900)
    )
    if oldest_job_age_seconds >= stalled_age_seconds:
        return "stalled"
    if pressure == "saturated":
        return "backlog"
    if pressure == "elevated" or oldest_job_age_seconds >= watch_age_seconds:
        return "watch"
    return "clear"


def derive_overall_pressure(queue_pressures: dict[str, str]) -> str:
    if "saturated" in queue_pressures.values():
        return "saturated"
    if "elevated" in queue_pressures.values():
        return "elevated"
    return "nominal"


def derive_overall_alert(queue_alerts: dict[str, str]) -> str:
    if "stalled" in queue_alerts.values():
        return "stalled"
    if "backlog" in queue_alerts.values():
        return "backlog"
    if "watch" in queue_alerts.values():
        return "watch"
    return "clear"


def _current_unix_ms() -> int:
    return int(time.time() * 1000)


def _score_to_oldest_job_age_seconds(score: float | int | None) -> int:
    if score is None:
        return 0
    age_ms = max(_current_unix_ms() - int(score), 0)
    return age_ms // 1000


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
    queue_names = get_queue_names()
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


async def enqueue_registered_job(
    job_name: str,
    correlation_id: str | None = None,
) -> QueueDispatchResult:
    job = get_registered_job(job_name)
    queue_pool = await get_queue_pool()
    before_snapshot = await capture_queue_snapshot(job.queue_name, queue_pool)
    normalized_correlation_id = sanitize_correlation_id(correlation_id)
    requested_job_id = (
        normalized_correlation_id
        if normalized_correlation_id is not None
        else f"{job.name}-{uuid4().hex}"
    )
    job_ref = await queue_pool.enqueue_job(
        job.name,
        _job_id=requested_job_id,
        _queue_name=job.queue_name,
    )
    enqueued_job_id = getattr(job_ref, "job_id", requested_job_id)
    if not isinstance(enqueued_job_id, str):
        enqueued_job_id = requested_job_id
    after_snapshot = await capture_queue_snapshot(job.queue_name, queue_pool)
    logger.info(
        "scheduler_job_enqueued",
        job_name=job.name,
        queue_name=job.queue_name,
        enqueued_job_id=enqueued_job_id,
        queue_job_id=enqueued_job_id,
        queue_correlation_id=normalized_correlation_id or enqueued_job_id,
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
        queue_correlation_id=normalized_correlation_id or enqueued_job_id,
        oldest_job_age_seconds_before=before_snapshot.oldest_job_age_seconds,
        oldest_job_age_seconds_after=after_snapshot.oldest_job_age_seconds,
        queue_alert_before=before_snapshot.queue_alert,
        queue_alert_after=after_snapshot.queue_alert,
    )
