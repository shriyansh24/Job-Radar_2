from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


async def _register_and_login(client: AsyncClient) -> str:
    email = f"profile-api-{uuid.uuid4().hex[:8]}@test.com"
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


@pytest.mark.asyncio
async def test_profile_get_creates_default_profile(client: AsyncClient) -> None:
    token = await _register_and_login(client)

    response = await client.get("/api/v1/profile", headers=_auth(token))

    assert response.status_code == 200
    assert response.json()["theme"] == "dark"
    assert response.json()["search_queries"] == []


@pytest.mark.asyncio
async def test_profile_patch_updates_fields(client: AsyncClient) -> None:
    token = await _register_and_login(client)

    response = await client.patch(
        "/api/v1/profile",
        headers=_auth(token),
        json={
            "full_name": "Profile User",
            "location": "Austin, TX",
            "preferred_job_types": ["full-time"],
        },
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Profile User"
    assert response.json()["location"] == "Austin, TX"
    assert response.json()["preferred_job_types"] == ["full-time"]


@pytest.mark.asyncio
async def test_profile_generate_answers_returns_pending_payload(client: AsyncClient) -> None:
    token = await _register_and_login(client)

    response = await client.post("/api/v1/profile/generate-answers", headers=_auth(token))

    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert "current_answers" in response.json()
