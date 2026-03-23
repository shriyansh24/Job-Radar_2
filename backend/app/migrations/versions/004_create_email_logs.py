"""create email_logs table

Revision ID: 004
Revises: 20260321_db_audit_fixes
Create Date: 2026-03-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "20260321_db_audit_fixes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_logs",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("sender", sa.String(500), nullable=False),
        sa.Column("subject", sa.String(1000), nullable=False),
        sa.Column("parsed_action", sa.String(30), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "matched_application_id",
            sa.Uuid(),
            sa.ForeignKey("applications.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("company_extracted", sa.String(300), nullable=True),
        sa.Column("job_title_extracted", sa.String(500), nullable=True),
        sa.Column("raw_body_hash", sa.String(64), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_logs_user_id", "email_logs", ["user_id"])
    op.create_index("ix_email_logs_processed_at", "email_logs", ["processed_at"])


def downgrade() -> None:
    op.drop_index("ix_email_logs_processed_at")
    op.drop_index("ix_email_logs_user_id")
    op.drop_table("email_logs")
