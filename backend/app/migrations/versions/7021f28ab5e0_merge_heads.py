"""merge_heads

Revision ID: 7021f28ab5e0
Revises: 004, 20260323_networking, 20260323_archetypes, +2 more
Create Date: 2026-03-23 09:09:39.939565

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '7021f28ab5e0'
down_revision: Union[str, None] = (
    '004', '20260323_networking', '20260323_archetypes',
    '20260323_create_dedup_feedback', '20260323_form_learning',
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

__all__ = [
    "revision",
    "down_revision",
    "branch_labels",
    "depends_on",
    "upgrade",
    "downgrade",
]


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
