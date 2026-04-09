from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import Response

import app.auth.service as auth_service
from app.shared.errors import AuthError


def test_hash_and_verify_password():
    password = "securepassword123"
    hashed = auth_service.hash_password(password)
    assert hashed != password
    assert auth_service.verify_password(password, hashed)
    assert not auth_service.verify_password("wrongpassword", hashed)


def test_create_access_token():
    token = auth_service.create_access_token("test-user-id", token_version=3)
    assert isinstance(token, str)
    assert len(token) > 0
    payload = auth_service.decode_token_payload(token, expected_type="access")
    assert payload["sub"] == "test-user-id"
    assert payload["ver"] == 3
    assert payload["jti"]


def test_create_and_decode_refresh_token():
    user_id = "test-user-id"
    token = auth_service.create_refresh_token(user_id, token_version=1)
    decoded_id = auth_service.decode_refresh_token(token)
    assert decoded_id == user_id
    payload = auth_service.decode_token_payload(token, expected_type="refresh")
    assert payload["ver"] == 1


def test_normalize_auth_reason_prefers_known_aliases() -> None:
    assert auth_service.normalize_auth_reason("Invalid token type") == "invalid_token_type"
    assert auth_service.normalize_auth_reason("Refresh token required") == "refresh_token_required"


def test_normalize_auth_reason_falls_back_to_slugified_code() -> None:
    assert (
        auth_service.normalize_auth_reason("Token issuer drift detected")
        == "token_issuer_drift_detected"
    )


def test_decode_invalid_refresh_token():
    with pytest.raises(AuthError):
        auth_service.decode_refresh_token("invalid-token")


@pytest.mark.asyncio
async def test_change_password_logs_success_without_sensitive_fields(
    monkeypatch: pytest.MonkeyPatch,
):
    logger = Mock()
    monkeypatch.setattr(auth_service, "logger", logger)
    audit_sink = Mock()
    monkeypatch.setattr(auth_service, "emit_auth_audit_event", audit_sink)
    db = SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    user = SimpleNamespace(
        id=uuid4(),
        password_hash=auth_service.hash_password("securepassword123"),
        token_version=0,
    )

    updated_user = await auth_service.change_password(
        db,
        user,
        "securepassword123",
        "newsecurepassword456",
    )

    assert updated_user is user
    logger.info.assert_called_once()
    event_name = logger.info.call_args.args[0]
    fields = logger.info.call_args.kwargs
    assert event_name == "auth_password_changed"
    assert fields["user_id"] == str(user.id)
    assert fields["token_version"] == 1
    assert "password" not in fields
    assert "email" not in fields
    audit_sink.assert_called_once_with(
        "auth_password_changed",
        user_id=str(user.id),
        token_version=1,
    )


@pytest.mark.asyncio
async def test_change_password_logs_failure_without_sensitive_fields(
    monkeypatch: pytest.MonkeyPatch,
):
    logger = Mock()
    monkeypatch.setattr(auth_service, "logger", logger)
    audit_sink = Mock()
    monkeypatch.setattr(auth_service, "emit_auth_audit_event", audit_sink)
    db = SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    user = SimpleNamespace(
        id=uuid4(),
        password_hash=auth_service.hash_password("securepassword123"),
        token_version=0,
    )

    with pytest.raises(AuthError):
        await auth_service.change_password(
            db,
            user,
            "wrongpassword",
            "newsecurepassword456",
        )

    logger.warning.assert_called_once()
    event_name = logger.warning.call_args.args[0]
    fields = logger.warning.call_args.kwargs
    assert event_name == "auth_password_change_failed"
    assert fields["user_id"] == str(user.id)
    assert fields["reason"] == "invalid_current_password"
    assert "password" not in fields
    assert "email" not in fields
    audit_sink.assert_called_once_with(
        "auth_password_change_failed",
        user_id=str(user.id),
        token_version=0,
        reason="invalid_current_password",
    )


@pytest.mark.asyncio
async def test_register_user_emits_auth_audit_event(
    monkeypatch: pytest.MonkeyPatch,
):
    logger = Mock()
    audit_sink = Mock()
    monkeypatch.setattr(auth_service, "logger", logger)
    monkeypatch.setattr(auth_service, "emit_auth_audit_event", audit_sink)
    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: None)),
        add=Mock(),
        commit=AsyncMock(),
        refresh=AsyncMock(),
    )
    data = SimpleNamespace(
        email="register-audit@example.com",
        password="securepassword123",
        display_name="Register Audit",
    )

    user = await auth_service.register_user(db, data)

    assert user.email == "register-audit@example.com"
    audit_sink.assert_called_once()
    assert audit_sink.call_args.args[0] == "auth_register_succeeded"


@pytest.mark.asyncio
async def test_authenticate_user_emits_failure_audit_event(
    monkeypatch: pytest.MonkeyPatch,
):
    logger = Mock()
    audit_sink = Mock()
    monkeypatch.setattr(auth_service, "logger", logger)
    monkeypatch.setattr(auth_service, "emit_auth_audit_event", audit_sink)
    user = SimpleNamespace(
        id=uuid4(),
        email="auth-failure@example.com",
        password_hash="hash",
        is_active=True,
    )
    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: user))
    )
    monkeypatch.setattr(auth_service, "verify_password", lambda _plain, _hashed: False)

    with pytest.raises(AuthError):
        await auth_service.authenticate_user(db, "auth-failure@example.com", "wrong")

    audit_sink.assert_called_once_with("auth_login_failed", reason="invalid_credentials")


def test_clear_auth_cookies_logs_session_clear_without_sensitive_fields(
    monkeypatch: pytest.MonkeyPatch,
):
    logger = Mock()
    monkeypatch.setattr(auth_service, "logger", logger)
    audit_sink = Mock()
    monkeypatch.setattr(auth_service, "emit_auth_audit_event", audit_sink)
    response = Response()
    user_id = str(uuid4())

    auth_service.clear_auth_cookies(response, reason="logout", user_id=user_id)

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
    audit_sink.assert_called_once_with(
        "auth_session_cleared",
        user_id=user_id,
        reason="logout",
        cleared_cookie_names=[
            "jr_access_token",
            "jr_refresh_token",
            "jr_csrf_token",
        ],
    )



def test_decode_token_payload_invalid_type():
    user_id = "test-user"
    token = auth_service.create_access_token(user_id)
    with pytest.raises(AuthError, match="Invalid token type"):
        auth_service.decode_token_payload(token, expected_type="refresh")



def test_decode_token_payload_invalid_sub(monkeypatch):
    monkeypatch.setattr(
        auth_service.jwt,
        "decode",
        lambda *args, **kwargs: {"type": "access", "sub": 123},
    )
    with pytest.raises(AuthError, match="Invalid token"):
        auth_service.decode_token_payload("dummy-token", expected_type="access")



def test_decode_token_payload_expired(monkeypatch):
    from jwt import ExpiredSignatureError

    def mock_decode(*args, **kwargs):
        raise ExpiredSignatureError("Token expired")

    monkeypatch.setattr(auth_service.jwt, "decode", mock_decode)

    with pytest.raises(AuthError, match="Invalid token"):
        auth_service.decode_token_payload("expired-token")



def test_normalize_auth_reason_edge_cases() -> None:
    assert auth_service.normalize_auth_reason(None) == "auth_error"
    assert auth_service.normalize_auth_reason(None, fallback="custom_fallback") == "custom_fallback"
    assert auth_service.normalize_auth_reason("") == "auth_error"
    assert auth_service.normalize_auth_reason("   ") == "auth_error"

    class ExceptionWithDetail:
        detail = "Some error detail"

    assert auth_service.normalize_auth_reason(ExceptionWithDetail()) == "some_error_detail"
    assert auth_service.normalize_auth_reason("!!!***@@@") == "auth_error"
    assert auth_service.normalize_auth_reason("---", fallback="custom") == "custom"



def test_create_csrf_token():
    token = auth_service.create_csrf_token()
    assert isinstance(token, str)
    assert len(token) == 32
    token2 = auth_service.create_csrf_token()
    assert token != token2



def test_decode_token_payload_missing_sub(monkeypatch: pytest.MonkeyPatch):
    import jwt as pyjwt
    from app.config import settings

    payload = {
        "exp": auth_service.datetime.now(auth_service.timezone.utc)
        + auth_service.timedelta(minutes=15),
        "type": "access",
        "jti": "fake-jti",
        "ver": 0,
    }
    token = pyjwt.encode(
        payload,
        settings.effective_jwt_signing_key,
        algorithm=settings.algorithm,
    )
    with pytest.raises(AuthError, match="Invalid token"):
        auth_service.decode_token_payload(token, expected_type="access")



def test_create_refresh_token():
    token = auth_service.create_refresh_token("test-user-id", token_version=2)
    assert isinstance(token, str)
    assert len(token) > 0
    payload = auth_service.decode_token_payload(token, expected_type="refresh")
    assert payload["sub"] == "test-user-id"
    assert payload["ver"] == 2
    assert payload["jti"]



def test_verify_password_with_known_hash():
    known_hash = "$2b$12$3zl1BmX2bM4rIlbhWMOaKOdpWw2jOWbIIqTZwJ/vbqtqgqoC9QF9."
    assert auth_service.verify_password("mysecretpassword", known_hash)
    assert not auth_service.verify_password("wrongpassword", known_hash)



def test_get_token_version():
    assert auth_service.get_token_version(SimpleNamespace()) == 0
    assert auth_service.get_token_version(SimpleNamespace(token_version=None)) == 0
    assert auth_service.get_token_version(SimpleNamespace(token_version=0)) == 0
    assert auth_service.get_token_version(SimpleNamespace(token_version=5)) == 5
    assert auth_service.get_token_version(SimpleNamespace(token_version="3")) == 3



def test_create_tokens(monkeypatch: pytest.MonkeyPatch):
    user_id = "test-user-id"
    token_version = 2
    mock_access_token = "mock.access.token"
    mock_refresh_token = "mock.refresh.token"

    mock_create_access_token = Mock(return_value=mock_access_token)
    mock_create_refresh_token = Mock(return_value=mock_refresh_token)

    monkeypatch.setattr(auth_service, "create_access_token", mock_create_access_token)
    monkeypatch.setattr(auth_service, "create_refresh_token", mock_create_refresh_token)

    tokens = auth_service.create_tokens(user_id, token_version=token_version)

    mock_create_access_token.assert_called_once_with(user_id, token_version=token_version)
    mock_create_refresh_token.assert_called_once_with(user_id, token_version=token_version)

    assert isinstance(tokens, auth_service.AuthTokens)
    assert tokens.access_token == mock_access_token
    assert tokens.refresh_token == mock_refresh_token



def test_create_access_token_default_version():
    token = auth_service.create_access_token("test-user-id")
    assert isinstance(token, str)
    payload = auth_service.decode_token_payload(token, expected_type="access")
    assert payload["sub"] == "test-user-id"
    assert payload["ver"] == 0
    assert payload["type"] == "access"
    assert "exp" in payload
    assert payload["jti"]
