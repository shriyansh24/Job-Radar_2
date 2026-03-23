"""migrate career_pages to scrape_targets and drop

Revision ID: e5d40ea7c9db
Revises: 45613a5a2f78
Create Date: 2026-03-19 19:43:43.923706

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5d40ea7c9db"
down_revision: Union[str, None] = "45613a5a2f78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Migrate career_pages data into scrape_targets with source_kind='career_page'.
    # Column mapping:
    #   career_pages.id           -> scrape_targets.id  (preserve UUID)
    #   career_pages.user_id      -> scrape_targets.user_id
    #   career_pages.url          -> scrape_targets.url
    #   career_pages.company_name -> scrape_targets.company_name
    #   career_pages.enabled      -> scrape_targets.enabled
    #   'career_page'             -> scrape_targets.source_kind
    #   career_pages.consecutive_failures -> scrape_targets.consecutive_failures
    #   career_pages.created_at   -> scrape_targets.created_at
    #   COALESCE(last_scraped_at, created_at) -> scrape_targets.updated_at
    #
    # Skipped columns (no direct mapping in ScrapeTarget):
    #   use_spider, last_error, last_scraped_at (partially mapped via updated_at)
    op.execute(
        sa.text("""
            INSERT INTO scrape_targets (
                id, user_id, url, company_name, enabled,
                source_kind, consecutive_failures,
                created_at, updated_at
            )
            SELECT
                id, user_id, url, company_name, enabled,
                'career_page', consecutive_failures,
                created_at, COALESCE(last_scraped_at, created_at)
            FROM career_pages
            ON CONFLICT (id) DO NOTHING
        """)
    )

    op.drop_table("career_pages")


def downgrade() -> None:
    # Recreate career_pages table with original schema
    op.create_table(
        "career_pages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("company_name", sa.String(300), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("use_spider", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "consecutive_failures", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("last_scraped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    # Copy career_page records back from scrape_targets
    op.execute(
        sa.text("""
            INSERT INTO career_pages (
                id, user_id, url, company_name, enabled,
                consecutive_failures, created_at
            )
            SELECT
                id, user_id, url, company_name, enabled,
                consecutive_failures, created_at
            FROM scrape_targets
            WHERE source_kind = 'career_page'
        """)
    )

    # Remove career_page records from scrape_targets since they are back in career_pages
    op.execute(
        sa.text("""
            DELETE FROM scrape_targets WHERE source_kind = 'career_page'
        """)
    )
