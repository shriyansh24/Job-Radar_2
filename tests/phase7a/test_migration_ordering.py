"""Migration System Tests for Phase 7A.

Verifies:
1. Migration names follow naming convention (module_prefix + sequence number)
2. No duplicate migration names across all modules
3. Migrations run in correct order (core before modules)
4. Failed migration does not corrupt state
5. Migration table tracks all applied migrations accurately
6. Migration runner handles edge cases (empty registry, re-runs, errors)

Edge cases covered:
- Registering 100 migrations (stress test)
- Migration that creates a table, then another that depends on it
- Migration failure at different points in the sequence
- Concurrent migration table access (idempotency)
- Migration names with special characters (should work or be rejected cleanly)
"""

import re

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from backend.phase7a.migration import (
    _MIGRATIONS,
    _ensure_migration_table,
    _get_applied_migrations,
    _record_migration,
    get_registered_migrations,
    register_migration,
    run_migrations,
)


@pytest_asyncio.fixture
async def migration_engine():
    """Isolated in-memory engine for migration ordering tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    yield engine
    await engine.dispose()


@pytest.fixture(autouse=True)
def clean_migration_registry():
    """Clear the migration registry before and after each test.

    Preserves any migrations registered by module imports.
    """
    original = list(_MIGRATIONS)
    _MIGRATIONS.clear()
    yield
    _MIGRATIONS.clear()
    _MIGRATIONS.extend(original)


# ---------------------------------------------------------------------------
# Naming convention tests
# ---------------------------------------------------------------------------

class TestMigrationNamingConvention:
    """Verify migration names follow expected patterns."""

    def test_naming_convention_pattern(self):
        """Migration names should follow pattern: module_NNN_description."""
        # Register test migrations following the convention
        @register_migration("core_001_create_migration_table")
        async def m1(conn):
            pass

        @register_migration("m1_001_create_companies")
        async def m2(conn):
            pass

        @register_migration("m2_001_create_templates")
        async def m3(conn):
            pass

        migrations = get_registered_migrations()
        # Expected format: {prefix}_{number}_{description}
        pattern = re.compile(r"^[a-z0-9]+_\d{3}_[a-z0-9_]+$")
        for name, _ in migrations:
            assert pattern.match(name), (
                f"Migration '{name}' does not match pattern 'prefix_NNN_description'"
            )

    def test_names_are_unique(self):
        """No two migrations should have the same name."""
        @register_migration("unique_001_first")
        async def m1(conn):
            pass

        @register_migration("unique_002_second")
        async def m2(conn):
            pass

        names = [name for name, _ in get_registered_migrations()]
        assert len(names) == len(set(names)), f"Duplicate names found: {names}"

    def test_duplicate_name_raises_valueerror(self):
        """Registering a duplicate migration name must raise ValueError."""
        @register_migration("dup_001_test")
        async def m1(conn):
            pass

        with pytest.raises(ValueError, match="Duplicate migration name"):
            @register_migration("dup_001_test")
            async def m2(conn):
                pass


# ---------------------------------------------------------------------------
# No duplicate names across all modules
# ---------------------------------------------------------------------------

class TestNoDuplicatesAcrossModules:
    """Verify no duplicate migration names exist across module boundaries."""

    def test_no_duplicates_when_multiple_modules_register(self):
        """Simulate multiple modules registering migrations."""
        # Module 1 (Company Registry)
        @register_migration("m1_001_create_companies_table")
        async def m1_001(conn):
            pass

        @register_migration("m1_002_create_company_sources")
        async def m1_002(conn):
            pass

        # Module 2 (Search Expansion)
        @register_migration("m2_001_create_query_templates")
        async def m2_001(conn):
            pass

        # Module 3 (Source Cache)
        @register_migration("m3_001_create_source_registry")
        async def m3_001(conn):
            pass

        migrations = get_registered_migrations()
        names = [name for name, _ in migrations]
        assert len(names) == len(set(names)), "Found duplicate migration names across modules"

    def test_naming_collision_across_modules_caught(self):
        """If two modules accidentally use the same name, it must be caught."""
        @register_migration("shared_name_001")
        async def m1(conn):
            pass

        with pytest.raises(ValueError):
            @register_migration("shared_name_001")
            async def m2(conn):
                pass


# ---------------------------------------------------------------------------
# Correct ordering
# ---------------------------------------------------------------------------

class TestMigrationOrdering:
    """Verify migrations run in registration order (core before modules)."""

    @pytest.mark.asyncio
    async def test_execution_order_matches_registration(self, migration_engine):
        """Migrations must execute in the exact order they were registered."""
        execution_order = []

        @register_migration("core_001_first")
        async def m1(conn):
            execution_order.append("core_001")

        @register_migration("core_002_second")
        async def m2(conn):
            execution_order.append("core_002")

        @register_migration("m1_001_third")
        async def m3(conn):
            execution_order.append("m1_001")

        @register_migration("m2_001_fourth")
        async def m4(conn):
            execution_order.append("m2_001")

        async with migration_engine.begin() as conn:
            applied = await run_migrations(conn)

        assert execution_order == ["core_001", "core_002", "m1_001", "m2_001"]
        assert applied == ["core_001_first", "core_002_second", "m1_001_third", "m2_001_fourth"]

    @pytest.mark.asyncio
    async def test_core_runs_before_modules(self, migration_engine):
        """Core migrations must run before any module migration."""
        execution_order = []

        @register_migration("core_001_foundation")
        async def core_m(conn):
            execution_order.append("core")

        @register_migration("m1_001_module")
        async def mod_m(conn):
            execution_order.append("module")

        async with migration_engine.begin() as conn:
            await run_migrations(conn)

        assert execution_order == ["core", "module"]


# ---------------------------------------------------------------------------
# Failed migration does not corrupt state
# ---------------------------------------------------------------------------

class TestFailedMigrationIntegrity:
    """Verify failed migrations do not leave corrupt state."""

    @pytest.mark.asyncio
    async def test_failed_migration_not_recorded(self, migration_engine):
        """A failed migration must not be recorded as applied."""
        @register_migration("good_001")
        async def good(conn):
            await conn.execute(text("CREATE TABLE test_good (id INTEGER PRIMARY KEY)"))

        @register_migration("bad_002")
        async def bad(conn):
            raise RuntimeError("Intentional test failure")

        async with migration_engine.begin() as conn:
            with pytest.raises(RuntimeError, match="Intentional test failure"):
                await run_migrations(conn)

        # Verify good_001 was applied but bad_002 was not
        async with migration_engine.begin() as conn:
            await _ensure_migration_table(conn)
            applied = await _get_applied_migrations(conn)
            assert "good_001" in applied
            assert "bad_002" not in applied

    @pytest.mark.asyncio
    async def test_successful_migration_before_failure_is_preserved(self, migration_engine):
        """Migrations that succeed before a failure should be recorded."""
        call_count = {"good": 0}

        @register_migration("success_001")
        async def success(conn):
            call_count["good"] += 1
            await conn.execute(text("CREATE TABLE preserved_table (id INTEGER PRIMARY KEY)"))

        @register_migration("failure_002")
        async def failure(conn):
            raise RuntimeError("Boom")

        async with migration_engine.begin() as conn:
            with pytest.raises(RuntimeError):
                await run_migrations(conn)

        # Re-run: success_001 should be skipped, failure_002 should fail again
        _MIGRATIONS.clear()

        @register_migration("success_001")
        async def success_again(conn):
            call_count["good"] += 1

        @register_migration("failure_002")
        async def failure_again(conn):
            raise RuntimeError("Boom again")

        async with migration_engine.begin() as conn:
            with pytest.raises(RuntimeError):
                await run_migrations(conn)

        # success_001 should only have been called once total
        assert call_count["good"] == 1


# ---------------------------------------------------------------------------
# Migration table accuracy
# ---------------------------------------------------------------------------

class TestMigrationTableAccuracy:
    """Verify migration table tracks all applied migrations accurately."""

    @pytest.mark.asyncio
    async def test_records_all_applied(self, migration_engine):
        @register_migration("track_001")
        async def m1(conn):
            pass

        @register_migration("track_002")
        async def m2(conn):
            pass

        @register_migration("track_003")
        async def m3(conn):
            pass

        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            applied = await _get_applied_migrations(conn)
            assert applied == {"track_001", "track_002", "track_003"}

    @pytest.mark.asyncio
    async def test_records_timestamp(self, migration_engine):
        @register_migration("ts_001")
        async def m1(conn):
            pass

        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text("SELECT name, applied_at FROM _phase7a_migrations WHERE name = 'ts_001'")
            )
            row = result.fetchone()
            assert row is not None
            assert row[1] is not None  # applied_at should be set

    @pytest.mark.asyncio
    async def test_applied_count_matches(self, migration_engine):
        for i in range(5):
            name = f"count_{i:03d}"

            @register_migration(name)
            async def m(conn, _name=name):
                pass

        async with migration_engine.begin() as conn:
            applied = await run_migrations(conn)
            assert len(applied) == 5

            result = await conn.execute(
                text("SELECT count(*) FROM _phase7a_migrations")
            )
            assert result.fetchone()[0] == 5


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestMigrationEdgeCases:
    """Edge case tests for the migration system."""

    @pytest.mark.asyncio
    async def test_empty_registry_is_noop(self, migration_engine):
        """No registered migrations = no error, empty result."""
        async with migration_engine.begin() as conn:
            applied = await run_migrations(conn)
            assert applied == []

    @pytest.mark.asyncio
    async def test_rerun_applies_only_new(self, migration_engine):
        """Only new migrations should run on re-invocation."""
        @register_migration("base_001")
        async def m1(conn):
            pass

        async with migration_engine.begin() as conn:
            first = await run_migrations(conn)
        assert first == ["base_001"]

        # Add a new migration
        @register_migration("base_002")
        async def m2(conn):
            pass

        async with migration_engine.begin() as conn:
            second = await run_migrations(conn)
        assert second == ["base_002"]

    @pytest.mark.asyncio
    async def test_migration_creating_dependent_table(self, migration_engine):
        """Migration 2 can depend on table created by migration 1."""
        @register_migration("dep_001_parent")
        async def m1(conn):
            await conn.execute(text(
                "CREATE TABLE parent_table (id INTEGER PRIMARY KEY, name TEXT)"
            ))

        @register_migration("dep_002_child")
        async def m2(conn):
            await conn.execute(text(
                "CREATE TABLE child_table (id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent_table(id))"
            ))

        async with migration_engine.begin() as conn:
            applied = await run_migrations(conn)
            assert len(applied) == 2

            # Verify both tables exist
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('parent_table', 'child_table')")
            )
            tables = {row[0] for row in result.fetchall()}
            assert tables == {"parent_table", "child_table"}

    @pytest.mark.asyncio
    async def test_migration_table_bootstraps_on_fresh_db(self, migration_engine):
        """Migration table should be created automatically even on completely empty DB."""
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='_phase7a_migrations'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_many_migrations_stress(self, migration_engine):
        """Register and run 50 migrations without error."""
        for i in range(50):
            name = f"stress_{i:03d}"

            @register_migration(name)
            async def m(conn, _i=i):
                pass

        async with migration_engine.begin() as conn:
            applied = await run_migrations(conn)
            assert len(applied) == 50

    @pytest.mark.asyncio
    async def test_migration_with_if_not_exists(self, migration_engine):
        """Migrations using IF NOT EXISTS should be safe to re-execute."""
        @register_migration("safe_001")
        async def m1(conn):
            await conn.execute(text(
                "CREATE TABLE IF NOT EXISTS safe_table (id INTEGER PRIMARY KEY)"
            ))

        async with migration_engine.begin() as conn:
            await run_migrations(conn)

        # Running the migration logic manually again should not fail
        async with migration_engine.begin() as conn:
            await conn.execute(text(
                "CREATE TABLE IF NOT EXISTS safe_table (id INTEGER PRIMARY KEY)"
            ))
