"""Multi-Resume Archetype Strategy (B5).

Supports fundamentally different resume archetypes (e.g. "ML Research",
"ML Production", "Data Science").  Each archetype stores a base IR snapshot
and emphasis / keyword configuration.  The service can auto-select the best
archetype for a given job via keyword overlap scoring.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import structlog
from sqlalchemy import JSON as JSONB
from sqlalchemy import DateTime, ForeignKey, String, Text, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.jobs.models import Job
from app.resume.models import ResumeVersion
from app.shared.errors import NotFoundError

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


class ResumeArchetype(Base):
    __tablename__ = "resume_archetypes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    target_role_type: Mapped[str | None] = mapped_column(String(200))
    base_ir_json: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    emphasis_sections: Mapped[list[str] | None] = mapped_column(JSONB)
    keyword_priorities: Mapped[list[str] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, Field  # noqa: E402


class ArchetypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    base_resume_id: uuid.UUID
    target_role: str | None = None
    description: str | None = None
    emphasis_sections: list[str] | None = None
    keyword_priorities: list[str] | None = None


class ArchetypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None = None
    target_role_type: str | None = None
    base_ir_json: dict[str, object] | None = None
    emphasis_sections: list[str] | None = None
    keyword_priorities: list[str] | None = None
    created_at: datetime


class AutoSelectResponse(BaseModel):
    archetype: ArchetypeResponse
    score: float
    reason: str


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ArchetypeService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_archetype(
        self,
        user_id: uuid.UUID,
        data: ArchetypeCreate,
    ) -> ResumeArchetype:
        resume = await self.db.scalar(
            select(ResumeVersion).where(
                ResumeVersion.id == data.base_resume_id,
                ResumeVersion.user_id == user_id,
            )
        )
        if resume is None:
            raise NotFoundError(detail=f"Resume version {data.base_resume_id} not found")

        base_ir: dict[str, Any] = {
            "text": resume.parsed_text or "",
            "structured": resume.parsed_structured or {},
        }

        archetype = ResumeArchetype(
            user_id=user_id,
            name=data.name,
            description=data.description,
            target_role_type=data.target_role,
            base_ir_json=base_ir,
            emphasis_sections=data.emphasis_sections or [],
            keyword_priorities=data.keyword_priorities or [],
        )
        self.db.add(archetype)
        await self.db.commit()
        await self.db.refresh(archetype)
        logger.info(
            "archetype.created",
            archetype_id=str(archetype.id),
            name=archetype.name,
            user_id=str(user_id),
        )
        return archetype

    async def list_archetypes(self, user_id: uuid.UUID) -> list[ResumeArchetype]:
        q = (
            select(ResumeArchetype)
            .where(ResumeArchetype.user_id == user_id)
            .order_by(ResumeArchetype.created_at.desc())
        )
        return list((await self.db.scalars(q)).all())

    async def get_archetype(
        self, archetype_id: uuid.UUID, user_id: uuid.UUID
    ) -> ResumeArchetype:
        archetype = await self.db.scalar(
            select(ResumeArchetype).where(
                ResumeArchetype.id == archetype_id,
                ResumeArchetype.user_id == user_id,
            )
        )
        if archetype is None:
            raise NotFoundError(detail=f"Archetype {archetype_id} not found")
        return archetype

    async def delete_archetype(self, user_id: uuid.UUID, archetype_id: uuid.UUID) -> None:
        result = await self.db.execute(
            delete(ResumeArchetype).where(
                ResumeArchetype.id == archetype_id,
                ResumeArchetype.user_id == user_id,
            )
        )
        rowcount = getattr(result, "rowcount", 0)
        if rowcount == 0:
            raise NotFoundError(detail=f"Archetype {archetype_id} not found")
        await self.db.commit()
        logger.info(
            "archetype.deleted",
            archetype_id=str(archetype_id),
            user_id=str(user_id),
        )

    async def select_best_archetype(
        self, user_id: uuid.UUID, job_id: str
    ) -> tuple[ResumeArchetype, float, str]:
        """Auto-select the best archetype for a job using keyword overlap scoring.

        Returns (archetype, score, reason).
        """
        job = await self.db.scalar(
            select(Job).where(Job.id == job_id, Job.user_id == user_id)
        )
        if job is None:
            raise NotFoundError(detail=f"Job {job_id} not found")

        archetypes = await self.list_archetypes(user_id)
        if not archetypes:
            raise NotFoundError(detail="No archetypes found for user")

        job_tokens = _tokenize(
            f"{job.title or ''} {job.description_clean or ''}"
        )
        job_skills = set(s.lower() for s in (job.skills_required or []))
        job_tokens |= job_skills

        best: ResumeArchetype | None = None
        best_score = -1.0
        best_reason = ""

        for arch in archetypes:
            score, reason = _score_archetype(arch, job_tokens)
            if score > best_score:
                best_score = score
                best = arch
                best_reason = reason

        assert best is not None  # we checked archetypes is non-empty
        logger.info(
            "archetype.auto_selected",
            archetype_id=str(best.id),
            name=best.name,
            score=best_score,
            job_id=job_id,
        )
        return best, best_score, best_reason


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> set[str]:
    """Simple whitespace + lowercased token set."""
    return {w.strip(".,;:!?()[]{}\"'").lower() for w in text.split() if len(w) > 2}


def _score_archetype(
    arch: ResumeArchetype, job_tokens: set[str]
) -> tuple[float, str]:
    """Score an archetype against job tokens using keyword overlap.

    Returns (score_0_to_1, human_reason).
    """
    arch_tokens: set[str] = set()

    # Add keyword priorities
    for kw in arch.keyword_priorities or []:
        arch_tokens |= _tokenize(kw)

    # Add emphasis sections
    for section in arch.emphasis_sections or []:
        arch_tokens |= _tokenize(section)

    # Add target role type
    if arch.target_role_type:
        arch_tokens |= _tokenize(arch.target_role_type)

    # Add base IR text (limited)
        ir = arch.base_ir_json or {}
        raw_ir_text = ir.get("text", "")
        ir_text = raw_ir_text if isinstance(raw_ir_text, str) else ""
        if ir_text:
            arch_tokens |= _tokenize(ir_text[:2000])

    if not arch_tokens or not job_tokens:
        return 0.0, "Insufficient data for scoring"

    overlap = arch_tokens & job_tokens
    # Jaccard-like score weighted toward recall against job tokens
    score = len(overlap) / max(len(job_tokens), 1)
    score = min(score, 1.0)

    matched_kws = [kw for kw in (arch.keyword_priorities or []) if kw.lower() in job_tokens]
    if matched_kws:
        reason = f"Matched keywords: {', '.join(matched_kws[:5])}"
    elif arch.target_role_type and arch.target_role_type.lower() in " ".join(job_tokens):
        reason = f"Target role '{arch.target_role_type}' matches job"
    else:
        reason = f"Token overlap: {len(overlap)} common terms"

    return score, reason
