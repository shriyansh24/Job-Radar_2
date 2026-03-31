from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, cast

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.email.gmail_sync import GOOGLE_PROVIDER
from app.integrations.gmail_client import GmailClient
from app.integrations.google_oauth import (
    GoogleOAuthError,
    build_google_connect_url,
)
from app.settings.models import UserIntegrationSecret
from app.shared.errors import NotFoundError, ValidationError

logger = structlog.get_logger()

API_KEY_INTEGRATIONS = ("openrouter", "serpapi", "theirstack", "apify")
SUPPORTED_INTEGRATIONS = (*API_KEY_INTEGRATIONS, GOOGLE_PROVIDER)


async def list_integrations(db: AsyncSession, user_id: uuid.UUID) -> list[dict[str, Any]]:
    result = await db.scalars(
        select(UserIntegrationSecret).where(UserIntegrationSecret.user_id == user_id)
    )
    by_provider = {integration.provider: integration for integration in result.all()}
    return [
        _serialize_integration(provider, by_provider.get(provider))
        for provider in SUPPORTED_INTEGRATIONS
    ]


async def upsert_integration(
    db: AsyncSession,
    provider: str,
    api_key: str,
    user_id: uuid.UUID,
) -> dict[str, Any]:
    normalized_provider = _normalize_provider(provider, api_key_only=True)
    result = await db.scalars(
        select(UserIntegrationSecret).where(
            UserIntegrationSecret.user_id == user_id,
            UserIntegrationSecret.provider == normalized_provider,
        )
    )
    integration = result.one_or_none()
    if integration is None:
        integration = UserIntegrationSecret(
            user_id=user_id,
            provider=normalized_provider,
            auth_type="api_key",
            secret_value=api_key,
        )
        db.add(integration)
    else:
        integration.auth_type = "api_key"
        integration.secret_value = api_key
        integration.secret_json = None
        integration.account_email = None
        integration.scopes = None
        integration.last_error = None
        integration.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(integration)
    logger.info("integration_upserted", provider=normalized_provider, user_id=str(user_id))
    return _serialize_integration(normalized_provider, integration)


async def delete_integration(db: AsyncSession, provider: str, user_id: uuid.UUID) -> None:
    normalized_provider = _normalize_provider(provider)
    integration = await _get_integration_record(db, normalized_provider, user_id)
    if integration is None:
        raise NotFoundError(f"Integration {normalized_provider} not found")
    await db.delete(integration)
    await db.commit()
    logger.info("integration_deleted", provider=normalized_provider, user_id=str(user_id))


def build_google_connect_url_for_user(user_id: uuid.UUID, *, return_to: str | None = None) -> str:
    return build_google_connect_url(user_id=str(user_id), return_to=return_to)


async def connect_google_integration(
    db: AsyncSession,
    *,
    code: str,
    state_token: str,
    decode_google_state_fn,
    exchange_google_code_fn,
    gmail_client_cls=GmailClient,
) -> dict[str, Any]:
    state = decode_google_state_fn(state_token)
    tokens = await exchange_google_code_fn(code)
    access_token = str(tokens.get("access_token") or "").strip()
    refresh_token = str(tokens.get("refresh_token") or "").strip()
    scopes = [
        scope for scope in str(tokens.get("scope") or "").split()
        if scope.strip()
    ]
    profile = await gmail_client_cls().get_profile(access_token)
    user_id = uuid.UUID(state.user_id)
    integration = await _get_integration_record(db, GOOGLE_PROVIDER, user_id)
    if integration is None:
        integration = UserIntegrationSecret(
            user_id=user_id,
            provider=GOOGLE_PROVIDER,
            auth_type="oauth",
        )
        db.add(integration)
    integration.auth_type = "oauth"
    integration.secret_value = None
    integration.secret_json = {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
    integration.account_email = str(profile["emailAddress"])
    integration.scopes = scopes
    integration.last_validated_at = datetime.now(timezone.utc)
    integration.last_error = None
    await db.commit()
    await db.refresh(integration)
    logger.info(
        "google_integration_connected",
        user_id=str(user_id),
        account_email=integration.account_email,
    )
    return {
        "provider": GOOGLE_PROVIDER,
        "account_email": integration.account_email,
        "return_to": state.return_to,
    }


async def sync_google_integration(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    sync_gmail_for_user_fn,
) -> dict[str, Any]:
    integration = await _get_integration_record(db, GOOGLE_PROVIDER, user_id)
    if integration is None:
        raise NotFoundError("Integration google not found")
    try:
        result = await sync_gmail_for_user_fn(
            db,
            user_id=user_id,
            query=settings.google_gmail_sync_query,
            max_messages=settings.google_gmail_sync_max_messages,
        )
    except GoogleOAuthError as exc:
        integration.last_error = str(exc)
        integration.updated_at = datetime.now(timezone.utc)
        await db.commit()
        raise ValidationError(str(exc)) from exc
    await db.refresh(integration)
    return {
        "provider": GOOGLE_PROVIDER,
        "messages_seen": result.messages_seen,
        "messages_processed": result.messages_processed,
        "duplicates_skipped": result.duplicates_skipped,
        "signals_detected": result.signals_detected,
        "transitions_applied": result.transitions_applied,
        "last_synced_at": integration.last_synced_at,
    }


async def _get_integration_record(
    db: AsyncSession,
    provider: str,
    user_id: uuid.UUID,
) -> UserIntegrationSecret | None:
    return cast(
        UserIntegrationSecret | None,
        await db.scalar(
            select(UserIntegrationSecret).where(
                UserIntegrationSecret.user_id == user_id,
                UserIntegrationSecret.provider == provider,
            )
        ),
    )


def _normalize_provider(provider: str, *, api_key_only: bool = False) -> str:
    normalized = provider.strip().lower()
    allowed = API_KEY_INTEGRATIONS if api_key_only else SUPPORTED_INTEGRATIONS
    if normalized not in allowed:
        raise ValidationError(f"Unsupported integration provider: {provider}")
    return normalized


def _serialize_integration(
    provider: str,
    integration: UserIntegrationSecret | None,
) -> dict[str, Any]:
    if integration is None:
        return {
            "provider": provider,
            "auth_type": "oauth" if provider == GOOGLE_PROVIDER else "api_key",
            "connected": False,
            "status": "not_configured",
            "masked_value": None,
            "account_email": None,
            "scopes": [],
            "updated_at": None,
            "last_validated_at": None,
            "last_synced_at": None,
            "last_error": None,
        }

    status = "connected"
    if integration.auth_type == "oauth":
        refresh_token = str((integration.secret_json or {}).get("refresh_token") or "").strip()
        if not refresh_token:
            status = "needs_reconnect"
        elif integration.last_error:
            status = "sync_error"

    return {
        "provider": provider,
        "auth_type": integration.auth_type,
        "connected": status == "connected",
        "status": status,
        "masked_value": (
            _mask_secret(integration.secret_value)
            if integration.auth_type == "api_key" and integration.secret_value
            else None
        ),
        "account_email": integration.account_email,
        "scopes": list(integration.scopes or []),
        "updated_at": integration.updated_at,
        "last_validated_at": integration.last_validated_at,
        "last_synced_at": integration.last_synced_at,
        "last_error": integration.last_error,
    }


def _mask_secret(value: str) -> str:
    if len(value) <= 8:
        return f"{value[:2]}...{value[-2:]}"
    return f"{value[:4]}...{value[-4:]}"
