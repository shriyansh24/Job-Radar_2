"""add google integration fields and email provenance

Revision ID: 20260330_google_integration
Revises: 20260330_saved_search_alerts
Create Date: 2026-03-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260330_google_integration"
down_revision = "20260330_saved_search_alerts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "user_integration_secrets",
        "secret_value",
        existing_type=sa.Text(),
        nullable=True,
    )
    op.add_column(
        "user_integration_secrets",
        sa.Column("auth_type", sa.String(length=20), server_default="api_key", nullable=False),
    )
    op.add_column(
        "user_integration_secrets",
        sa.Column("secret_json", sa.JSON(), nullable=True),
    )
    op.add_column(
        "user_integration_secrets",
        sa.Column("account_email", sa.String(length=320), nullable=True),
    )
    op.add_column(
        "user_integration_secrets",
        sa.Column("scopes", sa.JSON(), nullable=True),
    )
    op.add_column(
        "user_integration_secrets",
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "user_integration_secrets",
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "user_integration_secrets",
        sa.Column("last_error", sa.Text(), nullable=True),
    )

    op.add_column(
        "email_logs",
        sa.Column(
            "source_provider",
            sa.String(length=50),
            server_default="webhook",
            nullable=False,
        ),
    )
    op.add_column(
        "email_logs",
        sa.Column("source_message_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "email_logs",
        sa.Column("source_thread_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "email_logs",
        sa.Column("source_received_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("email_logs", "source_received_at")
    op.drop_column("email_logs", "source_thread_id")
    op.drop_column("email_logs", "source_message_id")
    op.drop_column("email_logs", "source_provider")

    op.drop_column("user_integration_secrets", "last_error")
    op.drop_column("user_integration_secrets", "last_synced_at")
    op.drop_column("user_integration_secrets", "last_validated_at")
    op.drop_column("user_integration_secrets", "scopes")
    op.drop_column("user_integration_secrets", "account_email")
    op.drop_column("user_integration_secrets", "secret_json")
    op.drop_column("user_integration_secrets", "auth_type")
    op.alter_column(
        "user_integration_secrets",
        "secret_value",
        existing_type=sa.Text(),
        nullable=False,
    )
