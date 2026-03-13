"""Tests for Module 2 Search Expansion Engine: Migrations.

Verifies that M2 migrations create tables correctly, seed default rules,
create indexes, and maintain backward compatibility with existing tables.
"""

import json

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from backend.phase7a.migration import (
    _MIGRATIONS,
    run_migrations,
)
from backend.phase7a.m2_rules import get_all_default_rules, SYNONYM_RULES, SKILL_RULES


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


class TestM2MigrationsRegistered:
    """Verify that M2 migrations are registered."""

    def test_m2_migrations_present(self):
        """All M2 migrations should be registered."""
        # Force import of m2_migrations module to register decorators
        import backend.phase7a.m2_migrations  # noqa: F401

        names = [name for name, _ in _MIGRATIONS]
        assert "m2_001_create_query_templates_table" in names
        assert "m2_002_create_expansion_rules_table" in names
        assert "m2_003_create_query_performance_table" in names
        assert "m2_004_create_query_performance_index" in names
        assert "m2_005_seed_default_rules" in names

    def test_m2_migrations_in_order(self):
        """M2 migrations should be registered in numeric order."""
        import backend.phase7a.m2_migrations  # noqa: F401

        m2_names = [name for name, _ in _MIGRATIONS if name.startswith("m2_")]
        expected_order = [
            "m2_001_create_query_templates_table",
            "m2_002_create_expansion_rules_table",
            "m2_003_create_query_performance_table",
            "m2_004_create_query_performance_index",
            "m2_005_seed_default_rules",
        ]
        # Check relative ordering
        for i in range(len(expected_order) - 1):
            idx_a = m2_names.index(expected_order[i])
            idx_b = m2_names.index(expected_order[i + 1])
            assert idx_a < idx_b, f"{expected_order[i]} should come before {expected_order[i + 1]}"


class TestM2TableCreation:
    """Tests that migrations correctly create M2 tables."""

    @pytest.mark.asyncio
    async def test_creates_query_templates_table(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='query_templates'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_creates_expansion_rules_table(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='expansion_rules'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_creates_query_performance_table(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='query_performance'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_creates_performance_index(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='index' AND name='idx_query_performance_template_source'"
                )
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_idempotent(self, migration_engine):
        """Running migrations twice should not raise errors."""
        async with migration_engine.begin() as conn:
            result1 = await run_migrations(conn)
        async with migration_engine.begin() as conn:
            result2 = await run_migrations(conn)
        assert len(result2) == 0, "Second run should find no new migrations"


class TestM2SchemaColumns:
    """Tests that table schemas have the correct columns."""

    @pytest.mark.asyncio
    async def test_query_templates_columns(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(text("PRAGMA table_info(query_templates)"))
            columns = {row[1]: row[2] for row in result.fetchall()}
            assert "template_id" in columns
            assert "intent" in columns
            assert "expansion_ast" in columns
            assert "source_translations" in columns
            assert "strictness" in columns
            assert "is_active" in columns
            assert "created_at" in columns
            assert "updated_at" in columns

    @pytest.mark.asyncio
    async def test_expansion_rules_columns(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(text("PRAGMA table_info(expansion_rules)"))
            columns = {row[1]: row[2] for row in result.fetchall()}
            assert "rule_id" in columns
            assert "rule_type" in columns
            assert "input_pattern" in columns
            assert "output_variants" in columns
            assert "priority" in columns
            assert "is_active" in columns

    @pytest.mark.asyncio
    async def test_query_performance_columns(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(text("PRAGMA table_info(query_performance)"))
            columns = {row[1]: row[2] for row in result.fetchall()}
            assert "id" in columns
            assert "template_id" in columns
            assert "source" in columns
            assert "query_string" in columns
            assert "results_count" in columns
            assert "new_jobs_count" in columns
            assert "executed_at" in columns
            assert "duration_ms" in columns


class TestM2SeedRules:
    """Tests that default rules are correctly seeded."""

    @pytest.mark.asyncio
    async def test_seeds_correct_count(self, migration_engine):
        expected_count = len(get_all_default_rules())
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(text("SELECT COUNT(*) FROM expansion_rules"))
            count = result.fetchone()[0]
            assert count == expected_count

    @pytest.mark.asyncio
    async def test_seeds_synonym_rules(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text("SELECT COUNT(*) FROM expansion_rules WHERE rule_type = 'synonym'")
            )
            count = result.fetchone()[0]
            assert count == len(SYNONYM_RULES)

    @pytest.mark.asyncio
    async def test_seeds_seniority_rule(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text("SELECT COUNT(*) FROM expansion_rules WHERE rule_type = 'seniority'")
            )
            count = result.fetchone()[0]
            assert count == 1  # Single wildcard rule

    @pytest.mark.asyncio
    async def test_seeds_skill_rules(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text("SELECT COUNT(*) FROM expansion_rules WHERE rule_type = 'skill'")
            )
            count = result.fetchone()[0]
            assert count == len(SKILL_RULES)

    @pytest.mark.asyncio
    async def test_ml_engineer_synonym_seeded(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text(
                    "SELECT output_variants FROM expansion_rules "
                    "WHERE rule_type = 'synonym' AND input_pattern = 'ML Engineer'"
                )
            )
            row = result.fetchone()
            assert row is not None
            variants = json.loads(row[0])
            assert "Machine Learning Engineer" in variants
            assert "Applied Scientist" in variants
            assert "AI Engineer" in variants

    @pytest.mark.asyncio
    async def test_seed_idempotent(self, migration_engine):
        """Running migrations twice should not double-insert rules."""
        expected_count = len(get_all_default_rules())
        async with migration_engine.begin() as conn:
            await run_migrations(conn)

        # Run again
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(text("SELECT COUNT(*) FROM expansion_rules"))
            count = result.fetchone()[0]
            assert count == expected_count, "Rules should not be duplicated"

    @pytest.mark.asyncio
    async def test_priorities_correct(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text(
                    "SELECT DISTINCT priority FROM expansion_rules "
                    "WHERE rule_type = 'synonym'"
                )
            )
            priorities = [row[0] for row in result.fetchall()]
            assert priorities == [10]

            result = await conn.execute(
                text(
                    "SELECT DISTINCT priority FROM expansion_rules "
                    "WHERE rule_type = 'seniority'"
                )
            )
            priorities = [row[0] for row in result.fetchall()]
            assert priorities == [20]

            result = await conn.execute(
                text(
                    "SELECT DISTINCT priority FROM expansion_rules "
                    "WHERE rule_type = 'skill'"
                )
            )
            priorities = [row[0] for row in result.fetchall()]
            assert priorities == [30]

    @pytest.mark.asyncio
    async def test_all_rules_active(self, migration_engine):
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text("SELECT COUNT(*) FROM expansion_rules WHERE is_active = 0")
            )
            count = result.fetchone()[0]
            assert count == 0, "All seeded rules should be active"


class TestM2BackwardCompatibility:
    """Verify M2 migrations don't break existing tables."""

    @pytest.mark.asyncio
    async def test_existing_tables_still_work(self, migration_engine):
        """All 4 existing models should create tables alongside M2 tables."""
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

            # Verify M2 tables also exist
            for table_name in ["query_templates", "expansion_rules", "query_performance"]:
                result = await conn.execute(
                    text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                )
                assert result.fetchone() is not None, f"M2 table {table_name} should exist"

    @pytest.mark.asyncio
    async def test_can_insert_existing_models_after_m2(self, migration_engine):
        """Inserting into existing tables should still work after M2 migrations."""
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
    async def test_migration_table_records_m2(self, migration_engine):
        """M2 migrations should be recorded in the _phase7a_migrations table."""
        async with migration_engine.begin() as conn:
            await run_migrations(conn)
            result = await conn.execute(
                text("SELECT name FROM _phase7a_migrations WHERE name LIKE 'm2_%'")
            )
            m2_migrations = [row[0] for row in result.fetchall()]
            assert len(m2_migrations) == 5


class TestM2TemplateRoundTrip:
    """Integration test: verify template creation round-trip through migrations."""

    @pytest.mark.asyncio
    async def test_insert_template_after_migration(self, migration_engine):
        """After running migrations, inserting into query_templates should work."""
        async with migration_engine.begin() as conn:
            await run_migrations(conn)

            from backend.phase7a.id_utils import compute_template_id

            tid = compute_template_id("ML Engineer")
            ast = json.dumps({
                "$schema": "query_ast_v1",
                "type": "OR",
                "children": [{"type": "term", "value": "ML Engineer"}],
                "seniority_variants": [""],
                "exclude": [],
            })
            translations = json.dumps({"serpapi": '"ML Engineer"'})

            await conn.execute(
                text(
                    "INSERT INTO query_templates "
                    "(template_id, intent, expansion_ast, source_translations, "
                    "strictness, is_active, created_at) "
                    "VALUES (:tid, :intent, :ast, :translations, "
                    "'balanced', 1, datetime('now'))"
                ),
                {
                    "tid": tid,
                    "intent": "ML Engineer",
                    "ast": ast,
                    "translations": translations,
                },
            )

            result = await conn.execute(
                text("SELECT intent FROM query_templates WHERE template_id = :tid"),
                {"tid": tid},
            )
            row = result.fetchone()
            assert row is not None
            assert row[0] == "ML Engineer"

    @pytest.mark.asyncio
    async def test_insert_performance_after_migration(self, migration_engine):
        """After running migrations, inserting into query_performance should work."""
        async with migration_engine.begin() as conn:
            await run_migrations(conn)

            from backend.phase7a.id_utils import compute_template_id

            tid = compute_template_id("Test Perf")
            ast = json.dumps({"type": "OR", "children": []})

            # Insert template first (FK constraint)
            await conn.execute(
                text(
                    "INSERT INTO query_templates "
                    "(template_id, intent, expansion_ast, strictness, is_active, created_at) "
                    "VALUES (:tid, 'Test Perf', :ast, 'balanced', 1, datetime('now'))"
                ),
                {"tid": tid, "ast": ast},
            )

            # Insert performance record
            await conn.execute(
                text(
                    "INSERT INTO query_performance "
                    "(template_id, source, query_string, results_count, "
                    "new_jobs_count, executed_at, duration_ms) "
                    "VALUES (:tid, 'serpapi', 'test query', 10, 3, "
                    "datetime('now'), 150)"
                ),
                {"tid": tid},
            )

            result = await conn.execute(
                text("SELECT results_count FROM query_performance WHERE template_id = :tid"),
                {"tid": tid},
            )
            row = result.fetchone()
            assert row is not None
            assert row[0] == 10
