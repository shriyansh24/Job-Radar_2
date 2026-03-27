from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from app.auth.models import User
from app.auto_apply.lever_adapter import ApplicationResult
from app.auto_apply.models import AutoApplyProfile
from app.auto_apply.orchestrator import AutoApplyOrchestrator
from app.auto_apply.safety import SafetyCheck, SafetyResult
from app.config import Settings
from app.jobs.models import Job
from app.pipeline.models import Application


def test_build_screenshot_path_uses_system_temp_dir(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("app.auto_apply.orchestrator.gettempdir", lambda: str(tmp_path))
    orchestrator = AutoApplyOrchestrator(db=None, settings=None, llm_client=None)  # type: ignore[arg-type]

    run_id = uuid.uuid4()
    screenshot_path = Path(orchestrator._build_screenshot_path(run_id))

    assert screenshot_path.parent == tmp_path
    assert screenshot_path.name == f"auto_apply_{run_id}.png"


@pytest.mark.asyncio
async def test_apply_to_job_uses_lever_api_and_records_application(db_session):
    user = User(email="auto@example.com", password_hash="pw")
    db_session.add(user)
    await db_session.flush()

    profile = AutoApplyProfile(
        user_id=user.id,
        name="Primary",
        full_name="Jane Doe",
        email="jane@example.com",
        is_active=True,
    )
    job = Job(
        id="job-lever-1",
        user_id=user.id,
        source="lever",
        source_url="https://jobs.lever.co/acme/12345678-1234-1234-1234-123456789abc",
        title="Software Engineer",
        company_name="Acme",
        status="new",
        is_active=True,
    )
    db_session.add_all([profile, job])
    await db_session.commit()

    orchestrator = AutoApplyOrchestrator(db_session, Settings(), llm_client=None)

    async def fake_build_safety_layer(*args, **kwargs):  # noqa: ANN002, ANN003
        class FakeSafety:
            async def check_safety(self, *args, **kwargs):  # noqa: ANN002, ANN003
                return SafetyResult(
                    passed=True,
                    checks=[SafetyCheck(name="duplicate", passed=True, detail="ok")],
                )

        return FakeSafety()

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(orchestrator, "_build_safety_layer", fake_build_safety_layer)
    monkeypatch.setattr(
        "app.auto_apply.orchestrator.LeverAPIAdapter.apply",
        AsyncMock(
            return_value=ApplicationResult(
                success=True,
                ats="lever",
                method="api",
                fields_filled={"email": "jane@example.com"},
            )
        ),
    )

    run = await orchestrator.apply_to_job(job, profile, allow_first_time_ats=True)

    application = await db_session.scalar(
        select(Application).where(
            Application.user_id == user.id,
            Application.job_id == job.id,
        )
    )

    monkeypatch.undo()

    assert run.status == "success"
    assert application is not None
    assert application.source == "auto_apply:lever"


@pytest.mark.asyncio
async def test_apply_to_job_blocks_when_safety_fails(db_session):
    user = User(email="blocked@example.com", password_hash="pw")
    db_session.add(user)
    await db_session.flush()

    profile = AutoApplyProfile(
        user_id=user.id,
        name="Primary",
        full_name="Jane Doe",
        email="jane@example.com",
        is_active=True,
    )
    job = Job(
        id="job-lever-2",
        user_id=user.id,
        source="lever",
        source_url="https://jobs.lever.co/acme/12345678-1234-1234-1234-123456789abd",
        title="Software Engineer",
        company_name="Acme",
        status="new",
        is_active=True,
    )
    db_session.add_all([profile, job])
    await db_session.commit()

    orchestrator = AutoApplyOrchestrator(db_session, Settings(), llm_client=None)

    async def fake_build_safety_layer(*args, **kwargs):  # noqa: ANN002, ANN003
        class FakeSafety:
            async def check_safety(self, *args, **kwargs):  # noqa: ANN002, ANN003
                return SafetyResult(
                    passed=False,
                    checks=[SafetyCheck(name="duplicate", passed=False, detail="Already applied")],
                )

        return FakeSafety()

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(orchestrator, "_build_safety_layer", fake_build_safety_layer)
    apply_mock = AsyncMock()
    monkeypatch.setattr("app.auto_apply.orchestrator.LeverAPIAdapter.apply", apply_mock)

    run = await orchestrator.apply_to_job(job, profile)

    monkeypatch.undo()

    assert run.status == "failed"
    assert "duplicate" in (run.error_message or "")
    apply_mock.assert_not_awaited()
