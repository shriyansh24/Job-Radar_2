"""add auto apply review items

Revision ID: 20260330_auto_apply_review
Revises: 20260330_google_integration
Create Date: 2026-03-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260330_auto_apply_review"
down_revision = "20260330_google_integration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "auto_apply_runs",
        sa.Column("review_items", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("auto_apply_runs", "review_items")
