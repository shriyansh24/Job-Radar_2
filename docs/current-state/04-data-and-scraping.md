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
- Target execution uses scheduler-based selection plus tier routing, and target batches now parse before escalation instead of recording zero-extraction success paths.
- Page crawling supports normalized loop detection and bounded pagination.
- Fetcher-based target batches now honor `ETag` / `If-Modified-Since` when target cache metadata exists, and successful fetches refresh `etag`, `last_modified`, `last_http_status`, and `content_hash` on the target record.
- Non-ATS target batches now evaluate `robots.txt` through Protego before network fetches, with allow/warn/block outcomes emitted in structured logs and persisted attempts.
- Browser-pool domain semaphores clean up after last use.
- Workday has a dedicated rate policy.

## Recent Verified Fixes
- Workday URL matching is case-insensitive.
- ATS adapters validate malformed root JSON payloads instead of crashing.
- Pagination is bounded by timeout.
- Pagination timeouts now fall back to first-page parsing instead of converting a successful fetch into a failed target run.
- Conditional requests are live on fetcher tiers and covered by dedicated request-cache regression tests.
- Protego enforcement is live on non-ATS targets and covered by deterministic allow/deny/unavailable policy tests.
- Target batches now persist discovered jobs from ATS, fetcher, and browser paths instead of only recording attempts.
- Scheduler intervals are clamped to positive minimums.
- Circuit-breaker timing uses a high-resolution monotonic clock path and deterministic regression coverage.
- Adaptive parser fixture coverage now includes selector-driven pages, JSON-LD-only pages, JS-shell blanks, and embedded hydration/state payloads so parser regressions are evidence-driven.
- Adaptive parser diagnostics now classify fixture outcomes by extraction path or anti-bot / JS-shell signal, so the remaining source-quality work can be isolated from real parser regressions.
- The queue-backed runtime no longer schedules a separate legacy career-page worker outside the target-batch pipeline; conditional requests, robots policy, and adaptive parsing now share one authoritative career-page execution path.

## Operational Notes
- Historical implementation/inventory context now lives in `docs/system-inventory/` and `docs/repo-hardening/`.
- `docs/audit/03-scraper.md` is the bug ledger for scraper issues.
- The live branch now executes scheduled scraping and adjacent background work through the dedicated scheduler plus ARQ queue boundary; `scraping`, `analysis`, and `ops` are owned by queue-specific worker services.
- ATS identity persistence is no longer branch-only: the current branch now includes the job-model columns, Alembic migration, and regression tests for ATS composite-key updates.

## Current Assessment
- No known blocking scraper or database bugs remain after the latest verified pass.
- Queue-backed scraping/runtime ownership is implemented locally. The remaining follow-through is deployment-level alert routing and dashboards rather than missing repo-local scraper/runtime behavior.
- Remaining parser work is source-specific render and anti-bot recovery on difficult JS-heavy sites; the base target-batch execution path, adaptive parser baselines, conditional requests, and robots policy are now live and locally validated.
- The remaining parser work is now backed by a deterministic fixture matrix that distinguishes selector, JSON-LD, embedded-state, JS-shell, and Cloudflare-challenge pages; anything beyond that is source-specific render or provider-side behavior rather than an unclassified parser gap.
