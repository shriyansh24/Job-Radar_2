"""Canonical job deduplication models.

A CanonicalJob aggregates multiple raw job postings (from different sources)
into a single logical listing.  RawJobSource links individual scraped jobs
to their canonical parent.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from sqlalchemy import JSON as JSONB


class CanonicalJob(Base):
    __tablename__ = "canonical_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    company_name: Mapped[str] = mapped_column(String(300), nullable=False)
    company_domain: Mapped[str | None] = mapped_column(String(200))
    location: Mapped[str | None] = mapped_column(String(300))
    remote_type: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="open")  # open, closed, stale
    source_count: Mapped[int] = mapped_column(Integer, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_refreshed_at: Mapped[datetime] = mapped_column(server_default=func.now())
    is_stale: Mapped[bool] = mapped_column(Boolean, default=False)
    merged_data: Mapped[dict | None] = mapped_column(JSONB)  # best-of-all-sources aggregate
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    sources: Mapped[list[RawJobSource]] = relationship(
        back_populates="canonical_job", cascade="all, delete-orphan"
    )


class RawJobSource(Base):
    __tablename__ = "raw_job_sources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    canonical_job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("canonical_jobs.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[str | None] = mapped_column(
        ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    scraped_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    canonical_job: Mapped[CanonicalJob] = relationship(back_populates="sources")
