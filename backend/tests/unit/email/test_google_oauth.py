from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest

from app.config import settings
from app.integrations import google_oauth as google_oauth_module
from app.integrations.google_oauth import GoogleOAuthError


def test_normalize_return_to_rejects_external_urls() -> None:
    expected = "/settings?tab=integrations"

    assert google_oauth_module.normalize_return_to("https://example.com/callback") == expected
    assert google_oauth_module.normalize_return_to("//evil.example") == expected
    assert google_oauth_module.normalize_return_to(expected) == expected


def test_build_google_connect_url_requests_offline_gmail_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "google_oauth_client_id", "google-client-id")
    monkeypatch.setattr(settings, "google_oauth_client_secret", "google-client-secret")
    monkeypatch.setattr(
        settings,
        "google_oauth_redirect_uri",
        "http://localhost:8000/api/v1/settings/integrations/google/callback",
    )

    url = google_oauth_module.build_google_connect_url(
        user_id="user-123",
        return_to="/settings?tab=integrations",
    )

    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.netloc == "accounts.google.com"
    assert query["client_id"] == ["google-client-id"]
    assert query["redirect_uri"] == [
        "http://localhost:8000/api/v1/settings/integrations/google/callback"
    ]
    assert query["scope"] == [google_oauth_module.GOOGLE_GMAIL_READONLY_SCOPE]
    assert query["access_type"] == ["offline"]
    assert query["prompt"] == ["consent"]

    state = google_oauth_module.decode_google_state(query["state"][0])
    assert state.user_id == "user-123"
    assert state.return_to == "/settings?tab=integrations"


def test_decode_google_state_rejects_invalid_tokens() -> None:
    with pytest.raises(GoogleOAuthError, match="Invalid Google OAuth state"):
        google_oauth_module.decode_google_state("not-a-valid-jwt")
