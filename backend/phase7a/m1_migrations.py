"""Module 1 — Company Intelligence Registry: Additive migrations.

All migrations here are registered via @register_migration and run by
the Phase 7A migration runner (backend.phase7a.migration.run_migrations).

Migration order:
    m1_001 — Create companies table + indexes
    m1_002 — Create company_sources table + indexes
    m1_003 — Create ats_detection_log table + indexes
    m1_004 — Seed companies from existing jobs table

Rules:
    - Additive only: no DROP, no RENAME of existing columns/tables.
    - All DDL uses CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS
      for idempotency.
    - Seed migration is safe to re-run (INSERT OR IGNORE).
"""

import logging

from sqlalchemy import text

from backend.phase7a.migration import register_migration

logger = logging.getLogger(__name__)


@register_migration("m1_001_create_companies_table")
async def create_companies_table(conn) -> None:
    """Create the companies table and its indexes."""
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS companies (
            company_id    TEXT(64) PRIMARY KEY,
            canonical_name TEXT(255) NOT NULL UNIQUE,
            domain        TEXT(255) UNIQUE,
            domain_aliases JSON,
            ats_provider  TEXT(32),
            ats_slug      TEXT(128),
            careers_url   TEXT(512),
            board_urls    JSON,
            logo_url      TEXT(512),
            validation_state TEXT(16) NOT NULL DEFAULT 'unverified',
            confidence_score INTEGER DEFAULT 0,
            last_validated_at DATETIME,
            last_probe_at DATETIME,
            probe_error   TEXT,
            manual_override BOOLEAN DEFAULT 0,
            override_fields JSON,
            created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at    DATETIME
        )
    """))

    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_companies_domain "
        "ON companies (domain)"
    ))
    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_companies_canonical_name "
        "ON companies (canonical_name)"
    ))
    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_companies_ats_provider_slug "
        "ON companies (ats_provider, ats_slug)"
    ))
    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_companies_validation_state "
        "ON companies (validation_state, last_validated_at)"
    ))

    logger.info("Created companies table with indexes")


@register_migration("m1_002_create_company_sources_table")
async def create_company_sources_table(conn) -> None:
    """Create the company_sources table and its indexes."""
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS company_sources (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id      TEXT(64) NOT NULL REFERENCES companies(company_id),
            source          TEXT(32) NOT NULL,
            source_identifier TEXT(255),
            source_url      TEXT(512),
            jobs_count      INTEGER DEFAULT 0,
            last_seen_at    DATETIME,
            first_seen_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))

    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_company_sources_company_id "
        "ON company_sources (company_id)"
    ))
    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_company_sources_source "
        "ON company_sources (source, source_identifier)"
    ))

    logger.info("Created company_sources table with indexes")


@register_migration("m1_003_create_ats_detection_log_table")
async def create_ats_detection_log_table(conn) -> None:
    """Create the ats_detection_log table and its indexes."""
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ats_detection_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id      TEXT(64) NOT NULL REFERENCES companies(company_id),
            probe_url       TEXT(512) NOT NULL,
            detected_provider TEXT(32),
            detection_method TEXT(32),
            confidence      INTEGER,
            probe_status    INTEGER,
            probe_duration_ms INTEGER,
            probed_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            error_message   TEXT
        )
    """))

    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_ats_detection_log_company_id "
        "ON ats_detection_log (company_id, probed_at)"
    ))

    logger.info("Created ats_detection_log table with indexes")


@register_migration("m1_004_seed_companies_from_jobs")
async def seed_companies_from_jobs(conn) -> None:
    """Seed the companies table from existing jobs data.

    This migration reads distinct (company_name, company_domain) pairs
    from the existing jobs table and creates company records for each.

    Behavior:
    - Uses INSERT OR IGNORE to be safe for re-runs.
    - Generates deterministic company_id using the same SHA256 logic
      as compute_company_id() from id_utils.
    - Companies with a domain use the domain for ID generation.
    - Companies without a domain use the name for ID generation.
    - All seeded companies start as 'unverified' with confidence_score=0.
    """
    # Check if the jobs table exists (it may not in fresh test DBs
    # that haven't created legacy tables)
    result = await conn.execute(text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'"
    ))
    if result.fetchone() is None:
        logger.info("No jobs table found; skipping seed migration")
        return

    # Count existing jobs for progress logging
    count_result = await conn.execute(text(
        "SELECT COUNT(DISTINCT company_name) FROM jobs"
    ))
    total = count_result.scalar() or 0
    if total == 0:
        logger.info("No jobs found; skipping seed migration")
        return

    logger.info("Seeding companies from %d distinct company names in jobs", total)

    # We need to compute SHA256 IDs in Python since SQLite doesn't have
    # a built-in SHA256 function. Fetch distinct pairs and insert.
    result = await conn.execute(text("""
        SELECT DISTINCT company_name, company_domain
        FROM jobs
        WHERE company_name IS NOT NULL AND company_name != ''
    """))
    rows = result.fetchall()

    # Import here to avoid circular imports at module load time
    from backend.phase7a.id_utils import compute_company_id, normalize_domain

    inserted = 0
    skipped = 0
    for row in rows:
        company_name = row[0]
        company_domain = row[1]

        # Determine ID from domain or name
        if company_domain and company_domain.strip():
            normalized = normalize_domain(company_domain)
            company_id = compute_company_id(normalized)
            domain_val = normalized
        else:
            company_id = compute_company_id(company_name)
            domain_val = None

        # INSERT OR IGNORE so duplicates are silently skipped
        try:
            await conn.execute(
                text("""
                    INSERT OR IGNORE INTO companies
                        (company_id, canonical_name, domain, validation_state,
                         confidence_score, manual_override, created_at)
                    VALUES
                        (:company_id, :canonical_name, :domain, 'unverified',
                         0, 0, CURRENT_TIMESTAMP)
                """),
                {
                    "company_id": company_id,
                    "canonical_name": company_name,
                    "domain": domain_val,
                },
            )
            inserted += 1
        except Exception as e:
            # This can happen with UNIQUE constraint violations on
            # canonical_name when two different domains map to the
            # same company name. Safe to skip.
            logger.debug(
                "Skipped seeding company '%s': %s", company_name, e
            )
            skipped += 1

    logger.info(
        "Seed complete: %d attempted, %d skipped (duplicates/conflicts)",
        inserted, skipped,
    )
