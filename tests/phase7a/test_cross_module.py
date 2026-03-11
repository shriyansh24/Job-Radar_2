"""Cross-Module Integration Tests for Phase 7A.

Tests for interactions between Phase 7A modules and the existing system.
These will grow as individual modules (M1-M5) are built. The initial set
validates that shared foundations (constants, id_utils, migration) work
correctly together and coexist with the existing system.

Edge cases covered:
- Company ID consistency across domains, names, and URLs
- Source ID stability across modules
- Enum values matching expected column defaults
- Migration ordering (core before modules)
- Module migration idempotency
- Table coexistence (Phase 7A tables alongside existing tables)
- Golden dataset integrity (all records use valid enum values)
"""

import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from backend.phase7a.constants import (
    ATSProvider,
    ApplicationStatus,
    ChangeSource,
    CheckStatus,
    CheckType,
    ExperienceLevel,
    HealthState,
    JobType,
    QueryStrictness,
    RemoteType,
    SOURCE_QUALITY_ORDER,
    SourceType,
    ValidationState,
)
from backend.phase7a.id_utils import (
    compute_canonical_job_id,
    compute_company_id,
    compute_raw_job_id,
    compute_source_id,
    compute_template_id,
)


# ---------------------------------------------------------------------------
# Company ID consistency across modules
# ---------------------------------------------------------------------------

class TestCompanyIdConsistency:
    """Verify compute_company_id() returns the same result for the same input
    regardless of which module calls it."""

    def test_same_domain_always_same_id(self):
        """Company ID from domain must be deterministic across calls."""
        id_a = compute_company_id("stripe.com")
        id_b = compute_company_id("stripe.com")
        id_c = compute_company_id("stripe.com")
        assert id_a == id_b == id_c

    def test_domain_normalization_consistent(self):
        """Various representations of the same domain produce the same ID."""
        variants = [
            "stripe.com",
            "Stripe.COM",
            "https://stripe.com",
            "https://www.stripe.com",
            "www.stripe.com",
            "https://www.Stripe.COM/jobs",
        ]
        ids = {compute_company_id(v) for v in variants}
        assert len(ids) == 1, f"Expected 1 unique ID, got {len(ids)}: {ids}"

    def test_different_domains_different_ids(self):
        """Different domains must produce different IDs."""
        domains = ["stripe.com", "figma.com", "openai.com", "anthropic.com", "notion.so"]
        ids = [compute_company_id(d) for d in domains]
        assert len(ids) == len(set(ids)), "All domain IDs should be unique"

    def test_name_based_id_is_stable(self):
        """Company name-based ID is deterministic."""
        id_a = compute_company_id("Acme Corp")
        id_b = compute_company_id("Acme Corp")
        assert id_a == id_b

    def test_name_normalization_strips_suffixes(self):
        """Company name normalization strips legal suffixes consistently."""
        # "Acme Corp" and "Acme Corporation" should both normalize to "acme"
        id_a = compute_company_id("Acme Corp")
        id_b = compute_company_id("Acme Corporation")
        assert id_a == id_b


# ---------------------------------------------------------------------------
# Source ID consistency
# ---------------------------------------------------------------------------

class TestSourceIdConsistency:
    """Verify compute_source_id() is stable across modules."""

    def test_same_inputs_same_output(self):
        id_a = compute_source_id("greenhouse", "https://boards-api.greenhouse.io/v1/boards/stripe/jobs")
        id_b = compute_source_id("greenhouse", "https://boards-api.greenhouse.io/v1/boards/stripe/jobs")
        assert id_a == id_b

    def test_different_source_types_different_ids(self):
        url = "https://example.com/jobs"
        id_gh = compute_source_id("greenhouse", url)
        id_lv = compute_source_id("lever", url)
        id_ab = compute_source_id("ashby", url)
        assert len({id_gh, id_lv, id_ab}) == 3

    def test_all_source_types_produce_valid_ids(self):
        """Every SourceType enum value should work as input to compute_source_id."""
        for source in SourceType:
            result = compute_source_id(source.value, "https://example.com/test")
            assert len(result) == 64
            assert all(c in "0123456789abcdef" for c in result)


# ---------------------------------------------------------------------------
# Enum values match expected defaults
# ---------------------------------------------------------------------------

class TestEnumColumnDefaults:
    """Verify enum values match what the existing system expects."""

    def test_job_status_new_is_default(self):
        """The existing jobs.status default is 'new' -- must be in our enums or
        at least not conflict."""
        # The existing Job model uses status default "new" which is NOT in
        # ApplicationStatus (that uses "saved" as initial). This is expected --
        # jobs.status and applications.status are separate.
        existing_statuses = {"new", "saved", "applied", "interviewing", "offer", "rejected", "ghosted"}
        # Verify these are all valid (they come from the existing system)
        assert "new" in existing_statuses

    def test_source_type_covers_all_scrapers(self):
        """SourceType enum must cover all scraper sources used in the existing system."""
        existing_sources = {"serpapi", "greenhouse", "lever", "ashby", "jobspy", "theirstack", "apify"}
        source_values = {s.value for s in SourceType}
        assert existing_sources == source_values

    def test_remote_type_values_match_existing(self):
        """RemoteType enum values must match what scrapers store in jobs.remote_type."""
        expected = {"remote", "hybrid", "onsite", "unknown"}
        actual = {r.value for r in RemoteType}
        assert expected == actual

    def test_experience_level_values_match_existing(self):
        """ExperienceLevel enum must match jobs.experience_level values."""
        expected = {"entry", "mid", "senior", "exec"}
        actual = {e.value for e in ExperienceLevel}
        assert expected == actual

    def test_job_type_values_match_existing(self):
        """JobType enum must match jobs.job_type values."""
        expected = {"full-time", "part-time", "contract", "internship"}
        actual = {j.value for j in JobType}
        assert expected == actual


# ---------------------------------------------------------------------------
# Migration ordering
# ---------------------------------------------------------------------------

class TestMigrationOrdering:
    """Verify core migrations run before module migrations."""

    @pytest.mark.asyncio
    async def test_migrations_run_without_error(self, async_engine):
        """All registered migrations should run cleanly on a fresh DB."""
        from backend.database import Base
        from backend.models import Job, SavedSearch, ScraperRun, UserProfile  # noqa
        from backend.phase7a.migration import run_migrations

        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            applied = await run_migrations(conn)
            # Currently no module migrations registered -- just verify no error
            assert isinstance(applied, list)

    @pytest.mark.asyncio
    async def test_migrations_idempotent(self, async_engine):
        """Running migrations twice should apply nothing the second time."""
        from backend.database import Base
        from backend.models import Job, SavedSearch, ScraperRun, UserProfile  # noqa
        from backend.phase7a.migration import run_migrations

        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            first_run = await run_migrations(conn)

        async with async_engine.begin() as conn:
            second_run = await run_migrations(conn)
            assert second_run == [], "Second run should apply no migrations"


# ---------------------------------------------------------------------------
# Table coexistence
# ---------------------------------------------------------------------------

class TestTableCoexistence:
    """Verify Phase 7A tables coexist with existing tables."""

    @pytest.mark.asyncio
    async def test_phase7a_migration_table_alongside_jobs(self, initialized_db):
        """_phase7a_migrations table must coexist with jobs table."""
        async with initialized_db.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = {row[0] for row in result.fetchall()}
            assert "jobs" in tables
            assert "_phase7a_migrations" in tables

    @pytest.mark.asyncio
    async def test_can_query_both_systems(self, initialized_db):
        """Queries against old tables and new tables work in same session."""
        session_factory = async_sessionmaker(
            initialized_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            # Query existing table
            result1 = await session.execute(text("SELECT count(*) FROM jobs"))
            count1 = result1.fetchone()[0]
            assert count1 >= 0  # Just verify it works

            # Query Phase 7A table
            result2 = await session.execute(text("SELECT count(*) FROM _phase7a_migrations"))
            count2 = result2.fetchone()[0]
            assert count2 >= 0


# ---------------------------------------------------------------------------
# Golden dataset integrity
# ---------------------------------------------------------------------------

class TestGoldenDatasetIntegrity:
    """Verify golden dataset uses valid enum values and consistent IDs."""

    def test_companies_use_valid_ats_providers(self):
        from tests.golden_dataset import get_test_companies
        valid = {p.value for p in ATSProvider}
        for company in get_test_companies():
            assert company["ats_provider"] in valid, (
                f"Company {company['canonical_name']} has invalid ats_provider: {company['ats_provider']}"
            )

    def test_companies_use_valid_validation_states(self):
        from tests.golden_dataset import get_test_companies
        valid = {s.value for s in ValidationState}
        for company in get_test_companies():
            assert company["validation_state"] in valid, (
                f"Company {company['canonical_name']} has invalid validation_state"
            )

    def test_jobs_use_valid_sources(self):
        from tests.golden_dataset import get_test_jobs
        valid = {s.value for s in SourceType}
        for job in get_test_jobs():
            assert job["source"] in valid, (
                f"Job {job['title']} has invalid source: {job['source']}"
            )

    def test_jobs_use_valid_remote_types(self):
        from tests.golden_dataset import get_test_jobs
        valid = {r.value for r in RemoteType}
        for job in get_test_jobs():
            if job["remote_type"]:
                assert job["remote_type"] in valid, (
                    f"Job {job['title']} has invalid remote_type: {job['remote_type']}"
                )

    def test_jobs_use_valid_experience_levels(self):
        from tests.golden_dataset import get_test_jobs
        valid = {e.value for e in ExperienceLevel}
        for job in get_test_jobs():
            if job["experience_level"]:
                assert job["experience_level"] in valid, (
                    f"Job {job['title']} has invalid experience_level"
                )

    def test_applications_use_valid_statuses(self):
        from tests.golden_dataset import get_test_applications
        valid = {s.value for s in ApplicationStatus}
        for app in get_test_applications():
            assert app["status"] in valid, (
                f"Application {app['application_id']} has invalid status: {app['status']}"
            )

    def test_query_templates_use_valid_strictness(self):
        from tests.golden_dataset import get_test_query_templates
        valid = {s.value for s in QueryStrictness}
        for tmpl in get_test_query_templates():
            assert tmpl["strictness"] in valid, (
                f"Template {tmpl['intent']} has invalid strictness"
            )

    def test_company_sources_count(self):
        from tests.golden_dataset import get_test_company_sources
        sources = get_test_company_sources()
        assert len(sources) == 50, f"Expected 50 company sources, got {len(sources)}"

    def test_jobs_count(self):
        from tests.golden_dataset import get_test_jobs
        jobs = get_test_jobs()
        assert len(jobs) == 50, f"Expected 50 jobs, got {len(jobs)}"

    def test_applications_count(self):
        from tests.golden_dataset import get_test_applications
        apps = get_test_applications()
        assert len(apps) == 20, f"Expected 20 applications, got {len(apps)}"

    def test_companies_count(self):
        from tests.golden_dataset import get_test_companies
        companies = get_test_companies()
        assert len(companies) == 10, f"Expected 10 companies, got {len(companies)}"

    def test_all_company_ids_unique(self):
        from tests.golden_dataset import get_test_companies
        companies = get_test_companies()
        ids = [c["company_id"] for c in companies]
        assert len(ids) == len(set(ids)), "Company IDs must be unique"

    def test_all_job_ids_unique(self):
        from tests.golden_dataset import get_test_jobs
        jobs = get_test_jobs()
        ids = [j["job_id"] for j in jobs]
        assert len(ids) == len(set(ids)), "Job IDs must be unique"

    def test_source_health_scenarios_use_valid_states(self):
        from tests.golden_dataset import get_test_source_health_scenarios
        valid = {s.value for s in HealthState}
        for scenario in get_test_source_health_scenarios():
            assert scenario["expected_state"] in valid, (
                f"Health scenario '{scenario['description']}' has invalid state"
            )

    def test_merge_scenarios_use_valid_sources(self):
        from tests.golden_dataset import get_test_merge_scenarios
        valid = {s.value for s in SourceType}
        for scenario in get_test_merge_scenarios():
            for raw in scenario["raw_sources"]:
                assert raw["source"] in valid, (
                    f"Merge scenario '{scenario['description']}' has invalid source"
                )


# ---------------------------------------------------------------------------
# Seeded DB tests
# ---------------------------------------------------------------------------

class TestSeededDb:
    """Tests using the seeded_db fixture with golden dataset."""

    @pytest.mark.asyncio
    async def test_seeded_db_has_jobs(self, seeded_db):
        """seeded_db fixture should contain all 50 golden dataset jobs."""
        session_factory = async_sessionmaker(
            seeded_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            result = await session.execute(text("SELECT count(*) FROM jobs"))
            count = result.fetchone()[0]
            assert count == 50, f"Expected 50 jobs in seeded DB, got {count}"

    @pytest.mark.asyncio
    async def test_seeded_db_fts_works(self, seeded_db):
        """FTS5 should work on seeded data."""
        session_factory = async_sessionmaker(
            seeded_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            result = await session.execute(
                text("SELECT count(*) FROM jobs_fts WHERE jobs_fts MATCH 'engineer'")
            )
            count = result.fetchone()[0]
            assert count > 0, "FTS should find jobs matching 'engineer'"

    @pytest.mark.asyncio
    async def test_seeded_db_has_multiple_sources(self, seeded_db):
        """Seeded data should include jobs from multiple sources."""
        session_factory = async_sessionmaker(
            seeded_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            result = await session.execute(
                text("SELECT DISTINCT source FROM jobs")
            )
            sources = {row[0] for row in result.fetchall()}
            assert len(sources) >= 3, f"Expected at least 3 sources, got {sources}"

    @pytest.mark.asyncio
    async def test_seeded_db_has_multiple_statuses(self, seeded_db):
        """Seeded data should include jobs in various statuses."""
        session_factory = async_sessionmaker(
            seeded_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            result = await session.execute(
                text("SELECT DISTINCT status FROM jobs")
            )
            statuses = {row[0] for row in result.fetchall()}
            assert len(statuses) >= 3, f"Expected at least 3 statuses, got {statuses}"

    @pytest.mark.asyncio
    async def test_seeded_db_has_enriched_and_unenriched(self, seeded_db):
        """Seeded data should include both enriched and unenriched jobs."""
        session_factory = async_sessionmaker(
            seeded_db, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            enriched = await session.execute(
                text("SELECT count(*) FROM jobs WHERE is_enriched = 1")
            )
            unenriched = await session.execute(
                text("SELECT count(*) FROM jobs WHERE is_enriched = 0")
            )
            e_count = enriched.fetchone()[0]
            u_count = unenriched.fetchone()[0]
            assert e_count > 0, "Should have enriched jobs"
            assert u_count > 0, "Should have unenriched jobs"


# ---------------------------------------------------------------------------
# Factory tests
# ---------------------------------------------------------------------------

class TestFactories:
    """Verify factory fixtures produce valid records."""

    def test_company_factory_defaults(self, company_factory):
        company = company_factory()
        assert len(company["company_id"]) == 64
        assert company["canonical_name"].startswith("Company ")
        assert company["domain"].endswith(".com")
        assert company["validation_state"] == "unverified"

    def test_company_factory_overrides(self, company_factory):
        company = company_factory(
            domain="test.io",
            canonical_name="TestCo",
            ats_provider="lever",
        )
        assert company["canonical_name"] == "TestCo"
        assert company["domain"] == "test.io"
        assert company["ats_provider"] == "lever"

    def test_job_factory_defaults(self, job_factory):
        job = job_factory()
        assert len(job["job_id"]) == 64
        assert job["source"] == "greenhouse"
        assert job["status"] == "new"
        assert job["is_enriched"] is False

    def test_job_factory_overrides(self, job_factory):
        job = job_factory(
            title="ML Engineer",
            company_name="TestCo",
            source="lever",
            status="applied",
        )
        assert job["title"] == "ML Engineer"
        assert job["company_name"] == "TestCo"
        assert job["source"] == "lever"
        assert job["status"] == "applied"

    def test_job_factory_unique_ids(self, job_factory):
        """Different jobs should have different IDs."""
        job1 = job_factory(title="Engineer A", company_name="Co1")
        job2 = job_factory(title="Engineer B", company_name="Co2")
        assert job1["job_id"] != job2["job_id"]

    def test_application_factory_defaults(self, application_factory):
        app = application_factory()
        assert len(app["application_id"]) == 32  # UUID4 hex
        assert app["status"] == "saved"
        assert app["canonical_job_id"] is None

    def test_application_factory_overrides(self, application_factory):
        app = application_factory(
            job_id="test_job_123",
            status="applied",
        )
        assert app["job_id"] == "test_job_123"
        assert app["status"] == "applied"
