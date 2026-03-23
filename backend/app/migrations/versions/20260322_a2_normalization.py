"""Feature A2: company/title normalization columns and company_aliases table

Revision ID: 20260322_a2_normalization
Revises: 20260321_db_audit_fixes
Create Date: 2026-03-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260322_a2_normalization"
down_revision = "20260321_db_audit_fixes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- normalized columns on jobs ----------------------------------------
    op.add_column("jobs", sa.Column("normalized_company", sa.String(200), nullable=True))
    op.add_column("jobs", sa.Column("normalized_title", sa.String(300), nullable=True))

    # -- company_aliases table ---------------------------------------------
    op.create_table(
        "company_aliases",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("alias", sa.String(200), nullable=False),
        sa.Column("canonical_name", sa.String(200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_company_aliases_alias", "company_aliases", ["alias"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_company_aliases_alias", table_name="company_aliases")
    op.drop_table("company_aliases")
    op.drop_column("jobs", "normalized_title")
    op.drop_column("jobs", "normalized_company")
