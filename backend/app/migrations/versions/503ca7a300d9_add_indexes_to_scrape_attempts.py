"""add indexes to scrape_attempts

Revision ID: 503ca7a300d9
Revises: aaba1d3f957f
Create Date: 2026-03-19 19:33:58.666146

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '503ca7a300d9'
down_revision: Union[str, None] = 'aaba1d3f957f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('idx_attempts_run', 'scrape_attempts', ['run_id'], unique=False)
    op.create_index('idx_attempts_target', 'scrape_attempts', ['target_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_attempts_target', table_name='scrape_attempts')
    op.drop_index('idx_attempts_run', table_name='scrape_attempts')
