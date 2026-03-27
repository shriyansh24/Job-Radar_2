from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.jobs.models import Job
from app.notifications.models import Notification
from app.pipeline.models import Application, ApplicationStatusHistory
from app.runtime.job_registry import OPS_QUEUE, get_registered_job
from app.workers import digest_worker


async def _create_user(
    db_session: AsyncSession,
    *,
    email: str,
    is_active: bool = True,
) -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash="hashed-password",
        display_name="Digest User",
        is_active=is_active,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _create_job(
    db_session: AsyncSession,
    *,
    user_id: uuid.UUID,
    job_id: str,
    title: str,
    company_name: str,
    created_at: datetime,
    match_score: Decimal | None = None,
) -> Job:
    job = Job(
        id=job_id,
        user_id=user_id,
        source="test",
        title=title,
        company_name=company_name,
        is_active=True,
        created_at=created_at,
        match_score=match_score,
    )
    db_session.add(job)
    await db_session.commit()
    return job


@pytest.mark.asyncio
async def test_daily_digest_is_registered_on_ops_queue() -> None:
    job = get_registered_job("daily_digest")

    assert job.queue_name == OPS_QUEUE
    assert job.max_tries == 2
    assert job.timeout_seconds == 1800


@pytest.mark.asyncio
async def test_generate_user_digest_creates_notification_for_new_jobs(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session, email="digest-new@example.com")
    now = datetime.now(UTC)
    await _create_job(
        db_session,
        user_id=user.id,
        job_id="digest-job-1",
        title="Platform Engineer",
        company_name="Acme",
        created_at=now - timedelta(hours=2),
        match_score=Decimal("91.5"),
    )
    await _create_job(
        db_session,
        user_id=user.id,
        job_id="digest-job-2",
        title="Data Engineer",
        company_name="Beta",
        created_at=now - timedelta(hours=4),
        match_score=Decimal("82.0"),
    )

    created = await digest_worker._generate_user_digest(db_session, user.id)
    await db_session.commit()

    assert created is True

    notification = await db_session.scalar(
        select(Notification).where(Notification.user_id == user.id)
    )
    assert notification is not None
    assert notification.notification_type == "daily_digest"
    assert notification.title == "Daily digest: 2 new jobs"
    assert notification.body is not None
    assert "2 new jobs" in notification.body
    assert "- Platform Engineer at Acme (91.5%)" in notification.body
    assert notification.link == "/jobs?sort=created_at&order=desc"


@pytest.mark.asyncio
async def test_generate_user_digest_skips_when_no_recent_activity(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session, email="digest-skip@example.com")
    await _create_job(
        db_session,
        user_id=user.id,
        job_id="digest-old-job",
        title="Old Engineer",
        company_name="Archive Corp",
        created_at=datetime.now(UTC) - timedelta(days=3),
    )

    created = await digest_worker._generate_user_digest(db_session, user.id)
    await db_session.commit()

    assert created is False
    notifications = list(
        (
            await db_session.scalars(
                select(Notification).where(Notification.user_id == user.id)
            )
        ).all()
    )
    assert notifications == []


@pytest.mark.asyncio
async def test_generate_user_digest_includes_status_changes_and_stale_apps(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session, email="digest-status@example.com")
    old_job = await _create_job(
        db_session,
        user_id=user.id,
        job_id="digest-status-job",
        title="Operations Analyst",
        company_name="Signal Co",
        created_at=datetime.now(UTC) - timedelta(days=2),
    )
    app = Application(
        user_id=user.id,
        job_id=old_job.id,
        company_name="Signal Co",
        position_title="Operations Analyst",
        status="screening",
        applied_at=datetime.now(UTC) - timedelta(days=10),
    )
    db_session.add(app)
    await db_session.flush()

    db_session.add(
        ApplicationStatusHistory(
            application_id=app.id,
            old_status="applied",
            new_status="screening",
            change_source="manual",
            changed_at=datetime.now(UTC) - timedelta(hours=3),
        )
    )
    await db_session.commit()

    created = await digest_worker._generate_user_digest(db_session, user.id)
    await db_session.commit()

    assert created is True

    notification = await db_session.scalar(
        select(Notification).where(Notification.user_id == user.id)
    )
    assert notification is not None
    assert notification.body is not None
    assert "1 status changes" in notification.body
    assert "1 follow-ups due" in notification.body


@pytest.mark.asyncio
async def test_run_daily_digest_processes_only_active_users(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active_user = await _create_user(db_session, email="digest-active@example.com")
    inactive_user = await _create_user(
        db_session,
        email="digest-inactive@example.com",
        is_active=False,
    )
    now = datetime.now(UTC)
    await _create_job(
        db_session,
        user_id=active_user.id,
        job_id="digest-active-job",
        title="Backend Engineer",
        company_name="Delta",
        created_at=now - timedelta(hours=1),
    )
    await _create_job(
        db_session,
        user_id=inactive_user.id,
        job_id="digest-inactive-job",
        title="Inactive Engineer",
        company_name="Echo",
        created_at=now - timedelta(hours=1),
    )

    @asynccontextmanager
    async def _session_factory():
        yield db_session

    monkeypatch.setattr(digest_worker, "async_session_factory", _session_factory)

    await digest_worker.run_daily_digest()

    notifications = list((await db_session.scalars(select(Notification))).all())
    assert len(notifications) == 1
    assert notifications[0].user_id == active_user.id
