from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.email.gmail_sync import GmailSyncResult
from app.integrations.google_oauth import GoogleOAuthState
from app.settings import service as settings_service_module
from app.settings.models import UserIntegrationSecret
from app.settings.schemas import AppSettingsUpdate, SavedSearchCreate
from app.settings.service import SettingsService
from app.shared.errors import NotFoundError, ValidationError
from app.shared.secrets import unseal_secret, unseal_secret_mapping


async def _create_user(
    db_session: AsyncSession,
    email: str = "settings-unit@example.com",
) -> User:
    user = User(email=email, password_hash="hashed-password")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_get_settings_creates_default_profile(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    service = SettingsService(db_session)

    settings = await service.get_settings(user.id)

    assert settings == {
        "theme": "dark",
        "notifications_enabled": True,
        "auto_apply_enabled": False,
    }
    profile = await service._get_or_create_profile(user.id)
    assert profile is not None


@pytest.mark.asyncio
async def test_saved_search_crud_is_user_scoped(db_session: AsyncSession) -> None:
    owner = await _create_user(db_session, "settings-owner@example.com")
    other = await _create_user(db_session, "settings-other@example.com")
    service = SettingsService(db_session)

    created = await service.create_saved_search(
        SavedSearchCreate(name="Remote Python", filters={"remote": True}, alert_enabled=True),
        owner.id,
    )
    listed = await service.list_saved_searches(owner.id)

    assert [search.id for search in listed] == [created.id]
    with pytest.raises(NotFoundError):
        await service.delete_saved_search(created.id, other.id)

    await service.delete_saved_search(created.id, owner.id)
    assert await service.list_saved_searches(owner.id) == []


@pytest.mark.asyncio
async def test_update_settings_persists_profile_flags(db_session: AsyncSession) -> None:
    user = await _create_user(db_session, "settings-update@example.com")
    service = SettingsService(db_session)

    updated = await service.update_settings(
        AppSettingsUpdate(
            theme="light",
            notifications_enabled=False,
            auto_apply_enabled=True,
        ),
        user.id,
    )

    assert updated == {
        "theme": "light",
        "notifications_enabled": False,
        "auto_apply_enabled": True,
    }


@pytest.mark.asyncio
async def test_list_integrations_includes_google_placeholder(db_session: AsyncSession) -> None:
    user = await _create_user(db_session, "settings-google-placeholder@example.com")
    service = SettingsService(db_session)

    integrations = await service.list_integrations(user.id)

    assert [integration["provider"] for integration in integrations] == [
        "openrouter",
        "serpapi",
        "theirstack",
        "apify",
        "google",
    ]
    assert integrations[-1] == {
        "provider": "google",
        "auth_type": "oauth",
        "connected": False,
        "status": "not_configured",
        "masked_value": None,
        "account_email": None,
        "scopes": [],
        "updated_at": None,
        "last_validated_at": None,
        "last_synced_at": None,
        "last_error": None,
    }


@pytest.mark.asyncio
async def test_upsert_integration_seals_api_key_at_rest(db_session: AsyncSession) -> None:
    user = await _create_user(db_session, "settings-api-key-encryption@example.com")
    service = SettingsService(db_session)

    result = await service.upsert_integration("openrouter", "sk-test-1234567890", user.id)

    assert result["provider"] == "openrouter"
    integration = await db_session.scalar(
        settings_service_module.select(UserIntegrationSecret).where(
            UserIntegrationSecret.user_id == user.id,
            UserIntegrationSecret.provider == "openrouter",
        )
    )
    assert integration is not None
    assert integration.secret_value is not None
    assert integration.secret_value != "sk-test-1234567890"
    assert unseal_secret(integration.secret_value) == "sk-test-1234567890"


@pytest.mark.asyncio
async def test_upsert_integration_rejects_blank_api_keys(db_session: AsyncSession) -> None:
    user = await _create_user(db_session, "settings-api-key-blank@example.com")
    service = SettingsService(db_session)

    with pytest.raises(ValidationError, match="cannot be blank"):
        await service.upsert_integration("openrouter", "   ", user.id)


@pytest.mark.asyncio
async def test_connect_google_integration_persists_oauth_metadata(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = await _create_user(db_session, "settings-google-connect@example.com")
    service = SettingsService(db_session)

    monkeypatch.setattr(
        settings_service_module,
        "decode_google_state",
        lambda token: GoogleOAuthState(
            user_id=str(user.id),
            return_to="/settings?tab=integrations",
        ),
    )

    async def _fake_exchange_google_code(code: str) -> dict[str, str]:
        assert code == "auth-code"
        return {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "scope": "scope:a scope:b",
        }

    async def _fake_get_profile(self, access_token: str) -> dict[str, str]:
        assert access_token == "access-token"
        return {"emailAddress": "owner@gmail.com"}

    monkeypatch.setattr(
        settings_service_module,
        "exchange_google_code",
        _fake_exchange_google_code,
    )
    monkeypatch.setattr(settings_service_module.GmailClient, "get_profile", _fake_get_profile)

    result = await service.connect_google_integration(code="auth-code", state_token="signed-state")

    assert result == {
        "provider": "google",
        "account_email": "owner@gmail.com",
        "return_to": "/settings?tab=integrations",
    }
    integration = await db_session.scalar(
        settings_service_module.select(UserIntegrationSecret).where(
            UserIntegrationSecret.user_id == user.id,
            UserIntegrationSecret.provider == "google",
        )
    )
    assert integration is not None
    assert integration.auth_type == "oauth"
    assert integration.secret_value is None
    assert integration.secret_json != {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
    }
    assert unseal_secret_mapping(integration.secret_json) == {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
    }
    assert integration.account_email == "owner@gmail.com"
    assert integration.scopes == ["scope:a", "scope:b"]
    assert integration.last_validated_at is not None
    assert integration.last_error is None


@pytest.mark.asyncio
async def test_sync_google_integration_returns_sync_counts(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = await _create_user(db_session, "settings-google-sync@example.com")
    integration = UserIntegrationSecret(
        user_id=user.id,
        provider="google",
        auth_type="oauth",
        secret_json={"access_token": "access-token", "refresh_token": "refresh-token"},
        account_email="owner@gmail.com",
    )
    db_session.add(integration)
    await db_session.commit()

    service = SettingsService(db_session)

    async def _fake_sync_gmail_for_user(
        db: AsyncSession,
        *,
        user_id,
        query: str,
        max_messages: int,
    ) -> GmailSyncResult:
        assert db is db_session
        assert user_id == user.id
        assert isinstance(query, str)
        assert max_messages > 0
        integration.last_synced_at = datetime.now(UTC)
        integration.last_validated_at = integration.last_synced_at
        integration.last_error = None
        await db.commit()
        return GmailSyncResult(
            messages_seen=4,
            messages_processed=3,
            messages_failed=0,
            duplicates_skipped=1,
            signals_detected=2,
            transitions_applied=1,
            last_synced_at=integration.last_synced_at,
        )

    monkeypatch.setattr(settings_service_module, "sync_gmail_for_user", _fake_sync_gmail_for_user)

    result = await service.sync_google_integration(user.id)

    assert result["provider"] == "google"
    assert result["messages_seen"] == 4
    assert result["messages_processed"] == 3
    assert result["messages_failed"] == 0
    assert result["duplicates_skipped"] == 1
    assert result["signals_detected"] == 2
    assert result["transitions_applied"] == 1
    assert result["last_synced_at"] is not None


@pytest.mark.asyncio
async def test_list_integrations_marks_google_reconnect_and_sync_error_states(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session, "settings-google-status@example.com")
    db_session.add_all(
        [
            UserIntegrationSecret(
                user_id=user.id,
                provider="google",
                auth_type="oauth",
                secret_json={"access_token": "access-only"},
                account_email="owner@gmail.com",
            ),
            UserIntegrationSecret(
                user_id=user.id,
                provider="openrouter",
                auth_type="api_key",
                secret_value="sk-test-1234567890",
                last_error="provider timeout",
            ),
        ]
    )
    await db_session.commit()

    service = SettingsService(db_session)
    integrations = await service.list_integrations(user.id)

    google = next(item for item in integrations if item["provider"] == "google")
    openrouter = next(item for item in integrations if item["provider"] == "openrouter")

    assert google["status"] == "needs_reconnect"
    assert google["connected"] is False
    assert google["account_email"] == "owner@gmail.com"
    assert openrouter["status"] == "connected"
    assert openrouter["masked_value"] == "sk-t...7890"


@pytest.mark.asyncio
async def test_list_integrations_marks_blank_api_key_rows_as_not_configured(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session, "settings-api-key-empty-row@example.com")
    db_session.add(
        UserIntegrationSecret(
            user_id=user.id,
            provider="openrouter",
            auth_type="api_key",
            secret_value="   ",
        )
    )
    await db_session.commit()

    service = SettingsService(db_session)
    integrations = await service.list_integrations(user.id)

    openrouter = next(item for item in integrations if item["provider"] == "openrouter")
    assert openrouter["status"] == "not_configured"
    assert openrouter["connected"] is False
    assert openrouter["masked_value"] is None


@pytest.mark.asyncio
async def test_sync_google_integration_persists_last_error_on_oauth_failure(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = await _create_user(db_session, "settings-google-sync-error@example.com")
    integration = UserIntegrationSecret(
        user_id=user.id,
        provider="google",
        auth_type="oauth",
        secret_json={"access_token": "access-token", "refresh_token": "refresh-token"},
        account_email="owner@gmail.com",
    )
    db_session.add(integration)
    await db_session.commit()

    async def _fake_sync_gmail_for_user(*args, **kwargs) -> GmailSyncResult:
        raise settings_service_module.GoogleOAuthError("expired credentials")

    monkeypatch.setattr(settings_service_module, "sync_gmail_for_user", _fake_sync_gmail_for_user)

    service = SettingsService(db_session)
    with pytest.raises(ValidationError, match="expired credentials"):
        await service.sync_google_integration(user.id)

    await db_session.refresh(integration)
    assert integration.last_error == "expired credentials"
