from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from app.auth.models import User
from app.auto_apply.models import AutoApplyProfile, AutoApplyRule, AutoApplyRun
from app.auto_apply.service import AutoApplyService
from app.jobs.models import Job


async def _make_user(db_session, email: str = "user@example.com") -> User:
    user = User(email=email, password_hash="pw")
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.mark.asyncio
async def test_trigger_run_returns_idle_without_profile(db_session):
    user = await _make_user(db_session)
    await db_session.commit()

    service = AutoApplyService(db_session)
    result = await service.trigger_run(user.id)

    assert result["status"] == "idle"
    assert "profile" in result["message"].lower()


@pytest.mark.asyncio
async def test_trigger_run_executes_batch(db_session, monkeypatch):
    user = await _make_user(db_session, "batch@example.com")
    profile = AutoApplyProfile(user_id=user.id, name="Primary", is_active=True)
    rule = AutoApplyRule(user_id=user.id, name="Match", is_active=True)
    db_session.add_all([profile, rule])
    await db_session.commit()

    fake_run = AutoApplyRun(id=uuid.uuid4(), status="success")
    fake_orchestrator = SimpleNamespace(run_batch=AsyncMock(return_value=[fake_run]))

    service = AutoApplyService(db_session)
    monkeypatch.setattr(service, "_build_orchestrator", lambda: fake_orchestrator)

    result = await service.trigger_run(user.id)

    assert result["status"] == "completed"
    assert result["runs_created"] == 1
    assert result["run_ids"] == [str(fake_run.id)]


@pytest.mark.asyncio
async def test_apply_single_executes_orchestrator(db_session, monkeypatch):
    user = await _make_user(db_session, "single@example.com")
    profile = AutoApplyProfile(user_id=user.id, name="Primary", is_active=True)
    job = Job(
        id="job-single-1",
        user_id=user.id,
        source="lever",
        source_url="https://jobs.lever.co/acme/12345678-1234-1234-1234-123456789abc",
        title="Engineer",
        status="new",
        is_active=True,
    )
    db_session.add_all([profile, job])
    await db_session.commit()

    fake_run = AutoApplyRun(id=uuid.uuid4(), job_id=job.id, status="filled")
    fake_orchestrator = SimpleNamespace(apply_to_job=AsyncMock(return_value=fake_run))

    service = AutoApplyService(db_session)
    monkeypatch.setattr(service, "_build_orchestrator", lambda: fake_orchestrator)

    result = await service.apply_single(job.id, user.id)

    assert result["status"] == "filled"
    assert result["job_id"] == job.id
    assert result["run_id"] == str(fake_run.id)
    assert result["review_required"] is True
    assert "Manual confirmation required before final submission." in result["review_items"]


@pytest.mark.asyncio
async def test_pause_deactivates_active_rules(db_session):
    user = await _make_user(db_session, "pause@example.com")
    rules = [
        AutoApplyRule(user_id=user.id, name="One", is_active=True),
        AutoApplyRule(user_id=user.id, name="Two", is_active=True),
    ]
    db_session.add_all(rules)
    await db_session.commit()

    service = AutoApplyService(db_session)
    result = await service.pause(user.id)

    refreshed = (
        await db_session.scalars(select(AutoApplyRule).where(AutoApplyRule.user_id == user.id))
    ).all()

    assert result["status"] == "paused"
    assert result["rules_paused"] == 2
    assert all(rule.is_active is False for rule in refreshed)


@pytest.mark.asyncio
async def test_get_stats_counts_filled_and_running(db_session):
    user = await _make_user(db_session, "stats@example.com")
    runs = [
        AutoApplyRun(user_id=user.id, status="success"),
        AutoApplyRun(user_id=user.id, status="filled"),
        AutoApplyRun(user_id=user.id, status="running"),
        AutoApplyRun(user_id=user.id, status="failed"),
    ]
    db_session.add_all(runs)
    await db_session.commit()

    service = AutoApplyService(db_session)
    stats = await service.get_stats(user.id)

    assert stats["total_runs"] == 4
    assert stats["successful"] == 2
    assert stats["pending"] == 1
    assert stats["failed"] == 1


@pytest.mark.asyncio
async def test_serialize_run_exposes_review_queue_details(db_session):
    user = await _make_user(db_session, "review@example.com")
    run = AutoApplyRun(
        user_id=user.id,
        job_id="job-review-1",
        status="filled",
        fields_filled={"email": "jane@example.com"},
        fields_missed=["LinkedIn Profile"],
        review_items=["Review custom question 'Work authorization'"],
    )
    db_session.add(run)
    await db_session.commit()

    service = AutoApplyService(db_session)
    payload = service.serialize_run(run)

    assert payload.review_required is True
    assert payload.review_items == [
        "Manual confirmation required before final submission.",
        "Review custom question 'Work authorization'",
        "Provide value for 'LinkedIn Profile'",
    ]
