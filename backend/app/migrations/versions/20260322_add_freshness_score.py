"""add freshness_score to jobs

Revision ID: 20260322_add_freshness_score
Revises: 20260321_db_audit_fixes
Create Date: 2026-03-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260322_add_freshness_score"
down_revision = "20260322_a2_normalization"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("freshness_score", sa.Float(), nullable=True))
    op.execute("UPDATE jobs SET freshness_score = 0.5 WHERE freshness_score IS NULL")


def downgrade() -> None:
    op.drop_column("jobs", "freshness_score")
