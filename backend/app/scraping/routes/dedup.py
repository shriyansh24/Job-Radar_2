from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.scraping.dedup_feedback import (
    AccuracyStats,
    DedupFeedbackCreate,
    DedupFeedbackResponse,
    PendingReviewItem,
)

dedup_router = APIRouter()


@dedup_router.post("/dedup/feedback", status_code=201)
async def record_dedup_feedback(
    data: DedupFeedbackCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DedupFeedbackResponse:
    """Record user's correction on whether two jobs are duplicates."""
    from app.scraping.dedup_feedback import DedupFeedbackService

    service = DedupFeedbackService(db)
    feedback = await service.record_feedback(
        job_a_id=data.job_a_id,
        job_b_id=data.job_b_id,
        decision=data.decision,
        user_id=user.id,
    )
    return DedupFeedbackResponse.model_validate(feedback)


@dedup_router.get("/dedup/review")
async def get_dedup_review(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50),
) -> list[PendingReviewItem]:
    """Get job pairs the system is least confident about for human review."""
    from app.scraping.dedup_feedback import DedupFeedbackService

    service = DedupFeedbackService(db)
    return await service.get_pending_reviews(user_id=user.id, limit=limit)


@dedup_router.get("/dedup/accuracy")
async def get_dedup_accuracy(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AccuracyStats:
    """Get dedup accuracy stats based on user feedback."""
    from app.scraping.dedup_feedback import DedupFeedbackService

    service = DedupFeedbackService(db)
    return await service.get_accuracy_stats(user_id=user.id)
