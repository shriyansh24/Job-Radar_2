from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.shared.middleware import api_rate_limiter


async def _register_user(
    client: AsyncClient,
    *,
    email: str | None = None,
    password: str = "securepassword123",
    display_name: str | None = None,
) -> str:
    email = email or f"security-{uuid.uuid4().hex[:12]}@example.com"
    payload: dict[str, str] = {
        "email": email,
        "password": password,
    }
    if display_name is not None:
        payload["display_name"] = display_name
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    return email


async def _login(
    client: AsyncClient,
    *,
    email: str,
    password: str = "securepassword123",
) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture(autouse=True)
async def clear_rate_limiter() -> None:
    await api_rate_limiter.clear()
    yield
    await api_rate_limiter.clear()


@pytest.mark.asyncio
async def test_public_and_private_admin_boundaries(client: AsyncClient) -> None:
    health = await client.get("/api/v1/admin/health")
    diagnostics = await client.get("/api/v1/admin/diagnostics")

    assert health.status_code == 200
    assert diagnostics.status_code == 401
    assert diagnostics.headers["X-Frame-Options"] == "DENY"
    assert diagnostics.headers["X-Content-Type-Options"] == "nosniff"
    assert diagnostics.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in diagnostics.headers


@pytest.mark.asyncio
async def test_auth_tokens_enforce_expected_type(client: AsyncClient) -> None:
    email = await _register_user(client)
    tokens = await _login(client, email=email)

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["access_token"]},
        headers={"X-CSRF-Token": client.cookies.get("jr_csrf_token", "")},
    )

    assert me_response.status_code == 401
    assert me_response.json()["detail"] == "Invalid token type"
    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"] == "Invalid token type"


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client: AsyncClient) -> None:
    email = await _register_user(client)
    tokens = await _login(client, email=email)

    logout_response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    assert logout_response.status_code == 200
    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"] == "Token revoked"


@pytest.mark.asyncio
async def test_login_sets_http_only_auth_cookies(client: AsyncClient) -> None:
    email = await _register_user(client)
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "securepassword123"},
    )

    assert response.status_code == 200
    set_cookie_headers = response.headers.get_list("set-cookie")
    assert len(set_cookie_headers) == 3
    assert any("jr_access_token=" in header for header in set_cookie_headers)
    assert any("jr_refresh_token=" in header for header in set_cookie_headers)
    assert any("jr_csrf_token=" in header for header in set_cookie_headers)
    for header in set_cookie_headers:
        header_lower = header.lower()
        if "jr_csrf_token=" in header:
            assert "httponly" not in header_lower
        else:
            assert "httponly" in header_lower
        assert "samesite=lax" in header_lower
        assert "path=/" in header_lower


@pytest.mark.asyncio
async def test_cookie_authenticated_logout_requires_csrf_header(client: AsyncClient) -> None:
    email = await _register_user(client)
    await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "securepassword123"},
    )

    rejected = await client.post("/api/v1/auth/logout")
    accepted = await client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": client.cookies.get("jr_csrf_token", "")},
    )

    assert rejected.status_code == 403
    assert rejected.json()["detail"] == "CSRF token missing or invalid"
    assert accepted.status_code == 200


@pytest.mark.asyncio
async def test_cookie_authenticated_refresh_requires_csrf_header(client: AsyncClient) -> None:
    email = await _register_user(client)
    await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "securepassword123"},
    )

    rejected = await client.post("/api/v1/auth/refresh")
    accepted = await client.post(
        "/api/v1/auth/refresh",
        headers={"X-CSRF-Token": client.cookies.get("jr_csrf_token", "")},
    )

    assert rejected.status_code == 403
    assert rejected.json()["detail"] == "CSRF token missing or invalid"
    assert accepted.status_code == 200


@pytest.mark.asyncio
async def test_cors_preflight_allows_configured_origin(client: AsyncClient) -> None:
    response = await client.options(
        "/api/v1/admin/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": (
                "Authorization,Content-Type,X-CSRF-Token,X-Request-ID"
            ),
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"
    allow_headers = response.headers["access-control-allow-headers"].lower()
    assert "authorization" in allow_headers
    assert "content-type" in allow_headers
    assert "x-csrf-token" in allow_headers
    assert "x-request-id" in allow_headers


@pytest.mark.asyncio
async def test_cors_preflight_rejects_disallowed_origin(client: AsyncClient) -> None:
    response = await client.options(
        "/api/v1/admin/health",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.asyncio
async def test_request_id_echoes_client_header(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/admin/health",
        headers={"X-Request-ID": "req-auth-123"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-auth-123"


@pytest.mark.asyncio
async def test_request_id_is_generated_when_missing(client: AsyncClient) -> None:
    response = await client.get("/api/v1/admin/health")

    assert response.status_code == 200
    assert uuid.UUID(response.headers["X-Request-ID"])


@pytest.mark.asyncio
async def test_trusted_host_rejects_disallowed_host_header(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/admin/health",
        headers={"Host": "evil.example"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_rate_limit_isolated_per_email(client: AsyncClient) -> None:
    blocked_email = await _register_user(client, email="blocked@example.com")
    other_email = await _register_user(client, email="other@example.com")

    last_response = None
    for _ in range(11):
        last_response = await client.post(
            "/api/v1/auth/login",
            json={"email": blocked_email, "password": "wrongpassword"},
        )

    other_response = await client.post(
        "/api/v1/auth/login",
        json={"email": other_email, "password": "wrongpassword"},
    )

    assert last_response is not None
    assert last_response.status_code == 429
    assert other_response.status_code == 401
    assert other_response.json()["detail"] == "Invalid email or password"
