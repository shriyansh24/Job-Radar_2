from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from sqlalchemy import JSON as JSONB  # Use JSON for SQLite compat; works on PG too

if TYPE_CHECKING:
    from app.pipeline.models import Application


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("idx_jobs_user", "user_id"),
        Index("idx_jobs_source", "source"),
        Index("idx_jobs_scraped_at", "scraped_at"),
        Index("idx_jobs_match_score", "match_score"),
        Index("idx_jobs_dedup", "dedup_hash"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(300))
    company_domain: Mapped[str | None] = mapped_column(String(200))
    company_logo_url: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(300))
    location_city: Mapped[str | None] = mapped_column(String(100))
    location_state: Mapped[str | None] = mapped_column(String(100))
    location_country: Mapped[str | None] = mapped_column(String(100))
    remote_type: Mapped[str | None] = mapped_column(String(20))
    description_raw: Mapped[str | None] = mapped_column(Text)
    description_clean: Mapped[str | None] = mapped_column(Text)
    description_markdown: Mapped[str | None] = mapped_column(Text)
    salary_min: Mapped[Decimal | None] = mapped_column(Numeric)
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric)
    salary_period: Mapped[str | None] = mapped_column(String(20))
    salary_currency: Mapped[str] = mapped_column(String(10), default="USD")
    experience_level: Mapped[str | None] = mapped_column(String(30))
    seniority_score: Mapped[int | None] = mapped_column(Integer)
    job_type: Mapped[str | None] = mapped_column(String(30))
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column()
    # Enrichment
    is_enriched: Mapped[bool] = mapped_column(Boolean, default=False)
    enriched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary_ai: Mapped[str | None] = mapped_column(Text)
    skills_required: Mapped[list | None] = mapped_column(JSONB, default=list)
    skills_nice_to_have: Mapped[list | None] = mapped_column(JSONB, default=list)
    tech_stack: Mapped[list | None] = mapped_column(JSONB, default=list)
    red_flags: Mapped[list | None] = mapped_column(JSONB, default=list)
    green_flags: Mapped[list | None] = mapped_column(JSONB, default=list)
    # Scoring
    match_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    tfidf_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    # embedding: Vector(384) — added conditionally for PostgreSQL only
    # Dedup
    dedup_hash: Mapped[str | None] = mapped_column(String(32))
    simhash: Mapped[int | None] = mapped_column(BigInteger)
    duplicate_of: Mapped[str | None] = mapped_column(String(64))
    # Status
    status: Mapped[str] = mapped_column(String(20), default="new")
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    # search_vector: TSVECTOR — PostgreSQL only
    # Lifecycle tracking
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    disappeared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    content_hash: Mapped[str | None] = mapped_column(String(64))
    previous_hash: Mapped[str | None] = mapped_column(String(64))
    seen_count: Mapped[int] = mapped_column(Integer, default=1)
    source_target_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("scrape_targets.id"))
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Relationships
    applications: Mapped[list["Application"]] = relationship("Application", back_populates="job")
