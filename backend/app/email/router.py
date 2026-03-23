from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.email.schemas import EmailLogResponse, EmailWebhookPayload, EmailWebhookResponse
from app.email.service import EmailService

router = APIRouter(prefix="/email", tags=["email"])


@router.post("/webhook", response_model=EmailWebhookResponse)
async def receive_email_webhook(
    payload: EmailWebhookPayload,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EmailWebhookResponse:
    svc = EmailService(db)
    return await svc.process_webhook(payload, user.id)


@router.get("/logs", response_model=list[EmailLogResponse])
async def list_email_logs(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EmailLogResponse]:
    svc = EmailService(db)
    return await svc.list_logs(user.id, limit=limit)
