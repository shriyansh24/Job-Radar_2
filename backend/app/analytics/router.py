from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.predictor import MatchPredictor
from app.analytics.schemas import (
    AnalyticsPatternsResponse,
    DailyStats,
    FeatureContributionSchema,
    FunnelStageData,
    ModelStatusResponse,
    OverviewStats,
    PredictionResponse,
    SkillStats,
    SourceStats,
    TrainResponse,
)
from app.analytics.service import AnalyticsService
from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.shared.errors import NotFoundError

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


@router.get("/patterns", response_model=AnalyticsPatternsResponse)
async def get_patterns(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsPatternsResponse:
    svc = AnalyticsService(db)
    return await svc.get_patterns(user.id)


@router.post("/predict/{job_id}", response_model=PredictionResponse)
async def predict_match(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PredictionResponse:
    predictor = MatchPredictor(db)
    result = await predictor.predict(user.id, job_id)
    if result is None:
        raise NotFoundError("No trained model or job not found")
    return PredictionResponse(
        probability=result.probability,
        confidence=result.confidence,
        top_features=[
            FeatureContributionSchema(
                feature=f.feature,
                value=f.value,
                contribution=f.contribution,
            )
            for f in result.top_features
        ],
        model_version=result.model_version,
        n_training_samples=result.n_training_samples,
    )


@router.post("/train", response_model=TrainResponse)
async def train_model(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TrainResponse:
    predictor = MatchPredictor(db)
    result = await predictor.train(user.id)
    return TrainResponse(
        status=result.status,
        n_samples=result.n_samples,
        cv_accuracy=result.cv_accuracy,
        positive_rate=result.positive_rate,
        model_version=result.model_version,
    )


@router.get("/model-status", response_model=ModelStatusResponse)
async def get_model_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ModelStatusResponse:
    predictor = MatchPredictor(db)
    status = await predictor.get_model_status(user.id)
    return ModelStatusResponse(
        is_trained=status.is_trained,
        model_version=status.model_version,
        n_samples=status.n_samples,
        cv_accuracy=status.cv_accuracy,
        positive_rate=status.positive_rate,
        trained_at=status.trained_at,
        feature_names=status.feature_names,
    )
