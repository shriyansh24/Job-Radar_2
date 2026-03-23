from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.settings.schemas import AppSettingsUpdate, SavedSearchCreate
from app.settings.service import SettingsService
from app.shared.errors import NotFoundError


async def _create_user(
    db_session: AsyncSession,
    email: str = "settings-unit@example.com",
) -> User:
    user = User(email=email, password_hash="hashed-password")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_get_settings_creates_default_profile(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    service = SettingsService(db_session)

    settings = await service.get_settings(user.id)

    assert settings == {
        "theme": "dark",
        "notifications_enabled": True,
        "auto_apply_enabled": False,
    }
    profile = await service._get_or_create_profile(user.id)
    assert profile is not None


@pytest.mark.asyncio
async def test_saved_search_crud_is_user_scoped(db_session: AsyncSession) -> None:
    owner = await _create_user(db_session, "settings-owner@example.com")
    other = await _create_user(db_session, "settings-other@example.com")
    service = SettingsService(db_session)

    created = await service.create_saved_search(
        SavedSearchCreate(name="Remote Python", filters={"remote": True}, alert_enabled=True),
        owner.id,
    )
    listed = await service.list_saved_searches(owner.id)

    assert [search.id for search in listed] == [created.id]
    with pytest.raises(NotFoundError):
        await service.delete_saved_search(created.id, other.id)

    await service.delete_saved_search(created.id, owner.id)
    assert await service.list_saved_searches(owner.id) == []


@pytest.mark.asyncio
async def test_update_settings_persists_profile_flags(db_session: AsyncSession) -> None:
    user = await _create_user(db_session, "settings-update@example.com")
    service = SettingsService(db_session)

    updated = await service.update_settings(
        AppSettingsUpdate(
            theme="light",
            notifications_enabled=False,
            auto_apply_enabled=True,
        ),
        user.id,
    )

    assert updated == {
        "theme": "light",
        "notifications_enabled": False,
        "auto_apply_enabled": True,
    }
