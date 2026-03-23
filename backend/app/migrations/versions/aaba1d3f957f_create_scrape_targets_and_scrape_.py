"""create scrape_targets and scrape_attempts tables

Revision ID: aaba1d3f957f
Revises: 003
Create Date: 2026-03-19 19:27:16.596405

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "aaba1d3f957f"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scrape_targets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("company_name", sa.String(length=300), nullable=True),
        sa.Column("company_domain", sa.String(length=255), nullable=True),
        sa.Column("source_kind", sa.String(length=50), nullable=False),
        sa.Column("ats_vendor", sa.String(length=50), nullable=True),
        sa.Column("ats_board_token", sa.String(length=255), nullable=True),
        sa.Column("start_tier", sa.SmallInteger(), nullable=False),
        sa.Column("max_tier", sa.SmallInteger(), nullable=False),
        sa.Column("priority_class", sa.String(length=10), nullable=False),
        sa.Column("schedule_interval_m", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("quarantined", sa.Boolean(), nullable=False),
        sa.Column("quarantine_reason", sa.Text(), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_tier", sa.SmallInteger(), nullable=True),
        sa.Column("last_http_status", sa.SmallInteger(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("etag", sa.String(length=255), nullable=True),
        sa.Column("last_modified", sa.String(length=255), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False),
        sa.Column("failure_count", sa.Integer(), nullable=False),
        sa.Column("next_scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lca_filings", sa.Integer(), nullable=True),
        sa.Column("industry", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_targets_active", "scrape_targets", ["enabled", "quarantined"], unique=False
    )
    op.create_index("idx_targets_ats", "scrape_targets", ["ats_vendor"], unique=False)
    op.create_index(
        "idx_targets_schedule",
        "scrape_targets",
        ["priority_class", "next_scheduled_at"],
        unique=False,
        postgresql_where=sa.text("enabled = TRUE AND quarantined = FALSE"),
    )

    op.create_table(
        "scrape_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("selected_tier", sa.SmallInteger(), nullable=False),
        sa.Column("actual_tier_used", sa.SmallInteger(), nullable=False),
        sa.Column("scraper_name", sa.String(length=50), nullable=False),
        sa.Column("parser_name", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("http_status", sa.SmallInteger(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("retries", sa.SmallInteger(), nullable=False),
        sa.Column("escalations", sa.SmallInteger(), nullable=False),
        sa.Column("jobs_extracted", sa.Integer(), nullable=False),
        sa.Column("content_hash_before", sa.String(length=64), nullable=True),
        sa.Column("content_hash_after", sa.String(length=64), nullable=True),
        sa.Column("content_changed", sa.Boolean(), nullable=True),
        sa.Column("error_class", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("browser_used", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["scraper_runs.id"],
        ),
        sa.ForeignKeyConstraint(
            ["target_id"],
            ["scrape_targets.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("scrape_attempts")
    op.drop_index(
        "idx_targets_schedule",
        table_name="scrape_targets",
        postgresql_where=sa.text("enabled = TRUE AND quarantined = FALSE"),
    )
    op.drop_index("idx_targets_ats", table_name="scrape_targets")
    op.drop_index("idx_targets_active", table_name="scrape_targets")
    op.drop_table("scrape_targets")
