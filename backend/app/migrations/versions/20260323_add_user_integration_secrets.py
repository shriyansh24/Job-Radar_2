"""add user integration secrets table

Revision ID: 20260323_integration_secrets
Revises: 005
Create Date: 2026-03-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260323_integration_secrets"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_integration_secrets",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("secret_value", sa.Text(), nullable=False),
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
        sa.UniqueConstraint("user_id", "provider", name="uq_user_integration_provider"),
    )
    op.create_index(
        "ix_user_integration_secrets_user_id",
        "user_integration_secrets",
        ["user_id"],
    )
    op.create_index(
        "ix_user_integration_secrets_provider",
        "user_integration_secrets",
        ["provider"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_integration_secrets_provider", table_name="user_integration_secrets")
    op.drop_index("ix_user_integration_secrets_user_id", table_name="user_integration_secrets")
    op.drop_table("user_integration_secrets")
