from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.canonical_jobs.schemas import (
    CanonicalJobDetailResponse,
    CanonicalJobResponse,
    RawJobSourceResponse,
)
from app.canonical_jobs.service import CanonicalJobService
from app.dependencies import get_current_user, get_db

router = APIRouter(prefix="/canonical-jobs", tags=["canonical-jobs"])


@router.get("", response_model=list[CanonicalJobResponse])
async def list_canonical_jobs(
    status: str | None = Query(None),
    stale_only: bool = Query(False),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CanonicalJobResponse]:
    svc = CanonicalJobService(db)
    items = await svc.list_canonical_jobs(
        user.id, status=status, stale_only=stale_only, limit=limit, offset=offset
    )
    return [CanonicalJobResponse.model_validate(j) for j in items]


@router.get("/stale", response_model=list[CanonicalJobResponse])
async def list_stale_jobs(
    limit: int = Query(50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CanonicalJobResponse]:
    svc = CanonicalJobService(db)
    items = await svc.list_canonical_jobs(user.id, stale_only=True, limit=limit)
    return [CanonicalJobResponse.model_validate(j) for j in items]


@router.get("/{job_id}", response_model=CanonicalJobDetailResponse)
async def get_canonical_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CanonicalJobDetailResponse:
    svc = CanonicalJobService(db)
    job = await svc.get_canonical_job(job_id, user.id)
    sources = [RawJobSourceResponse.model_validate(s) for s in job.sources]
    resp = CanonicalJobDetailResponse.model_validate(job)
    resp.sources = sources
    return resp


@router.post("/{job_id}/close", response_model=CanonicalJobResponse)
async def close_canonical_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CanonicalJobResponse:
    svc = CanonicalJobService(db)
    job = await svc.close_job(job_id, user.id)
    return CanonicalJobResponse.model_validate(job)


@router.post("/{job_id}/reactivate", response_model=CanonicalJobResponse)
async def reactivate_canonical_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CanonicalJobResponse:
    svc = CanonicalJobService(db)
    job = await svc.reactivate_job(job_id, user.id)
    return CanonicalJobResponse.model_validate(job)
