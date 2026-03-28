from __future__ import annotations

from unittest.mock import Mock

import pytest
from httpx import AsyncClient

import app.auth.service as auth_service
import app.shared.middleware as shared_middleware
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
async def test_register_logging_and_request_log_include_user_context(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    auth_logger = Mock()
    request_logger = Mock()
    monkeypatch.setattr(auth_service, "logger", auth_logger)
    monkeypatch.setattr(shared_middleware, "logger", request_logger)

    registered = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "logging-register@example.com",
            "password": "securepassword123",
            "display_name": "Register Logger",
        },
    )

    logged_in = await client.post(
        "/api/v1/auth/login",
        json={"email": "logging-register@example.com", "password": "securepassword123"},
    )
    me = await client.get("/api/v1/auth/me")

    assert registered.status_code == 201
    assert logged_in.status_code == 200
    assert me.status_code == 200

    info_events = {call.args[0]: call.kwargs for call in auth_logger.info.call_args_list}
    assert "auth_register_succeeded" in info_events
    assert info_events["auth_register_succeeded"]["auth_source"] == "registration"
    _assert_no_sensitive_fields(info_events["auth_register_succeeded"])

    request_events = [
        call.kwargs
        for call in request_logger.info.call_args_list
        if call.args[0] == "request_completed"
    ]
    me_event = next(event for event in request_events if event["path"] == "/api/v1/auth/me")
    assert me_event["auth_user_id"] == me.json()["id"]
    assert me_event["route_name"] == "me"
    assert me_event["route_path"] == "/api/v1/auth/me"


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
    assert data == {"authenticated": True, "token_type": "bearer"}
    assert "access_token" not in data
    assert "refresh_token" not in data
    assert data["token_type"] == "bearer"
    assert "jr_access_token" in resp.cookies
    assert "jr_refresh_token" in resp.cookies


def _assert_no_sensitive_fields(fields: dict[str, object]) -> None:
    forbidden_keys = {
        "password",
        "email",
        "access_token",
        "refresh_token",
        "csrf_token",
    }
    assert forbidden_keys.isdisjoint(fields.keys())


def _access_cookie(client: AsyncClient) -> str:
    token = client.cookies.get("jr_access_token")
    assert token
    return token


def _refresh_cookie(client: AsyncClient) -> str:
    token = client.cookies.get("jr_refresh_token")
    assert token
    return token


def _csrf_headers(client: AsyncClient) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("jr_csrf_token", "")}


@pytest.mark.asyncio
async def test_login_logging_omits_sensitive_fields(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    logger = Mock()
    monkeypatch.setattr(auth_service, "logger", logger)

    await client.post(
        "/api/v1/auth/register",
        json={"email": "logging-login@example.com", "password": "securepassword123"},
    )

    success = await client.post(
        "/api/v1/auth/login",
        json={"email": "logging-login@example.com", "password": "securepassword123"},
    )
    failed = await client.post(
        "/api/v1/auth/login",
        json={"email": "logging-login@example.com", "password": "wrongpassword"},
        headers=_csrf_headers(client),
    )

    assert success.status_code == 200
    assert failed.status_code == 401

    info_events = {call.args[0]: call.kwargs for call in logger.info.call_args_list}
    warning_events = {call.args[0]: call.kwargs for call in logger.warning.call_args_list}

    assert "auth_login_succeeded" in info_events
    assert info_events["auth_login_succeeded"]["auth_source"] == "password"
    _assert_no_sensitive_fields(info_events["auth_login_succeeded"])

    assert "auth_login_failed" in warning_events
    assert warning_events["auth_login_failed"]["reason"] == "invalid_credentials"
    _assert_no_sensitive_fields(warning_events["auth_login_failed"])


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
    token = login_resp.cookies["jr_access_token"]
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
    refresh_token = login_resp.cookies["jr_refresh_token"]
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
        headers=_csrf_headers(client),
    )
    assert resp.status_code == 200
    assert resp.json() == {"authenticated": True, "token_type": "bearer"}
    assert "access_token" not in resp.json()
    assert "refresh_token" not in resp.json()


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
    assert resp.status_code == 403
    resp = await client.post("/api/v1/auth/refresh", headers=_csrf_headers(client))
    assert resp.status_code == 200
    assert resp.json() == {"authenticated": True, "token_type": "bearer"}
    assert "access_token" not in resp.json()
    assert "refresh_token" not in resp.json()


@pytest.mark.asyncio
async def test_refresh_logging_omits_sensitive_fields(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    logger = Mock()
    monkeypatch.setattr(auth_service, "logger", logger)

    await client.post(
        "/api/v1/auth/register",
        json={"email": "logging-refresh@example.com", "password": "securepassword123"},
    )
    await client.post(
        "/api/v1/auth/login",
        json={"email": "logging-refresh@example.com", "password": "securepassword123"},
    )

    accepted = await client.post(
        "/api/v1/auth/refresh",
        headers=_csrf_headers(client),
    )
    rejected = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": _access_cookie(client)},
        headers=_csrf_headers(client),
    )

    assert accepted.status_code == 200
    assert rejected.status_code == 401

    info_events = {call.args[0]: call.kwargs for call in logger.info.call_args_list}
    warning_events = {call.args[0]: call.kwargs for call in logger.warning.call_args_list}

    assert "auth_refresh_succeeded" in info_events
    assert info_events["auth_refresh_succeeded"]["auth_source"] == "cookie"
    _assert_no_sensitive_fields(info_events["auth_refresh_succeeded"])

    assert "auth_refresh_failed" in warning_events
    assert warning_events["auth_refresh_failed"]["auth_source"] == "body"
    assert warning_events["auth_refresh_failed"]["reason"] == "invalid_token_type"
    _assert_no_sensitive_fields(warning_events["auth_refresh_failed"])


@pytest.mark.asyncio
async def test_refresh_missing_token_logs_normalized_reason(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    logger = Mock()
    monkeypatch.setattr(auth_service, "logger", logger)

    response = await client.post(
        "/api/v1/auth/refresh",
        headers={"X-CSRF-Token": "placeholder"},
    )

    assert response.status_code == 401

    warning_events = {call.args[0]: call.kwargs for call in logger.warning.call_args_list}
    assert warning_events["auth_refresh_failed"]["auth_source"] == "cookie"
    assert warning_events["auth_refresh_failed"]["reason"] == "refresh_token_required"
    _assert_no_sensitive_fields(warning_events["auth_refresh_failed"])


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
    token = login_resp.cookies["jr_access_token"]

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
async def test_logout_and_account_deletion_logging_omit_sensitive_fields(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    logger = Mock()
    monkeypatch.setattr(auth_service, "logger", logger)

    await client.post(
        "/api/v1/auth/register",
        json={"email": "logging-logout@example.com", "password": "securepassword123"},
    )
    logout_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "logging-logout@example.com", "password": "securepassword123"},
    )
    logout_resp = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {logout_login.cookies['jr_access_token']}"},
    )

    await client.post(
        "/api/v1/auth/register",
        json={"email": "logging-delete@example.com", "password": "securepassword123"},
    )
    delete_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "logging-delete@example.com", "password": "securepassword123"},
    )
    delete_resp = await client.delete(
        "/api/v1/auth/account",
        headers={"Authorization": f"Bearer {delete_login.cookies['jr_access_token']}"},
    )

    assert logout_resp.status_code == 200
    assert delete_resp.status_code == 204

    info_calls = logger.info.call_args_list
    event_names = [call.args[0] for call in info_calls]
    assert "auth_logout_succeeded" in event_names
    assert "auth_account_deleted" in event_names
    assert event_names.count("auth_session_cleared") == 2

    for call in info_calls:
        _assert_no_sensitive_fields(call.kwargs)


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
    old_token = login_resp.cookies["jr_access_token"]

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
        headers=_csrf_headers(client),
    )
    login_with_new_password = await client.post(
        "/api/v1/auth/login",
        json={"email": "change-password@example.com", "password": "newsecurepassword456"},
        headers=_csrf_headers(client),
    )

    assert changed.status_code == 200
    assert changed.json() == {"authenticated": True, "token_type": "bearer"}
    assert "access_token" not in changed.json()
    assert "refresh_token" not in changed.json()
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
    token = login_resp.cookies["jr_access_token"]

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
    token = login_resp.cookies["jr_access_token"]

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
