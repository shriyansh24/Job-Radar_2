"""db audit fixes

Revision ID: 20260321_db_audit_fixes
Revises: e5d40ea7c9db
Create Date: 2026-03-21
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260321_db_audit_fixes"
down_revision = "e5d40ea7c9db"
branch_labels = None
depends_on = None


def _replace_fk(
    table_name: str,
    constrained_columns: list[str],
    referred_table: str,
    referred_columns: list[str] | None = None,
    ondelete: str | None = None,
) -> None:
    referred_columns = referred_columns or ["id"]
    inspector = sa.inspect(op.get_bind())
    old_name = None
    for fk in inspector.get_foreign_keys(table_name):
        if (
            fk.get("constrained_columns") == constrained_columns
            and fk.get("referred_table") == referred_table
            and fk.get("referred_columns") == referred_columns
        ):
            old_name = fk.get("name")
            break

    if old_name:
        op.drop_constraint(old_name, table_name, type_="foreignkey")

    op.create_foreign_key(
        f"fk_{table_name}_{'_'.join(constrained_columns)}_{referred_table}",
        table_name,
        referred_table,
        constrained_columns,
        referred_columns,
        ondelete=ondelete,
    )


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("token_version", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.alter_column(
        "users",
        "created_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
    )
    op.alter_column(
        "users",
        "updated_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
    )

    op.alter_column(
        "jobs",
        "expires_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )

    op.add_column(
        "scrape_attempts",
        sa.Column("pages_crawled", sa.Integer(), nullable=True),
    )
    op.add_column(
        "scrape_attempts",
        sa.Column("pagination_stopped_reason", sa.String(length=100), nullable=True),
    )

    _replace_fk("auto_apply_runs", ["job_id"], "jobs", ondelete="SET NULL")
    _replace_fk("applications", ["job_id"], "jobs", ondelete="SET NULL")
    _replace_fk("cover_letters", ["job_id"], "jobs", ondelete="SET NULL")
    _replace_fk("interview_sessions", ["job_id"], "jobs", ondelete="SET NULL")


def downgrade() -> None:
    _replace_fk("interview_sessions", ["job_id"], "jobs", ondelete=None)
    _replace_fk("cover_letters", ["job_id"], "jobs", ondelete=None)
    _replace_fk("applications", ["job_id"], "jobs", ondelete=None)
    _replace_fk("auto_apply_runs", ["job_id"], "jobs", ondelete=None)

    op.drop_column("scrape_attempts", "pagination_stopped_reason")
    op.drop_column("scrape_attempts", "pages_crawled")

    op.alter_column(
        "jobs",
        "expires_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=True,
    )

    op.alter_column(
        "users",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
    )
    op.alter_column(
        "users",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
    )
    op.drop_column("users", "token_version")
