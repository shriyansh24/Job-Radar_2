from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.runtime import arq_worker
from app.runtime import queue as queue_runtime
from app.runtime.job_registry import (
    ANALYSIS_QUEUE,
    OPS_QUEUE,
    SCRAPING_QUEUE,
    get_registered_jobs,
)


def _fake_redis_settings() -> object:
    return object()


def _fake_current_unix_ms() -> int:
    return 361_000


def _fake_current_unix_ms_short() -> int:
    return 6_000


@pytest.mark.parametrize(
    ("role", "queue_name"),
    [
        ("scraping", SCRAPING_QUEUE),
        ("analysis", ANALYSIS_QUEUE),
        ("ops", OPS_QUEUE),
    ],
)
def test_build_worker_assigns_expected_queue(
    role: str,
    queue_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(arq_worker, "build_redis_settings", _fake_redis_settings)

    worker = arq_worker.build_worker(role)

    assert worker.queue_name == queue_name
    assert set(worker.functions) == {
        job.name for job in get_registered_jobs(queue_name=queue_name)
    }
    assert worker.max_jobs == arq_worker.ROLE_TO_MAX_JOBS[role]
    assert worker.queue_read_limit == arq_worker.ROLE_TO_QUEUE_READ_LIMIT[role]
    assert worker.health_check_key == arq_worker.ROLE_TO_HEALTHCHECK_KEY[role]


def test_build_worker_preserves_function_retry_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(arq_worker, "build_redis_settings", _fake_redis_settings)

    worker = arq_worker.build_worker("ops")

    assert worker.functions["auto_apply_batch"].max_tries == 1
    assert worker.functions["cleanup"].max_tries == 2
    assert "gmail_sync" in worker.functions
    assert worker.functions["gmail_sync"].max_tries == 2


def test_build_worker_rejects_unknown_role() -> None:
    with pytest.raises(ValueError, match="Unknown worker role"):
        arq_worker.build_worker("not-a-real-role")


def test_ready_marker_helper_uses_env_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    marker = tmp_path / "custom" / "analysis.ready"
    monkeypatch.setenv("JR_WORKER_READY_MARKER", str(marker))

    assert arq_worker._ready_marker_for_role("analysis") == marker


def test_healthcheck_helpers_use_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JR_WORKER_HEALTHCHECK_KEY", "jobradar:worker-health:test")
    monkeypatch.setenv("JR_WORKER_HEALTHCHECK_INTERVAL_SECONDS", "27")

    assert arq_worker._healthcheck_key_for_role("analysis") == "jobradar:worker-health:test"
    assert arq_worker._healthcheck_interval_seconds() == 27


@pytest.mark.asyncio
async def test_worker_startup_marks_ready_and_pings_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    seen: list[tuple[str, dict[str, object]]] = []

    class _FakeRedis:
        def __init__(self) -> None:
            self.ping_called = False
            self.metrics: dict[str, dict[str, str]] = {}
            self.expirations: dict[str, int] = {}

        async def ping(self) -> None:
            self.ping_called = True

        async def zcard(self, queue_name: str) -> int:
            assert queue_name == ANALYSIS_QUEUE
            return 6

        async def zrange(
            self,
            queue_name: str,
            _start: int,
            _stop: int,
            *,
            withscores: bool = False,
        ) -> list[tuple[str, int]]:
            assert queue_name == ANALYSIS_QUEUE
            assert withscores is True
            return [("job-1", 1_000)]

        async def hmget(self, key: str, *fields: str) -> list[str | None]:
            return [self.metrics.get(key, {}).get(field) for field in fields]

        async def hset(self, key: str, mapping: dict[str, object]) -> None:
            bucket = self.metrics.setdefault(key, {})
            bucket.update({field: str(value) for field, value in mapping.items()})

        async def expire(self, key: str, ttl: int) -> None:
            self.expirations[key] = ttl

    class _FakeLogger:
        def info(self, event: str, **fields: object) -> None:
            seen.append((event, fields))

    fake_redis = _FakeRedis()
    monkeypatch.setenv("JR_WORKER_READY_MARKER", str(tmp_path / "worker.ready"))
    monkeypatch.setattr(arq_worker, "setup_logging", _fake_setup_logging)
    monkeypatch.setattr(arq_worker, "validate_runtime_settings", _fake_validate_runtime_settings)
    monkeypatch.setattr(arq_worker, "engine", SimpleNamespace(connect=_fake_connect))
    monkeypatch.setattr(arq_worker, "logger", _FakeLogger())
    monkeypatch.setattr(queue_runtime, "_current_unix_ms", _fake_current_unix_ms)

    ctx: dict[str, object] = {
        "worker_role": "analysis",
        "queue_name": ANALYSIS_QUEUE,
        "job_count": 3,
        "job_names": ["embedding_batch", "enrichment_batch", "tfidf_scoring"],
        "max_jobs": 4,
        "queue_read_limit": 4,
        "health_check_key": "jobradar:worker-health:analysis",
        "health_check_interval_seconds": 15,
        "redis": fake_redis,
    }

    await arq_worker._on_startup(ctx)

    assert fake_redis.ping_called is True
    assert Path(tmp_path / "worker.ready").exists() is True
    assert fake_redis.metrics["jobradar:worker-metrics:analysis"]["queue_depth"] == "6"
    assert fake_redis.metrics["jobradar:worker-metrics:analysis"]["queue_alert"] == "watch"
    assert seen == [
        (
            "arq_worker_started",
            {
                "worker_role": "analysis",
                "queue_name": ANALYSIS_QUEUE,
                "job_count": 3,
                "job_names": ["embedding_batch", "enrichment_batch", "tfidf_scoring"],
                "max_jobs": 4,
                "queue_read_limit": 4,
                "health_check_key": "jobradar:worker-health:analysis",
                "health_check_interval_seconds": 15,
                "queue_depth": 6,
                "queue_pressure": "nominal",
                "oldest_job_age_seconds": 360,
                "queue_alert": "watch",
                "ready_marker": str(tmp_path / "worker.ready"),
            },
        )
    ]


@pytest.mark.asyncio
async def test_worker_shutdown_clears_ready_and_logs_role(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    seen: list[tuple[str, dict[str, object]]] = []

    async def _fake_dispose() -> None:
        return None

    class _FakeLogger:
        def info(self, event: str, **fields: object) -> None:
            seen.append((event, fields))

    marker = tmp_path / "worker.ready"
    marker.write_text("ready\n", encoding="utf-8")

    monkeypatch.setenv("JR_WORKER_READY_MARKER", str(marker))
    monkeypatch.setattr(arq_worker, "engine", SimpleNamespace(dispose=_fake_dispose))
    monkeypatch.setattr(arq_worker, "logger", _FakeLogger())

    await arq_worker._on_shutdown(
        {
            "worker_role": "ops",
            "queue_name": OPS_QUEUE,
            "health_check_key": "jobradar:worker-health:ops",
        }
    )

    assert marker.exists() is False
    assert seen == [
        (
            "arq_worker_stopped",
            {
                "worker_role": "ops",
                "queue_name": OPS_QUEUE,
                "health_check_key": "jobradar:worker-health:ops",
            },
        )
    ]


@pytest.mark.asyncio
async def test_worker_job_hooks_report_queue_depth(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[str, dict[str, object]]] = []

    class _FakeRedis:
        def __init__(self) -> None:
            self.metrics: dict[str, dict[str, str]] = {}

        async def zcard(self, queue_name: str) -> int:
            assert queue_name == SCRAPING_QUEUE
            return 5

        async def zrange(
            self,
            queue_name: str,
            _start: int,
            _stop: int,
            *,
            withscores: bool = False,
        ) -> list[tuple[str, int]]:
            assert queue_name == SCRAPING_QUEUE
            assert withscores is True
            return [("job-1", 1_000)]

        async def hmget(self, key: str, *fields: str) -> list[str | None]:
            return [self.metrics.get(key, {}).get(field) for field in fields]

        async def hset(self, key: str, mapping: dict[str, object]) -> None:
            bucket = self.metrics.setdefault(key, {})
            bucket.update({field: str(value) for field, value in mapping.items()})

        async def expire(self, key: str, _ttl: int) -> None:
            return None

    class _FakeLogger:
        def info(self, event: str, **fields: object) -> None:
            seen.append((event, fields))

    monkeypatch.setattr(arq_worker, "logger", _FakeLogger())
    monkeypatch.setattr(queue_runtime, "_current_unix_ms", _fake_current_unix_ms_short)
    ctx: dict[str, object] = {
        "worker_role": "scraping",
        "queue_name": SCRAPING_QUEUE,
        "job_id": "job-123",
        "job_try": 2,
        "health_check_interval_seconds": 15,
    }

    fake_redis = _FakeRedis()
    ctx["redis"] = fake_redis

    await arq_worker._on_job_start(ctx)
    await arq_worker._on_job_end(ctx)

    assert seen == [
        (
            "arq_worker_job_starting",
            {
                "worker_role": "scraping",
                "queue_name": SCRAPING_QUEUE,
                "job_id": "job-123",
                "queue_job_id": "job-123",
                "queue_correlation_id": "job-123",
                "job_try": 2,
                "queue_depth": 5,
                "queue_pressure": "nominal",
                "oldest_job_age_seconds": 5,
                "queue_alert": "clear",
            },
        ),
        (
            "arq_worker_job_finished",
            {
                "worker_role": "scraping",
                "queue_name": SCRAPING_QUEUE,
                "job_id": "job-123",
                "queue_job_id": "job-123",
                "queue_correlation_id": "job-123",
                "job_try": 2,
                "queue_depth": 5,
                "queue_pressure": "nominal",
                "oldest_job_age_seconds": 5,
                "queue_alert": "clear",
            },
        ),
    ]
    assert fake_redis.metrics["jobradar:worker-metrics:scraping"]["queue_depth"] == "5"
    assert fake_redis.metrics["jobradar:worker-metrics:scraping"]["queue_alert"] == "clear"


def _fake_setup_logging(*, debug: bool) -> None:
    return None


def _fake_validate_runtime_settings(_settings: object) -> None:
    return None


def _fake_connect() -> object:
    class _FakeConnection:
        async def execute(self, _query: object) -> None:
            return None

        async def __aenter__(self) -> "_FakeConnection":
            return self

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

    return _FakeConnection()
