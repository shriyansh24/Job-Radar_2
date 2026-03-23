"""add ats dedup columns

Revision ID: 005
Revises: 20260321_db_audit_fixes
Create Date: 2026-03-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "20260321_db_audit_fixes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("ats_job_id", sa.String(200), nullable=True))
    op.add_column("jobs", sa.Column("ats_requisition_id", sa.String(100), nullable=True))
    op.add_column("jobs", sa.Column("ats_provider", sa.String(50), nullable=True))
    op.add_column("jobs", sa.Column("ats_composite_key", sa.String(64), nullable=True))

    op.create_index("idx_jobs_ats_job_id", "jobs", ["ats_job_id"])
    op.create_index("idx_jobs_ats_provider", "jobs", ["ats_provider"])
    op.create_index(
        "uq_jobs_ats_composite_key",
        "jobs",
        ["ats_composite_key"],
        unique=True,
        postgresql_where=sa.text("ats_composite_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_jobs_ats_composite_key", table_name="jobs")
    op.drop_index("idx_jobs_ats_provider", table_name="jobs")
    op.drop_index("idx_jobs_ats_job_id", table_name="jobs")

    op.drop_column("jobs", "ats_composite_key")
    op.drop_column("jobs", "ats_provider")
    op.drop_column("jobs", "ats_requisition_id")
    op.drop_column("jobs", "ats_job_id")
