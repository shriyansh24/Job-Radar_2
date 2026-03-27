from __future__ import annotations

from types import SimpleNamespace

import pytest
from arq.connections import RedisSettings

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

    class _FakePool:
        async def enqueue_job(
            self,
            job_name: str,
            *,
            _queue_name: str | None = None,
        ) -> SimpleNamespace:
            seen.append((job_name, _queue_name))
            return SimpleNamespace(job_id="queued-123")

    monkeypatch.setattr(queue_runtime, "_queue_pool", _FakePool())

    job_id = await queue_runtime.enqueue_registered_job("scheduled_scrape")

    assert job_id == "queued-123"
    assert seen == [("scheduled_scrape", SCRAPING_QUEUE)]


def test_job_queues_cover_expected_runtime_lanes() -> None:
    from app.runtime.job_registry import get_registered_jobs

    queue_names = {job.queue_name for job in get_registered_jobs()}
    assert queue_names == {SCRAPING_QUEUE, ANALYSIS_QUEUE, OPS_QUEUE}
