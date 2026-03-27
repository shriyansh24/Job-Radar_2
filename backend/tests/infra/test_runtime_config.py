from __future__ import annotations

from app.config import DEFAULT_SECRET_KEY, Settings, validate_runtime_settings


def test_validate_runtime_settings_rejects_default_secret_in_non_debug():
    settings = Settings(debug=False, secret_key=DEFAULT_SECRET_KEY)

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_SECRET_KEY" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError for the default production secret")


def test_validate_runtime_settings_allows_default_secret_in_debug():
    settings = Settings(debug=True, secret_key=DEFAULT_SECRET_KEY)

    validate_runtime_settings(settings)


def test_validate_runtime_settings_rejects_samesite_none_without_secure_cookie():
    settings = Settings(cookie_samesite="none", cookie_secure=False, secret_key="not-default")

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_COOKIE_SECURE" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError for insecure SameSite=None cookie settings")


def test_validate_runtime_settings_rejects_missing_database_url():
    settings = Settings(database_url="", secret_key="not-default")

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_DATABASE_URL" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when database URL is missing")


def test_validate_runtime_settings_rejects_non_positive_rate_limits():
    settings = Settings(
        secret_key="not-default",
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
    settings = Settings(secret_key="not-default", trusted_hosts=[])

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_TRUSTED_HOSTS" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when trusted hosts are missing")


def test_validate_runtime_settings_rejects_wildcard_trusted_hosts_outside_debug():
    settings = Settings(secret_key="not-default", trusted_hosts=["*"], debug=False)

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_TRUSTED_HOSTS" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when wildcard trusted hosts are used")


def test_validate_runtime_settings_rejects_empty_cors_origins():
    settings = Settings(secret_key="not-default", cors_origins=[])

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_CORS_ORIGINS" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when CORS origins are missing")


def test_validate_runtime_settings_rejects_wildcard_cors_origin():
    settings = Settings(secret_key="not-default", cors_origins=["*"])

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_CORS_ORIGINS" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when wildcard CORS origins are used")


def test_validate_runtime_settings_rejects_malformed_cors_origin():
    settings = Settings(secret_key="not-default", cors_origins=["localhost:5173"])

    try:
        validate_runtime_settings(settings)
    except RuntimeError as exc:
        assert "JR_CORS_ORIGINS" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when a CORS origin is malformed")
