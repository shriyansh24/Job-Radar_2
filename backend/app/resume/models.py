from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON as JSONB  # Use JSON for SQLite compat; works on PG too
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    label: Mapped[str | None] = mapped_column(String(200))
    filename: Mapped[str | None] = mapped_column(String(200))
    file_path: Mapped[str | None] = mapped_column(Text)
    parsed_text: Mapped[str | None] = mapped_column(Text)
    parsed_structured: Mapped[dict | None] = mapped_column(JSONB)
    ir_json: Mapped[dict | None] = mapped_column(JSONB)
    format_type: Mapped[str | None] = mapped_column(String(20))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TailoringSession(Base):
    __tablename__ = "tailoring_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    resume_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resume_versions.id"), nullable=False
    )
    job_id: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    stage1_result: Mapped[dict | None] = mapped_column(JSONB)
    stage2_result: Mapped[dict | None] = mapped_column(JSONB)
    proposals: Mapped[list | None] = mapped_column(JSONB)
    approvals: Mapped[list | None] = mapped_column(JSONB)
    tailored_ir: Mapped[dict | None] = mapped_column(JSONB)
    tailored_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("resume_versions.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
