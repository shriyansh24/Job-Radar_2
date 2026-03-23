"""create dedup_feedback table

Revision ID: 20260323_create_dedup_feedback
Revises: 20260323_archetypes
Create Date: 2026-03-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260323_create_dedup_feedback"
down_revision = "20260323_archetypes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dedup_feedback",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_a_id", sa.String(64), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("job_b_id", sa.String(64), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("is_duplicate", sa.Boolean(), nullable=False),
        sa.Column("title_similarity", sa.Float(), nullable=True),
        sa.Column("company_ratio", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_dedup_feedback_pair", "dedup_feedback", ["job_a_id", "job_b_id"])
    op.create_index("idx_dedup_feedback_user", "dedup_feedback", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_dedup_feedback_user", table_name="dedup_feedback")
    op.drop_index("idx_dedup_feedback_pair", table_name="dedup_feedback")
    op.drop_table("dedup_feedback")
