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
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert deleted.status_code == 204
    assert after_delete.json() == []
