"""
Module 5 — Application Tracker: SQLAlchemy ORM models.

Tables:
  - applications: User-owned application tracking state, separate from jobs.
  - application_status_history: Audit trail for status transitions.

Design principles:
  - User-owned state ALWAYS wins over scraper refreshes.
  - canonical_job_id is soft FK (no constraint) — M4 not ready yet.
  - legacy_job_id links back to existing jobs table as fallback.
  - At least one of canonical_job_id or legacy_job_id must be provided
    (enforced at service layer, not DB constraint for flexibility).
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    JSON,
    ForeignKey,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Application(Base):
    """
    User-owned application tracking record.

    Separates user workflow state (status, notes, tags, reminders) from
    system-owned scraped job data. Links to jobs via legacy_job_id (now)
    or canonical_job_id (when M4 is ready).
    """
    __tablename__ = "applications"

    # Identity
    application_id: Mapped[str] = mapped_column(
        String(64), primary_key=True,
        comment="UUID hex via generate_application_id()"
    )

    # Job linkage — soft FK for canonical (M4 not ready), real FK for legacy
    canonical_job_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=False,
        comment="FK to canonical_jobs (nullable, M4 not ready yet)"
    )
    legacy_job_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("jobs.job_id"), nullable=True, index=False,
        comment="FK to jobs.job_id (fallback link)"
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="saved",
        comment="Current status from ApplicationStatus enum"
    )
    status_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="When status was last changed"
    )

    # User-owned fields
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="User notes (rich text)"
    )
    tags: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True,
        comment='e.g. ["dream-job", "referral"]'
    )
    custom_fields: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment="User-defined key-value pairs"
    )

    # Application timeline timestamps
    applied_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="When the user applied"
    )
    applied_via: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
        comment="manual|auto|referral"
    )
    response_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="First response received"
    )
    interview_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="Scheduled interview"
    )
    offer_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="Offer received"
    )
    rejected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="Rejection received"
    )

    # Reminders and follow-ups
    follow_up_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="Next follow-up date"
    )
    reminder_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="Reminder datetime"
    )
    reminder_note: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Reminder message"
    )

    # Archive
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="Hidden from active views"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(),
        comment="Record creation time"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=func.now(),
        comment="Last update time"
    )

    __table_args__ = (
        Index("idx_applications_canonical", "canonical_job_id"),
        Index("idx_applications_legacy", "legacy_job_id"),
        Index("idx_applications_status", "status", "is_archived"),
        Index(
            "idx_applications_followup", "follow_up_at",
            sqlite_where=text("follow_up_at IS NOT NULL"),
        ),
        Index(
            "idx_applications_reminder", "reminder_at",
            sqlite_where=text("reminder_at IS NOT NULL"),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Application(id={self.application_id!r}, "
            f"status={self.status!r}, "
            f"legacy_job_id={self.legacy_job_id!r})>"
        )


class ApplicationStatusHistory(Base):
    """
    Audit trail for application status transitions.

    Every status change is recorded with the old status, new status,
    who/what triggered it, and an optional note.
    """
    __tablename__ = "application_status_history"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    application_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("applications.application_id", ondelete="CASCADE"),
        nullable=False,
    )
    old_status: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True,
        comment="NULL for creation"
    )
    new_status: Mapped[str] = mapped_column(
        String(32), nullable=False,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(),
    )
    change_source: Mapped[Optional[str]] = mapped_column(
        String(16), nullable=True,
        comment="user|system|auto — from ChangeSource enum"
    )
    note: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Optional change note"
    )

    __table_args__ = (
        Index("idx_status_history_app", "application_id", "changed_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<StatusHistory(app={self.application_id!r}, "
            f"{self.old_status!r} -> {self.new_status!r})>"
        )
