"""add application_outcomes and company_insights tables

Revision ID: 20260323_add_outcome_tables
Revises: 005, 20260322_a2_normalization, 20260322_add_resume_ir_columns
Create Date: 2026-03-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260323_add_outcome_tables"
down_revision = ("005", "20260322_a2_normalization", "20260322_add_resume_ir_columns")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "application_outcomes",
        sa.Column("id", sa.Uuid(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column(
            "application_id",
            sa.Uuid(),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("stage_reached", sa.String(30), nullable=True),
        sa.Column("rejection_reason", sa.String(50), nullable=True),
        sa.Column("rejection_stage", sa.String(30), nullable=True),
        sa.Column("days_to_response", sa.Integer(), nullable=True),
        sa.Column("offer_amount", sa.Integer(), nullable=True),
        sa.Column("offer_equity", sa.String(200), nullable=True),
        sa.Column("offer_total_comp", sa.Integer(), nullable=True),
        sa.Column("negotiated_amount", sa.Integer(), nullable=True),
        sa.Column("final_decision", sa.String(30), nullable=True),
        sa.Column("was_ghosted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("referral_used", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "cover_letter_used", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("application_method", sa.String(20), nullable=True),
        sa.Column("feedback_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_application_outcomes_user_id", "application_outcomes", ["user_id"]
    )
    op.create_index(
        "ix_application_outcomes_application_id",
        "application_outcomes",
        ["application_id"],
        unique=True,
    )

    op.create_table(
        "company_insights",
        sa.Column("id", sa.Uuid(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("company_name", sa.String(200), nullable=False),
        sa.Column("total_applications", sa.Integer(), server_default="0", nullable=False),
        sa.Column("callback_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("avg_response_days", sa.Float(), nullable=True),
        sa.Column("ghosted_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("ghost_rate", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("rejection_rate", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("offer_rate", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("offers_received", sa.Integer(), server_default="0", nullable=False),
        sa.Column("avg_offer_amount", sa.Float(), nullable=True),
        sa.Column("interview_difficulty", sa.Float(), nullable=True),
        sa.Column("culture_notes", sa.Text(), nullable=True),
        sa.Column("last_applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_insights_company_name", "company_insights", ["company_name"])
    op.create_index(
        "ix_company_insights_user_company",
        "company_insights",
        ["user_id", "company_name"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("company_insights")
    op.drop_table("application_outcomes")
