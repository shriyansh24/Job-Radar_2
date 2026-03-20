from __future__ import annotations

from app.auth.service import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
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
    token = create_access_token("test-user-id")
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_and_decode_refresh_token():
    user_id = "test-user-id"
    token = create_refresh_token(user_id)
    decoded_id = decode_refresh_token(token)
    assert decoded_id == user_id


def test_decode_invalid_refresh_token():
    import pytest

    from app.shared.errors import AuthError

    with pytest.raises(AuthError):
        decode_refresh_token("invalid-token")
