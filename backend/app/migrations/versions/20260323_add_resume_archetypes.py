"""add resume_archetypes table (B5)

Revision ID: 20260323_archetypes
Revises: 20260323_networking
Create Date: 2026-03-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260323_archetypes"
down_revision = "20260323_networking"
branch_labels = None
depends_on = None


def _is_pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    json_type = sa.dialects.postgresql.JSONB if _is_pg() else sa.JSON

    op.create_table(
        "resume_archetypes",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_role_type", sa.String(200), nullable=True),
        sa.Column("base_ir_json", json_type(), nullable=True),
        sa.Column("emphasis_sections", json_type(), nullable=True),
        sa.Column("keyword_priorities", json_type(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_archetypes_user", "resume_archetypes", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_archetypes_user", table_name="resume_archetypes")
    op.drop_table("resume_archetypes")
