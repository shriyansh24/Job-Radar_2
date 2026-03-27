# Data And Scraping State - JobRadar V2

## Data Model Highlights
- `jobs` uses SHA-256 string primary keys.
- `scrape_targets`, `scrape_attempts`, and `scraper_runs` support target orchestration and telemetry.
- `jobs` now also persist ATS identity fields (`ats_job_id`, `ats_provider`, `ats_composite_key`) for normalization-aware dedup and stable source identity.
- Job lifecycle tracking includes first/last seen timestamps and disappearance tracking.
- Notification timestamps are timezone-aware in both ORM and schema.

## Scraping Platform Highlights
- ATS detection supports multiple vendors including Workday, Greenhouse, Lever, and Ashby.
- Greenhouse, Lever, and Workday scraping now emit ATS identity into the normalized `ScrapedJob` shape before persistence.
- Target execution uses scheduler-based selection plus tier routing.
- Page crawling supports normalized loop detection and bounded pagination.
- Browser-pool domain semaphores clean up after last use.
- Workday has a dedicated rate policy.

## Recent Verified Fixes
- Workday URL matching is case-insensitive.
- ATS adapters validate malformed root JSON payloads instead of crashing.
- Pagination is bounded by timeout.
- Scheduler intervals are clamped to positive minimums.
- Circuit-breaker timing uses a high-resolution monotonic clock path and deterministic regression coverage.

## Operational Notes
- Historical implementation/inventory context now lives in `docs/system-inventory/` and `docs/repo-hardening/`.
- `docs/audit/03-scraper.md` is the bug ledger for scraper issues.
- The live branch now executes scheduled scraping and adjacent background work through the dedicated scheduler plus ARQ queue boundary; `scraping`, `analysis`, and `ops` are owned by queue-specific worker services.
- ATS identity persistence is no longer branch-only: the current branch now includes the job-model columns, Alembic migration, and regression tests for ATS composite-key updates.

## Current Assessment
- No known blocking scraper or database bugs remain after the latest verified pass.
- The remaining runtime gaps are queue alerting / sustained-pressure visibility, retry-exhaustion handling, and broader worker coverage, not scraper topology ownership.
