from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.profile.models import UserProfile
from app.settings.models import SavedSearch
from app.settings.schemas import AppSettingsUpdate, SavedSearchCreate
from app.shared.errors import NotFoundError

logger = structlog.get_logger()


class SettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_saved_searches(self, user_id: uuid.UUID) -> list[SavedSearch]:
        result = await self.db.scalars(select(SavedSearch).where(SavedSearch.user_id == user_id))
        return list(result.all())

    async def create_saved_search(
        self, data: SavedSearchCreate, user_id: uuid.UUID
    ) -> SavedSearch:
        search = SavedSearch(
            user_id=user_id,
            name=data.name,
            filters=data.filters,
            alert_enabled=data.alert_enabled,
        )
        self.db.add(search)
        await self.db.commit()
        await self.db.refresh(search)
        logger.info("saved_search_created", search_id=str(search.id), user_id=str(user_id))
        return search

    async def delete_saved_search(self, search_id: uuid.UUID, user_id: uuid.UUID) -> None:
        result = await self.db.execute(select(SavedSearch).where(SavedSearch.id == search_id))
        search = result.scalar_one_or_none()
        if search is None:
            raise NotFoundError(f"Saved search {search_id} not found")
        if search.user_id != user_id:
            raise NotFoundError(f"Saved search {search_id} not found")
        await self.db.delete(search)
        await self.db.commit()
        logger.info("saved_search_deleted", search_id=str(search_id), user_id=str(user_id))

    async def _get_or_create_profile(self, user_id: uuid.UUID) -> UserProfile:
        result = await self.db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()
        if profile is None:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)
        return profile

    async def get_settings(self, user_id: uuid.UUID) -> dict:
        profile = await self._get_or_create_profile(user_id)
        return {
            "theme": profile.theme,
            "notifications_enabled": profile.notifications_enabled,
            "auto_apply_enabled": profile.auto_apply_enabled,
        }

    async def update_settings(self, data: AppSettingsUpdate, user_id: uuid.UUID) -> dict:
        profile = await self._get_or_create_profile(user_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)
        await self.db.commit()
        await self.db.refresh(profile)
        logger.info("settings_updated", user_id=str(user_id), fields=list(update_data.keys()))
        return {
            "theme": profile.theme,
            "notifications_enabled": profile.notifications_enabled,
            "auto_apply_enabled": profile.auto_apply_enabled,
        }
