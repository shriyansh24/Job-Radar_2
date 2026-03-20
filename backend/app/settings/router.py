from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.settings.schemas import (
    AppSettingsResponse,
    AppSettingsUpdate,
    SavedSearchCreate,
    SavedSearchResponse,
)
from app.settings.service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/searches", response_model=list[SavedSearchResponse])
async def list_saved_searches(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SavedSearchResponse]:
    svc = SettingsService(db)
    items = await svc.list_saved_searches(user.id)
    return [SavedSearchResponse.model_validate(s) for s in items]


@router.post("/searches", response_model=SavedSearchResponse, status_code=201)
async def create_saved_search(
    data: SavedSearchCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedSearchResponse:
    svc = SettingsService(db)
    s = await svc.create_saved_search(data, user.id)
    return SavedSearchResponse.model_validate(s)


@router.delete("/searches/{search_id}", status_code=204, response_model=None)
async def delete_saved_search(
    search_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = SettingsService(db)
    await svc.delete_saved_search(search_id, user.id)


@router.get("/app", response_model=AppSettingsResponse)
async def get_settings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AppSettingsResponse:
    svc = SettingsService(db)
    result = await svc.get_settings(user.id)
    return AppSettingsResponse(**result)


@router.patch("/app", response_model=AppSettingsResponse)
async def update_settings(
    data: AppSettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AppSettingsResponse:
    svc = SettingsService(db)
    result = await svc.update_settings(data, user.id)
    return AppSettingsResponse(**result)
