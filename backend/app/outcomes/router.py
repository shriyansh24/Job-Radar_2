from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.outcomes.schemas import (
    CompanyInsightResponse,
    OutcomeCreate,
    OutcomeResponse,
    OutcomeUpdate,
    UserOutcomeStats,
)
from app.outcomes.service import OutcomeService

router = APIRouter(prefix="/outcomes", tags=["outcomes"])


@router.post("/{application_id}", response_model=OutcomeResponse, status_code=201)
async def record_outcome(
    application_id: uuid.UUID,
    data: OutcomeCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OutcomeResponse:
    svc = OutcomeService(db)
    outcome = await svc.record_outcome(application_id, user.id, data)
    return OutcomeResponse.model_validate(outcome)


@router.patch("/{application_id}", response_model=OutcomeResponse)
async def update_outcome(
    application_id: uuid.UUID,
    data: OutcomeUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OutcomeResponse:
    svc = OutcomeService(db)
    outcome = await svc.update_outcome(application_id, user.id, data)
    return OutcomeResponse.model_validate(outcome)


@router.get("/{application_id}", response_model=OutcomeResponse)
async def get_outcome(
    application_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OutcomeResponse:
    svc = OutcomeService(db)
    outcome = await svc.get_outcome(application_id, user.id)
    return OutcomeResponse.model_validate(outcome)


@router.get("/stats/me", response_model=UserOutcomeStats)
async def get_user_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOutcomeStats:
    svc = OutcomeService(db)
    return await svc.get_user_stats(user.id)


@router.get("/companies/{company}/insights", response_model=CompanyInsightResponse)
async def get_company_insights(
    company: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompanyInsightResponse:
    svc = OutcomeService(db)
    return await svc.get_company_insights(company, user.id)
