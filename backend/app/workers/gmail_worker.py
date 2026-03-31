"""Gmail sync worker for connected Google integrations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import select

from app.config import settings
from app.database import async_session_factory
from app.email.gmail_sync import GOOGLE_PROVIDER, sync_gmail_for_user
from app.integrations.google_oauth import GoogleOAuthError
from app.settings.models import UserIntegrationSecret

logger = structlog.get_logger()


async def run_gmail_sync(ctx: dict[str, Any] | None = None) -> None:
    del ctx

    async with async_session_factory() as db:
        result = await db.scalars(
            select(UserIntegrationSecret).where(
                UserIntegrationSecret.provider == GOOGLE_PROVIDER,
                UserIntegrationSecret.auth_type == "oauth",
            )
        )
        integration_refs = [
            {
                "id": integration.id,
                "user_id": integration.user_id,
                "account_email": integration.account_email,
            }
            for integration in result.all()
        ]
        if not integration_refs:
            logger.info("gmail_worker_skipped", reason="no_connected_integrations")
            return

        logger.info("gmail_worker_started", integration_count=len(integration_refs))
        processed = 0
        retryable_failures = 0
        for integration_ref in integration_refs:
            integration_id = integration_ref["id"]
            user_id = uuid.UUID(str(integration_ref["user_id"]))
            account_email = integration_ref["account_email"]
            try:
                await sync_gmail_for_user(
                    db,
                    user_id=user_id,
                    query=settings.google_gmail_sync_query,
                    max_messages=settings.google_gmail_sync_max_messages,
                )
                processed += 1
            except Exception as exc:
                retryable = bool(getattr(exc, "retryable", False)) or not isinstance(
                    exc, GoogleOAuthError
                )
                if retryable:
                    retryable_failures += 1
                await db.rollback()
                failed_integration = await db.scalar(
                    select(UserIntegrationSecret).where(
                        UserIntegrationSecret.id == integration_id
                    )
                )
                if failed_integration is not None:
                    failed_integration.last_error = str(exc)
                    failed_integration.updated_at = datetime.now(timezone.utc)
                    try:
                        await db.commit()
                    except Exception:
                        await db.rollback()
                        logger.exception(
                            "gmail_worker_failure_state_persist_failed",
                            user_id=str(user_id),
                            account_email=account_email,
                        )
                logger.exception(
                    "gmail_worker_user_failed",
                    user_id=str(user_id),
                    account_email=account_email,
                    retryable=retryable,
                )
        logger.info(
            "gmail_worker_completed",
            processed_users=processed,
            retryable_failures=retryable_failures,
        )
        if retryable_failures:
            raise RuntimeError(
                f"gmail_worker encountered {retryable_failures} retryable integration failure(s)."
            )
