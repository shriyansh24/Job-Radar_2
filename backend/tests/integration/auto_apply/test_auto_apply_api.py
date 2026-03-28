from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.auth.models import User
from app.auto_apply.models import AutoApplyProfile, AutoApplyRule, AutoApplyRun
from app.auto_apply.service import AutoApplyService
from app.jobs.models import Job


async def _register_and_login(client: AsyncClient) -> tuple[uuid.UUID, str]:
    email = f"auto-apply-api-{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "testpassword123"},
    )
    token = login_response.cookies["jr_access_token"]
    me_response = await client.get(
        "/api/v1/auth/me",
        headers=_auth(token),
    )
    return uuid.UUID(me_response.json()["id"]), token


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _make_other_user(db_session) -> User:
    user = User(email=f"other-{uuid.uuid4().hex[:8]}@test.com", password_hash="pw")
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.mark.asyncio
async def test_trigger_run_returns_idle_without_active_profile(client: AsyncClient) -> None:
    _, token = await _register_and_login(client)

    response = await client.post("/api/v1/auto-apply/run", headers=_auth(token))

    assert response.status_code == 200
    assert response.json() == {
        "status": "idle",
        "message": "No active auto-apply profile",
    }


@pytest.mark.asyncio
async def test_trigger_run_executes_batch_when_profile_and_rules_exist(
    client: AsyncClient,
    db_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id, token = await _register_and_login(client)
    db_session.add_all(
        [
            AutoApplyProfile(user_id=user_id, name="Primary", is_active=True),
            AutoApplyRule(user_id=user_id, name="Match", is_active=True),
        ]
    )
    await db_session.commit()

    fake_run = SimpleNamespace(id=uuid.uuid4())
    fake_orchestrator = SimpleNamespace(run_batch=AsyncMock(return_value=[fake_run]))
    monkeypatch.setattr(
        AutoApplyService,
        "_build_orchestrator",
        lambda self: fake_orchestrator,
    )

    response = await client.post("/api/v1/auto-apply/run", headers=_auth(token))

    assert response.status_code == 200
    assert response.json() == {
        "status": "completed",
        "message": "Auto-apply batch executed",
        "runs_created": 1,
        "run_ids": [str(fake_run.id)],
    }
    fake_orchestrator.run_batch.assert_awaited_once_with(user_id)


@pytest.mark.asyncio
async def test_apply_single_runs_against_owned_job(
    client: AsyncClient,
    db_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id, token = await _register_and_login(client)
    profile = AutoApplyProfile(user_id=user_id, name="Primary", is_active=True)
    job = Job(
        id="auto-apply-job-001",
        user_id=user_id,
        source="lever",
        title="Automation Engineer",
        company_name="Acme",
        status="new",
    )
    db_session.add_all([profile, job])
    await db_session.commit()

    fake_run = SimpleNamespace(id=uuid.uuid4(), status="filled", error_message=None)
    fake_orchestrator = SimpleNamespace(apply_to_job=AsyncMock(return_value=fake_run))
    monkeypatch.setattr(
        AutoApplyService,
        "_build_orchestrator",
        lambda self: fake_orchestrator,
    )

    response = await client.post(
        "/api/v1/auto-apply/apply-single",
        headers=_auth(token),
        json={"job_id": job.id},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "filled",
        "job_id": job.id,
        "run_id": str(fake_run.id),
        "message": "Application filled and ready for review",
    }

    call = fake_orchestrator.apply_to_job.await_args
    assert call.args[0].id == job.id
    assert call.args[1].id == profile.id
    assert call.kwargs == {"allow_first_time_ats": True}


@pytest.mark.asyncio
async def test_pause_deactivates_only_current_users_active_rules(
    client: AsyncClient,
    db_session,
) -> None:
    user_id, token = await _register_and_login(client)
    other_user = await _make_other_user(db_session)

    current_rules = [
        AutoApplyRule(user_id=user_id, name="One", is_active=True),
        AutoApplyRule(user_id=user_id, name="Two", is_active=True),
    ]
    untouched_rules = [
        AutoApplyRule(user_id=user_id, name="Already paused", is_active=False),
        AutoApplyRule(user_id=other_user.id, name="Other user", is_active=True),
    ]
    db_session.add_all(current_rules + untouched_rules)
    await db_session.commit()

    response = await client.post("/api/v1/auto-apply/pause", headers=_auth(token))

    assert response.status_code == 200
    assert response.json() == {
        "status": "paused",
        "message": "Auto-apply paused",
        "rules_paused": 2,
    }

    await db_session.refresh(current_rules[0])
    await db_session.refresh(current_rules[1])
    await db_session.refresh(untouched_rules[0])
    await db_session.refresh(untouched_rules[1])
    assert current_rules[0].is_active is False
    assert current_rules[1].is_active is False
    assert untouched_rules[0].is_active is False
    assert untouched_rules[1].is_active is True


@pytest.mark.asyncio
async def test_stats_and_runs_are_user_scoped_and_runs_are_ordered(
    client: AsyncClient,
    db_session,
) -> None:
    user_id, token = await _register_and_login(client)
    other_user = await _make_other_user(db_session)
    now = datetime.now(UTC)

    db_session.add_all(
        [
            AutoApplyRun(
                user_id=user_id,
                status="filled",
                started_at=now - timedelta(minutes=5),
                completed_at=now - timedelta(minutes=4),
            ),
            AutoApplyRun(
                user_id=user_id,
                status="running",
                started_at=now - timedelta(minutes=1),
            ),
            AutoApplyRun(
                user_id=user_id,
                status="failed",
                started_at=now - timedelta(minutes=10),
                completed_at=now - timedelta(minutes=9),
                error_message="bad field mapping",
            ),
            AutoApplyRun(
                user_id=other_user.id,
                status="success",
                started_at=now,
                completed_at=now,
            ),
        ]
    )
    await db_session.commit()

    stats_response = await client.get("/api/v1/auto-apply/stats", headers=_auth(token))
    runs_response = await client.get("/api/v1/auto-apply/runs", headers=_auth(token))

    assert stats_response.status_code == 200
    assert stats_response.json() == {
        "total_runs": 3,
        "successful": 1,
        "failed": 1,
        "pending": 1,
    }

    assert runs_response.status_code == 200
    runs = runs_response.json()
    assert [item["status"] for item in runs] == ["running", "filled", "failed"]
    assert all(item["id"] for item in runs)
    assert all(item["error_message"] in {None, "bad field mapping"} for item in runs)
