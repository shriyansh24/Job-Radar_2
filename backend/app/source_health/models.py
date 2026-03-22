from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from sqlalchemy import JSON as JSONB


class SourceRegistry(Base):
    __tablename__ = "source_registry"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    health_state: Mapped[str] = mapped_column(String(20), default="unknown")
    quality_score: Mapped[Decimal] = mapped_column(Numeric, default=0)
    total_jobs_found: Mapped[int] = mapped_column(Integer, default=0)
    last_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    backoff_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Phase 7A additions
    source_type: Mapped[str | None] = mapped_column(String(30))  # api, scraper, ats
    config: Mapped[dict | None] = mapped_column(JSONB)
    backoff_multiplier: Mapped[float] = mapped_column(default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    check_logs: Mapped[list[SourceCheckLog]] = relationship(back_populates="source")


class SourceCheckLog(Base):
    __tablename__ = "source_check_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_registry.id"), nullable=True
    )
    check_type: Mapped[str | None] = mapped_column(String(30))
    check_status: Mapped[str | None] = mapped_column(String(20))
    jobs_found: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    source: Mapped[SourceRegistry | None] = relationship(back_populates="check_logs")
