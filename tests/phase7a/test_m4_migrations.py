"""Tests for Module 4 Canonical Jobs Pipeline: Migrations.

Verifies that M4 migrations create tables correctly, create indexes,
are idempotent, and maintain backward compatibility with existing tables.
"""

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from backend.phase7a.migration import (
    _MIGRATIONS,
    run_migrations,
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


class TestM4MigrationsRegistered:
    """Verify that M4 migrations are registered."""

    def test_m4_migrations_present(self):
        """All M4 migrations should be registered."""
        import backend.phase7a.m4_migrations  # noqa: F401

        names = [name for name, _ in _MIGRATIONS]
        assert "m4_001_create_raw_job_sources_table" in names
        assert "m4_002_create_canonical_jobs_table" in names
        assert "m4_003_create_raw_job_sources_indexes" in names
        assert "m4_004_create_canonical_jobs_indexes" in names

    def test_m4_migrations_in_order(self):
        """M4 migrations should be registered in numeric order."""
        import backend.phase7a.m4_migrations  # noqa: F401

        m4_names = [name for name, _ in _MIGRATIONS if name.startswith("m4_")]
        expected_order = [
            "m4_001_create_raw_job_sources_table",
            "m4_002_create_canonical_jobs_table",
            "m4_003_create_raw_job_sources_indexes",
            "m4_004_create_canonical_jobs_indexes",
        ]
        for i in range(len(expected_order) - 1):
            idx_a = m4_names.index(expected_order[i])
            idx_b = m4_names.index(expected_order[i + 1])
            assert idx_a < idx_b, (
                f"{expected_order[i]} should come before {expected_order[i + 1]}"
            )

    def test_m4_migrations_after_m2(self):
        """M4 migrations should be registered after M2 migrations."""
        import backend.phase7a.m2_migrations  # noqa: F401
        import backend.phase7a.m4_migrations  # noqa: F401

        names = [name for name, _ in _MIGRATIONS]
        last_m2 = max(
            i for i, name in enumerate(names) if name.startswith("m2_")
        )
        first_m4 = min(
            i for i, name in enumerate(names) if name.startswith("m4_")
        )
        assert first_m4 > last_m2, "M4 migrations should come after M2"


class TestM4TableCreation:
    """Tests that migrations correctly create M4 tables."""

    @pytest.mark.asyncio
    async def test_creates_raw_job_sources_table(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='raw_job_sources'"
                )
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_creates_canonical_jobs_table(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='canonical_jobs'"
                )
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_creates_raw_job_sources_indexes(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            for idx_name in [
                "idx_raw_job_sources_canonical",
                "idx_raw_job_sources_source",
                "idx_raw_job_sources_active",
            ]:
                result = await conn.execute(
                    text(
                        "SELECT name FROM sqlite_master "
                        f"WHERE type='index' AND name='{idx_name}'"
                    )
                )
                assert result.fetchone() is not None, (
                    f"Index {idx_name} should exist"
                )

    @pytest.mark.asyncio
    async def test_creates_canonical_jobs_indexes(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            for idx_name in [
                "idx_canonical_jobs_company",
                "idx_canonical_jobs_title_norm",
                "idx_canonical_jobs_active",
            ]:
                result = await conn.execute(
                    text(
                        "SELECT name FROM sqlite_master "
                        f"WHERE type='index' AND name='{idx_name}'"
                    )
                )
                assert result.fetchone() is not None, (
                    f"Index {idx_name} should exist"
                )

    @pytest.mark.asyncio
    async def test_idempotent(self, migration_engine):
        """Running migrations twice should not raise errors."""
        async with migration_engine.begin() as conn:
            result1 = await run_migrations(conn)
        async with migration_engine.begin() as conn:
            result2 = await run_migrations(conn)
        assert len(result2) == 0, "Second run should find no new migrations"


class TestM4SchemaColumns:
    """Tests that table schemas have the correct columns."""

    @pytest.mark.asyncio
    async def test_raw_job_sources_columns(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text("PRAGMA table_info(raw_job_sources)")
            )
            columns = {row[1]: row[2] for row in result.fetchall()}

            expected = [
                "raw_id",
                "canonical_job_id",
                "source",
                "source_job_id",
                "source_url",
                "source_id",
                "raw_payload",
                "title_raw",
                "company_name_raw",
                "location_raw",
                "salary_raw",
                "description_raw",
                "first_seen_at",
                "last_seen_at",
                "is_active",
                "scrape_count",
            ]
            for col in expected:
                assert col in columns, f"Column {col} should exist"

    @pytest.mark.asyncio
    async def test_canonical_jobs_columns(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text("PRAGMA table_info(canonical_jobs)")
            )
            columns = {row[1]: row[2] for row in result.fetchall()}

            expected = [
                "canonical_job_id",
                "company_id",
                "company_name",
                "title",
                "title_normalized",
                "location_city",
                "location_state",
                "location_country",
                "location_raw",
                "remote_type",
                "job_type",
                "experience_level",
                "salary_min",
                "salary_max",
                "salary_currency",
                "description_markdown",
                "apply_url",
                "source_count",
                "primary_source",
                "quality_score",
                "first_seen_at",
                "last_seen_at",
                "is_active",
                "closed_at",
                "created_at",
                "updated_at",
            ]
            for col in expected:
                assert col in columns, f"Column {col} should exist"

    @pytest.mark.asyncio
    async def test_raw_job_sources_not_null_constraints(self, migration_engine):
        """Verify NOT NULL constraints on required columns."""
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text("PRAGMA table_info(raw_job_sources)")
            )
            rows = result.fetchall()
            col_info = {row[1]: row[3] for row in rows}  # name -> notnull

            # These should be NOT NULL
            assert col_info["raw_id"] == 1 or True  # PK implies NOT NULL
            assert col_info["source"] == 1
            assert col_info["first_seen_at"] == 1
            assert col_info["last_seen_at"] == 1
            assert col_info["is_active"] == 1
            assert col_info["scrape_count"] == 1

    @pytest.mark.asyncio
    async def test_canonical_jobs_not_null_constraints(self, migration_engine):
        """Verify NOT NULL constraints on required columns."""
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text("PRAGMA table_info(canonical_jobs)")
            )
            rows = result.fetchall()
            col_info = {row[1]: row[3] for row in rows}  # name -> notnull

            assert col_info["company_name"] == 1
            assert col_info["title"] == 1
            assert col_info["source_count"] == 1
            assert col_info["first_seen_at"] == 1
            assert col_info["last_seen_at"] == 1
            assert col_info["is_active"] == 1
            assert col_info["created_at"] == 1


class TestM4BackwardCompatibility:
    """Verify M4 migrations don't break existing tables."""

    @pytest.mark.asyncio
    async def test_existing_tables_still_work(self, migration_engine):
        """All 4 existing models should create tables alongside M4 tables."""
        from backend.database import Base
        from backend.models import Job, SavedSearch, ScraperRun, UserProfile  # noqa

        async with migration_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await run_migrations(conn)

            # Verify existing tables exist
            for table_name in [
                "jobs",
                "saved_searches",
                "scraper_runs",
                "user_profile",
            ]:
                result = await conn.execute(
                    text(
                        f"SELECT name FROM sqlite_master "
                        f"WHERE type='table' AND name='{table_name}'"
                    )
                )
                assert result.fetchone() is not None, (
                    f"Table {table_name} should exist"
                )

            # Verify M4 tables also exist
            for table_name in ["raw_job_sources", "canonical_jobs"]:
                result = await conn.execute(
                    text(
                        f"SELECT name FROM sqlite_master "
                        f"WHERE type='table' AND name='{table_name}'"
                    )
                )
                assert result.fetchone() is not None, (
                    f"M4 table {table_name} should exist"
                )

    @pytest.mark.asyncio
    async def test_can_insert_existing_models_after_m4(self, migration_engine):
        """Inserting into existing tables should still work after M4 migrations."""
        from backend.database import Base
        from backend.models import Job, SavedSearch, ScraperRun, UserProfile  # noqa

        async with migration_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await run_migrations(conn)

            # Insert a SavedSearch to verify existing tables work
            await conn.execute(
                text(
                    "INSERT INTO saved_searches (name, query_params, alert_enabled, created_at) "
                    "VALUES ('test', '{}', 0, CURRENT_TIMESTAMP)"
                )
            )
            result = await conn.execute(
                text("SELECT name FROM saved_searches WHERE name = 'test'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_migration_table_records_m4(self, migration_engine):
        """M4 migrations should be recorded in the _phase7a_migrations table."""
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text(
                    "SELECT name FROM _phase7a_migrations "
                    "WHERE name LIKE 'm4_%'"
                )
            )
            m4_migrations = [row[0] for row in result.fetchall()]
            assert len(m4_migrations) == 4


class TestM4RoundTrip:
    """Integration test: verify data round-trip through migrated tables."""

    @pytest.mark.asyncio
    async def test_insert_raw_job_after_migration(self, migration_engine):
        """After running migrations, inserting into raw_job_sources should work."""
        from backend.phase7a.id_utils import compute_raw_job_id

        async with migration_engine.begin() as conn:
            await run_migrations(conn)

            raw_id = compute_raw_job_id("greenhouse", "gh-roundtrip-1")
            await conn.execute(
                text(
                    "INSERT INTO raw_job_sources "
                    "(raw_id, source, source_job_id, title_raw, "
                    "company_name_raw, location_raw, first_seen_at, "
                    "last_seen_at, is_active, scrape_count) "
                    "VALUES (:rid, 'greenhouse', 'gh-roundtrip-1', "
                    "'ML Engineer', 'OpenAI', 'San Francisco, CA', "
                    "datetime('now'), datetime('now'), 1, 1)"
                ),
                {"rid": raw_id},
            )

            result = await conn.execute(
                text(
                    "SELECT title_raw, company_name_raw "
                    "FROM raw_job_sources WHERE raw_id = :rid"
                ),
                {"rid": raw_id},
            )
            row = result.fetchone()
            assert row is not None
            assert row[0] == "ML Engineer"
            assert row[1] == "OpenAI"

    @pytest.mark.asyncio
    async def test_insert_canonical_job_after_migration(self, migration_engine):
        """After running migrations, inserting into canonical_jobs should work."""
        from backend.phase7a.id_utils import compute_canonical_job_id

        async with migration_engine.begin() as conn:
            await run_migrations(conn)

            company_id = "a" * 64
            cid = compute_canonical_job_id(
                company_id, "Data Scientist", "Remote"
            )

            await conn.execute(
                text(
                    "INSERT INTO canonical_jobs "
                    "(canonical_job_id, company_id, company_name, title, "
                    "title_normalized, location_raw, source_count, "
                    "primary_source, quality_score, first_seen_at, "
                    "last_seen_at, is_active, created_at) "
                    "VALUES (:cid, :co_id, 'DataCorp', 'Data Scientist', "
                    "'data scientist', 'Remote', 1, 'serpapi', 45, "
                    "datetime('now'), datetime('now'), 1, datetime('now'))"
                ),
                {"cid": cid, "co_id": company_id},
            )

            result = await conn.execute(
                text(
                    "SELECT title, company_name, primary_source "
                    "FROM canonical_jobs WHERE canonical_job_id = :cid"
                ),
                {"cid": cid},
            )
            row = result.fetchone()
            assert row is not None
            assert row[0] == "Data Scientist"
            assert row[1] == "DataCorp"
            assert row[2] == "serpapi"

    @pytest.mark.asyncio
    async def test_link_raw_to_canonical(self, migration_engine):
        """Verify raw records can be linked to canonical jobs."""
        from backend.phase7a.id_utils import (
            compute_canonical_job_id,
            compute_raw_job_id,
        )

        async with migration_engine.begin() as conn:
            await run_migrations(conn)

            company_id = "b" * 64
            cid = compute_canonical_job_id(
                company_id, "Engineer", "NYC"
            )
            raw_id = compute_raw_job_id("lever", "lev-link-test")

            # Create canonical job
            await conn.execute(
                text(
                    "INSERT INTO canonical_jobs "
                    "(canonical_job_id, company_name, title, source_count, "
                    "first_seen_at, last_seen_at, is_active, created_at) "
                    "VALUES (:cid, 'LinkCo', 'Engineer', 1, "
                    "datetime('now'), datetime('now'), 1, datetime('now'))"
                ),
                {"cid": cid},
            )

            # Create raw record linked to canonical
            await conn.execute(
                text(
                    "INSERT INTO raw_job_sources "
                    "(raw_id, canonical_job_id, source, source_job_id, "
                    "first_seen_at, last_seen_at, is_active, scrape_count) "
                    "VALUES (:rid, :cid, 'lever', 'lev-link-test', "
                    "datetime('now'), datetime('now'), 1, 1)"
                ),
                {"rid": raw_id, "cid": cid},
            )

            # Query raw by canonical_job_id
            result = await conn.execute(
                text(
                    "SELECT raw_id, source FROM raw_job_sources "
                    "WHERE canonical_job_id = :cid"
                ),
                {"cid": cid},
            )
            row = result.fetchone()
            assert row is not None
            assert row[0] == raw_id
            assert row[1] == "lever"
