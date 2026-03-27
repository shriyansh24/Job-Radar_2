from __future__ import annotations

import pytest

from app.runtime import job_registry
from app.runtime.job_registry import OPS_QUEUE, SCRAPING_QUEUE


class _FakeLogger:
    def __init__(self) -> None:
        self.info_calls: list[tuple[str, dict[str, object]]] = []
        self.exception_calls: list[tuple[str, dict[str, object]]] = []

    def info(self, event: str, **fields: object) -> None:
        self.info_calls.append((event, fields))

    def exception(self, event: str, **fields: object) -> None:
        self.exception_calls.append((event, fields))


@pytest.mark.asyncio
async def test_run_with_lifecycle_logs_retryable_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_logger = _FakeLogger()
    monkeypatch.setattr(job_registry, "logger", fake_logger)

    async def _failing_callback() -> None:
        raise RuntimeError("boom")

    with pytest.raises(job_registry.Retry):
        await job_registry._run_with_lifecycle(
            job_name="scheduled_scrape",
            queue_name=SCRAPING_QUEUE,
            ctx={"job_id": "job-1", "job_try": 1},
            callback=_failing_callback,
        )

    assert fake_logger.info_calls == [
        (
            "queue_job_started",
            {
                "job_name": "scheduled_scrape",
                "job_id": "job-1",
                "job_try": 1,
                "queue_name": SCRAPING_QUEUE,
                "job_max_tries": 2,
                "job_retryable": True,
                "job_retry_remaining": 1,
            },
        )
    ]
    assert fake_logger.exception_calls == [
        (
            "queue_job_retry_scheduled",
            {
                "job_name": "scheduled_scrape",
                "retry_in_seconds": 30,
                "job_id": "job-1",
                "job_try": 1,
                "queue_name": SCRAPING_QUEUE,
                "job_max_tries": 2,
                "job_retryable": True,
                "job_retry_remaining": 1,
            },
        )
    ]


@pytest.mark.asyncio
async def test_run_with_lifecycle_logs_non_retryable_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_logger = _FakeLogger()
    monkeypatch.setattr(job_registry, "logger", fake_logger)

    async def _failing_callback() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await job_registry._run_with_lifecycle(
            job_name="auto_apply_batch",
            queue_name=OPS_QUEUE,
            ctx={"job_id": "job-2", "job_try": 1},
            callback=_failing_callback,
        )

    assert fake_logger.exception_calls == [
        (
            "queue_job_failed",
            {
                "job_name": "auto_apply_batch",
                "will_retry": False,
                "retry_exhausted": False,
                "job_id": "job-2",
                "job_try": 1,
                "queue_name": OPS_QUEUE,
                "job_max_tries": 1,
                "job_retryable": False,
                "job_retry_remaining": 0,
            },
        )
    ]


@pytest.mark.asyncio
async def test_run_with_lifecycle_logs_final_attempt_without_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_logger = _FakeLogger()
    monkeypatch.setattr(job_registry, "logger", fake_logger)

    async def _failing_callback() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await job_registry._run_with_lifecycle(
            job_name="scheduled_scrape",
            queue_name=SCRAPING_QUEUE,
            ctx={"job_id": "job-3", "job_try": 2},
            callback=_failing_callback,
        )

    assert fake_logger.exception_calls == [
        (
            "queue_job_failed",
            {
                "job_name": "scheduled_scrape",
                "will_retry": False,
                "retry_exhausted": True,
                "job_id": "job-3",
                "job_try": 2,
                "queue_name": SCRAPING_QUEUE,
                "job_max_tries": 2,
                "job_retryable": True,
                "job_retry_remaining": 0,
            },
        )
    ]


@pytest.mark.asyncio
async def test_run_with_lifecycle_logs_completion_fields_for_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_logger = _FakeLogger()
    monkeypatch.setattr(job_registry, "logger", fake_logger)

    async def _successful_callback() -> None:
        return None

    await job_registry._run_with_lifecycle(
        job_name="embedding_batch",
        queue_name=job_registry.ANALYSIS_QUEUE,
        ctx={"job_id": "job-4", "job_try": 1},
        callback=_successful_callback,
    )

    assert fake_logger.info_calls == [
        (
            "queue_job_started",
            {
                "job_name": "embedding_batch",
                "job_id": "job-4",
                "job_try": 1,
                "queue_name": job_registry.ANALYSIS_QUEUE,
                "job_max_tries": 3,
                "job_retryable": True,
                "job_retry_remaining": 2,
            },
        ),
        (
            "queue_job_completed",
            {
                "job_name": "embedding_batch",
                "job_id": "job-4",
                "job_try": 1,
                "queue_name": job_registry.ANALYSIS_QUEUE,
                "job_max_tries": 3,
                "job_retryable": True,
                "job_retry_remaining": 2,
            },
        ),
    ]
