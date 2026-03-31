from __future__ import annotations

import base64
import hashlib

import pytest
from cryptography.fernet import Fernet

from app.config import settings
from app.shared.secrets import (
    clear_secret_key_caches,
    seal_secret,
    seal_secret_mapping,
    unseal_secret,
    unseal_secret_mapping,
)


def test_secret_round_trip_uses_sealed_prefix() -> None:
    sealed = seal_secret("top-secret-value")

    assert sealed != "top-secret-value"
    assert sealed.startswith("enc:v1:")
    assert unseal_secret(sealed) == "top-secret-value"


def test_unseal_secret_keeps_legacy_plaintext_values_readable() -> None:
    assert unseal_secret("legacy-plaintext-secret") == "legacy-plaintext-secret"


def test_secret_mapping_round_trip_seals_string_values_only() -> None:
    sealed = seal_secret_mapping(
        {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "issued_at": 123,
        }
    )

    assert sealed is not None
    assert sealed["access_token"] != "access-token"
    assert sealed["refresh_token"] != "refresh-token"
    assert sealed["issued_at"] == 123
    assert unseal_secret_mapping(sealed) == {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "issued_at": 123,
    }


def test_seal_secret_returns_empty_string_for_whitespace() -> None:
    assert seal_secret("   ") == ""


def test_unseal_secret_supports_legacy_secret_key_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy_secret_key = "legacy-signing-key"
    new_encryption_key = "new-encryption-key"
    legacy_digest = hashlib.sha256(legacy_secret_key.encode("utf-8")).digest()
    legacy_fernet = Fernet(base64.urlsafe_b64encode(legacy_digest))
    legacy_ciphertext = "enc:v1:" + legacy_fernet.encrypt(b"legacy-secret").decode("utf-8")

    monkeypatch.setattr(settings, "secret_key", legacy_secret_key)
    monkeypatch.setattr(settings, "credential_encryption_key", new_encryption_key)
    clear_secret_key_caches()

    assert unseal_secret(legacy_ciphertext) == "legacy-secret"

    clear_secret_key_caches()
