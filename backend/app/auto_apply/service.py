from __future__ import annotations

import uuid

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auto_apply.models import AutoApplyProfile, AutoApplyRule, AutoApplyRun
from app.auto_apply.orchestrator import AutoApplyOrchestrator
from app.auto_apply.schemas import (
    ApplySingleResponse,
    AutoApplyPauseResponse,
    AutoApplyProfileCreate,
    AutoApplyProfileUpdate,
    AutoApplyTriggerResponse,
    RuleCreate,
    RuleUpdate,
    RunResult,
)
from app.config import Settings
from app.enrichment.llm_client import LLMClient
from app.jobs.models import Job
from app.shared.errors import NotFoundError

logger = structlog.get_logger()


class AutoApplyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_profiles(self, user_id: uuid.UUID) -> list[AutoApplyProfile]:
        result = await self.db.scalars(
            select(AutoApplyProfile).where(AutoApplyProfile.user_id == user_id)
        )
        return list(result.all())

    async def create_profile(
        self, data: AutoApplyProfileCreate, user_id: uuid.UUID
    ) -> AutoApplyProfile:
        profile = AutoApplyProfile(
            user_id=user_id,
            **data.model_dump(),
        )
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        logger.info("auto_apply_profile_created", profile_id=str(profile.id), user_id=str(user_id))
        return profile

    async def update_profile(
        self,
        profile_id: uuid.UUID,
        data: AutoApplyProfileUpdate,
        user_id: uuid.UUID,
    ) -> AutoApplyProfile:
        result = await self.db.execute(
            select(AutoApplyProfile).where(
                AutoApplyProfile.id == profile_id,
                AutoApplyProfile.user_id == user_id,
            )
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            raise NotFoundError(f"Auto-apply profile {profile_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)

        await self.db.commit()
        await self.db.refresh(profile)
        logger.info("auto_apply_profile_updated", profile_id=str(profile_id), user_id=str(user_id))
        return profile

    async def list_rules(self, user_id: uuid.UUID) -> list[AutoApplyRule]:
        result = await self.db.scalars(
            select(AutoApplyRule).where(AutoApplyRule.user_id == user_id)
        )
        return list(result.all())

    async def create_rule(self, data: RuleCreate, user_id: uuid.UUID) -> AutoApplyRule:
        rule = AutoApplyRule(
            user_id=user_id,
            **data.model_dump(),
        )
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        logger.info("auto_apply_rule_created", rule_id=str(rule.id), user_id=str(user_id))
        return rule

    async def update_rule(
        self,
        rule_id: uuid.UUID,
        data: RuleUpdate,
        user_id: uuid.UUID,
    ) -> AutoApplyRule:
        result = await self.db.execute(
            select(AutoApplyRule).where(
                AutoApplyRule.id == rule_id,
                AutoApplyRule.user_id == user_id,
            )
        )
        rule = result.scalar_one_or_none()
        if rule is None:
            raise NotFoundError(f"Auto-apply rule {rule_id} not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(rule, key, value)
        await self.db.commit()
        await self.db.refresh(rule)
        logger.info("auto_apply_rule_updated", rule_id=str(rule_id), user_id=str(user_id))
        return rule

    async def delete_rule(self, rule_id: uuid.UUID, user_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(AutoApplyRule).where(
                AutoApplyRule.id == rule_id,
                AutoApplyRule.user_id == user_id,
            )
        )
        rule = result.scalar_one_or_none()
        if rule is None:
            raise NotFoundError(f"Auto-apply rule {rule_id} not found")
        await self.db.delete(rule)
        await self.db.commit()
        logger.info("auto_apply_rule_deleted", rule_id=str(rule_id), user_id=str(user_id))

    async def list_runs(self, user_id: uuid.UUID) -> list[AutoApplyRun]:
        result = await self.db.scalars(
            select(AutoApplyRun)
            .where(AutoApplyRun.user_id == user_id)
            .order_by(AutoApplyRun.started_at.desc().nullslast())
        )
        return list(result.all())

    def serialize_run(self, run: AutoApplyRun) -> RunResult:
        review_items = self._review_items_for_run(run)
        return RunResult(
            id=run.id,
            job_id=run.job_id,
            rule_id=run.rule_id,
            status=run.status,
            ats_provider=run.ats_provider,
            fields_filled=run.fields_filled or {},
            fields_missed=run.fields_missed or [],
            review_required=bool(review_items),
            review_items=review_items,
            screenshots=run.screenshots or [],
            error_message=run.error_message,
            started_at=run.started_at,
            completed_at=run.completed_at,
        )

    async def trigger_run(self, user_id: uuid.UUID) -> AutoApplyTriggerResponse:
        profile = await self._get_active_profile(user_id)
        if profile is None:
            return AutoApplyTriggerResponse(
                status="idle",
                message="No active auto-apply profile",
            )

        active_rule_count = await self.db.scalar(
            select(func.count()).where(
                AutoApplyRule.user_id == user_id,
                AutoApplyRule.is_active == True,  # noqa: E712
            )
        )
        if not active_rule_count:
            return AutoApplyTriggerResponse(
                status="idle",
                message="No active auto-apply rules",
            )

        orchestrator = self._build_orchestrator()
        runs = await orchestrator.run_batch(user_id)
        logger.info("auto_apply_trigger_run", user_id=str(user_id), runs=len(runs))
        return AutoApplyTriggerResponse(
            status="completed" if runs else "idle",
            message="Auto-apply batch executed" if runs else "No jobs matched active rules",
            runs_created=len(runs),
            run_ids=[str(run.id) for run in runs],
        )

    async def apply_single(self, job_id: str, user_id: uuid.UUID) -> ApplySingleResponse:
        profile = await self._get_active_profile(user_id)
        if profile is None:
            return ApplySingleResponse(
                status="idle",
                job_id=job_id,
                message="No active auto-apply profile",
            )

        job = await self.db.scalar(
            select(Job).where(
                Job.id == job_id,
                Job.user_id == user_id,
            )
        )
        if job is None:
            return ApplySingleResponse(
                status="not_found",
                job_id=job_id,
                message="Job not found",
            )

        orchestrator = self._build_orchestrator()
        run = await orchestrator.apply_to_job(job, profile, allow_first_time_ats=True)
        review_items = self._review_items_for_run(run)
        logger.info(
            "auto_apply_single",
            job_id=job_id,
            user_id=str(user_id),
            run_id=str(run.id),
            status=run.status,
        )
        return ApplySingleResponse(
            status=run.status,
            job_id=job_id,
            run_id=str(run.id),
            message=self._message_for_run(run.status, run.error_message),
            review_required=bool(review_items),
            review_items=review_items,
        )

    async def pause(self, user_id: uuid.UUID) -> AutoApplyPauseResponse:
        rules = (
            await self.db.scalars(
                select(AutoApplyRule).where(
                    AutoApplyRule.user_id == user_id,
                    AutoApplyRule.is_active == True,  # noqa: E712
                )
            )
        ).all()
        for rule in rules:
            rule.is_active = False

        await self.db.commit()
        logger.info("auto_apply_pause", user_id=str(user_id), rules_paused=len(rules))
        return AutoApplyPauseResponse(
            status="paused",
            message="Auto-apply paused",
            rules_paused=len(rules),
        )

    async def get_stats(self, user_id: uuid.UUID) -> dict[str, int]:
        # Total runs
        total = (
            await self.db.scalar(select(func.count()).where(AutoApplyRun.user_id == user_id)) or 0
        )

        # Successful runs
        successful = (
            await self.db.scalar(
                select(func.count()).where(
                    AutoApplyRun.user_id == user_id,
                    AutoApplyRun.status.in_(["success", "filled", "submitted"]),
                )
            )
            or 0
        )

        # Failed runs
        failed = (
            await self.db.scalar(
                select(func.count()).where(
                    AutoApplyRun.user_id == user_id,
                    AutoApplyRun.status == "failed",
                )
            )
            or 0
        )

        # Pending runs
        pending = (
            await self.db.scalar(
                select(func.count()).where(
                    AutoApplyRun.user_id == user_id,
                    AutoApplyRun.status.in_(["pending", "queued", "running"]),
                )
            )
            or 0
        )

        return {
            "total_runs": total,
            "successful": successful,
            "failed": failed,
            "pending": pending,
        }

    async def _get_active_profile(self, user_id: uuid.UUID) -> AutoApplyProfile | None:
        result = await self.db.execute(
            select(AutoApplyProfile).where(
                AutoApplyProfile.user_id == user_id,
                AutoApplyProfile.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    def _build_orchestrator(self) -> AutoApplyOrchestrator:
        settings = Settings()
        llm_client = LLMClient(settings.openrouter_api_key, settings.default_llm_model)
        return AutoApplyOrchestrator(self.db, settings, llm_client)

    def _message_for_run(self, status: str, error_message: str | None) -> str:
        if status in {"success", "submitted"}:
            return "Application submitted"
        if status == "filled":
            return "Application filled and ready for review"
        if status == "failed":
            return error_message or "Application attempt failed"
        return error_message or f"Run ended with status '{status}'"

    def _review_items_for_run(self, run: AutoApplyRun) -> list[str]:
        if run.status != "filled":
            return []

        review_items: list[str] = []

        review_items.append("Manual confirmation required before final submission.")

        for item in run.review_items or []:
            if item not in review_items:
                review_items.append(item)

        for field in run.fields_missed or []:
            message = f"Provide value for '{field}'"
            if message not in review_items:
                review_items.append(message)

        return review_items
