"""Tests for Module 1 — Company Intelligence Registry migrations.

Tests cover:
- Migration registration (all 4 migrations registered)
- Table creation (companies, company_sources, ats_detection_log)
- Index creation
- Seed migration from existing jobs data
- Idempotency (re-running migrations is safe)
- Backward compatibility (existing tables unaffected)
"""

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.database import Base
from backend.phase7a.migration import run_migrations, get_registered_migrations


@pytest_asyncio.fixture
async def engine():
    """Create in-memory engine for migration testing."""
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def engine_with_jobs():
    """Create in-memory engine with existing jobs table and sample data.

    This simulates a pre-Phase 7A database that has jobs but no
    companies table yet.
    """
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    # Create existing tables via Base.metadata (includes Job model)
    async with eng.begin() as conn:
        from backend.models import Job, SavedSearch, ScraperRun, UserProfile  # noqa
        await conn.run_sync(Base.metadata.create_all)

        # Insert sample jobs (include all NOT NULL columns)
        await conn.execute(text("""
            INSERT INTO jobs (job_id, source, url, company_name, company_domain, title, status,
                              scraped_at, last_updated, is_active, is_enriched, is_starred)
            VALUES
                ('job1_' || substr('0000000000000000000000000000000000000000000000000000000000000', 1, 59),
                 'greenhouse', 'https://example.com/1', 'Stripe', 'stripe.com', 'Backend Engineer', 'new',
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, 0, 0),
                ('job2_' || substr('0000000000000000000000000000000000000000000000000000000000000', 1, 59),
                 'lever', 'https://example.com/2', 'OpenAI', 'openai.com', 'ML Engineer', 'new',
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, 0, 0),
                ('job3_' || substr('0000000000000000000000000000000000000000000000000000000000000', 1, 59),
                 'greenhouse', 'https://example.com/3', 'Stripe', 'stripe.com', 'Frontend Engineer', 'new',
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, 0, 0),
                ('job4_' || substr('0000000000000000000000000000000000000000000000000000000000000', 1, 59),
                 'serpapi', 'https://example.com/4', 'Anthropic', NULL, 'Research Engineer', 'new',
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, 0, 0),
                ('job5_' || substr('0000000000000000000000000000000000000000000000000000000000000', 1, 59),
                 'jobspy', 'https://example.com/5', 'Anthropic', 'anthropic.com', 'Software Engineer', 'new',
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, 0, 0)
        """))

    yield eng
    await eng.dispose()


class TestMigrationRegistration:
    """Verify all M1 migrations are registered."""

    def test_m1_migrations_registered(self):
        """All 4 M1 migrations should be in the registry."""
        # Force import to register
        import backend.phase7a.m1_migrations  # noqa
        migrations = get_registered_migrations()
        names = [name for name, _ in migrations]

        assert "m1_001_create_companies_table" in names
        assert "m1_002_create_company_sources_table" in names
        assert "m1_003_create_ats_detection_log_table" in names
        assert "m1_004_seed_companies_from_jobs" in names

    def test_m1_migrations_in_order(self):
        """M1 migrations should appear in sequential order."""
        migrations = get_registered_migrations()
        m1_migrations = [
            (name, fn) for name, fn in migrations if name.startswith("m1_")
        ]
        names = [name for name, _ in m1_migrations]

        # Check ordering
        assert names.index("m1_001_create_companies_table") < \
            names.index("m1_002_create_company_sources_table")
        assert names.index("m1_002_create_company_sources_table") < \
            names.index("m1_003_create_ats_detection_log_table")
        assert names.index("m1_003_create_ats_detection_log_table") < \
            names.index("m1_004_seed_companies_from_jobs")


class TestMigrationsCreateTables:
    """Verify migrations create the expected tables and indexes."""

    async def test_creates_companies_table(self, engine):
        async with engine.begin() as conn:
            applied = await run_migrations(conn)

        assert "m1_001_create_companies_table" in applied

        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='companies'"
            ))
            assert result.fetchone() is not None

    async def test_creates_company_sources_table(self, engine):
        async with engine.begin() as conn:
            await run_migrations(conn)

        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='company_sources'"
            ))
            assert result.fetchone() is not None

    async def test_creates_ats_detection_log_table(self, engine):
        async with engine.begin() as conn:
            await run_migrations(conn)

        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='ats_detection_log'"
            ))
            assert result.fetchone() is not None

    async def test_creates_companies_indexes(self, engine):
        async with engine.begin() as conn:
            await run_migrations(conn)

        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='companies'"
            ))
            index_names = {row[0] for row in result.fetchall()}

        assert "idx_companies_domain" in index_names
        assert "idx_companies_canonical_name" in index_names
        assert "idx_companies_ats_provider_slug" in index_names
        assert "idx_companies_validation_state" in index_names

    async def test_creates_company_sources_indexes(self, engine):
        async with engine.begin() as conn:
            await run_migrations(conn)

        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='company_sources'"
            ))
            index_names = {row[0] for row in result.fetchall()}

        assert "idx_company_sources_company_id" in index_names
        assert "idx_company_sources_source" in index_names

    async def test_creates_ats_detection_log_indexes(self, engine):
        async with engine.begin() as conn:
            await run_migrations(conn)

        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='ats_detection_log'"
            ))
            index_names = {row[0] for row in result.fetchall()}

        assert "idx_ats_detection_log_company_id" in index_names

    async def test_companies_table_columns(self, engine):
        """Verify all expected columns exist on the companies table."""
        async with engine.begin() as conn:
            await run_migrations(conn)

        async with engine.connect() as conn:
            result = await conn.execute(text("PRAGMA table_info(companies)"))
            columns = {row[1] for row in result.fetchall()}

        expected = {
            "company_id", "canonical_name", "domain", "domain_aliases",
            "ats_provider", "ats_slug", "careers_url", "board_urls",
            "logo_url", "validation_state", "confidence_score",
            "last_validated_at", "last_probe_at", "probe_error",
            "manual_override", "override_fields", "created_at", "updated_at",
        }
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"


class TestMigrationIdempotency:
    """Verify running migrations multiple times is safe."""

    async def test_idempotent_run(self, engine):
        """Running migrations twice produces same result."""
        async with engine.begin() as conn:
            first_run = await run_migrations(conn)

        assert len(first_run) > 0

        async with engine.begin() as conn:
            second_run = await run_migrations(conn)

        assert second_run == []  # nothing new to apply

    async def test_migration_tracking_table_exists(self, engine):
        """Migration tracking table is created."""
        async with engine.begin() as conn:
            await run_migrations(conn)

        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='_phase7a_migrations'"
            ))
            assert result.fetchone() is not None

    async def test_applied_migrations_recorded(self, engine):
        """All applied migrations are recorded in tracking table."""
        async with engine.begin() as conn:
            applied = await run_migrations(conn)

        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT name FROM _phase7a_migrations ORDER BY id"
            ))
            recorded = [row[0] for row in result.fetchall()]

        for name in applied:
            assert name in recorded


class TestSeedMigration:
    """Tests for the m1_004 seed migration that populates companies from jobs."""

    async def test_seed_from_existing_jobs(self, engine_with_jobs):
        """Seed creates company records from distinct job company names."""
        async with engine_with_jobs.begin() as conn:
            await run_migrations(conn)

        async with engine_with_jobs.connect() as conn:
            result = await conn.execute(text(
                "SELECT canonical_name, domain FROM companies ORDER BY canonical_name"
            ))
            companies = [(row[0], row[1]) for row in result.fetchall()]

        # Should have distinct companies: Anthropic (2 jobs, one with domain),
        # OpenAI (1 job), Stripe (2 jobs)
        names = {c[0] for c in companies}
        assert "Stripe" in names
        assert "OpenAI" in names
        assert "Anthropic" in names

    async def test_seed_uses_domain_when_available(self, engine_with_jobs):
        """Seed prefers domain for company_id when domain is available."""
        from backend.phase7a.id_utils import compute_company_id

        async with engine_with_jobs.begin() as conn:
            await run_migrations(conn)

        async with engine_with_jobs.connect() as conn:
            result = await conn.execute(text(
                "SELECT company_id, domain FROM companies "
                "WHERE canonical_name = 'Stripe'"
            ))
            row = result.fetchone()
            assert row is not None
            assert row[1] == "stripe.com"
            assert row[0] == compute_company_id("stripe.com")

    async def test_seed_handles_null_domain(self, engine_with_jobs):
        """Seed handles jobs with NULL company_domain."""
        async with engine_with_jobs.begin() as conn:
            await run_migrations(conn)

        async with engine_with_jobs.connect() as conn:
            # The Anthropic entry from the NULL-domain job should exist
            # (it may have been created from the row with the domain instead)
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM companies WHERE canonical_name = 'Anthropic'"
            ))
            count = result.scalar()
            # At least one Anthropic record should exist
            assert count >= 1

    async def test_seed_default_validation_state(self, engine_with_jobs):
        """All seeded companies start as 'unverified'."""
        async with engine_with_jobs.begin() as conn:
            await run_migrations(conn)

        async with engine_with_jobs.connect() as conn:
            result = await conn.execute(text(
                "SELECT validation_state FROM companies"
            ))
            states = [row[0] for row in result.fetchall()]

        assert all(s == "unverified" for s in states)

    async def test_seed_default_confidence_score(self, engine_with_jobs):
        """All seeded companies start with confidence_score=0."""
        async with engine_with_jobs.begin() as conn:
            await run_migrations(conn)

        async with engine_with_jobs.connect() as conn:
            result = await conn.execute(text(
                "SELECT confidence_score FROM companies"
            ))
            scores = [row[0] for row in result.fetchall()]

        assert all(s == 0 for s in scores)

    async def test_seed_idempotent(self, engine_with_jobs):
        """Re-running seed doesn't duplicate companies."""
        async with engine_with_jobs.begin() as conn:
            await run_migrations(conn)

        async with engine_with_jobs.connect() as conn:
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM companies"
            ))
            count_first = result.scalar()

        # Migrations are tracked, so re-running won't re-apply the seed.
        # But even if the seed SQL ran again, INSERT OR IGNORE prevents dupes.
        async with engine_with_jobs.begin() as conn:
            await run_migrations(conn)

        async with engine_with_jobs.connect() as conn:
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM companies"
            ))
            count_second = result.scalar()

        assert count_first == count_second

    async def test_seed_without_jobs_table(self, engine):
        """Seed gracefully skips when no jobs table exists."""
        async with engine.begin() as conn:
            applied = await run_migrations(conn)

        assert "m1_004_seed_companies_from_jobs" in applied
        # Should succeed without error, just skip the seeding

    async def test_seed_empty_jobs_table(self, engine):
        """Seed handles empty jobs table gracefully."""
        # Create the jobs table but leave it empty
        async with engine.begin() as conn:
            from backend.models import Job  # noqa
            await conn.run_sync(Base.metadata.create_all)
            applied = await run_migrations(conn)

        assert "m1_004_seed_companies_from_jobs" in applied

        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM companies"
            ))
            count = result.scalar()
        assert count == 0


class TestBackwardCompatibilityMigrations:
    """Verify migrations don't break existing tables."""

    async def test_existing_jobs_table_unchanged(self, engine_with_jobs):
        """Jobs table columns are unchanged after migrations."""
        # Get columns before migration
        async with engine_with_jobs.connect() as conn:
            result = await conn.execute(text("PRAGMA table_info(jobs)"))
            columns_before = {row[1] for row in result.fetchall()}

        # Run migrations
        async with engine_with_jobs.begin() as conn:
            await run_migrations(conn)

        # Get columns after migration
        async with engine_with_jobs.connect() as conn:
            result = await conn.execute(text("PRAGMA table_info(jobs)"))
            columns_after = {row[1] for row in result.fetchall()}

        assert columns_before == columns_after, (
            f"Jobs table columns changed! "
            f"Added: {columns_after - columns_before}, "
            f"Removed: {columns_before - columns_after}"
        )

    async def test_existing_jobs_data_intact(self, engine_with_jobs):
        """Job records are preserved after migrations."""
        async with engine_with_jobs.begin() as conn:
            await run_migrations(conn)

        async with engine_with_jobs.connect() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM jobs"))
            count = result.scalar()
        assert count == 5  # same 5 jobs we inserted

    async def test_existing_tables_still_queryable(self, engine_with_jobs):
        """All existing tables can still be queried after migrations."""
        async with engine_with_jobs.begin() as conn:
            await run_migrations(conn)

        async with engine_with_jobs.connect() as conn:
            # Jobs
            result = await conn.execute(text("SELECT * FROM jobs LIMIT 1"))
            assert result.fetchone() is not None

            # SavedSearches (empty but queryable)
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM saved_searches"
            ))
            assert result.scalar() is not None

            # ScraperRuns (empty but queryable)
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM scraper_runs"
            ))
            assert result.scalar() is not None

            # UserProfile (empty but queryable)
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM user_profile"
            ))
            assert result.scalar() is not None
