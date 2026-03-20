from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.profile.models import UserProfile
from app.profile.schemas import ProfileUpdate

logger = structlog.get_logger()


class ProfileService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_profile(self, user_id: uuid.UUID) -> UserProfile:
        """Return the user profile, creating one if it does not exist."""
        logger.info("profile.get_profile", user_id=str(user_id))
        query = select(UserProfile).where(UserProfile.user_id == user_id)
        profile = await self.db.scalar(query)

        if profile is None:
            logger.info("profile.creating_default", user_id=str(user_id))
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)

        return profile

    async def generate_answers(self, user_id: uuid.UUID) -> dict:
        """Generate answer bank from profile. LLM integration pending."""
        logger.info("profile.generate_answers", user_id=str(user_id))
        profile = await self.get_profile(user_id)
        return {
            "status": "pending",
            "message": "Answer generation requires LLM integration",
            "current_answers": profile.answer_bank or {},
        }

    async def update_profile(
        self, data: ProfileUpdate, user_id: uuid.UUID
    ) -> UserProfile:
        """Update the user profile with the provided fields."""
        logger.info("profile.update_profile", user_id=str(user_id))
        profile = await self.get_profile(user_id)

        update_fields = data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(profile, field, value)

        profile.updated_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(profile)
        return profile
