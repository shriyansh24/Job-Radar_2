from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.notifications.schemas import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationListResponse:
    svc = NotificationService(db)
    items, unread_count = await svc.list_notifications(
        user.id, unread_only=unread_only, limit=limit
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        unread_count=unread_count,
        total=len(items),
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UnreadCountResponse:
    svc = NotificationService(db)
    count = await svc.get_unread_count(user.id)
    return UnreadCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", status_code=204, response_model=None)
async def mark_read(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = NotificationService(db)
    await svc.mark_read(notification_id, user.id)


@router.patch("/read-all", status_code=204, response_model=None)
async def mark_all_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = NotificationService(db)
    await svc.mark_all_read(user.id)


@router.get("/digest/latest", response_model=NotificationResponse | None)
async def get_latest_digest(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse | None:
    from sqlalchemy import select

    from app.notifications.models import Notification

    query = (
        select(Notification)
        .where(
            Notification.user_id == user.id,
            Notification.notification_type == "daily_digest",
        )
        .order_by(Notification.created_at.desc())
        .limit(1)
    )
    notif = await db.scalar(query)
    if notif is None:
        return None
    return NotificationResponse.model_validate(notif)


@router.delete("/{notification_id}", status_code=204, response_model=None)
async def delete_notification(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = NotificationService(db)
    await svc.delete(notification_id, user.id)
