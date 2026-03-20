from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.vault.schemas import VaultCoverLetterResponse, VaultResumeResponse
from app.vault.service import VaultService

router = APIRouter(prefix="/vault", tags=["vault"])


@router.get("/resumes", response_model=list[VaultResumeResponse])
async def list_resumes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[VaultResumeResponse]:
    svc = VaultService(db)
    items = await svc.list_resumes(user.id)
    return [VaultResumeResponse.model_validate(r) for r in items]


@router.get("/cover-letters", response_model=list[VaultCoverLetterResponse])
async def list_cover_letters(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[VaultCoverLetterResponse]:
    svc = VaultService(db)
    items = await svc.list_cover_letters(user.id)
    return [VaultCoverLetterResponse.model_validate(cl) for cl in items]


@router.patch("/resumes/{resume_id}", response_model=VaultResumeResponse)
async def update_resume(
    resume_id: uuid.UUID,
    label: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VaultResumeResponse:
    svc = VaultService(db)
    r = await svc.update_resume(resume_id, user.id, label=label)
    return VaultResumeResponse.model_validate(r)


@router.patch("/cover-letters/{letter_id}", response_model=VaultCoverLetterResponse)
async def update_cover_letter(
    letter_id: uuid.UUID,
    content: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VaultCoverLetterResponse:
    svc = VaultService(db)
    cl = await svc.update_cover_letter(letter_id, user.id, content=content)
    return VaultCoverLetterResponse.model_validate(cl)


@router.delete("/resumes/{resume_id}", status_code=204, response_model=None)
async def delete_resume(
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = VaultService(db)
    await svc.delete_resume(resume_id, user.id)


@router.delete("/cover-letters/{letter_id}", status_code=204, response_model=None)
async def delete_cover_letter(
    letter_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = VaultService(db)
    await svc.delete_cover_letter(letter_id, user.id)
