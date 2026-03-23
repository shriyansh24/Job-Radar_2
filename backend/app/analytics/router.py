from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.pattern_detector import PatternDetector
from app.analytics.schemas import (
    AllPatternsResponse,
    DailyStats,
    FunnelStageData,
    OverviewStats,
    SkillStats,
    SourceStats,
)
from app.analytics.service import AnalyticsService
from app.auth.models import User
from app.dependencies import get_current_user, get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=OverviewStats)
async def get_overview(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OverviewStats:
    svc = AnalyticsService(db)
    return await svc.get_overview(user.id)


@router.get("/daily", response_model=list[DailyStats])
async def get_daily(
    days: int = Query(30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DailyStats]:
    svc = AnalyticsService(db)
    return await svc.get_daily_stats(user.id, days)


@router.get("/sources", response_model=list[SourceStats])
async def get_sources(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SourceStats]:
    svc = AnalyticsService(db)
    return await svc.get_source_stats(user.id)


@router.get("/skills", response_model=list[SkillStats])
async def get_skills(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SkillStats]:
    svc = AnalyticsService(db)
    return await svc.get_skills_stats(user.id)


@router.get("/funnel", response_model=list[FunnelStageData])
async def get_funnel(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FunnelStageData]:
    svc = AnalyticsService(db)
    return await svc.get_funnel(user.id)


@router.get("/patterns", response_model=AllPatternsResponse)
async def get_patterns(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AllPatternsResponse:
    """Return all 6 pattern analyses aggregated into one response."""
    detector = PatternDetector(db)
    data = await detector.get_all_patterns(user.id)
    return AllPatternsResponse(**data)


@router.get("/patterns/funnel", response_model=list[FunnelStageData])
async def get_pattern_funnel(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FunnelStageData]:
    """Return just the conversion funnel from the pattern detector."""
    detector = PatternDetector(db)
    raw = await detector.conversion_funnel(user.id)
    return [FunnelStageData(stage=r["stage"], count=r["count"]) for r in raw]
