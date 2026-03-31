from __future__ import annotations

import base64
import hashlib
from collections.abc import Mapping
from functools import lru_cache
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

_SECRET_PREFIX = "enc:v1:"


class SecretDecryptionError(RuntimeError):
    """Raised when a stored secret cannot be decrypted with the current runtime key."""


@lru_cache
def _fernet_for_key(secret_material: str) -> Fernet:
    digest = hashlib.sha256(secret_material.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def clear_secret_key_caches() -> None:
    _fernet_for_key.cache_clear()


def _primary_encryption_key() -> str:
    encryption_key = settings.effective_credential_encryption_key.strip()
    if not encryption_key:
        raise RuntimeError("JR_CREDENTIAL_ENCRYPTION_KEY resolved to an empty value.")
    return encryption_key


def _decryption_keys() -> tuple[str, ...]:
    primary_key = _primary_encryption_key()
    keys = [primary_key]
    legacy_secret_key = settings.secret_key.strip()
    if legacy_secret_key and legacy_secret_key not in keys:
        keys.append(legacy_secret_key)
    return tuple(keys)


def seal_secret(value: str) -> str:
    plaintext = value.strip()
    if not plaintext:
        return ""
    token = _fernet_for_key(_primary_encryption_key()).encrypt(plaintext.encode("utf-8")).decode(
        "utf-8"
    )
    return f"{_SECRET_PREFIX}{token}"


def unseal_secret(value: str | None) -> str | None:
    if value is None:
        return None
    if not value.startswith(_SECRET_PREFIX):
        return value
    token = value[len(_SECRET_PREFIX):]
    for key in _decryption_keys():
        try:
            return _fernet_for_key(key).decrypt(token.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            continue
    raise SecretDecryptionError(
        "Stored integration secret could not be decrypted with the current "
        "JR_CREDENTIAL_ENCRYPTION_KEY or legacy JR_SECRET_KEY."
    )


def seal_secret_mapping(values: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if values is None:
        return None
    return {
        key: seal_secret(value) if isinstance(value, str) else value
        for key, value in values.items()
    }


def unseal_secret_mapping(values: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if values is None:
        return None
    return {
        key: unseal_secret(value) if isinstance(value, str) else value
        for key, value in values.items()
    }
