"""Tests for the daily digest worker."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.jobs.models import Job
from app.notifications.models import Notification
from app.pipeline.models import Application, ApplicationStatusHistory
from app.workers.digest_worker import _generate_user_digest


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email="digest-test@example.com",
        password_hash="hashed",
        display_name="Digest Tester",
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def recent_jobs(db_session: AsyncSession, test_user: User) -> list[Job]:
    now = datetime.now(timezone.utc)
    jobs = []
    for i in range(3):
        job = Job(
            id=f"digest-job-{i}",
            user_id=test_user.id,
            source="test",
            title=f"Engineer {i}",
            company_name=f"Company {i}",
            match_score=90 - i * 10,
            is_active=True,
            created_at=now - timedelta(hours=i + 1),
        )
        jobs.append(job)
    db_session.add_all(jobs)
    await db_session.commit()
    return jobs


@pytest.fixture
async def old_jobs(db_session: AsyncSession, test_user: User) -> list[Job]:
    jobs = []
    for i in range(2):
        job = Job(
            id=f"digest-old-job-{i}",
            user_id=test_user.id,
            source="test",
            title=f"Old Engineer {i}",
            company_name=f"Old Corp {i}",
            is_active=True,
            created_at=datetime.now(timezone.utc) - timedelta(days=3),
        )
        jobs.append(job)
    db_session.add_all(jobs)
    await db_session.commit()
    return jobs


@pytest.fixture
async def stale_application(
    db_session: AsyncSession, test_user: User, old_jobs: list[Job]
) -> Application:
    app = Application(
        user_id=test_user.id,
        job_id=old_jobs[0].id,
        company_name="Old Corp 0",
        position_title="Old Engineer 0",
        status="applied",
        applied_at=datetime.now(timezone.utc) - timedelta(days=10),
    )
    db_session.add(app)
    await db_session.commit()
    return app


@pytest.mark.asyncio
async def test_digest_creates_notification_with_new_jobs(
    db_session: AsyncSession, test_user: User, recent_jobs: list[Job]
) -> None:
    created = await _generate_user_digest(db_session, test_user.id)
    assert created is True

    result = await db_session.scalars(
        select(Notification).where(
            Notification.user_id == test_user.id,
            Notification.notification_type == "daily_digest",
        )
    )
    notifs = list(result.all())
    assert len(notifs) == 1
    assert "3 new job(s) discovered" in notifs[0].body
    assert "Engineer 0" in notifs[0].body
    assert notifs[0].title == "Daily Digest: 3 new jobs"


@pytest.mark.asyncio
async def test_digest_skips_when_nothing_new(
    db_session: AsyncSession, test_user: User, old_jobs: list[Job]
) -> None:
    created = await _generate_user_digest(db_session, test_user.id)
    assert created is False

    result = await db_session.scalars(
        select(Notification).where(
            Notification.user_id == test_user.id,
            Notification.notification_type == "daily_digest",
        )
    )
    assert len(list(result.all())) == 0


@pytest.mark.asyncio
async def test_digest_includes_stale_apps(
    db_session: AsyncSession,
    test_user: User,
    old_jobs: list[Job],
    stale_application: Application,
) -> None:
    created = await _generate_user_digest(db_session, test_user.id)
    assert created is True

    result = await db_session.scalars(
        select(Notification).where(
            Notification.user_id == test_user.id,
            Notification.notification_type == "daily_digest",
        )
    )
    notifs = list(result.all())
    assert len(notifs) == 1
    assert "may need follow-up" in notifs[0].body


@pytest.mark.asyncio
async def test_digest_includes_status_changes(
    db_session: AsyncSession,
    test_user: User,
    recent_jobs: list[Job],
) -> None:
    # Create an application with a recent status change
    app = Application(
        user_id=test_user.id,
        job_id=recent_jobs[0].id,
        company_name="Company 0",
        position_title="Engineer 0",
        status="screening",
    )
    db_session.add(app)
    await db_session.flush()

    history = ApplicationStatusHistory(
        application_id=app.id,
        old_status="applied",
        new_status="screening",
        change_source="manual",
        changed_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    db_session.add(history)
    await db_session.commit()

    created = await _generate_user_digest(db_session, test_user.id)
    assert created is True

    result = await db_session.scalars(
        select(Notification).where(
            Notification.user_id == test_user.id,
            Notification.notification_type == "daily_digest",
        )
    )
    notifs = list(result.all())
    assert len(notifs) == 1
    assert "status change" in notifs[0].body


@pytest.mark.asyncio
async def test_digest_notification_type_is_daily_digest(
    db_session: AsyncSession, test_user: User, recent_jobs: list[Job]
) -> None:
    await _generate_user_digest(db_session, test_user.id)

    result = await db_session.scalars(
        select(Notification).where(Notification.user_id == test_user.id)
    )
    notif = result.first()
    assert notif is not None
    assert notif.notification_type == "daily_digest"
    assert notif.link == "/jobs?sort=created_at&order=desc"
