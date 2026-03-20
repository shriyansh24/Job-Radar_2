from __future__ import annotations

import uuid

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.models import Notification

logger = structlog.get_logger()


class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_notifications(
        self, user_id: uuid.UUID, *, unread_only: bool = False, limit: int = 50
    ) -> tuple[list[Notification], int]:
        """Return notifications and unread count for user."""
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        if unread_only:
            query = query.where(Notification.read == False)  # noqa: E712

        result = await self.db.scalars(query)
        items = list(result.all())

        unread_count = await self._unread_count(user_id)
        return items, unread_count

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        return await self._unread_count(user_id)

    async def mark_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> None:
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id, Notification.user_id == user_id)
            .values(read=True)
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.read == False)  # noqa: E712
            .values(read=True)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount  # type: ignore[return-value]

    async def delete(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> None:
        query = select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user_id
        )
        notif = await self.db.scalar(query)
        if notif:
            await self.db.delete(notif)
            await self.db.commit()

    async def create(
        self,
        user_id: uuid.UUID,
        title: str,
        body: str | None = None,
        notification_type: str | None = None,
        link: str | None = None,
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            title=title,
            body=body,
            notification_type=notification_type,
            link=link,
        )
        self.db.add(notif)
        await self.db.commit()
        await self.db.refresh(notif)
        logger.info("notification.created", user_id=str(user_id), title=title)
        return notif

    async def _unread_count(self, user_id: uuid.UUID) -> int:
        result = await self.db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.read == False)  # noqa: E712
        )
        return result or 0
