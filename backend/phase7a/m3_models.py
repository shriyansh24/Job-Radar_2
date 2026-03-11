"""
Module 3 — Validated Source Cache: SQLAlchemy ORM Models.

Defines the `source_registry` and `source_check_log` tables for tracking
scraper source health, quality scoring, backoff state, and check history.

These are additive tables — they do not modify any existing Phase 1-6 tables.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class SourceRegistry(Base):
    """Tracks scraper source endpoints and their health state.

    Each row represents a distinct source URL (e.g. a Greenhouse board
    endpoint for Stripe, or the SerpApi Google Jobs endpoint). The
    primary key is a deterministic SHA-256 hash of (source_type, url).

    company_id is a soft FK to the companies table (Module 1). It is
    stored as TEXT(64) with no constraint so this module can function
    independently of Module 1.
    """

    __tablename__ = "source_registry"

    # Identity
    source_id: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )
    source_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    url: Mapped[str] = mapped_column(
        String(512), nullable=False
    )
    company_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )

    # Health state machine
    health_state: Mapped[str] = mapped_column(
        String(16), nullable=False, default="unknown"
    )

    # Quality and counters
    quality_score: Mapped[int] = mapped_column(
        Integer, default=50
    )
    success_count: Mapped[int] = mapped_column(
        Integer, default=0
    )
    failure_count: Mapped[int] = mapped_column(
        Integer, default=0
    )
    consecutive_failures: Mapped[int] = mapped_column(
        Integer, default=0
    )

    # Timestamps
    last_success_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    last_check_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    next_check_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    backoff_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Performance metrics
    avg_job_yield: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    avg_response_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # Compliance and rate limiting
    robots_compliant: Mapped[bool] = mapped_column(
        Boolean, default=True
    )
    rate_limit_hits: Mapped[int] = mapped_column(
        Integer, default=0
    )

    # Manual override: NULL=auto, TRUE=force-enable, FALSE=force-disable
    manual_enabled: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_source_registry_type", "source_type"),
        Index("idx_source_registry_health", "health_state", "next_check_at"),
        Index("idx_source_registry_company", "company_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<SourceRegistry(source_id={self.source_id!r}, "
            f"source_type={self.source_type!r}, "
            f"health_state={self.health_state!r})>"
        )


class SourceCheckLog(Base):
    """Append-only log of every check (scrape, probe, health) against a source.

    Used for historical analysis, debugging, and computing rolling
    averages for the source_registry quality score.
    """

    __tablename__ = "source_check_log"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    source_id: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    check_type: Mapped[str] = mapped_column(
        String(16), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False
    )
    http_status: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    jobs_found: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )

    __table_args__ = (
        Index("idx_source_check_log_source_time", "source_id", "checked_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<SourceCheckLog(id={self.id}, source_id={self.source_id!r}, "
            f"status={self.status!r}, checked_at={self.checked_at!r})>"
        )
