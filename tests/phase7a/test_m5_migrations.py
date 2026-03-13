"""
Tests for Module 5 — Application Tracker: Migrations.

Covers:
  - Migration registration in the global registry
  - m5_001: applications table creation with indexes
  - m5_002: application_status_history table creation with indexes
  - m5_003: seed migration from existing jobs
  - Idempotency: running migrations twice is safe
  - Round-trip CRUD after migration
  - Ordering
"""

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from backend.database import Base
from backend.models import Job  # noqa: F401 — needed for table creation
from backend.phase7a.migration import (
    get_registered_migrations,
    run_migrations,
)
# Importing m5_migrations triggers @register_migration decorators
import backend.phase7a.m5_migrations as m5_mig  # noqa: F401


pytestmark = pytest.mark.asyncio


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _get_migration_fn(name: str):
    """Look up a migration function by name from the registry."""
    for mig_name, fn in get_registered_migrations():
        if mig_name == name:
            return fn
    return None


async def _create_legacy_tables(conn):
    """Create only legacy pre-Phase7A tables (jobs, etc.) via selective ORM.

    This avoids creating M5 ORM tables (applications, application_status_history)
    so that migrations can create them with their own raw SQL schemas.
    """
    from backend.models import Job, SavedSearch, ScraperRun, UserProfile

    m5_tables = {"applications", "application_status_history"}
    tables_to_create = [
        t for t in Base.metadata.sorted_tables
        if t.name not in m5_tables
    ]
    def _create(sync_conn):
        Base.metadata.create_all(sync_conn, tables=tables_to_create)
    await conn.run_sync(_create)


# ------------------------------------------------------------------
# Migration registry tests
# ------------------------------------------------------------------


class TestMigrationRegistry:
    """Tests that migrations are properly registered."""

    def test_migrations_registered(self):
        """All three M5 migrations should be in the registry."""
        names = [name for name, _ in get_registered_migrations()]
        assert "m5_001_create_applications_table" in names
        assert "m5_002_create_status_history_table" in names
        assert "m5_003_migrate_existing_applications" in names

    def test_migration_ordering(self):
        """M5 migrations should be registered in order: 001 < 002 < 003."""
        names = [name for name, _ in get_registered_migrations()]
        m5_names = [n for n in names if n.startswith("m5_")]
        assert m5_names.index("m5_001_create_applications_table") < \
               m5_names.index("m5_002_create_status_history_table")
        assert m5_names.index("m5_002_create_status_history_table") < \
               m5_names.index("m5_003_migrate_existing_applications")

    def test_get_migration_by_name(self):
        """Can look up a migration function by name."""
        func = _get_migration_fn("m5_001_create_applications_table")
        assert func is not None
        assert callable(func)

    def test_get_migration_nonexistent(self):
        """Non-existent migration name returns None."""
        func = _get_migration_fn("nonexistent_migration")
        assert func is None


# ------------------------------------------------------------------
# Actual migration execution tests
# ------------------------------------------------------------------


@pytest_asyncio.fixture
async def migration_engine():
    """Separate engine for migration tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    yield engine
    await engine.dispose()


class TestMigrationExecution:
    """Tests for running migrations against a real database."""

    async def test_m5_001_creates_applications_table(self, migration_engine):
        """m5_001 creates the applications table."""
        async with migration_engine.begin() as conn:
            await _create_legacy_tables(conn)
            fn = _get_migration_fn("m5_001_create_applications_table")
            await fn(conn)

            result = await conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='applications'"
            ))
            assert result.scalar() == "applications"

    async def test_m5_001_creates_indexes(self, migration_engine):
        """m5_001 creates all required indexes."""
        async with migration_engine.begin() as conn:
            await _create_legacy_tables(conn)
            fn = _get_migration_fn("m5_001_create_applications_table")
            await fn(conn)

            result = await conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='applications'"
            ))
            index_names = {row[0] for row in result.fetchall()}

            assert "idx_applications_canonical" in index_names
            assert "idx_applications_legacy" in index_names
            assert "idx_applications_status" in index_names
            assert "idx_applications_followup" in index_names
            assert "idx_applications_reminder" in index_names

    async def test_m5_002_creates_status_history_table(self, migration_engine):
        """m5_002 creates the application_status_history table."""
        async with migration_engine.begin() as conn:
            await _create_legacy_tables(conn)
            fn_001 = _get_migration_fn("m5_001_create_applications_table")
            fn_002 = _get_migration_fn("m5_002_create_status_history_table")
            await fn_001(conn)
            await fn_002(conn)

            result = await conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='application_status_history'"
            ))
            assert result.scalar() == "application_status_history"

    async def test_m5_002_creates_index(self, migration_engine):
        """m5_002 creates the status history index."""
        async with migration_engine.begin() as conn:
            await _create_legacy_tables(conn)
            fn_001 = _get_migration_fn("m5_001_create_applications_table")
            fn_002 = _get_migration_fn("m5_002_create_status_history_table")
            await fn_001(conn)
            await fn_002(conn)

            result = await conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='application_status_history'"
            ))
            index_names = {row[0] for row in result.fetchall()}
            assert "idx_status_history_app" in index_names

    async def test_m5_003_migrates_existing_jobs(self, migration_engine):
        """m5_003 seeds applications from existing jobs with status != 'new'."""
        async with migration_engine.begin() as conn:
            await _create_legacy_tables(conn)
            for name in [
                "m5_001_create_applications_table",
                "m5_002_create_status_history_table",
            ]:
                await _get_migration_fn(name)(conn)

            # Insert some jobs directly
            await conn.execute(text("""
                INSERT INTO jobs (job_id, source, url, company_name, title, status,
                                  scraped_at, last_updated, is_active, is_enriched, is_starred)
                VALUES
                ('job_new_1', 'test', 'http://a.com', 'A Corp', 'Eng', 'new',
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, 0, 0),
                ('job_saved_1', 'test', 'http://b.com', 'B Corp', 'PM', 'saved',
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, 0, 0),
                ('job_applied_1', 'test', 'http://c.com', 'C Corp', 'DS', 'applied',
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, 0, 0)
            """))

            await _get_migration_fn("m5_003_migrate_existing_applications")(conn)

            # Verify: only non-'new' jobs should have applications
            result = await conn.execute(text(
                "SELECT legacy_job_id, status FROM applications ORDER BY legacy_job_id"
            ))
            rows = result.fetchall()

            assert len(rows) == 2
            job_ids = {row[0] for row in rows}
            assert "job_saved_1" in job_ids
            assert "job_applied_1" in job_ids
            assert "job_new_1" not in job_ids

            # Verify status was preserved
            status_map = {row[0]: row[1] for row in rows}
            assert status_map["job_saved_1"] == "saved"
            assert status_map["job_applied_1"] == "applied"

    async def test_m5_003_creates_status_history(self, migration_engine):
        """m5_003 also seeds initial status history for migrated records."""
        async with migration_engine.begin() as conn:
            await _create_legacy_tables(conn)
            for name in [
                "m5_001_create_applications_table",
                "m5_002_create_status_history_table",
            ]:
                await _get_migration_fn(name)(conn)

            await conn.execute(text("""
                INSERT INTO jobs (job_id, source, url, company_name, title, status,
                                  scraped_at, last_updated, is_active, is_enriched, is_starred)
                VALUES
                ('job_hist_1', 'test', 'http://a.com', 'A Corp', 'Eng', 'applied',
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, 0, 0)
            """))

            await _get_migration_fn("m5_003_migrate_existing_applications")(conn)

            result = await conn.execute(text(
                "SELECT old_status, new_status, change_source, note "
                "FROM application_status_history"
            ))
            rows = result.fetchall()
            assert len(rows) == 1
            assert rows[0][0] is None  # old_status
            assert rows[0][1] == "applied"  # new_status
            assert rows[0][2] == "system"  # change_source
            assert "Migrated" in rows[0][3]  # note

    async def test_m5_003_safe_on_empty_jobs(self, migration_engine):
        """m5_003 is safe when no jobs have status != 'new'."""
        async with migration_engine.begin() as conn:
            await _create_legacy_tables(conn)
            for name in [
                "m5_001_create_applications_table",
                "m5_002_create_status_history_table",
            ]:
                await _get_migration_fn(name)(conn)

            # No qualifying jobs
            await conn.execute(text("""
                INSERT INTO jobs (job_id, source, url, company_name, title, status,
                                  scraped_at, last_updated, is_active, is_enriched, is_starred)
                VALUES
                ('job_only_new', 'test', 'http://a.com', 'A Corp', 'Eng', 'new',
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, 0, 0)
            """))

            # Should not raise
            await _get_migration_fn("m5_003_migrate_existing_applications")(conn)

            result = await conn.execute(text("SELECT COUNT(*) FROM applications"))
            assert result.scalar() == 0

    async def test_m5_003_idempotent(self, migration_engine):
        """Running m5_003 twice does not duplicate records."""
        async with migration_engine.begin() as conn:
            await _create_legacy_tables(conn)
            for name in [
                "m5_001_create_applications_table",
                "m5_002_create_status_history_table",
            ]:
                await _get_migration_fn(name)(conn)

            await conn.execute(text("""
                INSERT INTO jobs (job_id, source, url, company_name, title, status,
                                  scraped_at, last_updated, is_active, is_enriched, is_starred)
                VALUES
                ('job_idem', 'test', 'http://a.com', 'A Corp', 'Eng', 'applied',
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, 0, 0)
            """))

            fn = _get_migration_fn("m5_003_migrate_existing_applications")
            await fn(conn)
            await fn(conn)

            result = await conn.execute(text("SELECT COUNT(*) FROM applications"))
            assert result.scalar() == 1

    async def test_migrations_idempotent_tables(self, migration_engine):
        """Running table creation migrations twice is safe (IF NOT EXISTS)."""
        async with migration_engine.begin() as conn:
            await _create_legacy_tables(conn)

            fn_001 = _get_migration_fn("m5_001_create_applications_table")
            fn_002 = _get_migration_fn("m5_002_create_status_history_table")

            # Run all twice — should not raise
            await fn_001(conn)
            await fn_001(conn)
            await fn_002(conn)
            await fn_002(conn)

    async def test_run_all_migrations(self, migration_engine):
        """run_migrations executes all in registration order."""
        async with migration_engine.begin() as conn:
            await _create_legacy_tables(conn)

            executed = await run_migrations(conn)

            # Verify M5 migrations ran (among others)
            m5_executed = [n for n in executed if n.startswith("m5_")]
            assert "m5_001_create_applications_table" in m5_executed
            assert "m5_002_create_status_history_table" in m5_executed
            assert "m5_003_migrate_existing_applications" in m5_executed

            # Verify order: 001 before 002, 002 before 003
            idx_001 = m5_executed.index("m5_001_create_applications_table")
            idx_002 = m5_executed.index("m5_002_create_status_history_table")
            idx_003 = m5_executed.index("m5_003_migrate_existing_applications")
            assert idx_001 < idx_002
            assert idx_002 < idx_003

    async def test_jobs_table_unchanged_after_migration(self, migration_engine):
        """The jobs table is not modified by any migration."""
        async with migration_engine.begin() as conn:
            await _create_legacy_tables(conn)

            await conn.execute(text("""
                INSERT INTO jobs (job_id, source, url, company_name, title, status,
                                  scraped_at, last_updated, is_active, is_enriched, is_starred)
                VALUES
                ('job_unchanged', 'test', 'http://a.com', 'A Corp', 'Eng', 'applied',
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, 0, 0)
            """))

            await run_migrations(conn)

            # Job still exists with original data
            result = await conn.execute(text(
                "SELECT status FROM jobs WHERE job_id = 'job_unchanged'"
            ))
            assert result.scalar() == "applied"


# ------------------------------------------------------------------
# Integration: round-trip CRUD after migration
# ------------------------------------------------------------------


class TestRoundTripAfterMigration:
    """Integration test: full CRUD cycle after running migrations."""

    async def test_insert_and_query_application(self, migration_engine):
        """Insert and query an application after running migrations."""
        async with migration_engine.begin() as conn:
            await _create_legacy_tables(conn)
            await run_migrations(conn)

            # Insert a job first
            await conn.execute(text("""
                INSERT INTO jobs (job_id, source, url, company_name, title, status,
                                  scraped_at, last_updated, is_active, is_enriched, is_starred)
                VALUES
                ('job_round', 'test', 'http://a.com', 'A Corp', 'Eng', 'new',
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, 0, 0)
            """))

            # Insert an application
            await conn.execute(text("""
                INSERT INTO applications (
                    application_id, legacy_job_id, status, notes, created_at
                ) VALUES (
                    'roundtrip_app_001', 'job_round', 'saved', 'Test notes',
                    CURRENT_TIMESTAMP
                )
            """))

            # Query back
            result = await conn.execute(text(
                "SELECT application_id, legacy_job_id, status, notes "
                "FROM applications WHERE application_id = 'roundtrip_app_001'"
            ))
            row = result.fetchone()
            assert row is not None
            assert row[0] == "roundtrip_app_001"
            assert row[1] == "job_round"
            assert row[2] == "saved"
            assert row[3] == "Test notes"

    async def test_insert_and_query_status_history(self, migration_engine):
        """Insert and query status history after running migrations."""
        async with migration_engine.begin() as conn:
            await _create_legacy_tables(conn)
            await run_migrations(conn)

            await conn.execute(text("""
                INSERT INTO jobs (job_id, source, url, company_name, title, status,
                                  scraped_at, last_updated, is_active, is_enriched, is_starred)
                VALUES ('job_hist_round', 'test', 'http://a.com', 'A Corp', 'Eng', 'new',
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, 0, 0)
            """))

            await conn.execute(text("""
                INSERT INTO applications (
                    application_id, legacy_job_id, status, created_at
                ) VALUES (
                    'hist_round_app', 'job_hist_round', 'saved', CURRENT_TIMESTAMP
                )
            """))

            await conn.execute(text("""
                INSERT INTO application_status_history (
                    application_id, old_status, new_status, changed_at,
                    change_source, note
                ) VALUES (
                    'hist_round_app', NULL, 'saved', CURRENT_TIMESTAMP,
                    'user', 'Created'
                )
            """))

            await conn.execute(text("""
                INSERT INTO application_status_history (
                    application_id, old_status, new_status, changed_at,
                    change_source, note
                ) VALUES (
                    'hist_round_app', 'saved', 'applied', CURRENT_TIMESTAMP,
                    'user', 'Applied manually'
                )
            """))

            result = await conn.execute(text(
                "SELECT old_status, new_status, change_source "
                "FROM application_status_history "
                "WHERE application_id = 'hist_round_app' "
                "ORDER BY id"
            ))
            rows = result.fetchall()
            assert len(rows) == 2
            assert rows[0][1] == "saved"
            assert rows[1][0] == "saved"
            assert rows[1][1] == "applied"

    async def test_update_application_status(self, migration_engine):
        """Update an application status after migration."""
        async with migration_engine.begin() as conn:
            await _create_legacy_tables(conn)
            await run_migrations(conn)

            await conn.execute(text("""
                INSERT INTO jobs (job_id, source, url, company_name, title, status,
                                  scraped_at, last_updated, is_active, is_enriched, is_starred)
                VALUES ('job_update_round', 'test', 'http://a.com', 'A Corp', 'Eng', 'new',
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, 0, 0)
            """))

            await conn.execute(text("""
                INSERT INTO applications (
                    application_id, legacy_job_id, status, created_at
                ) VALUES (
                    'update_round_app', 'job_update_round', 'saved', CURRENT_TIMESTAMP
                )
            """))

            # Update status
            await conn.execute(text("""
                UPDATE applications SET status = 'applied', applied_at = CURRENT_TIMESTAMP
                WHERE application_id = 'update_round_app'
            """))

            result = await conn.execute(text(
                "SELECT status, applied_at FROM applications "
                "WHERE application_id = 'update_round_app'"
            ))
            row = result.fetchone()
            assert row[0] == "applied"
            assert row[1] is not None
