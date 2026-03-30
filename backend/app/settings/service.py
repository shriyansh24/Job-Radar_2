from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.profile.models import UserProfile
from app.settings.alerts import check_saved_search_alert
from app.settings.models import SavedSearch, UserIntegrationSecret
from app.settings.schemas import AppSettingsUpdate, SavedSearchCreate, SavedSearchUpdate
from app.shared.errors import NotFoundError, ValidationError

logger = structlog.get_logger()

SUPPORTED_INTEGRATIONS = ("openrouter", "serpapi", "theirstack", "apify")


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

    async def update_saved_search(
        self, search_id: uuid.UUID, data: SavedSearchUpdate, user_id: uuid.UUID
    ) -> SavedSearch:
        search = await self._get_saved_search(search_id, user_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(search, key, value)
        if "alert_enabled" in update_data and not search.alert_enabled:
            search.last_checked_at = None
            search.last_matched_at = None
            search.last_match_count = 0
            search.last_error = None
        await self.db.commit()
        await self.db.refresh(search)
        logger.info(
            "saved_search_updated",
            search_id=str(search.id),
            user_id=str(user_id),
            fields=list(update_data.keys()),
        )
        return search

    async def delete_saved_search(self, search_id: uuid.UUID, user_id: uuid.UUID) -> None:
        search = await self._get_saved_search(search_id, user_id)
        await self.db.delete(search)
        await self.db.commit()
        logger.info("saved_search_deleted", search_id=str(search_id), user_id=str(user_id))

    async def list_integrations(self, user_id: uuid.UUID) -> list[dict[str, Any]]:
        result = await self.db.scalars(
            select(UserIntegrationSecret).where(UserIntegrationSecret.user_id == user_id)
        )
        by_provider = {integration.provider: integration for integration in result.all()}
        return [
            self._serialize_integration(provider, by_provider.get(provider))
            for provider in SUPPORTED_INTEGRATIONS
        ]

    async def upsert_integration(
        self, provider: str, api_key: str, user_id: uuid.UUID
    ) -> dict[str, Any]:
        normalized_provider = self._normalize_provider(provider)
        result = await self.db.scalars(
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
                secret_value=api_key,
            )
            self.db.add(integration)
        else:
            integration.secret_value = api_key
            integration.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(integration)
        logger.info("integration_upserted", provider=normalized_provider, user_id=str(user_id))
        return self._serialize_integration(normalized_provider, integration)

    async def delete_integration(self, provider: str, user_id: uuid.UUID) -> None:
        normalized_provider = self._normalize_provider(provider)
        result = await self.db.scalars(
            select(UserIntegrationSecret).where(
                UserIntegrationSecret.user_id == user_id,
                UserIntegrationSecret.provider == normalized_provider,
            )
        )
        integration = result.one_or_none()
        if integration is None:
            raise NotFoundError(f"Integration {normalized_provider} not found")
        await self.db.delete(integration)
        await self.db.commit()
        logger.info("integration_deleted", provider=normalized_provider, user_id=str(user_id))

    async def check_saved_search(self, search_id: uuid.UUID, user_id: uuid.UUID) -> dict[str, Any]:
        search = await self._get_saved_search(search_id, user_id)
        result = await check_saved_search_alert(self.db, search)
        await self.db.commit()
        await self.db.refresh(search)
        logger.info(
            "saved_search_checked",
            search_id=str(search.id),
            user_id=str(user_id),
            new_matches=result.new_matches,
            notification_created=result.notification_created,
        )
        return {
            "search": search,
            "status": "matched" if result.new_matches else "no_match",
            "new_matches": result.new_matches,
            "notification_created": result.notification_created,
            "notification_id": result.notification_id,
            "link": result.link,
        }

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

    async def _get_saved_search(self, search_id: uuid.UUID, user_id: uuid.UUID) -> SavedSearch:
        result = await self.db.execute(
            select(SavedSearch).where(SavedSearch.id == search_id, SavedSearch.user_id == user_id)
        )
        search = result.scalar_one_or_none()
        if search is None:
            raise NotFoundError(f"Saved search {search_id} not found")
        return search

    def _normalize_provider(self, provider: str) -> str:
        normalized = provider.strip().lower()
        if normalized not in SUPPORTED_INTEGRATIONS:
            raise ValidationError(f"Unsupported integration provider: {provider}")
        return normalized

    def _serialize_integration(
        self,
        provider: str,
        integration: UserIntegrationSecret | None,
    ) -> dict[str, Any]:
        if integration is None:
            return {
                "provider": provider,
                "connected": False,
                "status": "not_configured",
                "masked_value": None,
                "updated_at": None,
            }
        return {
            "provider": provider,
            "connected": True,
            "status": "connected",
            "masked_value": self._mask_secret(integration.secret_value),
            "updated_at": integration.updated_at,
        }

    def _mask_secret(self, value: str) -> str:
        if len(value) <= 8:
            return f"{value[:2]}...{value[-2:]}"
        return f"{value[:4]}...{value[-4:]}"
