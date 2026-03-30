from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_operator_user, get_db
from app.source_health.schemas import SourceHealthDetail, SourceHealthResponse
from app.source_health.service import SourceHealthService

router = APIRouter(prefix="/source-health", tags=["source_health"])


@router.get("", response_model=list[SourceHealthResponse])
async def list_sources(
    user: User = Depends(get_current_operator_user),
    db: AsyncSession = Depends(get_db),
) -> list[SourceHealthResponse]:
    svc = SourceHealthService(db)
    items = await svc.list_sources()
    return [SourceHealthResponse.model_validate(s) for s in items]


@router.get("/{source_id}", response_model=SourceHealthDetail)
async def get_source_health(
    source_id: uuid.UUID,
    user: User = Depends(get_current_operator_user),
    db: AsyncSession = Depends(get_db),
) -> SourceHealthDetail:
    svc = SourceHealthService(db)
    source, logs = await svc.get_source_health(source_id)
    resp = SourceHealthDetail.model_validate(source)
    from app.source_health.schemas import SourceCheckLogResponse

    resp.recent_checks = [SourceCheckLogResponse.model_validate(lg) for lg in logs]
    return resp
