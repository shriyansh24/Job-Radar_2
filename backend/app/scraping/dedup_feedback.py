from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal, cast

import structlog
from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.shared.errors import NotFoundError

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# SQLAlchemy model
# ---------------------------------------------------------------------------


class DedupFeedback(Base):
    __tablename__ = "dedup_feedback"
    __table_args__ = (
        Index("idx_dedup_feedback_pair", "job_a_id", "job_b_id"),
        Index("idx_dedup_feedback_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_a_id: Mapped[str] = mapped_column(String(64), ForeignKey("jobs.id"), nullable=False)
    job_b_id: Mapped[str] = mapped_column(String(64), ForeignKey("jobs.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, nullable=False)
    title_similarity: Mapped[float | None] = mapped_column(Float)
    company_ratio: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class DedupFeedbackCreate(BaseModel):
    job_a_id: str
    job_b_id: str
    decision: Literal["same", "different"]


class DedupFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_a_id: str
    job_b_id: str
    is_duplicate: bool
    title_similarity: float | None = None
    company_ratio: float | None = None
    created_at: datetime


class PendingReviewItem(BaseModel):
    job_a_id: str
    job_b_id: str
    title_similarity: float
    company_ratio: float
    confidence: float


class AccuracyStats(BaseModel):
    total_feedback: int
    confirmed_duplicates: int
    confirmed_different: int
    system_precision: float | None = None
    system_recall: float | None = None
    suggested_thresholds: dict[str, float] | None = None


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class DedupFeedbackService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def record_feedback(
        self,
        job_a_id: str,
        job_b_id: str,
        decision: Literal["same", "different"],
        user_id: uuid.UUID,
    ) -> DedupFeedback:
        # Canonical ordering so (a, b) and (b, a) are the same pair
        a_id, b_id = sorted([job_a_id, job_b_id])
        is_dup = decision == "same"

        # Compute similarity features for the pair
        title_sim, comp_ratio = await self._compute_pair_features(
            a_id,
            b_id,
            user_id=user_id,
        )

        feedback = DedupFeedback(
            job_a_id=a_id,
            job_b_id=b_id,
            user_id=user_id,
            is_duplicate=is_dup,
            title_similarity=title_sim,
            company_ratio=comp_ratio,
        )
        self._db.add(feedback)
        await self._db.commit()
        await self._db.refresh(feedback)

        logger.info(
            "dedup_feedback_recorded",
            job_a_id=a_id,
            job_b_id=b_id,
            decision=decision,
        )
        return feedback

    async def get_pending_reviews(
        self,
        *,
        user_id: uuid.UUID,
        limit: int = 10,
    ) -> list[PendingReviewItem]:
        """Return pairs that the system is least confident about.

        Confidence is proxied by title_similarity being in the ambiguous range
        (0.4 - 0.8) where the system is unsure whether jobs are duplicates.
        Pairs already reviewed are excluded.
        """
        from app.jobs.models import Job

        # Get jobs that share company names (potential near-dupes)
        stmt = (
            select(Job.id, Job.title, Job.company_name)
            .where(
                Job.user_id == user_id,
                Job.title.isnot(None),
                Job.company_name.isnot(None),
            )
            .order_by(Job.created_at.desc())
            .limit(200)
        )
        result = await self._db.execute(stmt)
        jobs = result.all()

        if len(jobs) < 2:
            return []

        # Find already-reviewed pairs
        reviewed_stmt = select(DedupFeedback.job_a_id, DedupFeedback.job_b_id).where(
            DedupFeedback.user_id == user_id
        )
        reviewed_result = await self._db.execute(reviewed_stmt)
        reviewed_pairs: set[tuple[str, str]] = {
            (str(r[0]), str(r[1])) for r in reviewed_result.all()
        }

        candidates: list[PendingReviewItem] = []

        for i in range(len(jobs)):
            for j in range(i + 1, len(jobs)):
                a_id, a_title, a_company = str(jobs[i][0]), jobs[i][1], jobs[i][2]
                b_id, b_title, b_company = str(jobs[j][0]), jobs[j][1], jobs[j][2]

                pair_key = tuple(sorted([a_id, b_id]))
                if pair_key in reviewed_pairs:
                    continue

                # Compute similarity
                title_sim = _string_similarity(a_title, b_title)
                comp_ratio = _string_similarity(a_company, b_company)

                # Only include ambiguous pairs (similarity between 0.3 and 0.85)
                combined = (title_sim + comp_ratio) / 2.0
                if 0.3 <= combined <= 0.85:
                    confidence = abs(combined - 0.5) / 0.5  # 0 = most uncertain
                    candidates.append(
                        PendingReviewItem(
                            job_a_id=a_id,
                            job_b_id=b_id,
                            title_similarity=round(title_sim, 4),
                            company_ratio=round(comp_ratio, 4),
                            confidence=round(confidence, 4),
                        )
                    )

                if len(candidates) >= limit * 5:
                    break
            if len(candidates) >= limit * 5:
                break

        # Sort by confidence ascending (least confident first)
        candidates.sort(key=lambda c: c.confidence)
        return candidates[:limit]

    async def adjust_thresholds(self, *, user_id: uuid.UUID) -> dict[str, object]:
        """Analyze feedback to suggest threshold adjustments.

        If users frequently say 'different' for pairs the system marked as dupes
        (high similarity), the threshold should be raised. Vice versa.
        """
        result = await self._db.execute(
            select(DedupFeedback).where(DedupFeedback.user_id == user_id)
        )
        rows = result.scalars().all()

        if len(rows) < 10:
            return {
                "status": "insufficient_data",
                "count": len(rows),
                "message": "Need at least 10 feedback entries to suggest adjustments",
            }

        # Separate confirmed dupes from confirmed different
        dupes = [r for r in rows if r.is_duplicate]
        diffs = [r for r in rows if not r.is_duplicate]

        # Compute average similarity for each group
        avg_dup_title = (
            sum(r.title_similarity for r in dupes if r.title_similarity is not None)
            / max(len([r for r in dupes if r.title_similarity is not None]), 1)
        )
        avg_diff_title = (
            sum(r.title_similarity for r in diffs if r.title_similarity is not None)
            / max(len([r for r in diffs if r.title_similarity is not None]), 1)
        )

        # Suggested threshold is midpoint between average dup and average diff similarity
        if dupes and diffs:
            suggested_title_threshold = round((avg_dup_title + avg_diff_title) / 2, 4)
        else:
            suggested_title_threshold = 0.85  # Default

        return {
            "status": "ok",
            "count": len(rows),
            "confirmed_duplicates": len(dupes),
            "confirmed_different": len(diffs),
            "avg_dup_title_similarity": round(avg_dup_title, 4),
            "avg_diff_title_similarity": round(avg_diff_title, 4),
            "suggested_thresholds": {
                "title_similarity": suggested_title_threshold,
                "simhash_distance": 3,
            },
        }

    async def get_accuracy_stats(self, *, user_id: uuid.UUID) -> AccuracyStats:
        """Compute precision/recall estimates from user feedback."""
        result = await self._db.execute(
            select(DedupFeedback).where(DedupFeedback.user_id == user_id)
        )
        rows = result.scalars().all()

        total = len(rows)
        confirmed_dupes = sum(1 for r in rows if r.is_duplicate)
        confirmed_diff = total - confirmed_dupes

        # Estimate precision/recall using a simple threshold on title_similarity
        # "system positive" = title_similarity >= 0.8 (system would say duplicate)
        if total == 0:
            return AccuracyStats(
                total_feedback=0,
                confirmed_duplicates=0,
                confirmed_different=0,
            )

        system_threshold = 0.8
        true_positives = 0
        false_positives = 0
        false_negatives = 0

        for r in rows:
            sim = r.title_similarity or 0.0
            system_says_dup = sim >= system_threshold
            user_says_dup = r.is_duplicate

            if system_says_dup and user_says_dup:
                true_positives += 1
            elif system_says_dup and not user_says_dup:
                false_positives += 1
            elif not system_says_dup and user_says_dup:
                false_negatives += 1

        precision = (
            round(true_positives / (true_positives + false_positives), 4)
            if (true_positives + false_positives) > 0
            else None
        )
        recall = (
            round(true_positives / (true_positives + false_negatives), 4)
            if (true_positives + false_negatives) > 0
            else None
        )

        # Get suggested thresholds
        adjustment = await self.adjust_thresholds(user_id=user_id)
        suggested = cast(
            dict[str, float] | None,
            adjustment.get("suggested_thresholds") if isinstance(adjustment, dict) else None
        )

        return AccuracyStats(
            total_feedback=total,
            confirmed_duplicates=confirmed_dupes,
            confirmed_different=confirmed_diff,
            system_precision=precision,
            system_recall=recall,
            suggested_thresholds=suggested,
        )

    async def lookup_pair(
        self,
        job_a_id: str,
        job_b_id: str,
        *,
        user_id: uuid.UUID,
    ) -> DedupFeedback | None:
        """Look up existing feedback for a pair (order-independent)."""
        a_id, b_id = sorted([job_a_id, job_b_id])
        result = await self._db.execute(
            select(DedupFeedback).where(
                DedupFeedback.job_a_id == a_id,
                DedupFeedback.job_b_id == b_id,
                DedupFeedback.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def _compute_pair_features(
        self,
        job_a_id: str,
        job_b_id: str,
        *,
        user_id: uuid.UUID,
    ) -> tuple[float | None, float | None]:
        """Compute title similarity and company ratio for a job pair."""
        from app.jobs.models import Job

        a_result = await self._db.execute(
            select(Job).where(Job.id == job_a_id, Job.user_id == user_id)
        )
        b_result = await self._db.execute(
            select(Job).where(Job.id == job_b_id, Job.user_id == user_id)
        )
        job_a = a_result.scalar_one_or_none()
        job_b = b_result.scalar_one_or_none()

        if not job_a or not job_b:
            raise NotFoundError("One or both jobs were not found in the current workspace")

        title_a = (job_a.title or "").lower().strip()
        title_b = (job_b.title or "").lower().strip()
        comp_a = (job_a.company_name or "").lower().strip()
        comp_b = (job_b.company_name or "").lower().strip()

        title_sim = _string_similarity(title_a, title_b)
        comp_ratio = _string_similarity(comp_a, comp_b)

        return round(title_sim, 4), round(comp_ratio, 4)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _string_similarity(a: str, b: str) -> float:
    """Simple character-level similarity using SequenceMatcher."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    from difflib import SequenceMatcher

    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def check_feedback_override(
    feedback_lookup: dict[tuple[str, str], bool],
    job_a_id: str,
    job_b_id: str,
) -> bool | None:
    """Check if user feedback exists for a pair. Returns True if user said
    'same', False if 'different', None if no feedback."""
    pair = cast(tuple[str, str], tuple(sorted([job_a_id, job_b_id])))
    return feedback_lookup.get(pair)
