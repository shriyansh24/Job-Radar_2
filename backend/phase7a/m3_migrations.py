"""
Module 3 — Validated Source Cache: Database Migrations.

Additive-only migrations for the source_registry and source_check_log tables.
All statements use IF NOT EXISTS guards for idempotency.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from backend.phase7a.migration import register_migration


@register_migration("m3_001_create_source_registry_table")
async def create_source_registry_table(conn: AsyncConnection) -> None:
    """Create the source_registry table and its indexes."""
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS source_registry (
            source_id       TEXT(64) PRIMARY KEY,
            source_type     TEXT(32) NOT NULL,
            url             TEXT(512) NOT NULL,
            company_id      TEXT(64),
            health_state    TEXT(16) NOT NULL DEFAULT 'unknown',
            quality_score   INTEGER DEFAULT 50,
            success_count   INTEGER DEFAULT 0,
            failure_count   INTEGER DEFAULT 0,
            consecutive_failures INTEGER DEFAULT 0,
            last_success_at DATETIME,
            last_failure_at DATETIME,
            last_check_at   DATETIME,
            next_check_at   DATETIME,
            backoff_until   DATETIME,
            avg_job_yield   REAL,
            avg_response_time_ms INTEGER,
            robots_compliant BOOLEAN DEFAULT 1,
            rate_limit_hits  INTEGER DEFAULT 0,
            manual_enabled   BOOLEAN,
            created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at       DATETIME
        )
    """))

    # Indexes
    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_source_registry_type "
        "ON source_registry (source_type)"
    ))
    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_source_registry_health "
        "ON source_registry (health_state, next_check_at)"
    ))
    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_source_registry_company "
        "ON source_registry (company_id)"
    ))


@register_migration("m3_002_create_source_check_log_table")
async def create_source_check_log_table(conn: AsyncConnection) -> None:
    """Create the source_check_log table and its index."""
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS source_check_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id       TEXT(64) NOT NULL REFERENCES source_registry(source_id),
            check_type      TEXT(16) NOT NULL,
            status          TEXT(16) NOT NULL,
            http_status     INTEGER,
            jobs_found      INTEGER,
            duration_ms     INTEGER,
            error_message   TEXT,
            checked_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))

    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_source_check_log_source_time "
        "ON source_check_log (source_id, checked_at DESC)"
    ))
