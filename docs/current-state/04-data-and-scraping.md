# Data And Scraping State - JobRadar V2

## Data Model Highlights
- `jobs` uses SHA-256 string primary keys.
- `scrape_targets`, `scrape_attempts`, and `scraper_runs` support target orchestration and telemetry.
- Job lifecycle tracking includes first/last seen timestamps and disappearance tracking.
- Notification timestamps are timezone-aware in both ORM and schema.

## Scraping Platform Highlights
- ATS detection supports multiple vendors including Workday, Greenhouse, Lever, and Ashby.
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
- `docs/superpowers/` contains the historical design/build plan for this subsystem.
- `docs/audit/03-scraper.md` is the bug ledger for scraper issues.

## Current Assessment
- No known blocking scraper or database bugs remain after the latest verified pass.
