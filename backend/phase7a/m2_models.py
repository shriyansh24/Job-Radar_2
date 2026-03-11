"""Module 2 — Search Expansion Engine: SQLAlchemy models.

Tables:
    query_templates  — Stores expanded query ASTs for user intents.
    expansion_rules  — Deterministic rule-based expansion definitions.
    query_performance — Per-source query execution metrics.

All tables are additive. They do not modify or replace existing tables.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class QueryTemplate(Base):
    """Stores a query expansion AST for a user intent.

    The template_id is deterministic: SHA256(normalized_intent)[:64].
    This ensures the same intent always maps to the same template.
    """

    __tablename__ = "query_templates"

    template_id: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )
    intent: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    expansion_ast: Mapped[dict] = mapped_column(
        JSON, nullable=False
    )
    source_translations: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    strictness: Mapped[str] = mapped_column(
        String(16), default="balanced", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )


class ExpansionRule(Base):
    """A deterministic expansion rule used by the Search Expansion Engine.

    Rule types:
        synonym   — Direct title/role synonyms (priority 10).
        seniority — Seniority prefix variants (priority 20).
        skill     — Skill-to-related-skill mappings (priority 30).
        boolean   — Boolean operator templates (priority 40).
    """

    __tablename__ = "expansion_rules"

    rule_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    rule_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    input_pattern: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    output_variants: Mapped[list] = mapped_column(
        JSON, nullable=False
    )
    priority: Mapped[int] = mapped_column(
        Integer, default=100, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )


class QueryPerformance(Base):
    """Tracks per-source query execution metrics for optimization.

    Each row records a single query execution against a specific source,
    enabling performance analysis and query tuning.
    """

    __tablename__ = "query_performance"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    template_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("query_templates.template_id"),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    query_string: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    results_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    new_jobs_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    executed_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # Note: The composite index (template_id, source, executed_at DESC) is
    # created via migration m2_004 using raw SQL for SQLite DESC compatibility.
