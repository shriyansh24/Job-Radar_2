"""add job lifecycle columns and tier counters to scraper_runs

Revision ID: 45613a5a2f78
Revises: 503ca7a300d9
Create Date: 2026-03-19 19:37:31.570058

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "45613a5a2f78"
down_revision: Union[str, None] = "503ca7a300d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
_ALEMBIC_METADATA = (revision, down_revision, branch_labels, depends_on)


def upgrade() -> None:
    # Job lifecycle tracking columns
    op.add_column("jobs", sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("disappeared_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("content_hash", sa.String(length=64), nullable=True))
    op.add_column("jobs", sa.Column("previous_hash", sa.String(length=64), nullable=True))
    op.add_column(
        "jobs", sa.Column("seen_count", sa.Integer(), nullable=False, server_default="1")
    )
    op.add_column("jobs", sa.Column("source_target_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_jobs_source_target_id",
        "jobs",
        "scrape_targets",
        ["source_target_id"],
        ["id"],
    )

    # ScraperRun tier execution counters
    op.add_column(
        "scraper_runs",
        sa.Column("targets_attempted", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "scraper_runs",
        sa.Column("targets_succeeded", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "scraper_runs",
        sa.Column("targets_failed", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "scraper_runs", sa.Column("tier_0_count", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column(
        "scraper_runs", sa.Column("tier_1_count", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column(
        "scraper_runs", sa.Column("tier_2_count", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column(
        "scraper_runs", sa.Column("tier_3_count", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column(
        "scraper_runs",
        sa.Column("tier_api_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    # ScraperRun tier execution counters
    op.drop_column("scraper_runs", "tier_api_count")
    op.drop_column("scraper_runs", "tier_3_count")
    op.drop_column("scraper_runs", "tier_2_count")
    op.drop_column("scraper_runs", "tier_1_count")
    op.drop_column("scraper_runs", "tier_0_count")
    op.drop_column("scraper_runs", "targets_failed")
    op.drop_column("scraper_runs", "targets_succeeded")
    op.drop_column("scraper_runs", "targets_attempted")

    # Job lifecycle tracking columns
    op.drop_constraint("fk_jobs_source_target_id", "jobs", type_="foreignkey")
    op.drop_column("jobs", "source_target_id")
    op.drop_column("jobs", "seen_count")
    op.drop_column("jobs", "previous_hash")
    op.drop_column("jobs", "content_hash")
    op.drop_column("jobs", "disappeared_at")
    op.drop_column("jobs", "last_seen_at")
    op.drop_column("jobs", "first_seen_at")
