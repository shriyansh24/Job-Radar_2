from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from tests.edge_cases._api_helpers import auth_headers, register_and_login


@pytest.mark.asyncio
async def test_unicode_display_name_roundtrip(client: AsyncClient) -> None:
    display_name = "Ren\u00e9e \U0001f680 \u6771\u4eac"
    _, tokens = await register_and_login(client, display_name=display_name)

    response = await client.get("/api/v1/auth/me", headers=auth_headers(tokens["access_token"]))

    assert response.status_code == 200
    assert response.json()["display_name"] == display_name


@pytest.mark.asyncio
async def test_duplicate_registration_returns_validation_error(client: AsyncClient) -> None:
    email = f"dupe-{uuid.uuid4().hex[:12]}@example.com"
    payload = {"email": email, "password": "securepassword123"}

    first = await client.post("/api/v1/auth/register", json=payload)
    second = await client.post("/api/v1/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 422
    assert second.json()["detail"] == "Email already registered"
