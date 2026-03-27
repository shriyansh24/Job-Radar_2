from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from arq.connections import RedisSettings, create_pool
from redis.exceptions import RedisError

from app.runtime import queue as queue_runtime
from app.runtime.job_registry import ANALYSIS_QUEUE, OPS_QUEUE, SCRAPING_QUEUE


def test_build_redis_settings_parses_password_database_and_tls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        queue_runtime.settings,
        "redis_url",
        "rediss://user:secret%40123@redis.example.com:6380/7",
    )
    monkeypatch.setattr(queue_runtime.settings, "redis_use_tls", False)

    redis_settings = queue_runtime.build_redis_settings()

    assert isinstance(redis_settings, RedisSettings)
    assert redis_settings.host == "redis.example.com"
    assert redis_settings.port == 6380
    assert redis_settings.database == 7
    assert redis_settings.username == "user"
    assert redis_settings.password == "secret@123"
    assert redis_settings.ssl is True


@pytest.mark.asyncio
async def test_enqueue_registered_job_uses_registered_queue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[tuple[str, str | None]] = []
    info_calls: list[tuple[str, dict[str, object]]] = []

    class _FakePool:
        def __init__(self) -> None:
            self.depth_by_queue = {SCRAPING_QUEUE: 3}

        async def zcard(self, queue_name: str) -> int:
            depth = self.depth_by_queue[queue_name]
            self.depth_by_queue[queue_name] = depth + 1
            return depth

        async def enqueue_job(
            self,
            job_name: str,
            *,
            _queue_name: str | None = None,
        ) -> SimpleNamespace:
            seen.append((job_name, _queue_name))
            return SimpleNamespace(job_id="queued-123")

    class _FakeLogger:
        def info(self, event: str, **fields: object) -> None:
            info_calls.append((event, fields))

    monkeypatch.setattr(queue_runtime, "_queue_pool", _FakePool())
    monkeypatch.setattr(queue_runtime, "logger", _FakeLogger())

    job_id = await queue_runtime.enqueue_registered_job("scheduled_scrape")

    assert job_id == "queued-123"
    assert seen == [("scheduled_scrape", SCRAPING_QUEUE)]
    assert info_calls == [
        (
            "scheduler_job_enqueued",
            {
                "job_name": "scheduled_scrape",
                "queue_name": SCRAPING_QUEUE,
                "enqueued_job_id": "queued-123",
                "queue_depth_before": 3,
                "queue_depth_after": 4,
                "job_max_tries": 2,
                "job_timeout_seconds": 1800,
            },
        )
    ]


def test_job_queues_cover_expected_runtime_lanes() -> None:
    from app.runtime.job_registry import get_registered_jobs

    queue_names = {job.queue_name for job in get_registered_jobs()}
    assert queue_names == {SCRAPING_QUEUE, ANALYSIS_QUEUE, OPS_QUEUE}


@pytest.mark.asyncio
async def test_real_redis_lane_isolation_preserves_other_queues() -> None:
    queue_pool = None
    try:
        queue_pool = await create_pool(queue_runtime.build_redis_settings())
    except RedisError as exc:
        pytest.skip(f"Redis unavailable for lane-isolation test: {exc}")

    assert queue_pool is not None

    scraping_lane = f"{SCRAPING_QUEUE}:lane-isolation:{uuid.uuid4().hex}"
    ops_lane = f"{OPS_QUEUE}:lane-isolation:{uuid.uuid4().hex}"

    try:
        await queue_pool.delete(scraping_lane, ops_lane)

        await queue_pool.enqueue_job("scheduled_scrape", _queue_name=scraping_lane)
        await queue_pool.enqueue_job("cleanup", _queue_name=ops_lane)

        assert await queue_pool.zcard(scraping_lane) == 1
        assert await queue_pool.zcard(ops_lane) == 1

        popped = await queue_pool.zpopmin(ops_lane)

        assert len(popped) == 1
        assert await queue_pool.zcard(ops_lane) == 0
        assert await queue_pool.zcard(scraping_lane) == 1
    finally:
        await queue_pool.delete(scraping_lane, ops_lane)
        await queue_pool.close(close_connection_pool=True)
