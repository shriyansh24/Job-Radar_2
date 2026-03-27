from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from app.runtime import worker as worker_runtime


def test_registered_job_ids_are_sorted_and_include_core_jobs() -> None:
    job_ids = worker_runtime.get_registered_job_ids()

    assert job_ids == sorted(job_ids)
    assert "scheduled_scrape" in job_ids
    assert "auto_apply_batch" in job_ids
    assert "target_batch_watchlist" in job_ids


@pytest.mark.asyncio
async def test_run_registered_job_rejects_unknown_jobs() -> None:
    with pytest.raises(ValueError, match="Unknown worker job"):
        await worker_runtime.run_registered_job("not-a-real-job")


@pytest.mark.asyncio
async def test_spawn_worker_process_raises_on_non_zero_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeProcess:
        async def wait(self) -> int:
            return 7

    async def _fake_create_subprocess_exec(*args: str) -> _FakeProcess:
        assert args[0]
        assert args[1:] == ("-m", "app.runtime.worker", "auto_apply_batch")
        return _FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", _fake_create_subprocess_exec)

    with pytest.raises(RuntimeError, match="exited with code 7"):
        await worker_runtime.spawn_worker_process("auto_apply_batch")


@pytest.mark.asyncio
async def test_spawn_worker_process_accepts_zero_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeProcess:
        async def wait(self) -> int:
            return 0

    seen: list[tuple[str, ...]] = []

    async def _fake_create_subprocess_exec(*args: str) -> _FakeProcess:
        seen.append(args)
        return _FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", _fake_create_subprocess_exec)

    await worker_runtime.spawn_worker_process("scheduled_scrape")

    assert seen == [
        (
            worker_runtime.sys.executable,
            "-m",
            "app.runtime.worker",
            "scheduled_scrape",
        )
    ]


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
