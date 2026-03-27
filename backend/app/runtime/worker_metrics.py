from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from arq.connections import ArqRedis

if TYPE_CHECKING:
    from app.runtime.queue import QueueSnapshot

COUNTER_FIELDS = (
    "retry_exhausted_total",
    "retry_scheduled_total",
    "queue_job_completed_total",
    "queue_job_failed_total",
)


def worker_metrics_key(role: str) -> str:
    return f"jobradar:worker-metrics:{role}"


def worker_metrics_ttl_seconds(health_interval_seconds: int) -> int:
    return max(health_interval_seconds * 4, 60)


async def _get_counter_values(
    redis: ArqRedis,
    *,
    key: str,
) -> dict[str, int]:
    raw_values = await cast(Any, redis).hmget(key, *COUNTER_FIELDS)
    counters: dict[str, int] = {}
    for field_name, raw_value in zip(COUNTER_FIELDS, raw_values, strict=True):
        if raw_value is None:
            counters[field_name] = 0
            continue
        if isinstance(raw_value, bytes):
            raw_value = raw_value.decode()
        counters[field_name] = int(raw_value)
    return counters


async def sync_worker_queue_metrics(
    redis: ArqRedis | None,
    *,
    role: str,
    snapshot: QueueSnapshot,
    health_interval_seconds: int,
) -> None:
    if redis is None:
        return

    key = worker_metrics_key(role)
    counters = await _get_counter_values(redis, key=key)
    mapping = {
        "queue_name": snapshot.queue_name,
        "queue_depth": snapshot.queue_depth,
        "queue_pressure": snapshot.queue_pressure,
        "oldest_job_age_seconds": snapshot.oldest_job_age_seconds,
        "queue_alert": snapshot.queue_alert,
        **counters,
    }
    await cast(Any, redis).hset(key, mapping=mapping)
    await cast(Any, redis).expire(key, worker_metrics_ttl_seconds(health_interval_seconds))


async def increment_worker_counter(
    redis: ArqRedis | None,
    *,
    role: str,
    counter_name: str,
    health_interval_seconds: int,
) -> int | None:
    if redis is None or not role:
        return None
    if counter_name not in COUNTER_FIELDS:
        raise ValueError(f"Unknown worker metric counter '{counter_name}'.")

    key = worker_metrics_key(role)
    value = await cast(Any, redis).hincrby(key, counter_name, 1)
    await cast(Any, redis).expire(key, worker_metrics_ttl_seconds(health_interval_seconds))
    return int(value)
