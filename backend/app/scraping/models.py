from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ScraperRun(Base):
    __tablename__ = "scraper_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="running")
    jobs_found: Mapped[int] = mapped_column(Integer, default=0)
    jobs_new: Mapped[int] = mapped_column(Integer, default=0)
    jobs_updated: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column()
    duration_seconds: Mapped[Decimal | None] = mapped_column(Numeric)


class CareerPage(Base):
    __tablename__ = "career_pages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    url: Mapped[str] = mapped_column(Text, nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(300))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    use_spider: Mapped[bool] = mapped_column(Boolean, default=False)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    last_scraped_at: Mapped[datetime | None] = mapped_column()
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ScrapeTarget(Base):
    __tablename__ = "scrape_targets"
    __table_args__ = (
        Index(
            "idx_targets_schedule",
            "priority_class",
            "next_scheduled_at",
            postgresql_where=text("enabled = TRUE AND quarantined = FALSE"),
        ),
        Index("idx_targets_ats", "ats_vendor"),
        Index("idx_targets_active", "enabled", "quarantined"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    url: Mapped[str] = mapped_column(Text, nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(300))
    company_domain: Mapped[str | None] = mapped_column(String(255))
    source_kind: Mapped[str] = mapped_column(String(50), default="career_page")
    ats_vendor: Mapped[str | None] = mapped_column(String(50))
    ats_board_token: Mapped[str | None] = mapped_column(String(255))
    start_tier: Mapped[int] = mapped_column(SmallInteger, default=1)
    max_tier: Mapped[int] = mapped_column(SmallInteger, default=3)
    priority_class: Mapped[str] = mapped_column(String(10), default="cool")
    schedule_interval_m: Mapped[int] = mapped_column(Integer, default=720)
    enabled: Mapped[bool] = mapped_column(default=True)
    quarantined: Mapped[bool] = mapped_column(default=False)
    quarantine_reason: Mapped[str | None] = mapped_column(Text)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_tier: Mapped[int | None] = mapped_column(SmallInteger)
    last_http_status: Mapped[int | None] = mapped_column(SmallInteger)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    etag: Mapped[str | None] = mapped_column(String(255))
    last_modified: Mapped[str | None] = mapped_column(String(255))
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    next_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lca_filings: Mapped[int | None] = mapped_column(Integer)
    industry: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ScrapeAttempt(Base):
    __tablename__ = "scrape_attempts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("scraper_runs.id"))
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scrape_targets.id"))
    selected_tier: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    actual_tier_used: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    scraper_name: Mapped[str] = mapped_column(String(50), nullable=False)
    parser_name: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    http_status: Mapped[int | None] = mapped_column(SmallInteger)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    retries: Mapped[int] = mapped_column(SmallInteger, default=0)
    escalations: Mapped[int] = mapped_column(SmallInteger, default=0)
    jobs_extracted: Mapped[int] = mapped_column(Integer, default=0)
    content_hash_before: Mapped[str | None] = mapped_column(String(64))
    content_hash_after: Mapped[str | None] = mapped_column(String(64))
    content_changed: Mapped[bool | None] = mapped_column()
    error_class: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    browser_used: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
