from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.runtime import worker as worker_runtime


def test_registered_job_ids_are_sorted_and_include_core_jobs() -> None:
    job_ids = worker_runtime.get_registered_job_ids()

    assert job_ids == sorted(job_ids)
    assert "scheduled_scrape" in job_ids
    assert "auto_apply_batch" in job_ids
    assert "daily_digest" in job_ids
    assert "gmail_sync" in job_ids
    assert "target_batch_career_page" in job_ids
    assert "target_batch_watchlist" in job_ids
    assert "career_page_scrape" not in job_ids


@pytest.mark.asyncio
async def test_run_registered_job_rejects_unknown_jobs() -> None:
    with pytest.raises(ValueError, match="Unknown worker job"):
        await worker_runtime.run_registered_job("not-a-real-job")


@pytest.mark.asyncio
async def test_run_registered_job_invokes_registered_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[dict[str, object]] = []

    async def _fake_runner(ctx: dict[str, object]) -> None:
        seen.append(ctx)

    async def _fake_dispose() -> None:
        return None

    monkeypatch.setattr(
        worker_runtime,
        "get_registered_job",
        lambda name: SimpleNamespace(
            name=name,
            queue_name="arq:queue:test",
            runner=_fake_runner,
        ),
    )
    monkeypatch.setattr(worker_runtime, "setup_logging", lambda debug: None)
    monkeypatch.setattr(worker_runtime, "validate_runtime_settings", lambda settings: None)
    monkeypatch.setattr(worker_runtime, "engine", SimpleNamespace(dispose=_fake_dispose))

    await worker_runtime.run_registered_job("scheduled_scrape")

    assert seen == [{}]


def test_worker_main_lists_jobs(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        worker_runtime,
        "_parse_args",
        lambda: SimpleNamespace(list_jobs=True, job_name=None),
    )

    exit_code = worker_runtime.main()

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "scheduled_scrape" in captured.out
