"""add form learning and application dedup tables

Revision ID: 20260323_form_learning
Revises: 20260321_db_audit_fixes
Create Date: 2026-03-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260323_form_learning"
down_revision = "20260321_db_audit_fixes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "field_mapping_rules",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("ats_provider", sa.String(50), nullable=False, index=True),
        sa.Column("field_label_hash", sa.String(64), nullable=False, index=True),
        sa.Column("field_label", sa.Text(), nullable=False),
        sa.Column("semantic_key", sa.String(200), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("source", sa.String(30), nullable=False, server_default="llm"),
        sa.Column("times_seen", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "last_seen",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "ats_provider", "field_label_hash", name="uq_field_mapping_provider_hash"
        ),
    )

    op.create_table(
        "application_dedup",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column(
            "job_id",
            sa.String(64),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("ats_provider", sa.String(50), nullable=True),
        sa.Column("application_url", sa.Text(), nullable=True),
        sa.Column(
            "applied_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "job_id", name="uq_application_dedup_user_job"),
    )


def downgrade() -> None:
    op.drop_table("application_dedup")
    op.drop_table("field_mapping_rules")
