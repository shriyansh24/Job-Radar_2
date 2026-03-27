from __future__ import annotations

import pytest

from app.runtime import arq_worker
from app.runtime.job_registry import ANALYSIS_QUEUE, OPS_QUEUE, SCRAPING_QUEUE


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
    monkeypatch.setattr(arq_worker, "build_redis_settings", lambda: object())

    worker = arq_worker.build_worker(role)

    assert worker.queue_name == queue_name
    assert set(worker.functions)


def test_build_worker_rejects_unknown_role() -> None:
    with pytest.raises(ValueError, match="Unknown worker role"):
        arq_worker.build_worker("not-a-real-role")
