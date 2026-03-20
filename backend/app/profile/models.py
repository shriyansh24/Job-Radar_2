from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

from sqlalchemy import JSON as JSONB  # Use JSON for SQLite compat; works on PG too


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    full_name: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    location: Mapped[str | None] = mapped_column(String(200))
    # Resume
    resume_text: Mapped[str | None] = mapped_column(Text)
    resume_filename: Mapped[str | None] = mapped_column(String(200))
    resume_parsed_structured: Mapped[dict | None] = mapped_column(JSONB)
    # Search config
    search_queries: Mapped[list | None] = mapped_column(JSONB, default=list)
    search_locations: Mapped[list | None] = mapped_column(JSONB, default=list)
    watchlist_companies: Mapped[list | None] = mapped_column(JSONB, default=list)
    # Extended profile
    linkedin_url: Mapped[str | None] = mapped_column(Text)
    github_url: Mapped[str | None] = mapped_column(Text)
    portfolio_url: Mapped[str | None] = mapped_column(Text)
    education: Mapped[list | None] = mapped_column(JSONB, default=list)
    work_experience: Mapped[list | None] = mapped_column(JSONB, default=list)
    work_authorization: Mapped[str | None] = mapped_column(String(100))
    # v1 extended fields
    address: Mapped[str | None] = mapped_column(String(300))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    zip_code: Mapped[str | None] = mapped_column(String(20))
    country: Mapped[str | None] = mapped_column(String(100))
    requires_sponsorship: Mapped[bool | None] = mapped_column(Boolean)
    notice_period: Mapped[str | None] = mapped_column(String(100))
    available_start: Mapped[datetime | None] = mapped_column()
    current_title: Mapped[str | None] = mapped_column(String(200))
    current_company: Mapped[str | None] = mapped_column(String(200))
    graduation_year: Mapped[int | None] = mapped_column(Integer)
    highest_degree: Mapped[str | None] = mapped_column(String(100))
    preferred_job_types: Mapped[list | None] = mapped_column(JSONB, default=list)
    preferred_remote_types: Mapped[list | None] = mapped_column(JSONB, default=list)
    salary_min: Mapped[Decimal | None] = mapped_column(Numeric)
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric)
    # Answer bank
    answer_bank: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    # Settings
    theme: Mapped[str] = mapped_column(String(20), default="dark")
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_apply_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
