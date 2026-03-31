from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.integrations.google_oauth import GoogleOAuthError
from app.settings.models import UserIntegrationSecret
from app.workers import gmail_worker


async def _create_user(db_session: AsyncSession, *, email: str) -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash="hashed-password",
        display_name="Gmail Worker User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_gmail_worker_records_last_error_and_continues(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failing_user = await _create_user(db_session, email="gmail-worker-fail@example.com")
    passing_user = await _create_user(db_session, email="gmail-worker-pass@example.com")
    failing_user_id = failing_user.id
    passing_user_id = passing_user.id

    failing_integration_id = uuid.uuid4()
    passing_integration_id = uuid.uuid4()
    failing_integration = UserIntegrationSecret(
        id=failing_integration_id,
        user_id=failing_user_id,
        provider="google",
        auth_type="oauth",
        secret_json={"access_token": "fail", "refresh_token": "refresh-fail"},
        account_email="fail@example.com",
    )
    passing_integration = UserIntegrationSecret(
        id=passing_integration_id,
        user_id=passing_user_id,
        provider="google",
        auth_type="oauth",
        secret_json={"access_token": "pass", "refresh_token": "refresh-pass"},
        account_email="pass@example.com",
    )
    db_session.add_all([failing_integration, passing_integration])
    await db_session.commit()

    @asynccontextmanager
    async def _session_factory():
        yield db_session

    processed_user_ids: list[uuid.UUID] = []

    async def _fake_sync_gmail_for_user(
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        query: str,
        max_messages: int,
    ) -> None:
        assert db is db_session
        assert query == gmail_worker.settings.google_gmail_sync_query
        assert max_messages == gmail_worker.settings.google_gmail_sync_max_messages
        processed_user_ids.append(user_id)
        if user_id == failing_user_id:
            raise GoogleOAuthError("refresh token expired")

    monkeypatch.setattr(gmail_worker, "async_session_factory", _session_factory)
    monkeypatch.setattr(gmail_worker, "sync_gmail_for_user", _fake_sync_gmail_for_user)

    await gmail_worker.run_gmail_sync()

    refreshed_failure = await db_session.scalar(
        select(UserIntegrationSecret).where(UserIntegrationSecret.id == failing_integration_id)
    )
    refreshed_success = await db_session.scalar(
        select(UserIntegrationSecret).where(UserIntegrationSecret.id == passing_integration_id)
    )

    assert processed_user_ids == [failing_user_id, passing_user_id]
    assert refreshed_failure is not None
    assert refreshed_failure.last_error == "refresh token expired"
    assert refreshed_success is not None
    assert refreshed_success.last_error is None


@pytest.mark.asyncio
async def test_gmail_worker_raises_after_retryable_failures(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failing_user = await _create_user(db_session, email="gmail-worker-runtime-fail@example.com")
    passing_user = await _create_user(db_session, email="gmail-worker-runtime-pass@example.com")
    failing_user_id = failing_user.id
    passing_user_id = passing_user.id

    db_session.add_all(
        [
            UserIntegrationSecret(
                id=uuid.uuid4(),
                user_id=failing_user_id,
                provider="google",
                auth_type="oauth",
                secret_json={"access_token": "fail", "refresh_token": "refresh-fail"},
                account_email="fail@example.com",
            ),
            UserIntegrationSecret(
                id=uuid.uuid4(),
                user_id=passing_user_id,
                provider="google",
                auth_type="oauth",
                secret_json={"access_token": "pass", "refresh_token": "refresh-pass"},
                account_email="pass@example.com",
            ),
        ]
    )
    await db_session.commit()

    @asynccontextmanager
    async def _session_factory():
        yield db_session

    processed_user_ids: list[uuid.UUID] = []

    async def _fake_sync_gmail_for_user(
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        query: str,
        max_messages: int,
    ) -> None:
        assert db is db_session
        processed_user_ids.append(user_id)
        if user_id == failing_user_id:
            raise RuntimeError("gmail upstream unavailable")

    monkeypatch.setattr(gmail_worker, "async_session_factory", _session_factory)
    monkeypatch.setattr(gmail_worker, "sync_gmail_for_user", _fake_sync_gmail_for_user)

    with pytest.raises(RuntimeError, match="retryable integration failure"):
        await gmail_worker.run_gmail_sync()

    failing_integration = await db_session.scalar(
        select(UserIntegrationSecret).where(UserIntegrationSecret.user_id == failing_user_id)
    )
    passing_integration = await db_session.scalar(
        select(UserIntegrationSecret).where(UserIntegrationSecret.user_id == passing_user_id)
    )

    assert processed_user_ids == [failing_user_id, passing_user_id]
    assert failing_integration is not None
    assert failing_integration.last_error == "gmail upstream unavailable"
    assert passing_integration is not None
    assert passing_integration.last_error is None
