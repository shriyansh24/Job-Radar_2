"""Module 1 — Company Intelligence Registry: SQLAlchemy models.

Three new tables (additive, no existing schema changes):
  - companies: Canonical company identity with ATS metadata
  - company_sources: Which scraper sources have seen this company
  - ats_detection_log: Probe history for ATS detection

These models use SQLAlchemy 2.0 Mapped columns, consistent with backend/models.py.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    Text,
    JSON,
    Boolean,
    Integer,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Company(Base):
    """Canonical company record in the Company Intelligence Registry.

    The company_id is deterministic: SHA256(normalized_domain or normalized_name)[:64].
    Use compute_company_id() from backend.phase7a.id_utils to generate it.

    Validation state machine:
        unverified -> probing -> verified -> stale -> (re-probe)
        unverified -> probing -> invalid -> (retry after 7 days)
        Any state: manual_override=True skips automated transitions
    """

    __tablename__ = "companies"

    # Identity
    company_id: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )
    canonical_name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    domain: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True
    )
    domain_aliases: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )

    # ATS metadata
    ats_provider: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )
    ats_slug: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )
    careers_url: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )
    board_urls: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )
    logo_url: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )

    # Validation
    validation_state: Mapped[str] = mapped_column(
        String(16), nullable=False, default="unverified"
    )
    confidence_score: Mapped[int] = mapped_column(
        Integer, default=0
    )
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )
    last_probe_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )
    probe_error: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # Manual override
    manual_override: Mapped[bool] = mapped_column(
        Boolean, default=False
    )
    override_fields: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_companies_domain", "domain"),
        Index("idx_companies_canonical_name", "canonical_name"),
        Index("idx_companies_ats_provider_slug", "ats_provider", "ats_slug"),
        Index("idx_companies_validation_state", "validation_state", "last_validated_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Company(company_id='{self.company_id[:12]}...', "
            f"name='{self.canonical_name}', "
            f"domain='{self.domain}', "
            f"state='{self.validation_state}')>"
        )


class CompanySource(Base):
    """Tracks which scraper sources have seen a given company.

    Each record links a company to a specific scraper source and its
    source-specific identifier (e.g., a Greenhouse board slug).
    """

    __tablename__ = "company_sources"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    company_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("companies.company_id"),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    source_identifier: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )
    jobs_count: Mapped[int] = mapped_column(
        Integer, default=0
    )
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        nullable=False, default=func.now()
    )

    __table_args__ = (
        Index("idx_company_sources_company_id", "company_id"),
        Index("idx_company_sources_source", "source", "source_identifier"),
    )

    def __repr__(self) -> str:
        return (
            f"<CompanySource(id={self.id}, "
            f"company_id='{self.company_id[:12]}...', "
            f"source='{self.source}')>"
        )


class ATSDetectionLog(Base):
    """Audit trail for ATS detection probes.

    Each probe attempt is logged regardless of success/failure,
    enabling analysis of detection accuracy and debugging.
    """

    __tablename__ = "ats_detection_log"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    company_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("companies.company_id"),
        nullable=False,
    )
    probe_url: Mapped[str] = mapped_column(
        String(512), nullable=False
    )
    detected_provider: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )
    detection_method: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )
    confidence: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    probe_status: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    probe_duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    probed_at: Mapped[datetime] = mapped_column(
        nullable=False, default=func.now()
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    __table_args__ = (
        Index("idx_ats_detection_log_company_id", "company_id", "probed_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ATSDetectionLog(id={self.id}, "
            f"company_id='{self.company_id[:12]}...', "
            f"provider='{self.detected_provider}')>"
        )
