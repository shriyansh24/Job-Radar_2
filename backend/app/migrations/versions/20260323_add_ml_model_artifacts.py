"""add ml_model_artifacts table

Revision ID: 20260323_ml_model_artifacts
Revises: 20260323_form_learning
Create Date: 2026-03-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260323_ml_model_artifacts"
down_revision = "20260323_form_learning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ml_model_artifacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("model_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("model_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("n_samples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cv_accuracy", sa.Float(), nullable=True),
        sa.Column("positive_rate", sa.Float(), nullable=True),
        sa.Column("feature_names", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ml_model_artifacts_user_model",
        "ml_model_artifacts",
        ["user_id", "model_name"],
    )


def downgrade() -> None:
    op.drop_index("ix_ml_model_artifacts_user_model", table_name="ml_model_artifacts")
    op.drop_table("ml_model_artifacts")
