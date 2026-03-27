from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.resume.archetypes import (
    ArchetypeCreate,
    ArchetypeResponse,
    ArchetypeService,
    AutoSelectResponse,
)
from app.resume.schemas import (
    CouncilRequest,
    CouncilResponse,
    CoverLetterGenerateRequest,
    CoverLetterGenerateResponse,
    GapAnalysisRequest,
    GapAnalysisResponse,
    ResumePreviewResponse,
    ResumeTailorRequest,
    ResumeTailorResponse,
    ResumeTemplateResponse,
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


@router.get("/templates", response_model=list[ResumeTemplateResponse])
async def list_templates(
    user: User = Depends(get_current_user),  # noqa: ARG001
    db: AsyncSession = Depends(get_db),
) -> list[ResumeTemplateResponse]:
    svc = ResumeService(db)
    return [ResumeTemplateResponse(**template) for template in await svc.list_templates()]


@router.get("/versions/{resume_id}/preview", response_model=ResumePreviewResponse)
async def preview_version(
    resume_id: uuid.UUID,
    template_id: str = Query("professional"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumePreviewResponse:
    svc = ResumeService(db)
    return ResumePreviewResponse(**(await svc.render_preview(resume_id, user.id, template_id)))


@router.get("/versions/{resume_id}/export")
async def export_version_pdf(
    resume_id: uuid.UUID,
    template_id: str = Query("professional"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    svc = ResumeService(db)
    pdf_bytes, filename = await svc.export_pdf(resume_id, user.id, template_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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


# ---------------------------------------------------------------------------
# Archetype endpoints (B5)
# ---------------------------------------------------------------------------


@router.get("/archetypes", response_model=list[ArchetypeResponse])
async def list_archetypes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ArchetypeResponse]:
    svc = ArchetypeService(db)
    items = await svc.list_archetypes(user.id)
    return [ArchetypeResponse.model_validate(a) for a in items]


@router.post("/archetypes", response_model=ArchetypeResponse, status_code=201)
async def create_archetype(
    data: ArchetypeCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArchetypeResponse:
    svc = ArchetypeService(db)
    arch = await svc.create_archetype(user.id, data)
    return ArchetypeResponse.model_validate(arch)


@router.get("/archetypes/{archetype_id}", response_model=ArchetypeResponse)
async def get_archetype(
    archetype_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArchetypeResponse:
    svc = ArchetypeService(db)
    arch = await svc.get_archetype(archetype_id, user.id)
    return ArchetypeResponse.model_validate(arch)


@router.delete("/archetypes/{archetype_id}", status_code=204, response_model=None)
async def delete_archetype(
    archetype_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = ArchetypeService(db)
    await svc.delete_archetype(user.id, archetype_id)


@router.post("/archetypes/auto-select/{job_id}", response_model=AutoSelectResponse)
async def auto_select_archetype(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AutoSelectResponse:
    svc = ArchetypeService(db)
    arch, score, reason = await svc.select_best_archetype(user.id, job_id)
    return AutoSelectResponse(
        archetype=ArchetypeResponse.model_validate(arch),
        score=score,
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Cover letter generation endpoint (B6)
# ---------------------------------------------------------------------------


@router.post("/cover-letter/generate", response_model=CoverLetterGenerateResponse)
async def generate_cover_letter_endpoint(
    data: CoverLetterGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CoverLetterGenerateResponse:
    svc = ResumeService(db)
    result = await svc.generate_cover_letter(data, user.id)
    return CoverLetterGenerateResponse(**result)
