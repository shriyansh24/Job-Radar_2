from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.jobs.models import Job
from app.notifications.models import Notification
from app.settings.models import SavedSearch
from app.workers import alert_worker


async def _create_user(db_session: AsyncSession, *, email: str) -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash="hashed-password",
        display_name="Alert Worker User",
        is_active=True,
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
) -> Job:
    job = Job(
        id=job_id,
        user_id=user_id,
        source="test",
        title=title,
        company_name=company_name,
        is_active=True,
        created_at=created_at,
    )
    db_session.add(job)
    await db_session.commit()
    return job


@pytest.mark.asyncio
async def test_check_saved_search_alerts_creates_notification_for_new_matches(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = await _create_user(db_session, email="alerts@example.com")
    now = datetime.now(UTC)
    await _create_job(
        db_session,
        user_id=user.id,
        job_id="alert-job-1",
        title="Backend Engineer",
        company_name="Acme",
        created_at=now - timedelta(hours=1),
    )
    saved_search = SavedSearch(
        user_id=user.id,
        name="Backend roles",
        filters={"q": "Engineer"},
        alert_enabled=True,
        last_checked_at=now - timedelta(days=1),
    )
    db_session.add(saved_search)
    await db_session.commit()
    await db_session.refresh(saved_search)

    @asynccontextmanager
    async def _session_factory():
        yield db_session

    monkeypatch.setattr(alert_worker, "async_session_factory", _session_factory)

    await alert_worker.check_saved_search_alerts()

    notification = await db_session.scalar(
        select(Notification).where(Notification.user_id == user.id)
    )
    refreshed_search = await db_session.get(SavedSearch, saved_search.id)

    assert notification is not None
    assert notification.notification_type == "saved_search_alert"
    assert notification.title == "Saved search: Backend roles"
    assert notification.link == "/jobs?q=Engineer"
    assert refreshed_search is not None
    assert refreshed_search.last_checked_at is not None
    assert refreshed_search.last_matched_at is not None
    assert refreshed_search.last_match_count == 1
    assert refreshed_search.last_error is None
    assert refreshed_search.last_checked_at > now - timedelta(minutes=1)
