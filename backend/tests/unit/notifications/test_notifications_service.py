from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.notifications.service import NotificationService


async def _create_user(
    db_session: AsyncSession,
    email: str = "notifications-unit@example.com",
) -> User:
    user = User(email=email, password_hash="hashed-password")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_and_list_notifications_returns_unread_count(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    service = NotificationService(db_session)

    await service.create(user.id, "First", "Body 1", notification_type="system")
    await service.create(user.id, "Second", "Body 2", notification_type="alert")
    items, unread_count = await service.list_notifications(user.id)

    assert {item.title for item in items} == {"First", "Second"}
    assert unread_count == 2


@pytest.mark.asyncio
async def test_mark_read_and_mark_all_read_are_user_scoped(db_session: AsyncSession) -> None:
    owner = await _create_user(db_session, "notifications-owner@example.com")
    other = await _create_user(db_session, "notifications-other@example.com")
    service = NotificationService(db_session)

    owner_notification = await service.create(owner.id, "Owner")
    other_notification = await service.create(other.id, "Other")

    await service.mark_read(owner_notification.id, owner.id)
    assert await service.get_unread_count(owner.id) == 0
    assert await service.get_unread_count(other.id) == 1

    changed = await service.mark_all_read(other.id)
    assert changed == 1
    assert await service.get_unread_count(other.id) == 0

    await service.delete(other_notification.id, owner.id)
    items, _ = await service.list_notifications(other.id)
    assert [item.id for item in items] == [other_notification.id]


@pytest.mark.asyncio
async def test_list_notifications_unread_only_filters_results(db_session: AsyncSession) -> None:
    user = await _create_user(db_session, "notifications-filter@example.com")
    service = NotificationService(db_session)

    unread = await service.create(user.id, "Unread")
    read = await service.create(user.id, "Read")
    await service.mark_read(read.id, user.id)

    items, unread_count = await service.list_notifications(user.id, unread_only=True)

    assert [item.id for item in items] == [unread.id]
    assert unread_count == 1
