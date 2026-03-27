from __future__ import annotations

import structlog
from sqlalchemy import select

from app.auto_apply.models import AutoApplyProfile
from app.auto_apply.orchestrator import AutoApplyOrchestrator
from app.config import Settings
from app.database import async_session_factory
from app.enrichment.llm_client import LLMClient

logger = structlog.get_logger()


async def run_auto_apply_batch(ctx: dict) -> None:  # noqa: ARG001
    """Background job: run auto-apply for configured rules."""
    settings = Settings()

    if not settings.auto_apply_enabled:
        logger.info("auto_apply_batch_skipped", reason="disabled")
        return

    llm_client = LLMClient(settings.openrouter_api_key, settings.default_llm_model)

    async with async_session_factory() as db:
        user_ids = (
            await db.scalars(
                select(AutoApplyProfile.user_id).where(
                    AutoApplyProfile.is_active == True,  # noqa: E712
                    AutoApplyProfile.user_id.is_not(None),
                )
            )
        ).all()
        active_user_ids = sorted({user_id for user_id in user_ids if user_id is not None})
        if not active_user_ids:
            logger.info("auto_apply_batch_skipped", reason="no_active_profiles")
            return

        orchestrator = AutoApplyOrchestrator(db, settings, llm_client)
        total_runs = 0
        for user_id in active_user_ids:
            runs = await orchestrator.run_batch(user_id)
            total_runs += len(runs)

        logger.info(
            "auto_apply_batch_completed",
            users=len(active_user_ids),
            runs=total_runs,
        )
