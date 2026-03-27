from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.runtime import healthcheck


class _FakeLogger:
    def __init__(self) -> None:
        self.info_calls: list[tuple[str, dict[str, object]]] = []
        self.exception_calls: list[tuple[str, dict[str, object]]] = []

    def info(self, event: str, **fields: object) -> None:
        self.info_calls.append((event, fields))

    def exception(self, event: str, **fields: object) -> None:
        self.exception_calls.append((event, fields))


@pytest.mark.asyncio
async def test_run_async_scheduler_healthcheck_reports_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_logger = _FakeLogger()

    async def _fake_check_scheduler() -> None:
        return None

    async def _fake_shutdown() -> None:
        return None

    async def _fake_dispose() -> None:
        return None

    monkeypatch.setattr(healthcheck, "logger", fake_logger)
    monkeypatch.setattr(healthcheck, "_check_scheduler", _fake_check_scheduler)
    monkeypatch.setattr(healthcheck, "shutdown_queue_pool", _fake_shutdown)
    monkeypatch.setattr(healthcheck, "engine", SimpleNamespace(dispose=_fake_dispose))
    monkeypatch.setattr(
        healthcheck, "_scheduler_healthcheck_key", lambda: "jobradar:scheduler-health"
    )

    exit_code = await healthcheck._run_async(SimpleNamespace(mode="scheduler"))

    assert exit_code == 0
    assert fake_logger.info_calls == [
        (
            "runtime_healthcheck_ok",
            {
                "mode": "scheduler",
                "health_check_key": "jobradar:scheduler-health",
            },
        )
    ]


@pytest.mark.asyncio
async def test_run_async_worker_healthcheck_reports_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_logger = _FakeLogger()

    async def _fake_check_worker(_role: str) -> None:
        raise RuntimeError("missing heartbeat")

    async def _fake_shutdown() -> None:
        return None

    async def _fake_dispose() -> None:
        return None

    monkeypatch.setattr(healthcheck, "logger", fake_logger)
    monkeypatch.setattr(healthcheck, "_check_worker", _fake_check_worker)
    monkeypatch.setattr(healthcheck, "shutdown_queue_pool", _fake_shutdown)
    monkeypatch.setattr(healthcheck, "engine", SimpleNamespace(dispose=_fake_dispose))

    exit_code = await healthcheck._run_async(SimpleNamespace(mode="worker", role="ops"))

    assert exit_code == 1
    assert fake_logger.exception_calls == [
        (
            "runtime_healthcheck_failed",
            {
                "mode": "worker",
            },
        )
    ]
