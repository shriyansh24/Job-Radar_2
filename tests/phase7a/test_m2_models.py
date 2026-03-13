"""Tests for Module 2 Search Expansion Engine: SQLAlchemy models.

Verifies that all three M2 tables (query_templates, expansion_rules,
query_performance) can be created and used via the ORM.
"""

import json
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.database import Base
from backend.phase7a.m2_models import (
    ExpansionRule,
    QueryPerformance,
    QueryTemplate,
)
from backend.phase7a.id_utils import compute_template_id


@pytest_asyncio.fixture
async def m2_engine():
    """In-memory SQLite engine with M2 tables created."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def m2_session(m2_engine):
    """Async session bound to the M2 test engine."""
    factory = async_sessionmaker(
        m2_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with factory() as session:
        yield session


class TestQueryTemplateModel:
    """Tests for the QueryTemplate ORM model."""

    @pytest.mark.asyncio
    async def test_table_exists(self, m2_engine):
        async with m2_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='query_templates'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_insert_and_read(self, m2_session):
        now = datetime.now(timezone.utc)
        template = QueryTemplate(
            template_id=compute_template_id("ML Engineer"),
            intent="ML Engineer",
            expansion_ast={"type": "OR", "children": [{"type": "term", "value": "ML Engineer"}]},
            source_translations={"serpapi": '"ML Engineer"'},
            strictness="balanced",
            is_active=True,
            created_at=now,
        )
        m2_session.add(template)
        await m2_session.commit()

        result = await m2_session.execute(
            text("SELECT * FROM query_templates WHERE intent = 'ML Engineer'")
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == compute_template_id("ML Engineer")  # template_id

    @pytest.mark.asyncio
    async def test_intent_unique_constraint(self, m2_session):
        now = datetime.now(timezone.utc)
        t1 = QueryTemplate(
            template_id="aaa",
            intent="Same Intent",
            expansion_ast={"type": "OR", "children": []},
            created_at=now,
        )
        t2 = QueryTemplate(
            template_id="bbb",
            intent="Same Intent",
            expansion_ast={"type": "OR", "children": []},
            created_at=now,
        )
        m2_session.add(t1)
        await m2_session.commit()

        m2_session.add(t2)
        with pytest.raises(Exception):
            await m2_session.commit()

    @pytest.mark.asyncio
    async def test_default_values(self, m2_session):
        now = datetime.now(timezone.utc)
        template = QueryTemplate(
            template_id="default_test",
            intent="Default Test",
            expansion_ast={"type": "OR", "children": []},
            created_at=now,
        )
        m2_session.add(template)
        await m2_session.commit()

        result = await m2_session.execute(
            text("SELECT strictness, is_active FROM query_templates WHERE template_id = 'default_test'")
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == "balanced"
        assert row[1] == 1  # True in SQLite

    @pytest.mark.asyncio
    async def test_nullable_fields(self, m2_session):
        now = datetime.now(timezone.utc)
        template = QueryTemplate(
            template_id="nullable_test",
            intent="Nullable Test",
            expansion_ast={"type": "OR", "children": []},
            created_at=now,
            source_translations=None,
            updated_at=None,
        )
        m2_session.add(template)
        await m2_session.commit()

        result = await m2_session.execute(
            text("SELECT source_translations, updated_at FROM query_templates WHERE template_id = 'nullable_test'")
        )
        row = result.fetchone()
        assert row is not None
        # JSON columns may store Python None as SQL NULL or JSON 'null' string
        assert row[0] is None or row[0] == "null"
        assert row[1] is None


class TestExpansionRuleModel:
    """Tests for the ExpansionRule ORM model."""

    @pytest.mark.asyncio
    async def test_table_exists(self, m2_engine):
        async with m2_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='expansion_rules'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_insert_and_read(self, m2_session):
        rule = ExpansionRule(
            rule_type="synonym",
            input_pattern="ML Engineer",
            output_variants=["Machine Learning Engineer", "AI Engineer"],
            priority=10,
            is_active=True,
        )
        m2_session.add(rule)
        await m2_session.commit()

        result = await m2_session.execute(
            text("SELECT * FROM expansion_rules WHERE input_pattern = 'ML Engineer'")
        )
        row = result.fetchone()
        assert row is not None
        assert row[1] == "synonym"  # rule_type

    @pytest.mark.asyncio
    async def test_autoincrement(self, m2_session):
        for i in range(3):
            rule = ExpansionRule(
                rule_type="synonym",
                input_pattern=f"Pattern {i}",
                output_variants=[f"Variant {i}"],
                priority=10,
            )
            m2_session.add(rule)
        await m2_session.commit()

        result = await m2_session.execute(
            text("SELECT rule_id FROM expansion_rules ORDER BY rule_id")
        )
        ids = [row[0] for row in result.fetchall()]
        assert len(ids) == 3
        assert ids[0] < ids[1] < ids[2]

    @pytest.mark.asyncio
    async def test_default_priority(self, m2_session):
        rule = ExpansionRule(
            rule_type="boolean",
            input_pattern="test",
            output_variants=["test_out"],
        )
        m2_session.add(rule)
        await m2_session.commit()

        result = await m2_session.execute(
            text("SELECT priority FROM expansion_rules WHERE input_pattern = 'test'")
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == 100

    @pytest.mark.asyncio
    async def test_json_output_variants(self, m2_session):
        variants = ["Machine Learning Engineer", "Applied Scientist", "AI Engineer"]
        rule = ExpansionRule(
            rule_type="synonym",
            input_pattern="ML Eng",
            output_variants=variants,
            priority=10,
        )
        m2_session.add(rule)
        await m2_session.commit()

        result = await m2_session.execute(
            text("SELECT output_variants FROM expansion_rules WHERE input_pattern = 'ML Eng'")
        )
        row = result.fetchone()
        assert row is not None
        stored = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        assert stored == variants


class TestQueryPerformanceModel:
    """Tests for the QueryPerformance ORM model."""

    @pytest.mark.asyncio
    async def test_table_exists(self, m2_engine):
        async with m2_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='query_performance'")
            )
            assert result.fetchone() is not None

    @pytest.mark.asyncio
    async def test_insert_with_template(self, m2_session):
        """Insert a performance record referencing a valid template."""
        now = datetime.now(timezone.utc)
        tid = compute_template_id("ML Engineer")

        # Create parent template first
        template = QueryTemplate(
            template_id=tid,
            intent="ML Engineer",
            expansion_ast={"type": "OR", "children": []},
            created_at=now,
        )
        m2_session.add(template)
        await m2_session.commit()

        # Create performance record
        perf = QueryPerformance(
            template_id=tid,
            source="serpapi",
            query_string='"ML Engineer" OR "Machine Learning Engineer"',
            results_count=47,
            new_jobs_count=12,
            executed_at=now,
            duration_ms=250,
        )
        m2_session.add(perf)
        await m2_session.commit()

        result = await m2_session.execute(
            text("SELECT * FROM query_performance WHERE template_id = :tid"),
            {"tid": tid},
        )
        row = result.fetchone()
        assert row is not None
        assert row[2] == "serpapi"  # source column

    @pytest.mark.asyncio
    async def test_nullable_counts(self, m2_session):
        """Performance records can have NULL results_count and new_jobs_count."""
        now = datetime.now(timezone.utc)
        tid = compute_template_id("Nullable Perf")

        template = QueryTemplate(
            template_id=tid,
            intent="Nullable Perf",
            expansion_ast={"type": "OR", "children": []},
            created_at=now,
        )
        m2_session.add(template)
        await m2_session.commit()

        perf = QueryPerformance(
            template_id=tid,
            source="greenhouse",
            query_string="test",
            executed_at=now,
            results_count=None,
            new_jobs_count=None,
            duration_ms=None,
        )
        m2_session.add(perf)
        await m2_session.commit()

        result = await m2_session.execute(
            text("SELECT results_count, new_jobs_count, duration_ms FROM query_performance WHERE template_id = :tid"),
            {"tid": tid},
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] is None
        assert row[1] is None
        assert row[2] is None


class TestBackwardCompatibility:
    """Verify M2 models coexist with existing tables without interference."""

    @pytest.mark.asyncio
    async def test_existing_tables_unaffected(self, m2_engine):
        """Creating M2 tables should not affect existing Job/SavedSearch/etc tables."""
        from backend.models import Job, SavedSearch, ScraperRun, UserProfile  # noqa

        async with m2_engine.begin() as conn:
            # Existing tables should still exist (they were created by Base.metadata.create_all)
            for table_name in ["jobs", "saved_searches", "scraper_runs", "user_profile"]:
                result = await conn.execute(
                    text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                )
                assert result.fetchone() is not None, f"Existing table {table_name} should still exist"

    @pytest.mark.asyncio
    async def test_m2_tables_are_new(self, m2_engine):
        """All M2 tables should be created alongside existing ones."""
        async with m2_engine.begin() as conn:
            for table_name in ["query_templates", "expansion_rules", "query_performance"]:
                result = await conn.execute(
                    text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                )
                assert result.fetchone() is not None, f"M2 table {table_name} should exist"
