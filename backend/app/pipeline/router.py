from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.pipeline.schemas import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    PipelineView,
    StatusHistoryResponse,
    StatusTransition,
)
from app.pipeline.service import PipelineService
from app.shared.pagination import PaginatedResponse

router = APIRouter(prefix="/applications", tags=["pipeline"])


@router.get("", response_model=PaginatedResponse[ApplicationResponse])
async def list_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    svc = PipelineService(db)
    return await svc.list_applications(user.id, page, page_size)


@router.get("/pipeline", response_model=PipelineView)
async def get_pipeline(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PipelineView:
    svc = PipelineService(db)
    return await svc.get_pipeline_view(user.id)


@router.post("", response_model=ApplicationResponse, status_code=201)
async def create_application(
    data: ApplicationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    svc = PipelineService(db)
    app = await svc.create_application(data, user.id)
    return ApplicationResponse.model_validate(app)


@router.patch("/{app_id}", response_model=ApplicationResponse)
async def update_application(
    app_id: uuid.UUID,
    data: ApplicationUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    svc = PipelineService(db)
    app = await svc.update_application(app_id, data, user.id)
    return ApplicationResponse.model_validate(app)


@router.post("/{app_id}/transition", response_model=ApplicationResponse)
async def transition_status(
    app_id: uuid.UUID,
    data: StatusTransition,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    svc = PipelineService(db)
    app = await svc.transition_status(app_id, data, user.id)
    return ApplicationResponse.model_validate(app)


@router.get("/{app_id}/history", response_model=list[StatusHistoryResponse])
async def get_history(
    app_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[StatusHistoryResponse]:
    svc = PipelineService(db)
    items = await svc.get_history(app_id, user.id)
    return [StatusHistoryResponse.model_validate(h) for h in items]
