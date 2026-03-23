from __future__ import annotations

import hashlib
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class FieldMappingRule(Base):
    """Learned field->semantic_key mappings per ATS provider."""

    __tablename__ = "field_mapping_rules"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ats_provider: Mapped[str] = mapped_column(String(50), index=True)
    field_label_hash: Mapped[str] = mapped_column(String(64), index=True)
    field_label: Mapped[str] = mapped_column(Text)
    semantic_key: Mapped[str] = mapped_column(String(200))
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    source: Mapped[str] = mapped_column(String(30), default="llm")
    times_seen: Mapped[int] = mapped_column(Integer, default=1)
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "ats_provider", "field_label_hash", name="uq_field_mapping_provider_hash"
        ),
    )


class ApplicationDedup(Base):
    """Tracks which jobs a user has already applied to."""

    __tablename__ = "application_dedup"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    job_id: Mapped[str] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), index=True
    )
    ats_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    application_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_application_dedup_user_job"),
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

# Minimum confidence to return a Tier 2 lookup hit
_DEFAULT_CONFIDENCE_THRESHOLD = 0.6
# Minimum times_seen before we trust a mapping
_DEFAULT_MIN_TIMES_SEEN = 3


def _label_hash(label: str) -> str:
    return hashlib.sha256(label.strip().lower().encode()).hexdigest()


class FormLearningService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # -- Field mapping --------------------------------------------------

    async def record_mapping(
        self,
        ats_provider: str,
        field_label: str,
        semantic_key: str,
        *,
        source: str = "llm",
        confidence: float = 0.8,
    ) -> FieldMappingRule:
        """Upsert a field mapping rule, incrementing times_seen on conflict."""
        lh = _label_hash(field_label)

        result = await self.db.execute(
            select(FieldMappingRule).where(
                FieldMappingRule.ats_provider == ats_provider,
                FieldMappingRule.field_label_hash == lh,
            )
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            existing.times_seen += 1
            existing.last_seen = func.now()  # type: ignore[assignment]
            # Boost confidence slightly on repeated sightings, cap at 1.0
            existing.confidence = min(1.0, existing.confidence + 0.02)
            if source == "user_confirmed":
                existing.source = source
                existing.confidence = min(1.0, existing.confidence + 0.1)
            await self.db.flush()
            return existing

        rule = FieldMappingRule(
            ats_provider=ats_provider,
            field_label_hash=lh,
            field_label=field_label,
            semantic_key=semantic_key,
            confidence=confidence,
            source=source,
            times_seen=1,
        )
        self.db.add(rule)
        await self.db.flush()
        return rule

    async def lookup_mapping(
        self,
        ats_provider: str,
        field_label: str,
        *,
        confidence_threshold: float = _DEFAULT_CONFIDENCE_THRESHOLD,
        min_times_seen: int = _DEFAULT_MIN_TIMES_SEEN,
    ) -> str | None:
        """Return semantic_key if a high-confidence mapping exists."""
        lh = _label_hash(field_label)
        result = await self.db.execute(
            select(FieldMappingRule).where(
                FieldMappingRule.ats_provider == ats_provider,
                FieldMappingRule.field_label_hash == lh,
                FieldMappingRule.confidence >= confidence_threshold,
                FieldMappingRule.times_seen >= min_times_seen,
            )
        )
        rule = result.scalar_one_or_none()
        return rule.semantic_key if rule else None

    async def list_mappings(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FieldMappingRule]:
        """List all learned mapping rules (admin view)."""
        result = await self.db.execute(
            select(FieldMappingRule)
            .order_by(FieldMappingRule.times_seen.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def delete_mapping(self, rule_id: uuid.UUID) -> bool:
        """Delete a mapping rule by ID. Returns True if found and deleted."""
        result = await self.db.execute(
            select(FieldMappingRule).where(FieldMappingRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        if rule is None:
            return False
        await self.db.delete(rule)
        await self.db.flush()
        return True

    # -- Application dedup -----------------------------------------------

    async def has_applied(self, user_id: uuid.UUID, job_id: str) -> bool:
        """Check if the user has already applied to this job."""
        result = await self.db.execute(
            select(ApplicationDedup.id).where(
                ApplicationDedup.user_id == user_id,
                ApplicationDedup.job_id == job_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def record_application(
        self,
        user_id: uuid.UUID,
        job_id: str,
        ats_provider: str | None = None,
        url: str | None = None,
    ) -> ApplicationDedup:
        """Record that a user applied to a job."""
        record = ApplicationDedup(
            user_id=user_id,
            job_id=job_id,
            ats_provider=ats_provider,
            application_url=url,
        )
        self.db.add(record)
        await self.db.flush()
        return record
