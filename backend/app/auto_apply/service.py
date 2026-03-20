from __future__ import annotations

import uuid

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auto_apply.models import AutoApplyProfile, AutoApplyRule, AutoApplyRun
from app.auto_apply.schemas import (
    AutoApplyProfileCreate,
    AutoApplyProfileUpdate,
    RuleCreate,
    RuleUpdate,
)
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

    async def create_rule(
        self, data: RuleCreate, user_id: uuid.UUID
    ) -> AutoApplyRule:
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

    async def trigger_run(self, user_id: uuid.UUID) -> dict:
        """Trigger auto-apply run. Full implementation pending."""
        logger.info("auto_apply_trigger_run", user_id=str(user_id))
        return {"status": "queued", "message": "Auto-apply run queued"}

    async def apply_single(self, job_id: str, user_id: uuid.UUID) -> dict:
        """Apply to a single job. Full implementation pending."""
        logger.info("auto_apply_single", job_id=job_id, user_id=str(user_id))
        return {"status": "queued", "job_id": job_id, "message": "Single application queued"}

    async def pause(self, user_id: uuid.UUID) -> dict:
        """Pause auto-apply. Full implementation pending."""
        logger.info("auto_apply_pause", user_id=str(user_id))
        return {"status": "paused", "message": "Auto-apply paused"}

    async def get_stats(self, user_id: uuid.UUID) -> dict:
        # Total runs
        total = await self.db.scalar(
            select(func.count()).where(AutoApplyRun.user_id == user_id)
        ) or 0

        # Successful runs
        successful = await self.db.scalar(
            select(func.count()).where(
                AutoApplyRun.user_id == user_id,
                AutoApplyRun.status == "success",
            )
        ) or 0

        # Failed runs
        failed = await self.db.scalar(
            select(func.count()).where(
                AutoApplyRun.user_id == user_id,
                AutoApplyRun.status == "failed",
            )
        ) or 0

        # Pending runs
        pending = await self.db.scalar(
            select(func.count()).where(
                AutoApplyRun.user_id == user_id,
                AutoApplyRun.status == "pending",
            )
        ) or 0

        return {
            "total_runs": total,
            "successful": successful,
            "failed": failed,
            "pending": pending,
        }
