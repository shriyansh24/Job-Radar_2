"""Module 4 -- Canonical Jobs Pipeline: Additive migrations.

Migrations create the raw_job_sources and canonical_jobs tables with
all required indexes.

All migrations are additive-only (no drops, no renames) per PHASE7A_LOCKED.md.
"""

import logging

from sqlalchemy import text

from backend.phase7a.migration import register_migration

logger = logging.getLogger(__name__)


@register_migration("m4_001_create_raw_job_sources_table")
async def m4_001_create_raw_job_sources_table(conn) -> None:
    """Create the raw_job_sources table for individual scraper source records."""
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS raw_job_sources (
            raw_id TEXT(64) PRIMARY KEY,
            canonical_job_id TEXT(64),
            source TEXT(32) NOT NULL,
            source_job_id TEXT(128),
            source_url TEXT(512),
            source_id TEXT(64),
            raw_payload JSON,
            title_raw TEXT(500),
            company_name_raw TEXT(255),
            location_raw TEXT(255),
            salary_raw TEXT(128),
            description_raw TEXT,
            first_seen_at DATETIME NOT NULL,
            last_seen_at DATETIME NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            scrape_count INTEGER NOT NULL DEFAULT 1
        )
    """))
    logger.info("Created raw_job_sources table.")


@register_migration("m4_002_create_canonical_jobs_table")
async def m4_002_create_canonical_jobs_table(conn) -> None:
    """Create the canonical_jobs table for deduplicated, merged job records."""
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS canonical_jobs (
            canonical_job_id TEXT(64) PRIMARY KEY,
            company_id TEXT(64),
            company_name TEXT(255) NOT NULL,
            title TEXT(500) NOT NULL,
            title_normalized TEXT(500),
            location_city TEXT(128),
            location_state TEXT(64),
            location_country TEXT(64),
            location_raw TEXT(255),
            remote_type TEXT(16),
            job_type TEXT(32),
            experience_level TEXT(16),
            salary_min INTEGER,
            salary_max INTEGER,
            salary_currency TEXT(3) DEFAULT 'USD',
            description_markdown TEXT,
            apply_url TEXT(512),
            source_count INTEGER NOT NULL DEFAULT 1,
            primary_source TEXT(32),
            quality_score INTEGER,
            first_seen_at DATETIME NOT NULL,
            last_seen_at DATETIME NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            closed_at DATETIME,
            created_at DATETIME NOT NULL,
            updated_at DATETIME
        )
    """))
    logger.info("Created canonical_jobs table.")


@register_migration("m4_003_create_raw_job_sources_indexes")
async def m4_003_create_raw_job_sources_indexes(conn) -> None:
    """Create indexes on raw_job_sources for common query patterns."""
    await conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_raw_job_sources_canonical
        ON raw_job_sources (canonical_job_id)
    """))
    await conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_raw_job_sources_source
        ON raw_job_sources (source, source_job_id)
    """))
    await conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_raw_job_sources_active
        ON raw_job_sources (is_active, last_seen_at)
    """))
    logger.info("Created raw_job_sources indexes.")


@register_migration("m4_004_create_canonical_jobs_indexes")
async def m4_004_create_canonical_jobs_indexes(conn) -> None:
    """Create indexes on canonical_jobs for common query patterns."""
    await conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_canonical_jobs_company
        ON canonical_jobs (company_id)
    """))
    await conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_canonical_jobs_title_norm
        ON canonical_jobs (title_normalized, company_id)
    """))
    await conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_canonical_jobs_active
        ON canonical_jobs (is_active, last_seen_at)
    """))
    logger.info("Created canonical_jobs indexes.")
