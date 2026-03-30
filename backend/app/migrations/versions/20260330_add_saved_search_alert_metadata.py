"""add saved search alert metadata

Revision ID: 20260330_saved_search_alerts
Revises: 20260327_job_ats_identity
Create Date: 2026-03-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260330_saved_search_alerts"
down_revision = "20260327_job_ats_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "saved_searches",
        sa.Column("last_matched_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "saved_searches",
        sa.Column(
            "last_match_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "saved_searches",
        sa.Column("last_error", sa.Text(), nullable=True),
    )

    op.alter_column("saved_searches", "last_match_count", server_default=None)


def downgrade() -> None:
    op.drop_column("saved_searches", "last_error")
    op.drop_column("saved_searches", "last_match_count")
    op.drop_column("saved_searches", "last_matched_at")
