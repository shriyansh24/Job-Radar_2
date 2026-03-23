# Codebase Audit Index - JobRadar V2

> **Date:** 2026-03-23 | **Original Audit Issues:** 44
>
> **Current Outcome:** 39 `FIXED` | 1 `VERIFIED_CLEAN` | 4 `STALE` | 0 `OPEN` | 0 `PARTIAL`

> This file is the bug ledger. For the current operational read order and live repo state, start at `docs/current-state/00-index.md`.

## Latest Validation Snapshot

- Full validation and stale-item recheck on `2026-03-23`:
  - `git ls-files '.env' 'backend/.env' '.env.*' 'backend/.env.*'`
  - `Get-ChildItem -Force .env*`
  - `Get-ChildItem -Force backend\\.env*`
  - `git grep -n "ApifyScraper|run_scrape|EventBus|DeduplicationService" backend/app backend/tests`
  - `cd backend && uv run python -m pip check`
  - `cd backend && uv export --frozen --format requirements-txt --no-emit-project -o .ci-requirements.txt`
  - `cd backend && uv tool run pip-audit -r .ci-requirements.txt`
  - `cd backend && uv tool run bandit -r app/ -c pyproject.toml --severity-level medium`
  - `cd backend && uv run ruff check .`
  - `cd backend && uv run mypy app/auth/service.py app/config.py app/shared/middleware.py app/scraping/deduplication.py app/scraping/port.py --ignore-missing-imports`
  - `cd backend && uv run pytest --cov=app --cov-fail-under=60 tests/`
  - `cd frontend && npm audit --audit-level high`
  - `cd frontend && npm run lint`
  - `cd frontend && npm run test -- --run`
  - `cd frontend && npm install --no-save @vitest/coverage-v8`
  - `cd frontend && npm run test -- --run --coverage --coverage.thresholds.statements=40`
  - `cd frontend && npm run build`
- Local results from this pass:
  - no tracked `.env` file in this clone; only `.env.example`
  - `ApifyScraper` is still imported and registered in the live `ScrapingService.run_scrape()` path
  - backend full suite passed: `539 passed`, coverage `60.10%`
  - frontend full suite passed: `23` test files, `35` tests, coverage `43.19%` statements
  - `pip check`, `pip-audit`, `bandit`, backend `ruff`, targeted backend `mypy`, frontend `npm audit`, lint, and build all passed

## How to Use This Index

1. Use the table below to find the current status of each audited item.
2. `FIXED` means the issue was real and is now resolved in code.
3. `VERIFIED_CLEAN` means the original issue claim was specifically rechecked and the repository is clean for that condition.
3. `STALE` means the original audit claim no longer matches the live code path.

## Segment Files

| File | Domain | Issues |
|------|--------|--------|
| [01-security.md](01-security.md) | Secrets, auth, CORS, headers | 7 |
| [02-backend.md](02-backend.md) | API, services, error handling | 9 |
| [03-scraper.md](03-scraper.md) | Scrapers, rate limiting, dedup | 14 |
| [04-database.md](04-database.md) | Models, migrations, queries | 6 |
| [05-frontend.md](05-frontend.md) | React, API clients, UI | 3 |
| [06-infra.md](06-infra.md) | Docker, CI/CD, deps, config | 5 |

## Master Issue Table

| ID | Sev | One-liner | Segment | Status |
|----|-----|-----------|---------|--------|
| SEC-01 | CRIT | Live API keys committed to `.env` in repo | security | VERIFIED_CLEAN |
| SEC-02 | CRIT | JWT tokens in localStorage (XSS vulnerable) | security | FIXED |
| SEC-03 | CRIT | Default secret key `change-me-in-production` not blocked | security | FIXED |
| SEC-04 | HIGH | CORS allows `*` methods and `*` headers | security | FIXED |
| SEC-05 | HIGH | No security headers (X-Frame-Options, HSTS, CSP) | security | FIXED |
| SEC-06 | MED | No token revocation mechanism for compromised JWTs | security | FIXED |
| SEC-07 | MED | No endpoint rate limiting on API routes | security | FIXED |
| BE-01 | CRIT | Hardcoded `/tmp` path in auto_apply crashes on Windows | backend | FIXED |
| BE-02 | CRIT | 9x bare `except Exception: pass` in scraping_worker | backend | FIXED |
| BE-03 | HIGH | `asyncio.gather(return_exceptions=True)` then commits partial failures | backend | FIXED |
| BE-04 | HIGH | LLM failures return empty dict, caller can't distinguish | backend | FIXED |
| BE-05 | HIGH | Interview service returns placeholder questions on failure | backend | FIXED |
| BE-06 | HIGH | No timeout on `run_scrape()` - can block indefinitely | backend | FIXED |
| BE-07 | MED | Assertion in production code (`rate_limiter.py:147`) | backend | FIXED |
| BE-08 | MED | Event callback failure treated as scraper failure | backend | FIXED |
| BE-09 | LOW | Adapter registry logs at DEBUG level - invisible in prod | backend | FIXED |
| SC-01 | CRIT | `ScrapeAttempt` pagination metadata still not persisted | scraper | FIXED |
| SC-02 | CRIT | Workday URL regex case-sensitive - NVIDIA uppercase fails | scraper | FIXED |
| SC-03 | CRIT | Circuit breaker stuck in half-open - never recovers | scraper | STALE |
| SC-04 | HIGH | No JSON validation in ATS scrapers - malformed responses crash | scraper | FIXED |
| SC-05 | HIGH | EventBus.publish() - one dead subscriber blocks all | scraper | STALE |
| SC-06 | HIGH | Missing Workday rate policy - falls back to generic behavior | scraper | FIXED |
| SC-07 | HIGH | Simhash threshold too aggressive - false positive dedup | scraper | STALE |
| SC-08 | MED | Browser pool domain semaphores never cleaned - memory leak | scraper | FIXED |
| SC-09 | MED | PageCrawler URL loop detection ignores normalization | scraper | FIXED |
| SC-10 | MED | Ashby GraphQL errors silently treated as "no jobs" | scraper | FIXED |
| SC-11 | MED | No pagination timeout - `crawler.crawl()` can hang | scraper | FIXED |
| SC-12 | MED | Scheduler no validation of `schedule_interval_m` | scraper | FIXED |
| SC-13 | LOW | ScrapingBee scraper remains unused in live registration paths | scraper | FIXED |
| SC-14 | LOW | Apify scraper: 65 lines, never used - DROP | scraper | STALE |
| DB-01 | HIGH | Multiple DateTime columns still missing `timezone=True` | database | FIXED |
| DB-02 | HIGH | Nullable FKs without cascade - orphaned records on delete | database | FIXED |
| DB-03 | HIGH | No connection pool config (pool_size, pool_pre_ping) | database | FIXED |
| DB-04 | MED | Embedding batch commits partial failures | database | FIXED |
| DB-05 | MED | Migration downgrade doesn't handle pgvector extension | database | FIXED |
| DB-06 | LOW | N+1 query patterns - Job.applications lazy-loaded | database | FIXED |
| FE-01 | HIGH | SSE token passed as URL query parameter | frontend | FIXED |
| FE-02 | HIGH | Admin "Rebuild Embeddings" calls wrong API (`reindex`) | frontend | FIXED |
| FE-03 | MED | Vault API client still missing PATCH update flows (DELETE implemented) | frontend | FIXED |
| INF-01 | HIGH | No `.dockerignore` - build includes secrets and tests | infra | FIXED |
| INF-02 | MED | No Docker health checks for backend/redis/nginx | infra | FIXED |
| INF-03 | MED | No Redis auth or TLS | infra | FIXED |
| INF-04 | LOW | CI has no security scanning (Dependabot, SAST) | infra | FIXED |
| INF-05 | LOW | Orphaned config keys are overstated; only `JR_SCRAPLING_ENABLED` still looks unused | infra | FIXED |

## Deferred Work (Not Bugs - Planned Features)

| ID | Feature | Phase | Segment |
|----|---------|-------|---------|
| DEF-01 | Resume PDF generation + templates | Phase D | backend |
| DEF-03 | Targets add/edit/delete career page UI | Phase B | frontend |
| DEF-04 | Saved Search Alerts UI + scheduler trigger | Phase B | frontend |
| DEF-05 | E2E Playwright tests | Phase C | infra |
| DEF-06 | Conditional requests (ETag/If-Modified-Since) | Phase 3 | scraper |
| DEF-07 | robots.txt checking via Protego | Phase 3 | scraper |
| DEF-08 | Protego library wired into execution loop | Phase 3 | scraper |

## Verified Fixes Since Initial Audit

> These were verified after the original audit and sit outside the 44-item list above.

| ID | Domain | One-liner | Status |
|----|--------|-----------|--------|
| FIX-01 | backend | `/api/v1/admin/health` no longer requires auth, restoring health probes and integration tests | FIXED |
| FIX-02 | infra | `uv run pytest` now resolves correctly via `[dependency-groups].dev` and explicit conflicting extras metadata | FIXED |
| FIX-03 | frontend | TypeScript nullability regressions in Auto Apply / Interview Prep / Vault / Resume Builder no longer fail `npm run build` | FIXED |
| FIX-04 | frontend | Login test now matches current heading markup instead of brittle combined text lookup | FIXED |
| FIX-05 | database | `Notification.created_at` now matches the timezone-aware schema and is covered by the model contract test | FIXED |
| FIX-06 | scraper | `CircuitBreaker` timing is hardened with a high-resolution monotonic clock path and deterministic recovery tests | FIXED |
| FIX-07 | backend | Failed enrichment no longer persists partial job cleanup/enrichment field mutations | FIXED |
| FIX-08 | backend | Interview generation/prep now fail on empty model payloads, and job context loads `company_name` correctly | FIXED |
| FIX-09 | infra | CI workflows are updated to `actions/*@v6` and now enforce lock-aware dependency-health checks (`pip check`, exported-requirements `pip-audit`, `npm audit`) | FIXED |
