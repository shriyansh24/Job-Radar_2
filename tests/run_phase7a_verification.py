"""
Phase 7A Verification Script
Run: python -m tests.run_phase7a_verification

Checks:
1. All imports resolve
2. All enums have expected members
3. All ID generators produce valid output
4. Migration table exists and is queryable
5. Existing models still functional
6. No schema conflicts between Phase 7A and existing tables
7. Golden dataset integrity

Exit code 0 = all checks passed
Exit code 1 = one or more checks failed
"""

import asyncio
import hashlib
import re
import sys
import traceback
from datetime import datetime, timezone

HEX_64 = re.compile(r"^[0-9a-f]{64}$")
HEX_32 = re.compile(r"^[0-9a-f]{32}$")

_passed = 0
_failed = 0
_errors = []


def check(description: str, condition: bool, detail: str = ""):
    """Record a check result."""
    global _passed, _failed
    if condition:
        _passed += 1
        print(f"  [PASS] {description}")
    else:
        _failed += 1
        msg = f"  [FAIL] {description}"
        if detail:
            msg += f" -- {detail}"
        print(msg)
        _errors.append(msg)


def section(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


# ---------------------------------------------------------------------------
# 1. Import checks
# ---------------------------------------------------------------------------

def check_imports():
    section("1. Import Checks")

    try:
        from backend.phase7a.constants import (
            ATSProvider, SourceType, ValidationState, HealthState,
            ApplicationStatus, RemoteType, ExperienceLevel, JobType,
            ChangeSource, CheckType, CheckStatus, QueryStrictness,
            SOURCE_QUALITY_ORDER, CONFIDENCE_SIGNALS, BACKOFF_SCHEDULE,
        )
        check("Phase 7A constants import", True)
    except ImportError as e:
        check("Phase 7A constants import", False, str(e))

    try:
        from backend.phase7a.id_utils import (
            compute_company_id, compute_source_id, compute_raw_job_id,
            compute_canonical_job_id, compute_template_id, generate_application_id,
            normalize_domain, normalize_company_name, normalize_title, normalize_location,
        )
        check("Phase 7A id_utils import", True)
    except ImportError as e:
        check("Phase 7A id_utils import", False, str(e))

    try:
        from backend.phase7a.migration import (
            register_migration, run_migrations, get_registered_migrations,
        )
        check("Phase 7A migration import", True)
    except ImportError as e:
        check("Phase 7A migration import", False, str(e))

    try:
        from backend.database import Base, init_db
        check("backend.database import", True)
    except ImportError as e:
        check("backend.database import", False, str(e))

    try:
        from backend.models import Job, SavedSearch, ScraperRun, UserProfile
        check("backend.models import", True)
    except ImportError as e:
        check("backend.models import", False, str(e))

    try:
        from tests.golden_dataset import (
            get_test_companies, get_test_jobs, get_test_applications,
            get_test_company_sources, get_test_query_templates,
            get_test_expansion_rules, get_full_golden_dataset,
        )
        check("Golden dataset import", True)
    except ImportError as e:
        check("Golden dataset import", False, str(e))


# ---------------------------------------------------------------------------
# 2. Enum membership checks
# ---------------------------------------------------------------------------

def check_enums():
    section("2. Enum Membership Checks")

    from backend.phase7a.constants import (
        ATSProvider, SourceType, ValidationState, HealthState,
        ApplicationStatus, RemoteType, ExperienceLevel, JobType,
    )

    check("ATSProvider has 8 members", len(ATSProvider) == 8,
          f"got {len(ATSProvider)}")
    check("SourceType has 7 members", len(SourceType) == 7,
          f"got {len(SourceType)}")
    check("ValidationState has 5 members", len(ValidationState) == 5,
          f"got {len(ValidationState)}")
    check("HealthState has 5 members", len(HealthState) == 5,
          f"got {len(HealthState)}")
    check("ApplicationStatus has 11 members", len(ApplicationStatus) == 11,
          f"got {len(ApplicationStatus)}")
    check("RemoteType has 4 members", len(RemoteType) == 4,
          f"got {len(RemoteType)}")
    check("ExperienceLevel has 4 members", len(ExperienceLevel) == 4,
          f"got {len(ExperienceLevel)}")
    check("JobType has 4 members", len(JobType) == 4,
          f"got {len(JobType)}")

    # Verify no duplicate values in any enum
    all_enums = [
        ATSProvider, SourceType, ValidationState, HealthState,
        ApplicationStatus, RemoteType, ExperienceLevel, JobType,
    ]
    for enum_cls in all_enums:
        values = [m.value for m in enum_cls]
        check(f"{enum_cls.__name__} has no duplicate values",
              len(values) == len(set(values)))


# ---------------------------------------------------------------------------
# 3. ID generator checks
# ---------------------------------------------------------------------------

def check_id_generators():
    section("3. ID Generator Checks")

    from backend.phase7a.id_utils import (
        compute_company_id, compute_source_id, compute_raw_job_id,
        compute_canonical_job_id, compute_template_id, generate_application_id,
    )

    # Company ID
    cid = compute_company_id("stripe.com")
    check("compute_company_id produces 64-char hex", bool(HEX_64.match(cid)),
          f"got '{cid}'")

    # Deterministic
    cid2 = compute_company_id("stripe.com")
    check("compute_company_id is deterministic", cid == cid2)

    # Case insensitive
    cid3 = compute_company_id("Stripe.COM")
    check("compute_company_id case insensitive", cid == cid3)

    # Source ID
    sid = compute_source_id("greenhouse", "https://example.com/jobs")
    check("compute_source_id produces 64-char hex", bool(HEX_64.match(sid)))

    # Raw job ID
    rid = compute_raw_job_id("greenhouse", "12345")
    check("compute_raw_job_id produces 64-char hex", bool(HEX_64.match(rid)))

    # Canonical job ID
    canon = compute_canonical_job_id("company1", "ML Engineer", "San Francisco, CA")
    check("compute_canonical_job_id produces 64-char hex", bool(HEX_64.match(canon)))

    # Template ID
    tid = compute_template_id("ML Engineer")
    check("compute_template_id produces 64-char hex", bool(HEX_64.match(tid)))

    # Application ID
    aid = generate_application_id()
    check("generate_application_id produces 32-char hex", bool(HEX_32.match(aid)))

    # Uniqueness
    aids = {generate_application_id() for _ in range(100)}
    check("generate_application_id produces unique IDs", len(aids) == 100)


# ---------------------------------------------------------------------------
# 4. Migration table check
# ---------------------------------------------------------------------------

async def check_migration_table():
    section("4. Migration Table Check")

    from sqlalchemy.ext.asyncio import create_async_engine
    from backend.database import Base
    from backend.models import Job, SavedSearch, ScraperRun, UserProfile  # noqa
    from backend.phase7a.migration import run_migrations
    from sqlalchemy import text

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            applied = await run_migrations(conn)
            check("run_migrations returns list", isinstance(applied, list))

            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='_phase7a_migrations'")
            )
            check("_phase7a_migrations table exists", result.fetchone() is not None)

            result = await conn.execute(text("PRAGMA table_info(_phase7a_migrations)"))
            columns = {row[1] for row in result.fetchall()}
            check("Migration table has 'name' column", "name" in columns)
            check("Migration table has 'applied_at' column", "applied_at" in columns)
    finally:
        await engine.dispose()


# ---------------------------------------------------------------------------
# 5. Existing models check
# ---------------------------------------------------------------------------

async def check_existing_models():
    section("5. Existing Models Check")

    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from backend.database import Base
    from backend.models import Job, SavedSearch, ScraperRun, UserProfile  # noqa
    from backend.phase7a.migration import run_migrations
    from sqlalchemy import text
    import json

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await run_migrations(conn)

        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with session_factory() as session:
            # Test Job insert
            now = datetime.now(timezone.utc).isoformat()
            try:
                await session.execute(text("""
                    INSERT INTO jobs (job_id, source, url, company_name, title, status,
                                      is_active, is_enriched, is_starred, scraped_at, last_updated)
                    VALUES ('verify_001', 'gh', 'https://x.com/v', 'VerifyCo', 'Eng', 'new',
                            1, 0, 0, :sa, :lu)
                """), {"sa": now, "lu": now})
                await session.commit()
                check("Job INSERT works", True)
            except Exception as e:
                check("Job INSERT works", False, str(e))

            # Test SavedSearch insert
            try:
                await session.execute(text("""
                    INSERT INTO saved_searches (name, query_params, alert_enabled, created_at)
                    VALUES ('verify_search', '{}', 0, CURRENT_TIMESTAMP)
                """))
                await session.commit()
                check("SavedSearch INSERT works", True)
            except Exception as e:
                check("SavedSearch INSERT works", False, str(e))

            # Test ScraperRun insert
            try:
                await session.execute(text("""
                    INSERT INTO scraper_runs (source, started_at, status, jobs_found, jobs_new, jobs_updated)
                    VALUES ('greenhouse', :sa, 'completed', 10, 5, 3)
                """), {"sa": now})
                await session.commit()
                check("ScraperRun INSERT works", True)
            except Exception as e:
                check("ScraperRun INSERT works", False, str(e))

            # Test UserProfile insert
            try:
                await session.execute(text("""
                    INSERT INTO user_profile (id) VALUES (1)
                """))
                await session.commit()
                check("UserProfile INSERT works", True)
            except Exception as e:
                check("UserProfile INSERT works", False, str(e))
    finally:
        await engine.dispose()


# ---------------------------------------------------------------------------
# 6. Schema conflict check
# ---------------------------------------------------------------------------

async def check_no_schema_conflicts():
    section("6. Schema Conflict Check")

    from sqlalchemy.ext.asyncio import create_async_engine
    from backend.database import Base
    from backend.models import Job, SavedSearch, ScraperRun, UserProfile  # noqa
    from backend.phase7a.migration import run_migrations
    from sqlalchemy import text

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await run_migrations(conn)

            # Get all tables
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = {row[0] for row in result.fetchall()}

            expected = {"jobs", "saved_searches", "scraper_runs", "user_profile", "_phase7a_migrations"}
            check("All expected tables exist",
                  expected.issubset(tables),
                  f"Missing: {expected - tables}")

            # Verify no table name conflicts
            check("No unexpected Phase 7A tables yet",
                  not any(t.startswith("companies") for t in tables),
                  "Module tables should not exist before module migrations run")
    finally:
        await engine.dispose()


# ---------------------------------------------------------------------------
# 7. Golden dataset integrity
# ---------------------------------------------------------------------------

def check_golden_dataset():
    section("7. Golden Dataset Integrity")

    from tests.golden_dataset import (
        get_test_companies, get_test_jobs, get_test_applications,
        get_test_company_sources, get_test_query_templates,
        get_test_expansion_rules, get_full_golden_dataset,
    )
    from backend.phase7a.constants import (
        ATSProvider, SourceType, ValidationState, ApplicationStatus,
    )

    companies = get_test_companies()
    check("10 test companies", len(companies) == 10, f"got {len(companies)}")

    sources = get_test_company_sources()
    check("50 company sources", len(sources) == 50, f"got {len(sources)}")

    jobs = get_test_jobs()
    check("50 test jobs", len(jobs) == 50, f"got {len(jobs)}")

    apps = get_test_applications()
    check("20 test applications", len(apps) == 20, f"got {len(apps)}")

    templates = get_test_query_templates()
    check("5 query templates", len(templates) == 5, f"got {len(templates)}")

    rules = get_test_expansion_rules()
    check("6 expansion rules", len(rules) == 6, f"got {len(rules)}")

    # Verify all company IDs are unique
    company_ids = [c["company_id"] for c in companies]
    check("All company IDs unique",
          len(company_ids) == len(set(company_ids)))

    # Verify all job IDs are unique
    job_ids = [j["job_id"] for j in jobs]
    check("All job IDs unique",
          len(job_ids) == len(set(job_ids)))

    # Full dataset
    full = get_full_golden_dataset()
    check("Full golden dataset has 8 keys", len(full) == 8)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n" + "=" * 60)
    print("  Phase 7A Verification Script")
    print("=" * 60)

    # Sync checks
    check_imports()
    check_enums()
    check_id_generators()
    check_golden_dataset()

    # Async checks
    asyncio.run(check_migration_table())
    asyncio.run(check_existing_models())
    asyncio.run(check_no_schema_conflicts())

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  RESULTS: {_passed} passed, {_failed} failed")
    print(f"{'=' * 60}")

    if _errors:
        print("\nFailed checks:")
        for err in _errors:
            print(err)

    sys.exit(0 if _failed == 0 else 1)


if __name__ == "__main__":
    main()
