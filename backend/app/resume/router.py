from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.resume.schemas import (
    CouncilRequest,
    CouncilResponse,
    GapAnalysisRequest,
    GapAnalysisResponse,
    ResumeTailorRequest,
    ResumeTailorResponse,
    ResumeVersionResponse,
)
from app.resume.service import ResumeService

router = APIRouter(prefix="/resume", tags=["resume"])


@router.get("/versions", response_model=list[ResumeVersionResponse])
async def list_versions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ResumeVersionResponse]:
    svc = ResumeService(db)
    items = await svc.list_versions(user.id)
    return [ResumeVersionResponse.model_validate(r) for r in items]


@router.get("/versions/{resume_id}", response_model=ResumeVersionResponse)
async def get_version(
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeVersionResponse:
    svc = ResumeService(db)
    r = await svc.get_version(resume_id, user.id)
    return ResumeVersionResponse.model_validate(r)


@router.post("/upload", response_model=ResumeVersionResponse, status_code=201)
async def upload_resume(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeVersionResponse:
    content = await file.read()
    svc = ResumeService(db)
    r = await svc.upload_resume(file.filename or "upload.txt", content, user.id)
    return ResumeVersionResponse.model_validate(r)


@router.patch("/versions/{resume_id}", response_model=ResumeVersionResponse)
async def update_version(
    resume_id: uuid.UUID,
    label: str | None = None,
    is_default: bool | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeVersionResponse:
    svc = ResumeService(db)
    r = await svc.update_version(resume_id, user.id, label=label, is_default=is_default)
    return ResumeVersionResponse.model_validate(r)


@router.delete("/versions/{resume_id}", status_code=204, response_model=None)
async def delete_version(
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = ResumeService(db)
    await svc.delete_version(resume_id, user.id)


@router.post("/tailor", response_model=ResumeTailorResponse)
async def tailor_resume(
    data: ResumeTailorRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeTailorResponse:
    svc = ResumeService(db)
    result = await svc.tailor_resume(data, user.id)
    return ResumeTailorResponse(**result)


@router.post("/gap-analysis", response_model=GapAnalysisResponse)
async def gap_analysis(
    data: GapAnalysisRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GapAnalysisResponse:
    svc = ResumeService(db)
    result = await svc.analyze_gaps(data, user.id)
    return GapAnalysisResponse(**result)


@router.post("/council", response_model=CouncilResponse)
async def council_evaluate(
    data: CouncilRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CouncilResponse:
    svc = ResumeService(db)
    result = await svc.council_evaluate(data, user.id)
    return CouncilResponse(**result)
