from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.email.gmail_sync import GmailSyncResult
from app.jobs.models import Job
from app.notifications.models import Notification
from app.settings import service as settings_service_module
from app.settings.models import UserIntegrationSecret


async def _register_and_login(client: AsyncClient) -> str:
    email = f"settings-api-{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "testpassword123"},
    )
    return response.cookies["jr_access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _not_configured_integration(provider: str, *, auth_type: str = "api_key") -> dict[str, object]:
    return {
        "provider": provider,
        "auth_type": auth_type,
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
async def test_settings_app_round_trip(client: AsyncClient) -> None:
    token = await _register_and_login(client)

    initial = await client.get("/api/v1/settings/app", headers=_auth(token))
    updated = await client.patch(
        "/api/v1/settings/app",
        headers=_auth(token),
        json={"theme": "light", "notifications_enabled": False, "auto_apply_enabled": True},
    )

    assert initial.status_code == 200
    assert initial.json() == {
        "theme": "dark",
        "notifications_enabled": True,
        "auto_apply_enabled": False,
    }
    assert updated.status_code == 200
    assert updated.json() == {
        "theme": "light",
        "notifications_enabled": False,
        "auto_apply_enabled": True,
    }


@pytest.mark.asyncio
async def test_saved_searches_crud(client: AsyncClient) -> None:
    token = await _register_and_login(client)

    created = await client.post(
        "/api/v1/settings/searches",
        headers=_auth(token),
        json={"name": "Remote Roles", "filters": {"remote": True}, "alert_enabled": True},
    )
    listed = await client.get("/api/v1/settings/searches", headers=_auth(token))
    deleted = await client.delete(
        f"/api/v1/settings/searches/{created.json()['id']}",
        headers=_auth(token),
    )
    after_delete = await client.get("/api/v1/settings/searches", headers=_auth(token))

    assert created.status_code == 201
    assert created.json()["last_checked_at"] is None
    assert created.json()["last_matched_at"] is None
    assert created.json()["last_match_count"] == 0
    assert created.json()["last_error"] is None
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert deleted.status_code == 204
    assert after_delete.json() == []


@pytest.mark.asyncio
async def test_saved_search_update(client: AsyncClient) -> None:
    token = await _register_and_login(client)

    created = await client.post(
        "/api/v1/settings/searches",
        headers=_auth(token),
        json={"name": "Remote Roles", "filters": {"remote": True}, "alert_enabled": False},
    )
    updated = await client.patch(
        f"/api/v1/settings/searches/{created.json()['id']}",
        headers=_auth(token),
        json={
            "name": "Remote ML Roles",
            "filters": {"remote": True, "keywords": ["ml", "python"]},
            "alert_enabled": True,
        },
    )

    assert updated.status_code == 200
    payload = updated.json()
    assert payload["name"] == "Remote ML Roles"
    assert payload["filters"] == {"remote": True, "keywords": ["ml", "python"]}
    assert payload["alert_enabled"] is True
    assert payload["last_checked_at"] is None
    assert payload["last_matched_at"] is None
    assert payload["last_match_count"] == 0
    assert payload["last_error"] is None


@pytest.mark.asyncio
async def test_saved_search_check_creates_notification_and_updates_metadata(
    client: AsyncClient,
    db_session,
) -> None:
    token = await _register_and_login(client)
    created = await client.post(
        "/api/v1/settings/searches",
        headers=_auth(token),
        json={"name": "Remote Roles", "filters": {"q": "Engineer"}, "alert_enabled": True},
    )

    from app.auth.models import User

    auth_user = await db_session.scalar(
        select(User).where(User.email.like("settings-api-%@test.com")).order_by(User.created_at.desc())
    )
    assert auth_user is not None
    user_id = auth_user.id

    db_session.add(
        Job(
            id=f"settings-check-{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            source="test",
            title="Backend Engineer",
            company_name="Acme",
            is_active=True,
            created_at=datetime.now(UTC) - timedelta(minutes=5),
        )
    )
    await db_session.commit()

    checked = await client.post(
        f"/api/v1/settings/searches/{created.json()['id']}/check",
        headers=_auth(token),
    )

    assert checked.status_code == 200
    payload = checked.json()
    assert payload["status"] == "matched"
    assert payload["new_matches"] == 1
    assert payload["notification_created"] is True
    assert payload["link"] == "/jobs?q=Engineer"
    assert payload["search"]["last_checked_at"] is not None
    assert payload["search"]["last_matched_at"] is not None
    assert payload["search"]["last_match_count"] == 1
    assert payload["search"]["last_error"] is None

    notification = await db_session.scalar(
        select(Notification).where(Notification.user_id == user_id)
    )
    assert notification is not None
    assert notification.notification_type == "saved_search_alert"


@pytest.mark.asyncio
async def test_integrations_round_trip_with_masked_reads(client: AsyncClient) -> None:
    token = await _register_and_login(client)

    initial = await client.get("/api/v1/settings/integrations", headers=_auth(token))
    upserted = await client.put(
        "/api/v1/settings/integrations/openrouter",
        headers=_auth(token),
        json={"api_key": "sk-test-1234567890"},
    )
    deleted = await client.delete(
        "/api/v1/settings/integrations/openrouter",
        headers=_auth(token),
    )
    after_delete = await client.get("/api/v1/settings/integrations", headers=_auth(token))

    assert initial.status_code == 200
    assert initial.json() == [
        _not_configured_integration("openrouter"),
        _not_configured_integration("serpapi"),
        _not_configured_integration("theirstack"),
        _not_configured_integration("apify"),
        _not_configured_integration("google", auth_type="oauth"),
    ]
    assert upserted.status_code == 200
    assert upserted.json()["provider"] == "openrouter"
    assert upserted.json()["auth_type"] == "api_key"
    assert upserted.json()["connected"] is True
    assert upserted.json()["status"] == "connected"
    assert upserted.json()["masked_value"] == "sk-t...7890"
    assert upserted.json()["account_email"] is None
    assert upserted.json()["scopes"] == []
    assert upserted.json()["updated_at"] is not None
    assert upserted.json()["last_validated_at"] is None
    assert upserted.json()["last_synced_at"] is None
    assert upserted.json()["last_error"] is None
    assert deleted.status_code == 204
    assert after_delete.status_code == 200
    assert after_delete.json()[0] == _not_configured_integration("openrouter")


@pytest.mark.asyncio
async def test_google_connect_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/settings/integrations/google/connect")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_google_callback_missing_params_redirects_with_error(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/settings/integrations/google/callback",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"].startswith("http://localhost:5173/")
    assert "integration_status=error" in response.headers["location"]
    assert "integration_provider=google" in response.headers["location"]
    assert "missing_oauth_callback_params" in response.headers["location"]


@pytest.mark.asyncio
async def test_google_callback_success_redirects_back_to_frontend(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_connect_google_integration(
        self,
        *,
        code: str,
        state_token: str,
    ) -> dict[str, str]:
        assert code == "auth-code"
        assert state_token == "signed-state"
        return {
            "provider": "google",
            "account_email": "owner@gmail.com",
            "return_to": "/settings?tab=integrations",
        }

    monkeypatch.setattr(
        settings_service_module.SettingsService,
        "connect_google_integration",
        _fake_connect_google_integration,
    )

    response = await client.get(
        "/api/v1/settings/integrations/google/callback?code=auth-code&state=signed-state",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"].startswith("http://localhost:5173/settings?tab=integrations")
    assert "integration_status=connected" in response.headers["location"]
    assert "integration_provider=google" in response.headers["location"]
    assert "owner%40gmail.com" in response.headers["location"]


@pytest.mark.asyncio
async def test_google_api_key_upsert_is_rejected(client: AsyncClient) -> None:
    token = await _register_and_login(client)

    response = await client.put(
        "/api/v1/settings/integrations/google",
        headers=_auth(token),
        json={"api_key": "not-supported"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Unsupported integration provider: google"}


@pytest.mark.asyncio
async def test_google_sync_returns_counts_for_connected_account(
    client: AsyncClient,
    db_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = await _register_and_login(client)

    from app.auth.models import User

    auth_user = await db_session.scalar(
        select(User).where(User.email.like("settings-api-%@test.com")).order_by(User.created_at.desc())
    )
    assert auth_user is not None
    db_session.add(
        UserIntegrationSecret(
            user_id=auth_user.id,
            provider="google",
            auth_type="oauth",
            secret_json={"access_token": "access-token", "refresh_token": "refresh-token"},
            account_email="owner@gmail.com",
        )
    )
    await db_session.commit()

    async def _fake_sync_gmail_for_user(
        db,
        *,
        user_id,
        query: str,
        max_messages: int,
    ) -> GmailSyncResult:
        integration = await db.scalar(
            select(UserIntegrationSecret).where(
                UserIntegrationSecret.user_id == user_id,
                UserIntegrationSecret.provider == "google",
            )
        )
        assert integration is not None
        integration.last_synced_at = datetime.now(UTC)
        integration.last_validated_at = integration.last_synced_at
        integration.last_error = None
        await db.commit()
        return GmailSyncResult(
            messages_seen=5,
            messages_processed=4,
            duplicates_skipped=1,
            signals_detected=2,
            transitions_applied=1,
            last_synced_at=integration.last_synced_at,
        )

    monkeypatch.setattr(settings_service_module, "sync_gmail_for_user", _fake_sync_gmail_for_user)

    response = await client.post(
        "/api/v1/settings/integrations/google/sync",
        headers=_auth(token),
    )

    assert response.status_code == 200
    assert response.json()["provider"] == "google"
    assert response.json()["messages_seen"] == 5
    assert response.json()["messages_processed"] == 4
    assert response.json()["duplicates_skipped"] == 1
    assert response.json()["signals_detected"] == 2
    assert response.json()["transitions_applied"] == 1
    assert response.json()["last_synced_at"] is not None
