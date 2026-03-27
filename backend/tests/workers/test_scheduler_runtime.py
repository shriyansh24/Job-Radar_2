from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from apscheduler.events import EVENT_JOB_EXECUTED, JobExecutionEvent

from app.runtime import scheduler as scheduler_runtime
from app.runtime.queue import QueueDispatchResult
from app.workers import scheduler as worker_scheduler


class _FakeScheduler:
    def __init__(self, *, fail_on_start: bool = False) -> None:
        self.fail_on_start = fail_on_start
        self.started = False
        self.shutdown_called = False

    def start(self) -> None:
        if self.fail_on_start:
            raise RuntimeError("boom")
        self.started = True

    def get_jobs(self) -> list[object]:
        return []

    def shutdown(self, *, wait: bool) -> None:
        self.shutdown_called = True


def test_create_scheduler_registers_daily_digest() -> None:
    scheduler = scheduler_runtime.create_scheduler()
    job_ids = {job.id for job in scheduler.get_jobs()}

    assert "daily_digest" in job_ids


def test_log_job_event_includes_dispatch_result(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[str, dict[str, object]]] = []

    class _FakeLogger:
        def info(self, event: str, **fields: object) -> None:
            seen.append((event, fields))

    monkeypatch.setattr(worker_scheduler, "logger", _FakeLogger())

    worker_scheduler._log_job_event(
        JobExecutionEvent(
            EVENT_JOB_EXECUTED,
            "daily_digest",
            "default",
            None,
            retval=QueueDispatchResult(
                job_name="daily_digest",
                queue_name="arq:queue:ops",
                enqueued_job_id="daily_digest-123",
                queue_depth_before=1,
                queue_depth_after=2,
                queue_pressure_before="nominal",
                queue_pressure_after="elevated",
                queue_job_id="daily_digest-123",
                queue_correlation_id="daily_digest-123",
                oldest_job_age_seconds_before=12,
                oldest_job_age_seconds_after=24,
                queue_alert_before="clear",
                queue_alert_after="watch",
            ),
        )
    )

    assert seen == [
        (
            "scheduler_job_dispatched",
            {
                "job_id": "daily_digest",
                "scheduled_run_time": None,
                "enqueued_job_id": "daily_digest-123",
                "queue_job_id": "daily_digest-123",
                "queue_correlation_id": "daily_digest-123",
                "queue_name": "arq:queue:ops",
                "queue_depth_before": 1,
                "queue_depth_after": 2,
                "queue_pressure_before": "nominal",
                "queue_pressure_after": "elevated",
                "oldest_job_age_seconds_before": 12,
                "oldest_job_age_seconds_after": 24,
                "queue_alert_before": "clear",
                "queue_alert_after": "watch",
            },
        )
    ]


@pytest.mark.asyncio
async def test_scheduler_runtime_starts_and_cleans_up_ready_marker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake_scheduler = _FakeScheduler()
    stop_event: asyncio.Event | None = None

    monkeypatch.setattr(scheduler_runtime, "READY_MARKER", tmp_path / "scheduler.ready")
    monkeypatch.setattr(scheduler_runtime, "setup_logging", lambda debug: None)
    monkeypatch.setattr(scheduler_runtime, "validate_runtime_settings", lambda settings: None)
    monkeypatch.setattr(scheduler_runtime, "create_scheduler", lambda: fake_scheduler)
    monkeypatch.setattr(scheduler_runtime, "_verify_dependencies", lambda: asyncio.sleep(0))
    monkeypatch.setattr(scheduler_runtime, "_record_health", lambda: asyncio.sleep(0))
    monkeypatch.setattr(scheduler_runtime, "_clear_health", lambda: asyncio.sleep(0))
    monkeypatch.setattr(scheduler_runtime, "shutdown_queue_pool", lambda: asyncio.sleep(0))

    def _install_signal_handlers(event: asyncio.Event) -> None:
        nonlocal stop_event
        stop_event = event
        asyncio.get_running_loop().call_soon(event.set)

    monkeypatch.setattr(scheduler_runtime, "_install_signal_handlers", _install_signal_handlers)
    monkeypatch.setattr(
        scheduler_runtime,
        "_health_loop",
        lambda event: event.wait(),
    )

    exit_code = await scheduler_runtime.run()

    assert exit_code == 0
    assert fake_scheduler.started is True
    assert fake_scheduler.shutdown_called is True
    assert scheduler_runtime.READY_MARKER.exists() is False
    assert stop_event is not None


@pytest.mark.asyncio
async def test_scheduler_record_health_includes_pressure_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[tuple[str, int, bytes]] = []

    class _FakeQueuePool:
        async def psetex(self, key: str, ttl_ms: int, payload: bytes) -> None:
            captured.append((key, ttl_ms, payload))

    async def _fake_startup_queue_pool() -> _FakeQueuePool:
        return _FakeQueuePool()

    async def _fake_get_queue_snapshots_runtime(
        _queue_pool: object,
    ) -> dict[str, object]:
        return {
            "arq:queue:scraping": type(
                "_Snapshot",
                (),
                {
                    "queue_name": "arq:queue:scraping",
                    "queue_depth": 12,
                    "queue_pressure": "elevated",
                    "oldest_job_age_seconds": 45,
                    "queue_alert": "watch",
                },
            )(),
            "arq:queue:analysis": type(
                "_Snapshot",
                (),
                {
                    "queue_name": "arq:queue:analysis",
                    "queue_depth": 4,
                    "queue_pressure": "nominal",
                    "oldest_job_age_seconds": 0,
                    "queue_alert": "clear",
                },
            )(),
            "arq:queue:ops": type(
                "_Snapshot",
                (),
                {
                    "queue_name": "arq:queue:ops",
                    "queue_depth": 16,
                    "queue_pressure": "saturated",
                    "oldest_job_age_seconds": 601,
                    "queue_alert": "stalled",
                },
            )(),
        }

    monkeypatch.setattr(scheduler_runtime, "startup_queue_pool", _fake_startup_queue_pool)
    monkeypatch.setattr(
        scheduler_runtime,
        "get_queue_snapshots",
        _fake_get_queue_snapshots_runtime,
    )
    monkeypatch.setattr(
        scheduler_runtime,
        "_scheduler_healthcheck_key",
        lambda: "jobradar:scheduler-health",
    )
    monkeypatch.setattr(
        scheduler_runtime,
        "_scheduler_healthcheck_interval_seconds",
        lambda: 15,
    )

    await scheduler_runtime._record_health()

    assert len(captured) == 1
    key, ttl_ms, payload = captured[0]
    payload_text = payload.decode()
    assert key == "jobradar:scheduler-health"
    assert ttl_ms == 20000
    assert "scheduler_running=1" in payload_text
    assert "overall_pressure=saturated" in payload_text
    assert "overall_alert=stalled" in payload_text
    assert "arq:queue:scraping=12" in payload_text
    assert "arq:queue:scraping.pressure=elevated" in payload_text
    assert "arq:queue:scraping.alert=watch" in payload_text
    assert "arq:queue:scraping.oldest_job_age_seconds=45" in payload_text
    assert "arq:queue:ops=16" in payload_text
    assert "arq:queue:ops.pressure=saturated" in payload_text
    assert "arq:queue:ops.alert=stalled" in payload_text


@pytest.mark.asyncio
async def test_scheduler_runtime_returns_non_zero_when_startup_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake_scheduler = _FakeScheduler(fail_on_start=True)

    monkeypatch.setattr(scheduler_runtime, "READY_MARKER", tmp_path / "scheduler.ready")
    monkeypatch.setattr(scheduler_runtime, "setup_logging", lambda debug: None)
    monkeypatch.setattr(scheduler_runtime, "validate_runtime_settings", lambda settings: None)
    monkeypatch.setattr(scheduler_runtime, "create_scheduler", lambda: fake_scheduler)
    monkeypatch.setattr(scheduler_runtime, "_verify_dependencies", lambda: asyncio.sleep(0))
    monkeypatch.setattr(scheduler_runtime, "shutdown_queue_pool", lambda: asyncio.sleep(0))

    exit_code = await scheduler_runtime.run()

    assert exit_code == 1
    assert scheduler_runtime.READY_MARKER.exists() is False
    assert fake_scheduler.shutdown_called is False


@pytest.mark.asyncio
async def test_scheduler_runtime_returns_non_zero_when_dependency_probe_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake_scheduler = _FakeScheduler()

    async def _fail_dependencies() -> None:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(scheduler_runtime, "READY_MARKER", tmp_path / "scheduler.ready")
    monkeypatch.setattr(scheduler_runtime, "setup_logging", lambda debug: None)
    monkeypatch.setattr(scheduler_runtime, "validate_runtime_settings", lambda settings: None)
    monkeypatch.setattr(scheduler_runtime, "create_scheduler", lambda: fake_scheduler)
    monkeypatch.setattr(scheduler_runtime, "_verify_dependencies", _fail_dependencies)
    monkeypatch.setattr(scheduler_runtime, "shutdown_queue_pool", lambda: asyncio.sleep(0))

    exit_code = await scheduler_runtime.run()

    assert exit_code == 1
    assert scheduler_runtime.READY_MARKER.exists() is False
    assert fake_scheduler.started is False
    assert fake_scheduler.shutdown_called is False
