from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import Response

import app.auth.service as auth_service
from app.auth.service import (
    change_password,
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    decode_token_payload,
    hash_password,
    normalize_auth_reason,
    verify_password,
)
from app.shared.errors import AuthError


def test_hash_and_verify_password():
    password = "securepassword123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)


def test_create_access_token():
    token = create_access_token("test-user-id", token_version=3)
    assert isinstance(token, str)
    assert len(token) > 0
    payload = decode_token_payload(token, expected_type="access")
    assert payload["sub"] == "test-user-id"
    assert payload["ver"] == 3
    assert payload["jti"]


def test_create_and_decode_refresh_token():
    user_id = "test-user-id"
    token = create_refresh_token(user_id, token_version=1)
    decoded_id = decode_refresh_token(token)
    assert decoded_id == user_id
    payload = decode_token_payload(token, expected_type="refresh")
    assert payload["ver"] == 1


def test_normalize_auth_reason_prefers_known_aliases() -> None:
    assert normalize_auth_reason("Invalid token type") == "invalid_token_type"
    assert normalize_auth_reason("Refresh token required") == "refresh_token_required"


def test_normalize_auth_reason_falls_back_to_slugified_code() -> None:
    assert normalize_auth_reason("Token issuer drift detected") == "token_issuer_drift_detected"


def test_decode_invalid_refresh_token():
    with pytest.raises(AuthError):
        decode_refresh_token("invalid-token")


@pytest.mark.asyncio
async def test_change_password_logs_success_without_sensitive_fields(
    monkeypatch: pytest.MonkeyPatch,
):
    logger = Mock()
    monkeypatch.setattr(auth_service, "logger", logger)
    db = SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    user = SimpleNamespace(
        id=uuid4(),
        password_hash=hash_password("securepassword123"),
        token_version=0,
    )

    updated_user = await change_password(db, user, "securepassword123", "newsecurepassword456")

    assert updated_user is user
    logger.info.assert_called_once()
    event_name = logger.info.call_args.args[0]
    fields = logger.info.call_args.kwargs
    assert event_name == "auth_password_changed"
    assert fields["user_id"] == str(user.id)
    assert fields["token_version"] == 1
    assert "password" not in fields
    assert "email" not in fields


@pytest.mark.asyncio
async def test_change_password_logs_failure_without_sensitive_fields(
    monkeypatch: pytest.MonkeyPatch,
):
    logger = Mock()
    monkeypatch.setattr(auth_service, "logger", logger)
    db = SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    user = SimpleNamespace(
        id=uuid4(),
        password_hash=hash_password("securepassword123"),
        token_version=0,
    )

    with pytest.raises(AuthError):
        await change_password(db, user, "wrongpassword", "newsecurepassword456")

    logger.warning.assert_called_once()
    event_name = logger.warning.call_args.args[0]
    fields = logger.warning.call_args.kwargs
    assert event_name == "auth_password_change_failed"
    assert fields["user_id"] == str(user.id)
    assert fields["reason"] == "invalid_current_password"
    assert "password" not in fields
    assert "email" not in fields


def test_clear_auth_cookies_logs_session_clear_without_sensitive_fields(
    monkeypatch: pytest.MonkeyPatch,
):
    logger = Mock()
    monkeypatch.setattr(auth_service, "logger", logger)
    response = Response()
    user_id = str(uuid4())

    clear_auth_cookies(response, reason="logout", user_id=user_id)

    logger.info.assert_called_once()
    event_name = logger.info.call_args.args[0]
    fields = logger.info.call_args.kwargs
    assert event_name == "auth_session_cleared"
    assert fields["user_id"] == user_id
    assert fields["reason"] == "logout"
    assert fields["cleared_cookie_names"] == [
        "jr_access_token",
        "jr_refresh_token",
        "jr_csrf_token",
    ]
    assert "refresh_token" not in fields
    assert "access_token" not in fields
    assert "email" not in fields
