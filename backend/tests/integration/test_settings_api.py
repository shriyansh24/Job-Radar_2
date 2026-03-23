from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


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
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


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
    assert payload["last_checked_at"] is not None


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
        {
            "provider": "openrouter",
            "connected": False,
            "status": "not_configured",
            "masked_value": None,
            "updated_at": None,
        },
        {
            "provider": "serpapi",
            "connected": False,
            "status": "not_configured",
            "masked_value": None,
            "updated_at": None,
        },
        {
            "provider": "theirstack",
            "connected": False,
            "status": "not_configured",
            "masked_value": None,
            "updated_at": None,
        },
        {
            "provider": "apify",
            "connected": False,
            "status": "not_configured",
            "masked_value": None,
            "updated_at": None,
        },
    ]
    assert upserted.status_code == 200
    assert upserted.json()["provider"] == "openrouter"
    assert upserted.json()["connected"] is True
    assert upserted.json()["status"] == "connected"
    assert upserted.json()["masked_value"] == "sk-t...7890"
    assert upserted.json()["updated_at"] is not None
    assert deleted.status_code == 204
    assert after_delete.status_code == 200
    assert after_delete.json()[0] == {
        "provider": "openrouter",
        "connected": False,
        "status": "not_configured",
        "masked_value": None,
        "updated_at": None,
    }
