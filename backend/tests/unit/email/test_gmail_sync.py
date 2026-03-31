from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.email import gmail_sync as gmail_sync_module
from app.email.gmail_sync import sync_gmail_for_user
from app.email.schemas import EmailWebhookResponse
from app.integrations.gmail_client import GmailMessage
from app.integrations.google_oauth import GoogleOAuthError
from app.settings.models import UserIntegrationSecret


async def _create_user(db_session: AsyncSession, email: str) -> User:
    user = User(email=email, password_hash="hashed-password")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_sync_gmail_for_user_refreshes_expired_access_tokens(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = await _create_user(db_session, "gmail-sync-refresh@example.com")
    integration = UserIntegrationSecret(
        user_id=user.id,
        provider="google",
        auth_type="oauth",
        secret_json={"access_token": "expired-access", "refresh_token": "refresh-token"},
        account_email="owner@gmail.com",
    )
    db_session.add(integration)
    await db_session.commit()

    class _FakeGmailClient:
        def __init__(self) -> None:
            self.list_calls = 0

        async def list_message_ids(
            self,
            access_token: str,
            *,
            query: str,
            max_results: int,
        ) -> list[str]:
            self.list_calls += 1
            assert query == "label:important"
            assert max_results == 5
            if self.list_calls == 1:
                assert access_token == "expired-access"
                raise GoogleOAuthError("expired")
            assert access_token == "fresh-access"
            return ["gmail-1"]

        async def get_message(self, access_token: str, message_id: str) -> GmailMessage:
            assert access_token == "fresh-access"
            assert message_id == "gmail-1"
            return GmailMessage(
                message_id="gmail-1",
                thread_id="thread-1",
                sender="recruiting@acme-corp.com",
                recipient="owner@jobradar.dev",
                subject="Interview Invitation",
                text_body="We would like to schedule an interview with you.",
                html_body="",
                received_at=datetime.now(UTC),
            )

    class _FakeEmailService:
        def __init__(self, db: AsyncSession) -> None:
            assert db is db_session

        async def process_inbound_message(
            self,
            inbound,
            user_id,
            *,
            auto_transition_min_confidence: float,
        ):
            assert inbound.source_provider == "google"
            assert inbound.source_message_id == "gmail-1"
            assert user_id == user.id
            assert auto_transition_min_confidence == 0.85
            return EmailWebhookResponse(
                status="updated",
                action="interview",
                company="Acme Corp",
                confidence=0.9,
            )

    async def _fake_refresh_google_access_token(refresh_token: str) -> dict[str, str]:
        assert refresh_token == "refresh-token"
        return {"access_token": "fresh-access"}

    monkeypatch.setattr(gmail_sync_module, "GmailClient", _FakeGmailClient)
    monkeypatch.setattr(gmail_sync_module, "EmailService", _FakeEmailService)
    monkeypatch.setattr(
        gmail_sync_module,
        "refresh_google_access_token",
        _fake_refresh_google_access_token,
    )

    result = await sync_gmail_for_user(
        db_session,
        user_id=user.id,
        query="label:important",
        max_messages=5,
    )

    await db_session.refresh(integration)
    assert result.messages_seen == 1
    assert result.messages_processed == 1
    assert result.duplicates_skipped == 0
    assert result.signals_detected == 1
    assert result.transitions_applied == 1
    assert integration.secret_json == {
        "access_token": "fresh-access",
        "refresh_token": "refresh-token",
    }
    assert integration.last_synced_at is not None
    assert integration.last_validated_at is not None
    assert integration.last_error is None


@pytest.mark.asyncio
async def test_sync_gmail_for_user_requires_refreshable_credentials(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session, "gmail-sync-missing-refresh@example.com")
    db_session.add(
        UserIntegrationSecret(
            user_id=user.id,
            provider="google",
            auth_type="oauth",
            secret_json={"access_token": "access-only"},
        )
    )
    await db_session.commit()

    with pytest.raises(GoogleOAuthError, match="missing refreshable credentials"):
        await sync_gmail_for_user(
            db_session,
            user_id=user.id,
            query="label:important",
            max_messages=5,
        )
