from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.copilot.schemas import CopilotRequest, CoverLetterCreate, CoverLetterResponse
from app.copilot.service import CopilotService
from app.dependencies import get_current_user, get_db

router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.post("/chat")
async def copilot_chat(
    data: CopilotRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = CopilotService(db)
    chunks = []
    async for chunk in svc.chat(data.message, data.context, user.id):
        chunks.append(chunk)
    return {"response": "".join(chunks)}


@router.post("/cover-letter", response_model=CoverLetterResponse, status_code=201)
async def generate_cover_letter(
    data: CoverLetterCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CoverLetterResponse:
    svc = CopilotService(db)
    cl = await svc.generate_cover_letter(
        data.job_id, data.style, user.id, template=data.template
    )
    return CoverLetterResponse.model_validate(cl)
