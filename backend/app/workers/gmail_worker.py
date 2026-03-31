"""Gmail sync worker for connected Google integrations."""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import select

from app.config import settings
from app.database import async_session_factory
from app.email.gmail_sync import GOOGLE_PROVIDER, sync_gmail_for_user
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
        integrations = list(result.all())
        if not integrations:
            logger.info("gmail_worker_skipped", reason="no_connected_integrations")
            return

        logger.info("gmail_worker_started", integration_count=len(integrations))
        processed = 0
        for integration in integrations:
            try:
                await sync_gmail_for_user(
                    db,
                    user_id=integration.user_id,
                    query=settings.google_gmail_sync_query,
                    max_messages=settings.google_gmail_sync_max_messages,
                )
                processed += 1
            except Exception:
                logger.exception(
                    "gmail_worker_user_failed",
                    user_id=str(integration.user_id),
                    account_email=integration.account_email,
                )
        logger.info("gmail_worker_completed", processed_users=processed)
