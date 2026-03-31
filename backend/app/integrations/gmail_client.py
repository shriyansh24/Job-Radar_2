from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

import httpx

from app.integrations.google_oauth import GoogleOAuthError

_GMAIL_API_ROOT = "https://gmail.googleapis.com/gmail/v1/users/me"


@dataclass(frozen=True)
class GmailMessage:
    message_id: str
    thread_id: str | None
    sender: str
    recipient: str
    subject: str
    text_body: str
    html_body: str
    received_at: datetime | None


class GmailClient:
    async def get_profile(self, access_token: str) -> dict[str, Any]:
        payload = await self._get_json("/profile", access_token)
        email_address = str(payload.get("emailAddress") or "").strip()
        if not email_address:
            raise GoogleOAuthError("Gmail profile response was missing emailAddress.")
        return payload

    async def list_message_ids(
        self,
        access_token: str,
        *,
        query: str,
        max_results: int,
    ) -> list[str]:
        payload = await self._get_json(
            "/messages",
            access_token,
            params={"q": query, "maxResults": max_results},
        )
        messages = payload.get("messages") or []
        return [
            str(message.get("id"))
            for message in messages
            if str(message.get("id") or "").strip()
        ]

    async def get_message(self, access_token: str, message_id: str) -> GmailMessage:
        payload = await self._get_json(
            f"/messages/{message_id}",
            access_token,
            params={"format": "full"},
        )
        return _parse_message(payload)

    async def _get_json(
        self,
        path: str,
        access_token: str,
        *,
        params: dict[str, str | int] | None = None,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{_GMAIL_API_ROOT}{path}",
                params=params,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if response.status_code == 401:
            raise GoogleOAuthError("Google access token is invalid or expired.")
        if response.is_error:
            raise GoogleOAuthError(
                f"Gmail API request failed with status {response.status_code}."
            )
        return cast(dict[str, Any], response.json())


def _parse_message(payload: dict[str, Any]) -> GmailMessage:
    raw_headers = payload.get("payload", {}).get("headers") or []
    headers = {
        str(item.get("name") or "").lower(): str(item.get("value") or "").strip()
        for item in raw_headers
        if item.get("name")
    }
    text_parts: list[str] = []
    html_parts: list[str] = []
    _collect_body_parts(payload.get("payload") or {}, text_parts=text_parts, html_parts=html_parts)
    internal_date = str(payload.get("internalDate") or "").strip()
    received_at = None
    if internal_date.isdigit():
        received_at = datetime.fromtimestamp(int(internal_date) / 1000, tz=UTC)
    return GmailMessage(
        message_id=str(payload.get("id") or "").strip(),
        thread_id=str(payload.get("threadId") or "").strip() or None,
        sender=headers.get("from", ""),
        recipient=headers.get("to", ""),
        subject=headers.get("subject", ""),
        text_body="\n\n".join(part for part in text_parts if part).strip(),
        html_body="\n\n".join(part for part in html_parts if part).strip(),
        received_at=received_at,
    )


def _collect_body_parts(
    payload: dict[str, Any],
    *,
    text_parts: list[str],
    html_parts: list[str],
) -> None:
    mime_type = str(payload.get("mimeType") or "").lower()
    body = payload.get("body") or {}
    data = _decode_body_data(body.get("data"))
    if mime_type == "text/plain" and data:
        text_parts.append(data)
    elif mime_type == "text/html" and data:
        html_parts.append(data)

    for part in payload.get("parts") or []:
        if isinstance(part, dict):
            _collect_body_parts(part, text_parts=text_parts, html_parts=html_parts)


def _decode_body_data(encoded: object) -> str:
    if not isinstance(encoded, str) or not encoded.strip():
        return ""
    padding = "=" * (-len(encoded) % 4)
    try:
        decoded = base64.urlsafe_b64decode(f"{encoded}{padding}".encode("utf-8"))
    except (ValueError, TypeError):
        return ""
    return decoded.decode("utf-8", errors="ignore").strip()
