from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON as JSONB  # Use JSON for SQLite compat; works on PG too
from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    job_id: Mapped[str | None] = mapped_column(
        ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True
    )
    questions: Mapped[list] = mapped_column(JSONB, nullable=False)
    answers: Mapped[list | None] = mapped_column(JSONB, default=list)
    scores: Mapped[list | None] = mapped_column(JSONB, default=list)
    overall_score: Mapped[Decimal | None] = mapped_column(Numeric)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class InterviewPrepPackage(Base):
    __tablename__ = "interview_prep_packages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    stage: Mapped[str] = mapped_column(String(30), default="general")
    prep_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
