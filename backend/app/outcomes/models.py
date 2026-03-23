from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ApplicationOutcome(Base):
    __tablename__ = "application_outcomes"
    __table_args__ = (
        Index("ix_application_outcomes_user_id", "user_id"),
        Index("ix_application_outcomes_application_id", "application_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    stage_reached: Mapped[str | None] = mapped_column(String(30))
    rejection_reason: Mapped[str | None] = mapped_column(String(50))
    rejection_stage: Mapped[str | None] = mapped_column(String(30))
    days_to_response: Mapped[int | None] = mapped_column(Integer)
    offer_amount: Mapped[int | None] = mapped_column(Integer)
    offer_equity: Mapped[str | None] = mapped_column(String(200))
    offer_total_comp: Mapped[int | None] = mapped_column(Integer)
    negotiated_amount: Mapped[int | None] = mapped_column(Integer)
    final_decision: Mapped[str | None] = mapped_column(String(30))
    was_ghosted: Mapped[bool] = mapped_column(Boolean, default=False)
    referral_used: Mapped[bool] = mapped_column(Boolean, default=False)
    cover_letter_used: Mapped[bool] = mapped_column(Boolean, default=False)
    application_method: Mapped[str | None] = mapped_column(String(20))
    feedback_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CompanyInsight(Base):
    __tablename__ = "company_insights"
    __table_args__ = (
        Index("ix_company_insights_user_company", "user_id", "company_name", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    company_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    total_applications: Mapped[int] = mapped_column(Integer, default=0)
    callback_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_response_days: Mapped[float | None] = mapped_column(Float)
    ghosted_count: Mapped[int] = mapped_column(Integer, default=0)
    ghost_rate: Mapped[float] = mapped_column(Float, default=0.0)
    rejection_rate: Mapped[float] = mapped_column(Float, default=0.0)
    offer_rate: Mapped[float] = mapped_column(Float, default=0.0)
    offers_received: Mapped[int] = mapped_column(Integer, default=0)
    avg_offer_amount: Mapped[float | None] = mapped_column(Float)
    interview_difficulty: Mapped[float | None] = mapped_column(Float)
    culture_notes: Mapped[str | None] = mapped_column(Text)
    last_applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
