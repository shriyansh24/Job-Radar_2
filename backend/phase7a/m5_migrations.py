"""
Module 5 — Application Tracker: Registered migrations.

Migrations:
  m5_001_create_applications_table
    - Creates the applications table with all columns and indexes.

  m5_002_create_status_history_table
    - Creates the application_status_history table with indexes.

  m5_003_migrate_existing_applications
    - Seeds application records from existing jobs with status != 'new'.
    - Safe to run on empty jobs table (INSERT ... SELECT returns 0 rows).
    - Does NOT modify the jobs table or remove jobs.status.

All migrations are additive only. They do not drop or rename existing tables.
"""

from sqlalchemy import text

from backend.phase7a.migration import register_migration


@register_migration("m5_001_create_applications_table")
async def create_applications_table(conn) -> None:
    """Create the applications table."""
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS applications (
            application_id   TEXT(64) PRIMARY KEY,
            canonical_job_id TEXT(64),
            legacy_job_id    TEXT(64) REFERENCES jobs(job_id),
            status           TEXT(32) NOT NULL DEFAULT 'saved',
            status_changed_at DATETIME,
            notes            TEXT,
            tags             JSON,
            custom_fields    JSON,
            applied_at       DATETIME,
            applied_via      TEXT(64),
            response_at      DATETIME,
            interview_at     DATETIME,
            offer_at         DATETIME,
            rejected_at      DATETIME,
            follow_up_at     DATETIME,
            reminder_at      DATETIME,
            reminder_note    TEXT,
            is_archived      BOOLEAN NOT NULL DEFAULT 0,
            created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at       DATETIME
        )
    """))

    # Create indexes
    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_applications_canonical "
        "ON applications (canonical_job_id)"
    ))
    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_applications_legacy "
        "ON applications (legacy_job_id)"
    ))
    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_applications_status "
        "ON applications (status, is_archived)"
    ))
    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_applications_followup "
        "ON applications (follow_up_at) "
        "WHERE follow_up_at IS NOT NULL"
    ))
    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_applications_reminder "
        "ON applications (reminder_at) "
        "WHERE reminder_at IS NOT NULL"
    ))


@register_migration("m5_002_create_status_history_table")
async def create_status_history_table(conn) -> None:
    """Create the application_status_history table."""
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS application_status_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id  TEXT(64) NOT NULL
                            REFERENCES applications(application_id) ON DELETE CASCADE,
            old_status      TEXT(32),
            new_status      TEXT(32) NOT NULL,
            changed_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            change_source   TEXT(16),
            note            TEXT
        )
    """))

    # Create index
    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_status_history_app "
        "ON application_status_history (application_id, changed_at DESC)"
    ))


@register_migration("m5_003_migrate_existing_applications")
async def migrate_existing_applications(conn) -> None:
    """
    Seed application records from existing jobs with status != 'new'.

    This migration:
    - Creates an application record for each job that has been tracked
      (i.e., has a status other than 'new').
    - Uses hex(randomblob(16)) to generate unique application_ids.
    - Links via legacy_job_id (canonical_job_id is NULL, M4 not ready).
    - Copies user-owned fields: status, notes, tags, applied_at.
    - Does NOT modify or remove the original jobs table data.
    - Safe to run when jobs table has no qualifying rows (0 inserts).
    - Skips jobs that already have an application record (idempotent).
    - Safe to run when jobs table does not exist (no-op).
    """
    # Check if jobs table exists (may not in isolated module tests)
    result = await conn.execute(text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'"
    ))
    if result.fetchone() is None:
        return  # No jobs table — nothing to seed from

    await conn.execute(text("""
        INSERT INTO applications (
            application_id,
            legacy_job_id,
            status,
            notes,
            tags,
            applied_at,
            created_at,
            status_changed_at
        )
        SELECT
            hex(randomblob(16)),
            j.job_id,
            j.status,
            j.notes,
            j.tags,
            j.applied_at,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        FROM jobs j
        WHERE j.status != 'new'
          AND NOT EXISTS (
              SELECT 1 FROM applications a
              WHERE a.legacy_job_id = j.job_id
          )
    """))

    # Also seed initial status history for migrated records
    await conn.execute(text("""
        INSERT INTO application_status_history (
            application_id,
            old_status,
            new_status,
            changed_at,
            change_source,
            note
        )
        SELECT
            a.application_id,
            NULL,
            a.status,
            a.created_at,
            'system',
            'Migrated from jobs table'
        FROM applications a
        WHERE NOT EXISTS (
            SELECT 1 FROM application_status_history h
            WHERE h.application_id = a.application_id
        )
    """))
