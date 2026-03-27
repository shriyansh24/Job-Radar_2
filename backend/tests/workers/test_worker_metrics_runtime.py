from __future__ import annotations

import pytest

from app.runtime.worker_metrics import (
    COUNTER_FIELDS,
    _get_counter_values,
    increment_worker_counter,
    sync_worker_queue_metrics,
    worker_metrics_key,
    worker_metrics_ttl_seconds,
)


class _FakeRedis:
    def __init__(self) -> None:
        self.hashes: dict[str, dict[str, object]] = {}
        self.expirations: list[tuple[str, int]] = []

    async def hmget(self, key: str, *fields: str) -> list[object | None]:
        mapping = self.hashes.get(key, {})
        return [mapping.get(field) for field in fields]

    async def hset(self, key: str, mapping: dict[str, object]) -> None:
        stored = self.hashes.setdefault(key, {})
        stored.update(mapping)

    async def expire(self, key: str, ttl: int) -> None:
        self.expirations.append((key, ttl))

    async def hincrby(self, key: str, field: str, amount: int) -> int:
        stored = self.hashes.setdefault(key, {})
        next_value = int(stored.get(field, 0)) + amount
        stored[field] = next_value
        return next_value


def test_worker_metrics_ttl_seconds_has_floor() -> None:
    assert worker_metrics_ttl_seconds(5) == 60
    assert worker_metrics_ttl_seconds(20) == 80


@pytest.mark.asyncio
async def test_get_counter_values_defaults_missing_fields_to_zero() -> None:
    redis = _FakeRedis()
    redis.hashes["jobradar:worker-metrics:ops"] = {
        "retry_exhausted_total": b"4",
        "queue_job_failed_total": "3",
    }

    counters = await _get_counter_values(redis, key="jobradar:worker-metrics:ops")

    assert counters == {
        "retry_exhausted_total": 4,
        "retry_scheduled_total": 0,
        "queue_job_completed_total": 0,
        "queue_job_failed_total": 3,
    }


@pytest.mark.asyncio
async def test_sync_worker_queue_metrics_writes_snapshot_and_preserves_counters() -> None:
    from app.runtime.queue import QueueSnapshot

    redis = _FakeRedis()
    key = worker_metrics_key("analysis")
    redis.hashes[key] = {
        "retry_exhausted_total": 1,
        "retry_scheduled_total": 2,
        "queue_job_completed_total": 8,
        "queue_job_failed_total": 3,
    }

    await sync_worker_queue_metrics(
        redis,
        role="analysis",
        snapshot=QueueSnapshot(
            queue_name="analysis",
            queue_depth=5,
            queue_pressure="elevated",
            oldest_job_age_seconds=42,
            queue_alert="watch",
        ),
        health_interval_seconds=30,
    )

    assert redis.hashes[key] == {
        "queue_name": "analysis",
        "queue_depth": 5,
        "queue_pressure": "elevated",
        "oldest_job_age_seconds": 42,
        "queue_alert": "watch",
        "retry_exhausted_total": 1,
        "retry_scheduled_total": 2,
        "queue_job_completed_total": 8,
        "queue_job_failed_total": 3,
    }
    assert redis.expirations == [(key, 120)]


@pytest.mark.asyncio
async def test_increment_worker_counter_updates_hash_and_ttl() -> None:
    redis = _FakeRedis()
    key = worker_metrics_key("scraping")

    value = await increment_worker_counter(
        redis,
        role="scraping",
        counter_name="queue_job_completed_total",
        health_interval_seconds=15,
    )

    assert value == 1
    assert redis.hashes[key]["queue_job_completed_total"] == 1
    assert redis.expirations == [(key, 60)]


@pytest.mark.asyncio
async def test_increment_worker_counter_rejects_unknown_counter() -> None:
    redis = _FakeRedis()

    with pytest.raises(ValueError, match="Unknown worker metric counter"):
        await increment_worker_counter(
            redis,
            role="ops",
            counter_name="not_a_counter",
            health_interval_seconds=15,
        )


def test_counter_fields_stay_stable() -> None:
    assert COUNTER_FIELDS == (
        "retry_exhausted_total",
        "retry_scheduled_total",
        "queue_job_completed_total",
        "queue_job_failed_total",
    )
