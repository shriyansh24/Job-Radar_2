"""Tests for Phase 7A migration runner."""

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from backend.phase7a.migration import (
    _ensure_migration_table,
    _get_applied_migrations,
    _record_migration,
    run_migrations,
    _MIGRATIONS,
    register_migration,
)


@pytest_asyncio.fixture
async def migration_engine():
    """Isolated in-memory engine for migration tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    yield engine
    await engine.dispose()


@pytest.fixture(autouse=True)
def clean_migration_registry():
    """Clear the migration registry before and after each test."""
    original = list(_MIGRATIONS)
    _MIGRATIONS.clear()
    yield
    _MIGRATIONS.clear()
    _MIGRATIONS.extend(original)


class TestEnsureMigrationTable:
    @pytest.mark.asyncio
    async def test_creates_table(self, migration_engine):
        async with migration_engine.begin() as conn:
            await _ensure_migration_table(conn)
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='_phase7a_migrations'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_idempotent(self, migration_engine):
        async with migration_engine.begin() as conn:
            await _ensure_migration_table(conn)
            await _ensure_migration_table(conn)  # Should not raise


class TestGetAppliedMigrations:
    @pytest.mark.asyncio
    async def test_empty_on_fresh_db(self, migration_engine):
        async with migration_engine.begin() as conn:
            await _ensure_migration_table(conn)
            applied = await _get_applied_migrations(conn)
            assert applied == set()

    @pytest.mark.asyncio
    async def test_returns_recorded_migrations(self, migration_engine):
        async with migration_engine.begin() as conn:
            await _ensure_migration_table(conn)
            await _record_migration(conn, "test_001")
            await _record_migration(conn, "test_002")
            applied = await _get_applied_migrations(conn)
            assert applied == {"test_001", "test_002"}


class TestRecordMigration:
    @pytest.mark.asyncio
    async def test_records_name(self, migration_engine):
        async with migration_engine.begin() as conn:
            await _ensure_migration_table(conn)
            await _record_migration(conn, "test_migration")
            result = await conn.execute(
                text("SELECT name FROM _phase7a_migrations WHERE name = 'test_migration'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_records_timestamp(self, migration_engine):
        async with migration_engine.begin() as conn:
            await _ensure_migration_table(conn)
            await _record_migration(conn, "test_migration")
            result = await conn.execute(
                text("SELECT applied_at FROM _phase7a_migrations WHERE name = 'test_migration'")
            )
            row = result.fetchone()
            assert row is not None
            assert row[0] is not None  # timestamp should be set

    @pytest.mark.asyncio
    async def test_duplicate_name_raises(self, migration_engine):
        async with migration_engine.begin() as conn:
            await _ensure_migration_table(conn)
            await _record_migration(conn, "duplicate")
            with pytest.raises(Exception):
                await _record_migration(conn, "duplicate")


class TestRunMigrations:
    @pytest.mark.asyncio
    async def test_no_migrations_is_noop(self, migration_engine):
        async with migration_engine.begin() as conn:
            result = await run_migrations(conn)
            assert result == []

    @pytest.mark.asyncio
    async def test_runs_single_migration(self, migration_engine):
        @register_migration("test_001_create_table")
        async def migrate(conn):
            await conn.execute(text("CREATE TABLE test_table (id INTEGER PRIMARY KEY)"))

        async with migration_engine.begin() as conn:
            applied = await run_migrations(conn)
            assert applied == ["test_001_create_table"]
            # Verify table was created
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_runs_multiple_in_order(self, migration_engine):
        execution_order = []

        @register_migration("test_001")
        async def migrate_1(conn):
            execution_order.append("001")

        @register_migration("test_002")
        async def migrate_2(conn):
            execution_order.append("002")

        @register_migration("test_003")
        async def migrate_3(conn):
            execution_order.append("003")

        async with migration_engine.begin() as conn:
            applied = await run_migrations(conn)
            assert applied == ["test_001", "test_002", "test_003"]
            assert execution_order == ["001", "002", "003"]

    @pytest.mark.asyncio
    async def test_skips_already_applied(self, migration_engine):
        call_count = 0

        @register_migration("test_001")
        async def migrate(conn):
            nonlocal call_count
            call_count += 1

        # Run once
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
        assert call_count == 1

        # Run again — should skip
        async with migration_engine.begin() as conn:
            applied = await run_migrations(conn)
        assert applied == []
        assert call_count == 1  # Not called again

    @pytest.mark.asyncio
    async def test_failed_migration_not_recorded(self, migration_engine):
        @register_migration("test_will_fail")
        async def migrate(conn):
            raise RuntimeError("Intentional failure")

        async with migration_engine.begin() as conn:
            with pytest.raises(RuntimeError, match="Intentional failure"):
                await run_migrations(conn)

        # Verify it was NOT recorded
        async with migration_engine.begin() as conn:
            await _ensure_migration_table(conn)
            applied = await _get_applied_migrations(conn)
            assert "test_will_fail" not in applied

    @pytest.mark.asyncio
    async def test_migration_table_bootstraps(self, migration_engine):
        """Migration table should be created even with no registered migrations."""
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='_phase7a_migrations'")
            )
            assert result.fetchone() is not None


class TestRegisterMigration:
    def test_duplicate_name_raises(self):
        @register_migration("unique_name")
        async def migrate_1(conn):
            pass

        with pytest.raises(ValueError, match="Duplicate migration name"):
            @register_migration("unique_name")
            async def migrate_2(conn):
                pass

    def test_registration_preserves_function(self):
        @register_migration("test_fn_preserved")
        async def my_migration(conn):
            pass

        assert _MIGRATIONS[-1][0] == "test_fn_preserved"
        assert _MIGRATIONS[-1][1] is my_migration


class TestBackwardCompatibility:
    """Verify Phase 7A migrations don't break existing tables."""

    @pytest.mark.asyncio
    async def test_existing_models_still_work(self, migration_engine):
        """All 4 existing models should create tables alongside migration table."""
        from backend.database import Base
        from backend.models import Job, SavedSearch, ScraperRun, UserProfile  # noqa

        async with migration_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await run_migrations(conn)

            # Verify existing tables exist
            for table_name in ["jobs", "saved_searches", "scraper_runs", "user_profile"]:
                result = await conn.execute(
                    text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                )
                assert result.fetchone() is not None, f"Table {table_name} should exist"

            # Verify migration table also exists
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='_phase7a_migrations'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_init_db_idempotent(self, migration_engine):
        """Running init_db pattern twice should not raise."""
        from backend.database import Base
        from backend.models import Job, SavedSearch, ScraperRun, UserProfile  # noqa

        async with migration_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await run_migrations(conn)

        async with migration_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await run_migrations(conn)
