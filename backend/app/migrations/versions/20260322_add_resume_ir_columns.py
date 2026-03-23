"""add ir_json and format_type to resume_versions

Revision ID: 20260322_add_resume_ir_columns
Revises: 20260322_add_freshness_score
Create Date: 2026-03-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260322_add_resume_ir_columns"
down_revision = "20260322_add_freshness_score"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resume_versions", sa.Column("ir_json", sa.JSON(), nullable=True))
    op.add_column(
        "resume_versions", sa.Column("format_type", sa.String(20), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("resume_versions", "format_type")
    op.drop_column("resume_versions", "ir_json")
