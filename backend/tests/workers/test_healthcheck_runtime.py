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


def test_parse_health_fields_extracts_key_value_pairs() -> None:
    payload = (
        b"2026-03-27T20:15:00+00:00 "
        b"scheduler_running=1 overall_pressure=elevated overall_alert=watch"
    )

    assert healthcheck._parse_health_fields(payload) == {
        "scheduler_running": "1",
        "overall_pressure": "elevated",
        "overall_alert": "watch",
    }


@pytest.mark.asyncio
async def test_check_scheduler_rejects_missing_pressure(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_db_ready() -> None:
        return None

    async def _fake_assert_redis_health_key(_key: str) -> bytes:
        return b"2026-03-27T20:15:00+00:00 scheduler_running=1"

    monkeypatch.setattr(healthcheck, "_assert_database_ready", _fake_db_ready)
    monkeypatch.setattr(healthcheck, "_assert_redis_health_key", _fake_assert_redis_health_key)

    with pytest.raises(RuntimeError, match="overall_pressure"):
        await healthcheck._check_scheduler()


@pytest.mark.asyncio
async def test_check_scheduler_rejects_inconsistent_queue_pressure_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_db_ready() -> None:
        return None

    async def _fake_assert_redis_health_key(_key: str) -> bytes:
        return (
            b"2026-03-27T20:15:00+00:00 "
            b"scheduler_running=1 overall_pressure=nominal overall_alert=watch "
            b"arq:queue:scraping=12 arq:queue:scraping.pressure=elevated "
            b"arq:queue:scraping.alert=watch arq:queue:scraping.oldest_job_age_seconds=0 "
            b"arq:queue:analysis=3 arq:queue:analysis.pressure=nominal "
            b"arq:queue:analysis.alert=clear arq:queue:analysis.oldest_job_age_seconds=0 "
            b"arq:queue:ops=1 arq:queue:ops.pressure=nominal "
            b"arq:queue:ops.alert=clear arq:queue:ops.oldest_job_age_seconds=0"
        )

    monkeypatch.setattr(healthcheck, "_assert_database_ready", _fake_db_ready)
    monkeypatch.setattr(healthcheck, "_assert_redis_health_key", _fake_assert_redis_health_key)

    with pytest.raises(RuntimeError, match="overall_pressure does not match"):
        await healthcheck._check_scheduler()


@pytest.mark.asyncio
async def test_check_scheduler_rejects_inconsistent_queue_alert_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_db_ready() -> None:
        return None

    async def _fake_assert_redis_health_key(_key: str) -> bytes:
        return (
            b"2026-03-27T20:15:00+00:00 "
            b"scheduler_running=1 overall_pressure=elevated overall_alert=clear "
            b"arq:queue:scraping=12 arq:queue:scraping.pressure=elevated "
            b"arq:queue:scraping.alert=watch arq:queue:scraping.oldest_job_age_seconds=0 "
            b"arq:queue:analysis=3 arq:queue:analysis.pressure=nominal "
            b"arq:queue:analysis.alert=clear arq:queue:analysis.oldest_job_age_seconds=0 "
            b"arq:queue:ops=1 arq:queue:ops.pressure=nominal "
            b"arq:queue:ops.alert=clear arq:queue:ops.oldest_job_age_seconds=0"
        )

    monkeypatch.setattr(healthcheck, "_assert_database_ready", _fake_db_ready)
    monkeypatch.setattr(healthcheck, "_assert_redis_health_key", _fake_assert_redis_health_key)

    with pytest.raises(RuntimeError, match="overall_alert does not match"):
        await healthcheck._check_scheduler()


@pytest.mark.asyncio
async def test_check_worker_rejects_missing_queue_stats(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_db_ready() -> None:
        return None

    async def _fake_assert_redis_health_key(_key: str) -> bytes:
        return b"Mar-27 15:00:00 j_complete=1 j_failed=0"

    async def _fake_assert_redis_hash_fields(_key: str) -> dict[str, str]:
        return {}

    monkeypatch.setattr(healthcheck, "_assert_database_ready", _fake_db_ready)
    monkeypatch.setattr(healthcheck, "_assert_redis_health_key", _fake_assert_redis_health_key)
    monkeypatch.setattr(healthcheck, "_assert_redis_hash_fields", _fake_assert_redis_hash_fields)

    with pytest.raises(RuntimeError, match="missing .*j_ongoing.*j_retried.*queued"):
        await healthcheck._check_worker("ops")


@pytest.mark.asyncio
async def test_check_worker_rejects_non_numeric_queue_stats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_db_ready() -> None:
        return None

    async def _fake_assert_redis_health_key(_key: str) -> bytes:
        return b"Mar-27 15:00:00 j_complete=1 j_failed=0 j_retried=0 j_ongoing=x queued=2"

    async def _fake_assert_redis_hash_fields(_key: str) -> dict[str, str]:
        return {}

    monkeypatch.setattr(healthcheck, "_assert_database_ready", _fake_db_ready)
    monkeypatch.setattr(healthcheck, "_assert_redis_health_key", _fake_assert_redis_health_key)
    monkeypatch.setattr(healthcheck, "_assert_redis_hash_fields", _fake_assert_redis_hash_fields)

    with pytest.raises(RuntimeError, match="j_ongoing.*must be an integer"):
        await healthcheck._check_worker("ops")


@pytest.mark.asyncio
async def test_check_worker_rejects_missing_worker_metrics_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_db_ready() -> None:
        return None

    async def _fake_assert_redis_health_key(_key: str) -> bytes:
        return b"Mar-27 15:00:00 j_complete=1 j_failed=0 j_retried=0 j_ongoing=0 queued=2"

    async def _fake_assert_redis_hash_fields(_key: str) -> dict[str, str]:
        return {}

    monkeypatch.setattr(healthcheck, "_assert_database_ready", _fake_db_ready)
    monkeypatch.setattr(healthcheck, "_assert_redis_health_key", _fake_assert_redis_health_key)
    monkeypatch.setattr(healthcheck, "_assert_redis_hash_fields", _fake_assert_redis_hash_fields)

    with pytest.raises(RuntimeError, match="queue_name"):
        await healthcheck._check_worker("ops")


@pytest.mark.asyncio
async def test_check_worker_validates_metrics_hash_against_queue_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_db_ready() -> None:
        return None

    async def _fake_assert_redis_health_key(_key: str) -> bytes:
        return b"Mar-27 15:00:00 j_complete=1 j_failed=0 j_retried=0 j_ongoing=0 queued=2"

    async def _fake_assert_redis_hash_fields(_key: str) -> dict[str, str]:
        return {
            "queue_name": "arq:queue:ops",
            "queue_depth": "2",
            "queue_pressure": "nominal",
            "oldest_job_age_seconds": "0",
            "queue_alert": "clear",
            "retry_exhausted_total": "1",
            "retry_scheduled_total": "2",
            "queue_job_completed_total": "3",
            "queue_job_failed_total": "1",
        }

    monkeypatch.setattr(healthcheck, "_assert_database_ready", _fake_db_ready)
    monkeypatch.setattr(healthcheck, "_assert_redis_health_key", _fake_assert_redis_health_key)
    monkeypatch.setattr(healthcheck, "_assert_redis_hash_fields", _fake_assert_redis_hash_fields)

    await healthcheck._check_worker("ops")


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
