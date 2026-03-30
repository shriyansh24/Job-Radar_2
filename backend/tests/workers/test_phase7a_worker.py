from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.followup.models import FollowupReminder
from app.notifications.models import Notification
from app.pipeline.models import Application
from app.scraping.models import ScraperRun
from app.source_health.models import SourceRegistry
from app.workers import phase7a_worker


async def _create_user(db_session: AsyncSession, *, email: str) -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash="hashed-password",
        display_name="Phase7A User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_run_source_health_checks_marks_failing_sources(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = SourceRegistry(source_name="greenhouse", health_state="unknown")
    db_session.add(source)
    today = datetime.now(UTC).replace(hour=12, minute=0, second=0, microsecond=0)
    for index in range(10):
        db_session.add(
            ScraperRun(
                source="greenhouse",
                status="failed" if index < 8 else "completed",
                started_at=today - timedelta(minutes=index),
            )
        )
    await db_session.commit()

    @asynccontextmanager
    async def _session_factory():
        yield db_session

    monkeypatch.setattr(phase7a_worker, "async_session_factory", _session_factory)

    await phase7a_worker.run_source_health_checks()

    refreshed_source = await db_session.get(SourceRegistry, source.id)
    assert refreshed_source is not None
    assert refreshed_source.health_state == "failing"
    assert refreshed_source.last_check_at is not None


@pytest.mark.asyncio
async def test_run_followup_reminders_creates_notification_and_marks_sent(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = await _create_user(db_session, email="followup@example.com")
    application = Application(
        user_id=user.id,
        company_name="Acme",
        position_title="Platform Engineer",
        status="applied",
    )
    db_session.add(application)
    await db_session.flush()

    reminder = FollowupReminder(
        user_id=user.id,
        application_id=application.id,
        reminder_at=datetime.now(UTC) - timedelta(hours=1),
        reminder_note="Follow up on recruiter thread",
        is_sent=False,
    )
    db_session.add(reminder)
    await db_session.commit()

    @asynccontextmanager
    async def _session_factory():
        yield db_session

    monkeypatch.setattr(phase7a_worker, "async_session_factory", _session_factory)

    await phase7a_worker.run_followup_reminders()

    notification = await db_session.scalar(
        select(Notification).where(Notification.user_id == user.id)
    )
    refreshed_reminder = await db_session.get(FollowupReminder, reminder.id)

    assert notification is not None
    assert notification.notification_type == "followup"
    assert "Platform Engineer" in notification.title
    assert refreshed_reminder is not None
    assert refreshed_reminder.is_sent is True
