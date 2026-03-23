from __future__ import annotations

from app.auth.service import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    decode_token_payload,
    hash_password,
    verify_password,
)


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


def test_decode_invalid_refresh_token():
    import pytest

    from app.shared.errors import AuthError

    with pytest.raises(AuthError):
        decode_refresh_token("invalid-token")
