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
