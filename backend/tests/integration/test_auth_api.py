from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.shared.middleware import api_rate_limiter


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/api/v1/admin/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
            "display_name": "Test User",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["display_name"] == "Test User"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "dupe@example.com", "password": "securepassword123"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "securepassword123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "securepassword123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "jr_access_token" in resp.cookies
    assert "jr_refresh_token" in resp.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wrong@example.com", "password": "securepassword123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "me@example.com", "password": "securepassword123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "me@example.com", "password": "securepassword123"},
    )
    token = login_resp.json()["access_token"]
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_me_uses_auth_cookie(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "cookie@example.com", "password": "securepassword123"},
    )
    await client.post(
        "/api/v1/auth/login",
        json={"email": "cookie@example.com", "password": "securepassword123"},
    )
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == "cookie@example.com"


@pytest.mark.asyncio
async def test_me_no_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh@example.com", "password": "securepassword123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "securepassword123"},
    )
    refresh_token = login_resp.json()["refresh_token"]
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_refresh_uses_cookie_when_body_missing(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "cookie-refresh@example.com", "password": "securepassword123"},
    )
    await client.post(
        "/api/v1/auth/login",
        json={"email": "cookie-refresh@example.com", "password": "securepassword123"},
    )
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_logout_revokes_existing_bearer_token(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "logout@example.com", "password": "securepassword123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "logout@example.com", "password": "securepassword123"},
    )
    token = login_resp.json()["access_token"]

    logout_resp = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_resp.status_code == 200

    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 401


@pytest.mark.asyncio
async def test_change_password_rotates_credentials(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "change-password@example.com", "password": "securepassword123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "change-password@example.com", "password": "securepassword123"},
    )
    old_token = login_resp.json()["access_token"]

    changed = await client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {old_token}"},
        json={
            "current_password": "securepassword123",
            "new_password": "newsecurepassword456",
        },
    )
    me_with_old_token = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {old_token}"},
    )
    login_with_old_password = await client.post(
        "/api/v1/auth/login",
        json={"email": "change-password@example.com", "password": "securepassword123"},
    )
    login_with_new_password = await client.post(
        "/api/v1/auth/login",
        json={"email": "change-password@example.com", "password": "newsecurepassword456"},
    )

    assert changed.status_code == 200
    assert "access_token" in changed.json()
    assert "refresh_token" in changed.json()
    assert me_with_old_token.status_code == 401
    assert login_with_old_password.status_code == 401
    assert login_with_new_password.status_code == 200


@pytest.mark.asyncio
async def test_change_password_rejects_wrong_current_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wrong-current@example.com", "password": "securepassword123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrong-current@example.com", "password": "securepassword123"},
    )
    token = login_resp.json()["access_token"]

    changed = await client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "badpassword",
            "new_password": "newsecurepassword456",
        },
    )

    assert changed.status_code == 401


@pytest.mark.asyncio
async def test_delete_account_removes_user_and_revokes_token(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "delete-account@example.com", "password": "securepassword123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "delete-account@example.com", "password": "securepassword123"},
    )
    token = login_resp.json()["access_token"]

    deleted = await client.delete(
        "/api/v1/auth/account",
        headers={"Authorization": f"Bearer {token}"},
    )
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    login_resp_after_delete = await client.post(
        "/api/v1/auth/login",
        json={"email": "delete-account@example.com", "password": "securepassword123"},
    )

    assert deleted.status_code == 204
    assert me_resp.status_code == 401
    assert login_resp_after_delete.status_code == 401


@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient):
    resp = await client.get("/api/v1/admin/health")
    assert resp.status_code == 200
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert "Content-Security-Policy" in resp.headers


@pytest.mark.asyncio
async def test_login_rate_limited(client: AsyncClient):
    await api_rate_limiter.clear()
    await client.post(
        "/api/v1/auth/register",
        json={"email": "ratelimit@example.com", "password": "securepassword123"},
    )

    last_response = None
    for _ in range(11):
        last_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "ratelimit@example.com", "password": "wrongpassword"},
        )

    assert last_response is not None
    assert last_response.status_code == 429
    await api_rate_limiter.clear()
