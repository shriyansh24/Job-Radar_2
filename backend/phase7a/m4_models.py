"""Module 4 -- Canonical Jobs Pipeline: SQLAlchemy models.

Tables:
    raw_job_sources   -- Raw job records from individual scraper sources.
    canonical_jobs    -- Deduplicated, merged canonical job records.

All tables are additive. They do not modify or replace the existing ``jobs`` table.
The existing ``jobs`` table continues to work during rollout (coexistence-first).

Soft FKs:
    - canonical_job_id in raw_job_sources references canonical_jobs (TEXT, no constraint)
    - company_id in canonical_jobs references companies (TEXT, no constraint)
    - source_id in raw_job_sources references source_registry (TEXT, no constraint)
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class RawJobSource(Base):
    """Raw job record from an individual scraper source.

    Each row represents a single sighting of a job from a single source.
    The raw_id is deterministic: SHA256(source:source_job_id)[:64] via
    ``compute_raw_job_id()``.

    A raw record may be linked to a canonical job via ``canonical_job_id``
    once the canonical matching/merge pipeline processes it.
    """

    __tablename__ = "raw_job_sources"

    # Identity
    raw_id: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )
    canonical_job_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )

    # Source metadata
    source: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    source_job_id: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )
    source_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )

    # Raw payload
    raw_payload: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )

    # Raw fields (pre-normalization)
    title_raw: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    company_name_raw: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    location_raw: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    salary_raw: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )
    description_raw: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # Lifecycle
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    scrape_count: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )


class CanonicalJob(Base):
    """Deduplicated, merged canonical job record.

    Each canonical job aggregates data from one or more raw_job_sources.
    The canonical_job_id is deterministic:
    SHA256(company_id:normalized_title:normalized_location)[:64]
    via ``compute_canonical_job_id()``.

    The ``company_id`` is a soft FK to the ``companies`` table (M1).
    No actual foreign key constraint is used to allow M4 to work
    independently of M1.
    """

    __tablename__ = "canonical_jobs"

    # Identity
    canonical_job_id: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )

    # Company (soft FK to companies table)
    company_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    company_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    # Title
    title: Mapped[str] = mapped_column(
        String(500), nullable=False
    )
    title_normalized: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )

    # Location
    location_city: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )
    location_state: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    location_country: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    location_raw: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    # Classification
    remote_type: Mapped[Optional[str]] = mapped_column(
        String(16), nullable=True
    )
    job_type: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )
    experience_level: Mapped[Optional[str]] = mapped_column(
        String(16), nullable=True
    )

    # Compensation
    salary_min: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    salary_max: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    salary_currency: Mapped[Optional[str]] = mapped_column(
        String(3), default="USD", nullable=True
    )

    # Content
    description_markdown: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    apply_url: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )

    # Provenance
    source_count: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )
    primary_source: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )
    quality_score: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # Lifecycle
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
