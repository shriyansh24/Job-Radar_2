from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.service import AdminService
from app.auth.models import User
from app.dependencies import get_current_user, get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health")
async def health(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = AdminService(db)
    return await svc.health_check()


@router.get("/diagnostics")
async def diagnostics(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = AdminService(db)
    return await svc.diagnostics()


@router.post("/reindex")
async def reindex(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = AdminService(db)
    return await svc.reindex(user.id)


@router.post("/export")
async def export_data(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    svc = AdminService(db)
    content = await svc.export_data(user.id)
    return Response(content=content, media_type="application/json")


@router.post("/import")
async def import_data(
    data: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = AdminService(db)
    return await svc.import_data(data, user.id)
