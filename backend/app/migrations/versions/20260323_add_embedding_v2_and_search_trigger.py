"""add embedding_v2 column, HNSW index, and search_vector trigger

Revision ID: 20260323_embedding_v2_search
Revises: 20260322_add_resume_ir_columns
Create Date: 2026-03-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260323_embedding_v2_search"
down_revision = "20260322_add_resume_ir_columns"
branch_labels = None
depends_on = None


def _is_pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_pg():
        return

    from pgvector.sqlalchemy import Vector

    # 1. Add embedding_v2 (768d) alongside existing embedding (384d)
    op.add_column("jobs", sa.Column("embedding_v2", Vector(768), nullable=True))

    # 2. Create HNSW index for fast cosine similarity on v2 embeddings
    op.execute(
        "CREATE INDEX ix_jobs_embedding_v2_hnsw ON jobs "
        "USING hnsw (embedding_v2 vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )

    # 3. Create or replace the search_vector trigger for auto-updating tsvector
    op.execute("""
        CREATE OR REPLACE FUNCTION jobs_search_vector_update() RETURNS trigger AS $$
        BEGIN
          NEW.search_vector :=
            setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.company_name, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(NEW.description_clean, '')), 'C');
          RETURN NEW;
        END $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS jobs_search_vector_trigger ON jobs;
        CREATE TRIGGER jobs_search_vector_trigger
        BEFORE INSERT OR UPDATE OF title, company_name, description_clean ON jobs
        FOR EACH ROW EXECUTE FUNCTION jobs_search_vector_update();
    """)

    # 4. Backfill search_vector for existing rows
    op.execute("""
        UPDATE jobs SET search_vector =
            setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(company_name, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(description_clean, '')), 'C')
        WHERE search_vector IS NULL
    """)


def downgrade() -> None:
    if not _is_pg():
        return

    op.execute("DROP TRIGGER IF EXISTS jobs_search_vector_trigger ON jobs")
    op.execute("DROP FUNCTION IF EXISTS jobs_search_vector_update()")
    op.execute("DROP INDEX IF EXISTS ix_jobs_embedding_v2_hnsw")
    op.drop_column("jobs", "embedding_v2")
