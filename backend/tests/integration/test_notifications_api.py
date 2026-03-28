from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.service import NotificationService


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    email = f"notifications-api-{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "testpassword123"},
    )
    token = login.cookies["jr_access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return token, me.json()["id"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_notifications_list_and_unread_count(client: AsyncClient) -> None:
    token, _ = await _register_and_login(client)

    listed = await client.get("/api/v1/notifications", headers=_auth(token))
    unread = await client.get("/api/v1/notifications/unread-count", headers=_auth(token))

    assert listed.status_code == 200
    assert listed.json() == {"items": [], "unread_count": 0, "total": 0}
    assert unread.status_code == 200
    assert unread.json() == {"unread_count": 0}


@pytest.mark.asyncio
async def test_notifications_mark_read_delete_and_read_all(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    token, user_id = await _register_and_login(client)
    service = NotificationService(db_session)
    first = await service.create(uuid.UUID(user_id), "First")
    second = await service.create(uuid.UUID(user_id), "Second")

    mark_one = await client.patch(
        f"/api/v1/notifications/{first.id}/read",
        headers=_auth(token),
    )
    unread_after_one = await client.get("/api/v1/notifications/unread-count", headers=_auth(token))
    mark_all = await client.patch("/api/v1/notifications/read-all", headers=_auth(token))
    delete = await client.delete(f"/api/v1/notifications/{second.id}", headers=_auth(token))
    listed = await client.get("/api/v1/notifications", headers=_auth(token))

    assert mark_one.status_code == 204
    assert unread_after_one.json() == {"unread_count": 1}
    assert mark_all.status_code == 204
    assert delete.status_code == 204
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == str(first.id)
    assert listed.json()["unread_count"] == 0
