from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.email import gmail_sync as gmail_sync_module
from app.email.gmail_sync import sync_gmail_for_user
from app.email.schemas import EmailWebhookResponse
from app.integrations.gmail_client import GmailAPIError, GmailMessage
from app.integrations.google_oauth import GoogleOAuthError
from app.settings.models import UserIntegrationSecret
from app.shared.secrets import seal_secret_mapping, unseal_secret_mapping


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
        secret_json=seal_secret_mapping(
            {"access_token": "expired-access", "refresh_token": "refresh-token"}
        ),
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
                raise GmailAPIError(
                    "Google access token is invalid or expired.",
                    status_code=401,
                    token_refresh_recommended=True,
                )
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
    assert result.messages_failed == 0
    assert result.duplicates_skipped == 0
    assert result.signals_detected == 1
    assert result.transitions_applied == 1
    assert integration.secret_json != {
        "access_token": "fresh-access",
        "refresh_token": "refresh-token",
    }
    assert unseal_secret_mapping(integration.secret_json) == {
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
            secret_json=seal_secret_mapping({"access_token": "access-only"}),
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


@pytest.mark.asyncio
async def test_sync_gmail_for_user_continues_after_message_processing_failure(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = await _create_user(db_session, "gmail-sync-partial@example.com")
    integration = UserIntegrationSecret(
        user_id=user.id,
        provider="google",
        auth_type="oauth",
        secret_json=seal_secret_mapping(
            {"access_token": "access-token", "refresh_token": "refresh-token"}
        ),
        account_email="owner@gmail.com",
    )
    db_session.add(integration)
    await db_session.commit()

    class _FakeGmailClient:
        async def list_message_ids(
            self,
            access_token: str,
            *,
            query: str,
            max_results: int,
        ) -> list[str]:
            assert access_token == "access-token"
            return ["gmail-bad", "gmail-good"]

        async def get_message(self, access_token: str, message_id: str) -> GmailMessage:
            if message_id == "gmail-bad":
                raise RuntimeError("broken message payload")
            return GmailMessage(
                message_id="gmail-good",
                thread_id="thread-2",
                sender="recruiting@acme-corp.com",
                recipient="owner@jobradar.dev",
                subject="Status update",
                text_body="We moved you to the next stage.",
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
            assert inbound.source_message_id == "gmail-good"
            assert user_id == user.id
            assert auto_transition_min_confidence == 0.85
            return EmailWebhookResponse(
                status="updated",
                action="status_update",
                company="Acme Corp",
                confidence=0.92,
            )

    monkeypatch.setattr(gmail_sync_module, "GmailClient", _FakeGmailClient)
    monkeypatch.setattr(gmail_sync_module, "EmailService", _FakeEmailService)

    result = await sync_gmail_for_user(
        db_session,
        user_id=user.id,
        query="label:important",
        max_messages=5,
    )

    await db_session.refresh(integration)
    assert result.messages_seen == 2
    assert result.messages_processed == 1
    assert result.messages_failed == 1
    assert result.duplicates_skipped == 0
    assert result.signals_detected == 1
    assert result.transitions_applied == 1
    assert integration.last_synced_at is not None
    assert integration.last_error is not None
    assert "1 failed message" in integration.last_error


@pytest.mark.asyncio
async def test_sync_gmail_for_user_does_not_refresh_on_non_auth_list_failures(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = await _create_user(db_session, "gmail-sync-quota@example.com")
    db_session.add(
        UserIntegrationSecret(
            user_id=user.id,
            provider="google",
            auth_type="oauth",
            secret_json=seal_secret_mapping(
                {"access_token": "access-token", "refresh_token": "refresh-token"}
            ),
        )
    )
    await db_session.commit()

    class _FakeGmailClient:
        async def list_message_ids(
            self,
            access_token: str,
            *,
            query: str,
            max_results: int,
        ) -> list[str]:
            raise GmailAPIError(
                "Gmail API request failed with status 429.",
                status_code=429,
                retryable=True,
            )

    async def _fake_refresh_google_access_token(refresh_token: str) -> dict[str, str]:
        raise AssertionError("refresh should not be attempted for non-auth Gmail failures")

    monkeypatch.setattr(gmail_sync_module, "GmailClient", _FakeGmailClient)
    monkeypatch.setattr(
        gmail_sync_module,
        "refresh_google_access_token",
        _fake_refresh_google_access_token,
    )

    with pytest.raises(GmailAPIError, match="status 429"):
        await sync_gmail_for_user(
            db_session,
            user_id=user.id,
            query="label:important",
            max_messages=5,
        )


@pytest.mark.asyncio
async def test_sync_gmail_for_user_refreshes_expired_tokens_during_message_fetch(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = await _create_user(db_session, "gmail-sync-midrun-refresh@example.com")
    integration = UserIntegrationSecret(
        user_id=user.id,
        provider="google",
        auth_type="oauth",
        secret_json=seal_secret_mapping(
            {"access_token": "expired-access", "refresh_token": "refresh-token"}
        ),
    )
    db_session.add(integration)
    await db_session.commit()

    class _FakeGmailClient:
        def __init__(self) -> None:
            self.message_calls = 0

        async def list_message_ids(
            self,
            access_token: str,
            *,
            query: str,
            max_results: int,
        ) -> list[str]:
            assert access_token == "expired-access"
            return ["gmail-1"]

        async def get_message(self, access_token: str, message_id: str) -> GmailMessage:
            self.message_calls += 1
            if self.message_calls == 1:
                raise GmailAPIError(
                    "Google access token is invalid or expired.",
                    status_code=401,
                    token_refresh_recommended=True,
                )
            assert access_token == "fresh-access"
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
            assert inbound.source_message_id == "gmail-1"
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
    assert result.messages_processed == 1
    assert integration.last_error is None
    assert unseal_secret_mapping(integration.secret_json) == {
        "access_token": "fresh-access",
        "refresh_token": "refresh-token",
    }
