from __future__ import annotations

import uuid

from httpx import AsyncClient


async def register_and_login(
    client: AsyncClient,
    *,
    email: str | None = None,
    display_name: str | None = None,
) -> tuple[str, dict[str, str]]:
    email = email or f"edge-{uuid.uuid4().hex[:12]}@example.com"
    payload: dict[str, str] = {
        "email": email,
        "password": "securepassword123",
    }
    if display_name is not None:
        payload["display_name"] = display_name

    register_response = await client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 201

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "securepassword123"},
    )
    assert login_response.status_code == 200
    return email, login_response.json()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
