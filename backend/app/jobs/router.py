from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.jobs.schemas import (
    JobExportRequest,
    JobListParams,
    JobResponse,
    JobUpdate,
    SemanticSearchRequest,
)
from app.jobs.service import JobService
from app.shared.pagination import PaginatedResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=PaginatedResponse[JobResponse])
async def list_jobs(
    q: str | None = None,
    source: str | None = None,
    remote_type: str | None = None,
    experience_level: str | None = None,
    job_type: str | None = None,
    min_match_score: float | None = None,
    status: str | None = None,
    is_starred: bool | None = None,
    sort_by: str = "scraped_at",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    params = JobListParams(
        q=q,
        source=source,
        remote_type=remote_type,
        experience_level=experience_level,
        job_type=job_type,
        min_match_score=min_match_score,
        status=status,
        is_starred=is_starred,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    svc = JobService(db)
    return await svc.list_jobs(params, user.id)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    svc = JobService(db)
    job = await svc.get_job(job_id, user.id)
    return JobResponse.model_validate(job)


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    data: JobUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    svc = JobService(db)
    job = await svc.update_job(job_id, data, user.id)
    return JobResponse.model_validate(job)


@router.delete("/{job_id}", status_code=204, response_model=None)
async def delete_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = JobService(db)
    await svc.delete_job(job_id, user.id)


@router.post("/search/semantic", response_model=list[JobResponse])
async def semantic_search(
    data: SemanticSearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[JobResponse]:
    svc = JobService(db)
    jobs = await svc.semantic_search(data.query, data.limit, user.id)
    return [JobResponse.model_validate(j) for j in jobs]


@router.post("/export")
async def export_jobs(
    data: JobExportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    svc = JobService(db)
    content = await svc.export_jobs(data, user.id)
    media = "text/csv" if data.format == "csv" else "application/json"
    return Response(content=content, media_type=media)
