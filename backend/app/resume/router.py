from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.config import settings
from app.dependencies import get_current_user, get_db
from app.enrichment.llm_client import LLMClient
from app.resume.schemas import (
    ATSValidationResult,
    CouncilRequest,
    CouncilResponse,
    GapAnalysisRequest,
    GapAnalysisResponse,
    ResumeTailorRequest,
    ResumeTailorResponse,
    ResumeVersionResponse,
    TailorApprovalRequest,
    TailorApprovalResponse,
    TailorStartRequest,
    TailorStartResponse,
    TemplateInfo,
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


# ---------------------------------------------------------------------------
# B2: 4-Stage Tailoring with User Review
# ---------------------------------------------------------------------------


@router.post("/tailor/start", response_model=TailorStartResponse, status_code=201)
async def start_tailoring(
    data: TailorStartRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TailorStartResponse:
    from app.resume.tailoring import TailoringEngine

    llm = LLMClient(api_key=settings.openrouter_api_key, model=settings.default_llm_model)
    engine = TailoringEngine(db, llm)
    session = await engine.start(data.resume_version_id, data.job_id, user.id)
    return TailorStartResponse(
        session_id=session.id,
        status=session.status,
        proposals=session.proposals or [],
        stage1_result=session.stage1_result,
        stage2_result=session.stage2_result,
    )


@router.post(
    "/tailor/{session_id}/approve",
    response_model=TailorApprovalResponse,
)
async def approve_tailoring(
    session_id: uuid.UUID,
    data: TailorApprovalRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TailorApprovalResponse:
    from app.resume.tailoring import TailoringEngine

    llm = LLMClient(api_key=settings.openrouter_api_key, model=settings.default_llm_model)
    engine = TailoringEngine(db, llm)
    session = await engine.approve(session_id, data.approvals, user.id)
    return TailorApprovalResponse(
        session_id=session.id,
        status=session.status,
        tailored_version_id=session.tailored_version_id,
        tailored_ir=session.tailored_ir,
    )


# ---------------------------------------------------------------------------
# B3: PDF Rendering
# ---------------------------------------------------------------------------


@router.get("/templates", response_model=list[TemplateInfo])
async def list_templates() -> list[TemplateInfo]:
    from app.resume.renderer import ResumeRenderer

    renderer = ResumeRenderer()
    return [TemplateInfo(**t) for t in renderer.get_templates()]


@router.get("/versions/{resume_id}/pdf")
async def render_pdf(
    resume_id: uuid.UUID,
    template: str = Query(default="professional"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    from app.resume.renderer import ResumeRenderer

    svc = ResumeService(db)
    version = await svc.get_version(resume_id, user.id)
    ir = version.ir_json
    if not ir:
        from app.shared.errors import ValidationError

        raise ValidationError("Resume has no IR data for rendering")

    renderer = ResumeRenderer()
    pdf_bytes = renderer.render_pdf(ir, template_id=template)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="resume_{resume_id}.pdf"'},
    )


# ---------------------------------------------------------------------------
# B4: ATS Validation
# ---------------------------------------------------------------------------


@router.post("/versions/{resume_id}/validate", response_model=ATSValidationResult)
async def validate_ats(
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ATSValidationResult:
    from app.resume.validator import ATSValidator

    svc = ResumeService(db)
    version = await svc.get_version(resume_id, user.id)
    ir = version.ir_json
    if not ir:
        from app.shared.errors import ValidationError

        raise ValidationError("Resume has no IR data for validation")

    validator = ATSValidator()
    return validator.validate(ir)


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
