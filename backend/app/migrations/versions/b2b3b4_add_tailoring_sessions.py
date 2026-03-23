"""Add tailoring_sessions table for B2 4-stage tailoring

Revision ID: b2b3b4_tailor
Revises: 20260323_add_outcome_tables
Create Date: 2026-03-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "b2b3b4_tailor"
down_revision = "20260323_add_outcome_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tailoring_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "resume_version_id",
            sa.Uuid(),
            sa.ForeignKey("resume_versions.id"),
            nullable=False,
        ),
        sa.Column("job_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("stage1_result", sa.JSON(), nullable=True),
        sa.Column("stage2_result", sa.JSON(), nullable=True),
        sa.Column("proposals", sa.JSON(), nullable=True),
        sa.Column("approvals", sa.JSON(), nullable=True),
        sa.Column("tailored_ir", sa.JSON(), nullable=True),
        sa.Column(
            "tailored_version_id",
            sa.Uuid(),
            sa.ForeignKey("resume_versions.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_tailoring_sessions_user_id",
        "tailoring_sessions",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_tailoring_sessions_user_id")
    op.drop_table("tailoring_sessions")
