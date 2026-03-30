from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

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


def test_classify_queue_pressure_uses_lane_thresholds() -> None:
    assert queue_runtime.classify_queue_pressure(SCRAPING_QUEUE, 0) == "nominal"
    assert queue_runtime.classify_queue_pressure(SCRAPING_QUEUE, 10) == "elevated"
    assert queue_runtime.classify_queue_pressure(SCRAPING_QUEUE, 25) == "saturated"
    assert queue_runtime.classify_queue_pressure(OPS_QUEUE, 5) == "elevated"
    assert queue_runtime.classify_queue_pressure(ANALYSIS_QUEUE, 50) == "saturated"


def test_classify_queue_alert_uses_pressure_and_oldest_age() -> None:
    assert (
        queue_runtime.classify_queue_alert(
            SCRAPING_QUEUE,
            pressure="nominal",
            oldest_job_age_seconds=0,
        )
        == "clear"
    )
    assert (
        queue_runtime.classify_queue_alert(
            SCRAPING_QUEUE,
            pressure="elevated",
            oldest_job_age_seconds=0,
        )
        == "watch"
    )
    assert (
        queue_runtime.classify_queue_alert(
            OPS_QUEUE,
            pressure="saturated",
            oldest_job_age_seconds=0,
        )
        == "backlog"
    )
    assert (
        queue_runtime.classify_queue_alert(
            ANALYSIS_QUEUE,
            pressure="nominal",
            oldest_job_age_seconds=900,
        )
        == "stalled"
    )


def test_derive_overall_pressure_uses_highest_lane_pressure() -> None:
    assert (
        queue_runtime.derive_overall_pressure(
            {
                SCRAPING_QUEUE: "nominal",
                ANALYSIS_QUEUE: "elevated",
                OPS_QUEUE: "nominal",
            }
        )
        == "elevated"
    )
    assert (
        queue_runtime.derive_overall_pressure(
            {
                SCRAPING_QUEUE: "nominal",
                ANALYSIS_QUEUE: "nominal",
                OPS_QUEUE: "saturated",
            }
        )
        == "saturated"
    )


def test_derive_overall_alert_uses_highest_lane_alert() -> None:
    assert (
        queue_runtime.derive_overall_alert(
            {
                SCRAPING_QUEUE: "clear",
                ANALYSIS_QUEUE: "watch",
                OPS_QUEUE: "clear",
            }
        )
        == "watch"
    )
    assert (
        queue_runtime.derive_overall_alert(
            {
                SCRAPING_QUEUE: "clear",
                ANALYSIS_QUEUE: "backlog",
                OPS_QUEUE: "watch",
            }
        )
        == "backlog"
    )
    assert (
        queue_runtime.derive_overall_alert(
            {
                SCRAPING_QUEUE: "clear",
                ANALYSIS_QUEUE: "watch",
                OPS_QUEUE: "stalled",
            }
        )
        == "stalled"
    )


@pytest.mark.asyncio
async def test_capture_queue_snapshot_reports_oldest_age_and_alert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakePool:
        async def zcard(self, queue_name: str) -> int:
            assert queue_name == OPS_QUEUE
            return 6

        async def zrange(
            self,
            queue_name: str,
            _start: int,
            _stop: int,
            *,
            withscores: bool = False,
        ) -> list[tuple[str, int]]:
            assert queue_name == OPS_QUEUE
            assert withscores is True
            return [("job-1", 1_000)]

    monkeypatch.setattr(queue_runtime, "_current_unix_ms", lambda: 601_000)

    snapshot = await queue_runtime.capture_queue_snapshot(OPS_QUEUE, _FakePool())

    assert snapshot == queue_runtime.QueueSnapshot(
        queue_name=OPS_QUEUE,
        queue_depth=6,
        queue_pressure="elevated",
        oldest_job_age_seconds=600,
        queue_alert="stalled",
    )


@pytest.mark.asyncio
async def test_enqueue_registered_job_uses_registered_queue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[tuple[str, str | None, str | None]] = []
    info_calls: list[tuple[str, dict[str, object]]] = []

    class _FakePool:
        def __init__(self) -> None:
            self.depth_by_queue = {SCRAPING_QUEUE: 3}
            self.oldest_score_by_queue = {SCRAPING_QUEUE: 298_000}

        async def zcard(self, queue_name: str) -> int:
            depth = self.depth_by_queue[queue_name]
            self.depth_by_queue[queue_name] = depth + 1
            return depth

        async def zrange(
            self,
            queue_name: str,
            _start: int,
            _stop: int,
            *,
            withscores: bool = False,
        ) -> list[tuple[str, int]]:
            assert withscores is True
            score = self.oldest_score_by_queue[queue_name]
            self.oldest_score_by_queue[queue_name] = score - 2_000
            return [("job-1", score)]

        async def enqueue_job(
            self,
            job_name: str,
            *,
            _job_id: str | None = None,
            _queue_name: str | None = None,
            **_: object,
        ) -> SimpleNamespace:
            seen.append((job_name, _queue_name, _job_id))
            return SimpleNamespace(job_id=_job_id)

    class _FakeLogger:
        def info(self, event: str, **fields: object) -> None:
            info_calls.append((event, fields))

    monkeypatch.setattr(queue_runtime, "_queue_pool", _FakePool())
    monkeypatch.setattr(queue_runtime, "logger", _FakeLogger())
    monkeypatch.setattr(queue_runtime, "_current_unix_ms", lambda: 300_000)
    monkeypatch.setattr(
        queue_runtime,
        "sync_worker_queue_metrics_for_queue",
        _sync_worker_queue_metrics_for_queue := AsyncMock(),
    )
    monkeypatch.setattr(
        queue_runtime,
        "configured_worker_health_interval_seconds",
        lambda: 27,
    )

    result = await queue_runtime.enqueue_registered_job("scheduled_scrape")

    assert isinstance(result, queue_runtime.QueueDispatchResult)
    assert result.job_name == "scheduled_scrape"
    assert result.queue_name == SCRAPING_QUEUE
    assert result.enqueued_job_id is not None
    assert result.enqueued_job_id.startswith("scheduled_scrape-")
    assert result.queue_depth_before == 3
    assert result.queue_depth_after == 4
    assert result.queue_pressure_before == "nominal"
    assert result.queue_pressure_after == "nominal"
    assert result.queue_job_id == result.enqueued_job_id
    assert result.queue_correlation_id is None
    assert result.oldest_job_age_seconds_before == 2
    assert result.oldest_job_age_seconds_after == 4
    assert result.queue_alert_before == "clear"
    assert result.queue_alert_after == "clear"
    assert seen == [("scheduled_scrape", SCRAPING_QUEUE, result.enqueued_job_id)]
    _sync_worker_queue_metrics_for_queue.assert_awaited_once()
    assert _sync_worker_queue_metrics_for_queue.await_args.kwargs["health_interval_seconds"] == 27
    synced_snapshot = _sync_worker_queue_metrics_for_queue.await_args.kwargs["snapshot"]
    assert synced_snapshot.queue_name == SCRAPING_QUEUE
    assert synced_snapshot.queue_depth == 4
    assert info_calls == [
        (
            "scheduler_job_enqueued",
            {
                "job_name": "scheduled_scrape",
                "queue_name": SCRAPING_QUEUE,
                "enqueued_job_id": result.enqueued_job_id,
                "queue_job_id": result.enqueued_job_id,
                "queue_correlation_id": None,
                "queue_depth_before": 3,
                "queue_depth_after": 4,
                "queue_pressure_before": "nominal",
                "queue_pressure_after": "nominal",
                "oldest_job_age_seconds_before": 2,
                "oldest_job_age_seconds_after": 4,
                "queue_alert_before": "clear",
                "queue_alert_after": "clear",
                "job_max_tries": 2,
                "job_timeout_seconds": 1800,
            },
        )
    ]


@pytest.mark.asyncio
async def test_enqueue_registered_job_uses_provided_correlation_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[tuple[str, str | None, str | None, dict[str, object]]] = []
    stored_metadata: list[tuple[str, str, int | None]] = []

    class _FakePool:
        async def zcard(self, _queue_name: str) -> int:
            return 1

        async def zrange(
            self,
            _queue_name: str,
            _start: int,
            _stop: int,
            *,
            withscores: bool = False,
        ) -> list[tuple[str, int]]:
            assert withscores is True
            return []

        async def enqueue_job(
            self,
            job_name: str,
            *,
            _job_id: str | None = None,
            _queue_name: str | None = None,
            **kwargs: object,
        ) -> SimpleNamespace:
            seen.append((job_name, _queue_name, _job_id, kwargs))
            return SimpleNamespace(job_id=_job_id)

        async def set(self, key: str, value: str, *, ex: int | None = None) -> bool:
            stored_metadata.append((key, value, ex))
            return True

    monkeypatch.setattr(queue_runtime, "_queue_pool", _FakePool())
    monkeypatch.setattr(
        queue_runtime,
        "sync_worker_queue_metrics_for_queue",
        AsyncMock(),
    )

    result = await queue_runtime.enqueue_registered_job(
        "enrichment_batch",
        correlation_id="request-123",
        user_id="user-123",
    )

    assert result.enqueued_job_id is not None
    assert result.enqueued_job_id.startswith("enrichment_batch-")
    assert result.queue_job_id == result.enqueued_job_id
    assert result.queue_correlation_id == "request-123"
    assert seen == [("enrichment_batch", ANALYSIS_QUEUE, result.enqueued_job_id, {})]
    assert stored_metadata == [
        (
            queue_runtime.build_job_metadata_key(result.enqueued_job_id),
            '{"_queue_correlation_id":"request-123","user_id":"user-123"}',
            queue_runtime.JOB_METADATA_TTL_SECONDS,
        )
    ]


@pytest.mark.asyncio
async def test_enqueue_registered_job_rejects_missing_job_reference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakePool:
        async def zcard(self, _queue_name: str) -> int:
            return 0

        async def zrange(
            self,
            _queue_name: str,
            _start: int,
            _stop: int,
            *,
            withscores: bool = False,
        ) -> list[tuple[str, int]]:
            assert withscores is True
            return []

        async def enqueue_job(self, *_args: object, **_kwargs: object) -> None:
            return None

    monkeypatch.setattr(queue_runtime, "_queue_pool", _FakePool())

    with pytest.raises(RuntimeError, match="returned no job reference"):
        await queue_runtime.enqueue_registered_job("cleanup")


@pytest.mark.asyncio
async def test_enqueue_registered_job_rejects_invalid_job_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakePool:
        async def zcard(self, _queue_name: str) -> int:
            return 0

        async def zrange(
            self,
            _queue_name: str,
            _start: int,
            _stop: int,
            *,
            withscores: bool = False,
        ) -> list[tuple[str, int]]:
            assert withscores is True
            return []

        async def enqueue_job(self, *_args: object, **_kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(job_id="")

    monkeypatch.setattr(queue_runtime, "_queue_pool", _FakePool())

    with pytest.raises(RuntimeError, match="returned an invalid job id"):
        await queue_runtime.enqueue_registered_job("cleanup")


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
