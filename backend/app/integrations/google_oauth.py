from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from urllib.parse import urlencode

import httpx
import jwt

from app.config import settings

GOOGLE_GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_STATE_AUDIENCE = "google_oauth_state"
_DEFAULT_RETURN_TO = "/settings?tab=integrations"


class GoogleOAuthError(RuntimeError):
    """Raised when the Google OAuth flow cannot be completed."""


@dataclass(frozen=True)
class GoogleOAuthState:
    user_id: str
    return_to: str


def ensure_google_oauth_configured() -> None:
    if not settings.google_oauth_client_id.strip():
        raise GoogleOAuthError("JR_GOOGLE_OAUTH_CLIENT_ID is not configured.")
    if not settings.google_oauth_client_secret.strip():
        raise GoogleOAuthError("JR_GOOGLE_OAUTH_CLIENT_SECRET is not configured.")
    if not settings.google_oauth_redirect_uri.strip():
        raise GoogleOAuthError("JR_GOOGLE_OAUTH_REDIRECT_URI is not configured.")


def normalize_return_to(return_to: str | None) -> str:
    candidate = (return_to or _DEFAULT_RETURN_TO).strip()
    if not candidate.startswith("/") or candidate.startswith("//"):
        return _DEFAULT_RETURN_TO
    return candidate


def build_google_connect_url(*, user_id: str, return_to: str | None = None) -> str:
    ensure_google_oauth_configured()
    normalized_return_to = normalize_return_to(return_to)
    state = _encode_state(user_id=user_id, return_to=normalized_return_to)
    query = urlencode(
        {
            "client_id": settings.google_oauth_client_id,
            "response_type": "code",
            "redirect_uri": settings.google_oauth_redirect_uri,
            "scope": GOOGLE_GMAIL_READONLY_SCOPE,
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent",
            "state": state,
        }
    )
    return f"{_GOOGLE_AUTH_URL}?{query}"


def decode_google_state(state_token: str) -> GoogleOAuthState:
    try:
        payload = jwt.decode(
            state_token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            audience=_STATE_AUDIENCE,
        )
    except jwt.PyJWTError as exc:
        raise GoogleOAuthError("Invalid Google OAuth state.") from exc

    user_id = str(payload.get("sub") or "").strip()
    return_to = normalize_return_to(str(payload.get("return_to") or _DEFAULT_RETURN_TO))
    if not user_id:
        raise GoogleOAuthError("Google OAuth state is missing a user id.")
    return GoogleOAuthState(user_id=user_id, return_to=return_to)


async def exchange_google_code(code: str) -> dict[str, Any]:
    ensure_google_oauth_configured()
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.google_oauth_redirect_uri,
            },
        )
    if response.is_error:
        raise GoogleOAuthError(
            f"Google token exchange failed with status {response.status_code}."
        )
    payload = cast(dict[str, Any], response.json())
    access_token = str(payload.get("access_token") or "").strip()
    refresh_token = str(payload.get("refresh_token") or "").strip()
    if not access_token or not refresh_token:
        raise GoogleOAuthError("Google token exchange did not return offline access.")
    return payload


async def refresh_google_access_token(refresh_token: str) -> dict[str, Any]:
    ensure_google_oauth_configured()
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
    if response.is_error:
        raise GoogleOAuthError(
            f"Google access token refresh failed with status {response.status_code}."
        )
    payload = cast(dict[str, Any], response.json())
    access_token = str(payload.get("access_token") or "").strip()
    if not access_token:
        raise GoogleOAuthError("Google access token refresh returned no access token.")
    return payload


def _encode_state(*, user_id: str, return_to: str) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": user_id,
            "aud": _STATE_AUDIENCE,
            "type": _STATE_AUDIENCE,
            "return_to": return_to,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=10)).timestamp()),
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )
