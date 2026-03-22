from __future__ import annotations

import uuid
from pathlib import Path

from app.auto_apply.orchestrator import AutoApplyOrchestrator


def test_build_screenshot_path_uses_system_temp_dir(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("app.auto_apply.orchestrator.gettempdir", lambda: str(tmp_path))
    orchestrator = AutoApplyOrchestrator(db=None, settings=None, llm_client=None)  # type: ignore[arg-type]

    run_id = uuid.uuid4()
    screenshot_path = Path(orchestrator._build_screenshot_path(run_id))

    assert screenshot_path.parent == tmp_path
    assert screenshot_path.name == f"auto_apply_{run_id}.png"
