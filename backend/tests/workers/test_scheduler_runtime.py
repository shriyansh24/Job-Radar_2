from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from app.runtime import scheduler as scheduler_runtime


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

    def _install_signal_handlers(event: asyncio.Event) -> None:
        nonlocal stop_event
        stop_event = event
        asyncio.get_running_loop().call_soon(event.set)

    monkeypatch.setattr(scheduler_runtime, "_install_signal_handlers", _install_signal_handlers)

    exit_code = await scheduler_runtime.run()

    assert exit_code == 0
    assert fake_scheduler.started is True
    assert fake_scheduler.shutdown_called is True
    assert scheduler_runtime.READY_MARKER.exists() is False
    assert stop_event is not None


@pytest.mark.asyncio
async def test_scheduler_runtime_returns_non_zero_when_startup_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake_scheduler = _FakeScheduler(fail_on_start=True)

    monkeypatch.setattr(scheduler_runtime, "READY_MARKER", tmp_path / "scheduler.ready")
    monkeypatch.setattr(scheduler_runtime, "setup_logging", lambda debug: None)
    monkeypatch.setattr(scheduler_runtime, "validate_runtime_settings", lambda settings: None)
    monkeypatch.setattr(scheduler_runtime, "create_scheduler", lambda: fake_scheduler)

    exit_code = await scheduler_runtime.run()

    assert exit_code == 1
    assert scheduler_runtime.READY_MARKER.exists() is False
    assert fake_scheduler.shutdown_called is False
