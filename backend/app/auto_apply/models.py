from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON as JSONB  # Use JSON for SQLite compat; works on PG too
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AutoApplyProfile(Base):
    __tablename__ = "auto_apply_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    linkedin_url: Mapped[str | None] = mapped_column(Text)
    github_url: Mapped[str | None] = mapped_column(Text)
    portfolio_url: Mapped[str | None] = mapped_column(Text)
    cover_letter_template: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    rules: Mapped[list[AutoApplyRule]] = relationship(back_populates="profile")


class AutoApplyRule(Base):
    __tablename__ = "auto_apply_rules"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("auto_apply_profiles.id"), nullable=True
    )
    name: Mapped[str | None] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    min_match_score: Mapped[float | None] = mapped_column(Numeric)
    required_keywords: Mapped[list | None] = mapped_column(JSONB, default=list)
    excluded_keywords: Mapped[list | None] = mapped_column(JSONB, default=list)
    required_companies: Mapped[list | None] = mapped_column(JSONB, default=list)
    excluded_companies: Mapped[list | None] = mapped_column(JSONB, default=list)
    experience_levels: Mapped[list | None] = mapped_column(JSONB, default=list)
    remote_types: Mapped[list | None] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    profile: Mapped[AutoApplyProfile | None] = relationship(back_populates="rules")


class AutoApplyRun(Base):
    __tablename__ = "auto_apply_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    job_id: Mapped[str | None] = mapped_column(
        ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True
    )
    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("auto_apply_rules.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(30), default="pending")
    ats_provider: Mapped[str | None] = mapped_column(String(50))
    fields_filled: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    fields_missed: Mapped[list | None] = mapped_column(JSONB, default=list)
    screenshots: Mapped[list | None] = mapped_column(JSONB, default=list)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
