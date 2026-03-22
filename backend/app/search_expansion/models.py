from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

from sqlalchemy import JSON as JSONB


class QueryTemplate(Base):
    """Saved search expansion templates that users can configure."""

    __tablename__ = "query_templates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    base_query: Mapped[str] = mapped_column(Text, nullable=False)
    expanded_queries: Mapped[list | None] = mapped_column(JSONB)  # list of expanded query strings
    strictness: Mapped[str] = mapped_column(String(20), default="balanced")  # loose, balanced, strict
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ExpansionRule(Base):
    """Rules for how queries should be expanded (synonym mappings, etc.)."""

    __tablename__ = "expansion_rules"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    source_term: Mapped[str] = mapped_column(String(200), nullable=False)
    expanded_terms: Mapped[list] = mapped_column(JSONB, nullable=False)
    rule_type: Mapped[str] = mapped_column(String(30), default="synonym")  # synonym, related, broader
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class QueryPerformance(Base):
    """Tracks how effective each expanded query is at finding relevant jobs."""

    __tablename__ = "query_performance"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("query_templates.id", ondelete="SET NULL"), nullable=True
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    jobs_found: Mapped[int] = mapped_column(Integer, default=0)
    relevant_jobs: Mapped[int] = mapped_column(Integer, default=0)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
