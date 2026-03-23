from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.salary.schemas import (
    OfferEvalRequest,
    OfferEvalResponse,
    SalaryBrief,
    SalaryBriefRequest,
    SalaryResearchRequest,
    SalaryResearchResponse,
)
from app.salary.service import SalaryService

router = APIRouter(prefix="/salary", tags=["salary"])


@router.post("/research", response_model=SalaryResearchResponse)
async def research_salary(
    data: SalaryResearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SalaryResearchResponse:
    svc = SalaryService(db)
    result = await svc.research_salary(data, user.id)
    return SalaryResearchResponse(**result)


@router.post("/evaluate-offer", response_model=OfferEvalResponse)
async def evaluate_offer(
    data: OfferEvalRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OfferEvalResponse:
    svc = SalaryService(db)
    result = await svc.evaluate_offer(data, user.id)
    return OfferEvalResponse(**result)


@router.post("/brief/{job_id}", response_model=SalaryBrief)
async def generate_brief(
    job_id: str,
    data: SalaryBriefRequest | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SalaryBrief:
    svc = SalaryService(db)
    return await svc.generate_brief(job_id, user.id, data)
