from __future__ import annotations

import hashlib
import hmac
import uuid

import pytest
from httpx import AsyncClient


def _signed_payload(email: str, *, signature: str) -> dict[str, str]:
    return {
        "to": f"JobRadar <{email}>",
        "sender": "newsletter@example.com",
        "subject": "Weekly Update",
        "text": "Here are the latest updates from our team.",
        "timestamp": "1700",
        "token": "token-123",
        "signature": signature,
    }


@pytest.mark.asyncio
async def test_email_webhook_accepts_valid_signed_request_without_auth(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    email = f"email-webhook-{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "securepassword123"},
    )

    secret = "email-webhook-signing-secret-for-tests"
    monkeypatch.setattr("app.email.service.settings.secret_key", secret)
    monkeypatch.setattr("app.email.service.settings.jwt_signing_key", "")
    signature = hmac.new(secret.encode(), b"1700token-123", hashlib.sha256).hexdigest()

    response = await client.post(
        "/api/v1/email/webhook",
        json=_signed_payload(email, signature=signature),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "no_signal"


@pytest.mark.asyncio
async def test_email_webhook_rejects_invalid_signature_without_auth(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    email = f"email-webhook-{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "securepassword123"},
    )

    monkeypatch.setattr("app.email.service.settings.secret_key", "email-webhook-signing-secret")
    monkeypatch.setattr("app.email.service.settings.jwt_signing_key", "")

    response = await client.post(
        "/api/v1/email/webhook",
        json=_signed_payload(email, signature="bad-signature"),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid webhook signature"
