from __future__ import annotations

from app.config import (
    DEFAULT_DATABASE_URL,
    DEFAULT_REDIS_URL,
    DEFAULT_SECRET_KEY,
    Settings,
    validate_runtime_settings,
)


def _valid_runtime_settings(**overrides: object) -> Settings:
    values = {
        "debug": False,
        "secret_key": "not-default",
        "credential_encryption_key": "not-default-encryption",
        "cookie_secure": True,
        "database_url": "postgresql+asyncpg://jobradar:jobradar@db.example.com:5432/jobradar",
        "redis_url": "redis://:jobradar-redis@redis.example.com:6379/0",
        "operator_emails": ["ops@example.com"],
    }
    values.update(overrides)
    return Settings(**values)


def test_validate_runtime_settings_rejects_default_secret_in_non_debug():
    settings = _valid_runtime_settings(debug=False, secret_key=DEFAULT_SECRET_KEY)

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_SECRET_KEY" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError for the default production secret")


def test_validate_runtime_settings_allows_default_secret_in_debug():
    settings = Settings(debug=True, secret_key=DEFAULT_SECRET_KEY)

    validate_runtime_settings(settings)


def test_validate_runtime_settings_requires_credential_encryption_key():
    settings = _valid_runtime_settings(credential_encryption_key="")

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_CREDENTIAL_ENCRYPTION_KEY" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when credential encryption key is missing")


def test_validate_runtime_settings_rejects_shared_signing_and_encryption_keys():
    settings = _valid_runtime_settings(credential_encryption_key="not-default")

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_CREDENTIAL_ENCRYPTION_KEY" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when encryption and signing keys match")


def test_validate_runtime_settings_rejects_samesite_none_without_secure_cookie():
    settings = _valid_runtime_settings(cookie_samesite="none", cookie_secure=False)

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_COOKIE_SECURE" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError for insecure SameSite=None cookie settings")


def test_validate_runtime_settings_rejects_insecure_cookies_outside_debug():
    settings = _valid_runtime_settings(
        debug=False,
        cookie_secure=False,
    )

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_COOKIE_SECURE" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError for insecure cookies outside debug")


def test_validate_runtime_settings_allows_secure_cookies_outside_debug():
    settings = _valid_runtime_settings(
        debug=False,
    )

    validate_runtime_settings(settings)


def test_validate_runtime_settings_rejects_missing_database_url():
    settings = _valid_runtime_settings(database_url="")

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_DATABASE_URL" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when database URL is missing")


def test_validate_runtime_settings_rejects_invalid_redis_url():
    settings = _valid_runtime_settings(redis_url="http://redis")

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_REDIS_URL" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when redis URL is invalid")


def test_validate_runtime_settings_rejects_non_positive_rate_limits():
    settings = _valid_runtime_settings(
        api_rate_limit_per_minute=0,
        login_rate_limit_per_minute=0,
    )

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_API_RATE_LIMIT_PER_MINUTE" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when API rate limit is invalid")


def test_validate_runtime_settings_rejects_empty_trusted_hosts():
    settings = _valid_runtime_settings(trusted_hosts=[])

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_TRUSTED_HOSTS" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when trusted hosts are missing")


def test_validate_runtime_settings_rejects_wildcard_trusted_hosts_outside_debug():
    settings = _valid_runtime_settings(
        trusted_hosts=["*"],
        debug=False,
    )

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_TRUSTED_HOSTS" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when wildcard trusted hosts are used")


def test_validate_runtime_settings_rejects_missing_operator_emails_outside_debug():
    settings = _valid_runtime_settings(operator_emails=[])

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_OPERATOR_EMAILS" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when operator emails are missing")


def test_validate_runtime_settings_rejects_empty_cors_origins():
    settings = _valid_runtime_settings(cors_origins=[])

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_CORS_ORIGINS" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when CORS origins are missing")


def test_validate_runtime_settings_rejects_wildcard_cors_origin():
    settings = _valid_runtime_settings(cors_origins=["*"])

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_CORS_ORIGINS" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when wildcard CORS origins are used")


def test_validate_runtime_settings_rejects_malformed_cors_origin():
    settings = _valid_runtime_settings(cors_origins=["localhost:5173"])

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_CORS_ORIGINS" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when a CORS origin is malformed")


def test_validate_runtime_settings_rejects_default_database_url_outside_debug():
    settings = _valid_runtime_settings(database_url=DEFAULT_DATABASE_URL)

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_DATABASE_URL" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when using the built-in database URL")


def test_validate_runtime_settings_rejects_default_redis_url_outside_debug():
    settings = _valid_runtime_settings(redis_url=DEFAULT_REDIS_URL)

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_REDIS_URL" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when using the built-in redis URL")
