"""merge v1 features — notifications, canonical_jobs, followup_reminders,
search expansion, profile enhancements

Revision ID: 003
Revises: 002
Create Date: 2026-03-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def _is_pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _jsonb_col(name: str, *, nullable: bool = True, server_default: str | None = None):
    if _is_pg():
        col_type = sa.dialects.postgresql.JSONB
    else:
        col_type = sa.JSON
    kw: dict = {"nullable": nullable}
    if server_default is not None:
        kw["server_default"] = server_default
    return sa.Column(name, col_type(), **kw)


def _uuid_pk():
    return sa.Column(
        "id",
        sa.Uuid(),
        nullable=False,
        default=sa.text("gen_random_uuid()"),
    )


def _ts(name: str, *, nullable: bool = True, has_default: bool = True):
    kw: dict = {"nullable": nullable}
    if has_default:
        kw["server_default"] = sa.func.now()
    return sa.Column(name, sa.DateTime(timezone=True), **kw)


def upgrade() -> None:
    # ---------------------------------------------------------------
    # NEW TABLE: notifications
    # ---------------------------------------------------------------
    op.create_table(
        "notifications",
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("notification_type", sa.String(50), nullable=True),
        sa.Column("link", sa.Text(), nullable=True),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])

    # ---------------------------------------------------------------
    # NEW TABLE: canonical_jobs
    # ---------------------------------------------------------------
    op.create_table(
        "canonical_jobs",
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("company_name", sa.String(300), nullable=False),
        sa.Column("company_domain", sa.String(200), nullable=True),
        sa.Column("location", sa.String(300), nullable=True),
        sa.Column("remote_type", sa.String(30), nullable=True),
        sa.Column("status", sa.String(30), server_default="open", nullable=False),
        sa.Column("source_count", sa.Integer(), server_default="1", nullable=False),
        _ts("first_seen_at"),
        _ts("last_refreshed_at"),
        sa.Column("is_stale", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        _jsonb_col("merged_data"),
        _ts("created_at"),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_canonical_jobs_user_id", "canonical_jobs", ["user_id"])

    # ---------------------------------------------------------------
    # NEW TABLE: raw_job_sources
    # ---------------------------------------------------------------
    op.create_table(
        "raw_job_sources",
        _uuid_pk(),
        sa.Column(
            "canonical_job_id",
            sa.Uuid(),
            sa.ForeignKey("canonical_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            sa.String(64),
            sa.ForeignKey("jobs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        _ts("scraped_at", has_default=False),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_raw_job_sources_canonical_job_id", "raw_job_sources", ["canonical_job_id"])

    # ---------------------------------------------------------------
    # NEW TABLE: followup_reminders
    # ---------------------------------------------------------------
    op.create_table(
        "followup_reminders",
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "application_id",
            sa.Uuid(),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reminder_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reminder_note", sa.Text(), nullable=True),
        sa.Column("is_sent", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_followup_reminders_user_id", "followup_reminders", ["user_id"])
    op.create_index(
        "ix_followup_reminders_application_id", "followup_reminders", ["application_id"]
    )

    # ---------------------------------------------------------------
    # NEW TABLE: query_templates
    # ---------------------------------------------------------------
    op.create_table(
        "query_templates",
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("base_query", sa.Text(), nullable=False),
        _jsonb_col("expanded_queries"),
        sa.Column("strictness", sa.String(20), server_default="balanced", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        _ts("created_at"),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_query_templates_user_id", "query_templates", ["user_id"])

    # ---------------------------------------------------------------
    # NEW TABLE: expansion_rules
    # ---------------------------------------------------------------
    op.create_table(
        "expansion_rules",
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("source_term", sa.String(200), nullable=False),
        _jsonb_col("expanded_terms", nullable=False),
        sa.Column("rule_type", sa.String(30), server_default="synonym", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_expansion_rules_user_id", "expansion_rules", ["user_id"])

    # ---------------------------------------------------------------
    # NEW TABLE: query_performance
    # ---------------------------------------------------------------
    op.create_table(
        "query_performance",
        _uuid_pk(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "template_id",
            sa.Uuid(),
            sa.ForeignKey("query_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("jobs_found", sa.Integer(), server_default="0", nullable=False),
        sa.Column("relevant_jobs", sa.Integer(), server_default="0", nullable=False),
        _ts("executed_at"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_query_performance_user_id", "query_performance", ["user_id"])

    # ---------------------------------------------------------------
    # ALTER TABLE: companies — add Phase 7A columns
    # ---------------------------------------------------------------
    with op.batch_alter_table("companies") as batch_op:
        batch_op.add_column(sa.Column("ats_slug", sa.String(100), nullable=True))
        batch_op.add_column(_jsonb_col("board_urls"))
        batch_op.add_column(_jsonb_col("domain_aliases"))
        batch_op.add_column(
            sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("last_probe_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("probe_error", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("manual_override", sa.Boolean(), server_default=sa.text("false"))
        )
        batch_op.add_column(_jsonb_col("override_fields"))

    # ---------------------------------------------------------------
    # ALTER TABLE: source_registry — add Phase 7A columns
    # ---------------------------------------------------------------
    with op.batch_alter_table("source_registry") as batch_op:
        batch_op.add_column(sa.Column("source_type", sa.String(30), nullable=True))
        batch_op.add_column(_jsonb_col("config"))
        batch_op.add_column(sa.Column("backoff_multiplier", sa.Float(), server_default="1.0"))

    # ---------------------------------------------------------------
    # ALTER TABLE: user_profiles — add v1 extended fields
    # ---------------------------------------------------------------
    with op.batch_alter_table("user_profiles") as batch_op:
        batch_op.add_column(sa.Column("address", sa.String(300), nullable=True))
        batch_op.add_column(sa.Column("city", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("state", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("zip_code", sa.String(20), nullable=True))
        batch_op.add_column(sa.Column("country", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("requires_sponsorship", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("notice_period", sa.String(100), nullable=True))
        batch_op.add_column(
            sa.Column("available_start", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("current_title", sa.String(200), nullable=True))
        batch_op.add_column(sa.Column("current_company", sa.String(200), nullable=True))
        batch_op.add_column(sa.Column("graduation_year", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("highest_degree", sa.String(100), nullable=True))

    # ---------------------------------------------------------------
    # ALTER TABLE: saved_searches — add last_checked_at
    # ---------------------------------------------------------------
    with op.batch_alter_table("saved_searches") as batch_op:
        batch_op.add_column(
            sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True)
        )


def downgrade() -> None:
    # Drop new columns
    with op.batch_alter_table("saved_searches") as batch_op:
        batch_op.drop_column("last_checked_at")

    with op.batch_alter_table("user_profiles") as batch_op:
        for col in [
            "address",
            "city",
            "state",
            "zip_code",
            "country",
            "requires_sponsorship",
            "notice_period",
            "available_start",
            "current_title",
            "current_company",
            "graduation_year",
            "highest_degree",
        ]:
            batch_op.drop_column(col)

    with op.batch_alter_table("source_registry") as batch_op:
        batch_op.drop_column("backoff_multiplier")
        batch_op.drop_column("config")
        batch_op.drop_column("source_type")

    with op.batch_alter_table("companies") as batch_op:
        for col in [
            "ats_slug",
            "board_urls",
            "domain_aliases",
            "last_validated_at",
            "last_probe_at",
            "probe_error",
            "manual_override",
            "override_fields",
        ]:
            batch_op.drop_column(col)

    # Drop new tables (reverse order of creation)
    op.drop_table("query_performance")
    op.drop_table("expansion_rules")
    op.drop_table("query_templates")
    op.drop_table("followup_reminders")
    op.drop_table("raw_job_sources")
    op.drop_table("canonical_jobs")
    op.drop_table("notifications")
