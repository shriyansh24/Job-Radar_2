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
    llm_client = LLMClient(settings.openrouter_api_key, settings.default_llm_model)

    async with async_session_factory() as db:
        # Get users with active auto-apply profiles
        profile = await db.scalar(
            select(AutoApplyProfile).where(AutoApplyProfile.is_active == True).limit(1)  # noqa: E712
        )
        if not profile:
            logger.info("auto_apply_batch_skipped", reason="no_active_profiles")
            return

        orchestrator = AutoApplyOrchestrator(db, settings, llm_client)
        runs = await orchestrator.run_batch(profile.user_id)  # type: ignore[arg-type]
        logger.info("auto_apply_batch_completed", runs=len(runs))
