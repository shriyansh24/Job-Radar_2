from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.email.inbound import InboundEmailMessage
from app.email.service import EmailService
from app.integrations.gmail_client import GmailClient
from app.integrations.google_oauth import GoogleOAuthError, refresh_google_access_token
from app.settings.models import UserIntegrationSecret

logger = structlog.get_logger()

GOOGLE_PROVIDER = "google"


@dataclass(frozen=True)
class GmailSyncResult:
    messages_seen: int
    messages_processed: int
    duplicates_skipped: int
    signals_detected: int
    transitions_applied: int
    last_synced_at: datetime | None


async def sync_gmail_for_user(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    query: str,
    max_messages: int,
) -> GmailSyncResult:
    integration = await db.scalar(
        select(UserIntegrationSecret).where(
            UserIntegrationSecret.user_id == user_id,
            UserIntegrationSecret.provider == GOOGLE_PROVIDER,
        )
    )
    if integration is None or integration.auth_type != "oauth" or not integration.secret_json:
        raise GoogleOAuthError("Google integration is not connected.")

    access_token = str(integration.secret_json.get("access_token") or "").strip()
    refresh_token = str(integration.secret_json.get("refresh_token") or "").strip()
    if not access_token or not refresh_token:
        raise GoogleOAuthError("Google integration is missing refreshable credentials.")

    gmail = GmailClient()
    email_service = EmailService(db)
    try:
        message_ids = await gmail.list_message_ids(
            access_token,
            query=query,
            max_results=max_messages,
        )
    except GoogleOAuthError:
        tokens = await refresh_google_access_token(refresh_token)
        integration.secret_json = {
            **integration.secret_json,
            "access_token": str(tokens["access_token"]),
            "refresh_token": refresh_token,
        }
        integration.last_validated_at = datetime.now(timezone.utc)
        access_token = str(tokens["access_token"])
        message_ids = await gmail.list_message_ids(
            access_token,
            query=query,
            max_results=max_messages,
        )

    messages_processed = 0
    duplicates_skipped = 0
    signals_detected = 0
    transitions_applied = 0

    for message_id in message_ids:
        message = await gmail.get_message(access_token, message_id)
        inbound = InboundEmailMessage(
            sender=message.sender,
            from_address=message.sender,
            to_address=message.recipient,
            subject=message.subject,
            text=message.text_body,
            html=message.html_body,
            source_provider=GOOGLE_PROVIDER,
            source_message_id=message.message_id,
            source_thread_id=message.thread_id,
            received_at=message.received_at,
        )
        result = await email_service.process_inbound_message(
            inbound,
            user_id,
            auto_transition_min_confidence=0.85,
        )
        if result.status == "duplicate":
            duplicates_skipped += 1
            continue
        messages_processed += 1
        if result.action is not None:
            signals_detected += 1
        if result.status == "updated":
            transitions_applied += 1

    integration.last_synced_at = datetime.now(timezone.utc)
    integration.last_validated_at = integration.last_synced_at
    integration.last_error = None
    await db.commit()
    logger.info(
        "gmail_sync_completed",
        user_id=str(user_id),
        provider=GOOGLE_PROVIDER,
        messages_seen=len(message_ids),
        messages_processed=messages_processed,
        duplicates_skipped=duplicates_skipped,
        signals_detected=signals_detected,
        transitions_applied=transitions_applied,
    )
    return GmailSyncResult(
        messages_seen=len(message_ids),
        messages_processed=messages_processed,
        duplicates_skipped=duplicates_skipped,
        signals_detected=signals_detected,
        transitions_applied=transitions_applied,
        last_synced_at=integration.last_synced_at,
    )
