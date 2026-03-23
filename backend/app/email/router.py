from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.email.schemas import EmailLogResponse, EmailWebhookPayload, EmailWebhookResponse
from app.email.service import EmailService
from app.shared.errors import AuthError

router = APIRouter(prefix="/email", tags=["email"])
_optional_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


@router.post("/webhook", response_model=EmailWebhookResponse)
async def receive_email_webhook(
    request: Request,
    payload: EmailWebhookPayload,
    token: str | None = Depends(_optional_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> EmailWebhookResponse:
    svc = EmailService(db)
    try:
        user = await get_current_user(request=request, token=token, db=db)
        user_id = user.id
    except AuthError:
        if not svc.verify_webhook_signature(
            payload.timestamp,
            payload.token,
            payload.signature,
        ):
            raise AuthError("Invalid webhook signature")
        user_id = await svc.resolve_webhook_user_id(payload)

    return await svc.process_webhook(payload, user_id)


@router.get("/logs", response_model=list[EmailLogResponse])
async def list_email_logs(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EmailLogResponse]:
    svc = EmailService(db)
    return await svc.list_logs(user.id, limit=limit)
