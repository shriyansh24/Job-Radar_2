"""
Tests for Module 3 — Validated Source Cache: Migrations.

Covers:
  - Tables are created correctly via migrations
  - Indexes are created correctly
  - Migrations are idempotent (running twice is safe)
  - Migration tracking table records applied migrations
  - Round-trip data operations after migration
"""

import pytest

try:
    import pytest_asyncio
    async_fixture = pytest_asyncio.fixture
except (ImportError, AttributeError):
    async_fixture = pytest.fixture

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


@async_fixture
async def raw_engine():
    """Create a fresh in-memory engine with no tables."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    yield engine
    await engine.dispose()


class TestM3Migrations:
    """Tests for the M3 migration functions."""

    async def test_migrations_create_tables(self, raw_engine):
        """Verify that running migrations creates both M3 tables."""
        from backend.phase7a.migration import run_migrations
        # Import to register migrations
        import backend.phase7a.m3_migrations  # noqa: F401

        async with raw_engine.begin() as conn:
            applied = await run_migrations(conn)

        assert "m3_001_create_source_registry_table" in applied
        assert "m3_002_create_source_check_log_table" in applied

        # Verify tables exist
        async with raw_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = {row[0] for row in result.fetchall()}

        assert "source_registry" in tables
        assert "source_check_log" in tables
        assert "_phase7a_migrations" in tables

    async def test_migrations_create_indexes(self, raw_engine):
        """Verify that migrations create expected indexes."""
        from backend.phase7a.migration import run_migrations
        import backend.phase7a.m3_migrations  # noqa: F401

        async with raw_engine.begin() as conn:
            await run_migrations(conn)

        # Check indexes
        async with raw_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='index'")
            )
            indexes = {row[0] for row in result.fetchall()}

        assert "idx_source_registry_type" in indexes
        assert "idx_source_registry_health" in indexes
        assert "idx_source_registry_company" in indexes
        assert "idx_source_check_log_source_time" in indexes

    async def test_migrations_are_idempotent(self, raw_engine):
        """Running migrations twice should not error or duplicate."""
        from backend.phase7a.migration import run_migrations
        import backend.phase7a.m3_migrations  # noqa: F401

        # First run
        async with raw_engine.begin() as conn:
            applied_1 = await run_migrations(conn)

        # Second run — should skip all
        async with raw_engine.begin() as conn:
            applied_2 = await run_migrations(conn)

        assert len(applied_1) >= 2  # At least M3's 2 migrations (plus other modules)
        assert len(applied_2) == 0

    async def test_migration_tracking(self, raw_engine):
        """Verify applied migrations are tracked in phase7a_migrations table."""
        from backend.phase7a.migration import run_migrations
        import backend.phase7a.m3_migrations  # noqa: F401

        async with raw_engine.begin() as conn:
            await run_migrations(conn)

        async with raw_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM _phase7a_migrations ORDER BY name")
            )
            names = [row[0] for row in result.fetchall()]

        assert "m3_001_create_source_registry_table" in names
        assert "m3_002_create_source_check_log_table" in names

    async def test_data_round_trip_after_migration(self, raw_engine):
        """Verify data can be inserted and read after migration."""
        from backend.phase7a.migration import run_migrations
        import backend.phase7a.m3_migrations  # noqa: F401

        async with raw_engine.begin() as conn:
            await run_migrations(conn)

        # Insert a source
        async with raw_engine.begin() as conn:
            await conn.execute(text("""
                INSERT INTO source_registry
                    (source_id, source_type, url, health_state, created_at)
                VALUES
                    ('test_id_123', 'greenhouse', 'https://example.com/jobs',
                     'unknown', CURRENT_TIMESTAMP)
            """))

        # Read it back
        async with raw_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT source_id, source_type, health_state FROM source_registry")
            )
            row = result.fetchone()

        assert row is not None
        assert row[0] == "test_id_123"
        assert row[1] == "greenhouse"
        assert row[2] == "unknown"

    async def test_source_registry_defaults_via_sql(self, raw_engine):
        """Verify SQL-level defaults for source_registry columns."""
        from backend.phase7a.migration import run_migrations
        import backend.phase7a.m3_migrations  # noqa: F401

        async with raw_engine.begin() as conn:
            await run_migrations(conn)

        # Insert with minimal fields
        async with raw_engine.begin() as conn:
            await conn.execute(text("""
                INSERT INTO source_registry (source_id, source_type, url)
                VALUES ('default_test', 'lever', 'https://api.lever.co/test')
            """))

        async with raw_engine.begin() as conn:
            result = await conn.execute(text(
                "SELECT health_state, quality_score, success_count, failure_count, "
                "consecutive_failures, robots_compliant, rate_limit_hits "
                "FROM source_registry WHERE source_id = 'default_test'"
            ))
            row = result.fetchone()

        assert row is not None
        assert row[0] == "unknown"    # health_state default
        assert row[1] == 50           # quality_score default
        assert row[2] == 0            # success_count default
        assert row[3] == 0            # failure_count default
        assert row[4] == 0            # consecutive_failures default
        assert row[5] == 1            # robots_compliant default (TRUE=1)
        assert row[6] == 0            # rate_limit_hits default

    async def test_check_log_fk_constraint(self, raw_engine):
        """Verify check log references source_registry via FK."""
        from backend.phase7a.migration import run_migrations
        import backend.phase7a.m3_migrations  # noqa: F401

        async with raw_engine.begin() as conn:
            await run_migrations(conn)
            # Enable FK enforcement for this test
            await conn.execute(text("PRAGMA foreign_keys = ON"))

        # Insert a source first
        async with raw_engine.begin() as conn:
            await conn.execute(text("PRAGMA foreign_keys = ON"))
            await conn.execute(text("""
                INSERT INTO source_registry (source_id, source_type, url)
                VALUES ('fk_test_source', 'ashby', 'https://api.ashbyhq.com/test')
            """))

            # Insert a check log referencing it (should succeed)
            await conn.execute(text("""
                INSERT INTO source_check_log
                    (source_id, check_type, status, checked_at)
                VALUES
                    ('fk_test_source', 'scrape', 'success', CURRENT_TIMESTAMP)
            """))

        # Verify it was inserted
        async with raw_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT source_id, status FROM source_check_log WHERE source_id = 'fk_test_source'")
            )
            row = result.fetchone()
            assert row is not None
            assert row[0] == "fk_test_source"
            assert row[1] == "success"
