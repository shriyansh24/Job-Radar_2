from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

from sqlalchemy import JSON as JSONB


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(300), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(200))
    careers_url: Mapped[str | None] = mapped_column(Text)
    logo_url: Mapped[str | None] = mapped_column(Text)
    ats_provider: Mapped[str | None] = mapped_column(String(50))
    validation_state: Mapped[str] = mapped_column(String(20), default="unverified")
    confidence_score: Mapped[Decimal] = mapped_column(Numeric, default=0)
    job_count: Mapped[int] = mapped_column(Integer, default=0)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    # Phase 7A fields
    ats_slug: Mapped[str | None] = mapped_column(String(100))
    board_urls: Mapped[list | None] = mapped_column(JSONB)
    domain_aliases: Mapped[list | None] = mapped_column(JSONB)
    last_validated_at: Mapped[datetime | None] = mapped_column()
    last_probe_at: Mapped[datetime | None] = mapped_column()
    probe_error: Mapped[str | None] = mapped_column(Text)
    manual_override: Mapped[bool] = mapped_column(Boolean, default=False)
    override_fields: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
