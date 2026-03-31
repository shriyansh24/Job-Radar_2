# Change Rationale Log

## Purpose
Record why major repo-hardening decisions were made, what alternatives were rejected, and what risk remains.

## Source-Of-Truth Status
- Status: `DOCUMENTED_WORKING_SET`
- Scope: rationale for hardening-program changes
- Last validation basis: direct repo edits and evidence artifacts on `2026-03-27`

## Entries

### Compose-first runtime baseline
- Status: `FIXED`
- Changed because:
  - `.env.example`, `docker-compose.yml`, and backend config already agreed on the compose DB/Redis baseline
  - `CLAUDE.md` and older README text still described a manual-local `5433` path as if it were canonical
- Alternatives considered:
  - make the manual-local `5433` path canonical
- Why rejected:
  - it conflicts with the checked-in compose stack and backend defaults
- Files touched:
  - `.env.example`
  - `backend/app/config.py`
  - `README.md`
  - `CLAUDE.md`
  - `docs/current-state/05-ops-and-ci.md`
- Remaining risk:
  - developers who still use the legacy manual container path need it documented as an override, not removed from their heads

### Dedicated scheduler runtime split
- Status: `FIXED`
- Changed because:
  - `backend/app/main.py` previously owned the APScheduler lifecycle, which made API readiness and scheduler readiness indistinguishable
  - the completion plan requires an explicit process topology rather than scheduler work hiding inside the web process
- Alternatives considered:
  - keep the scheduler in the API process and only document the coupling
- Why rejected:
  - that would preserve the exact ambiguity and operational coupling the hardening pass is supposed to remove
- Files touched:
  - `backend/app/main.py`
  - `backend/app/runtime/scheduler.py`
  - `backend/app/workers/scheduler.py`
  - `backend/Dockerfile`
  - `docker-compose.yml`
  - `docker-compose.dev.yml`
  - `backend/tests/workers/test_scheduler_runtime.py`
  - `backend/tests/infra/test_runtime_config.py`
- Remaining risk:
  - there is still no separate long-running worker-process set beyond the dedicated scheduler, so worker execution semantics remain only partially explicit

### Committed browser/e2e lane
- Status: `FIXED`
- Changed because:
  - manual screenshots alone were not enough to prove auth/bootstrap and theme persistence behavior
  - the completion plan requires committed browser coverage with visible ownership
- Alternatives considered:
  - keep browser validation purely manual in `.claude/ui-captures/`
- Why rejected:
  - manual screenshots cannot catch route boot regressions or theme persistence drift early in CI
- Files touched:
  - `frontend/package.json`
  - `frontend/playwright.config.ts`
  - `frontend/e2e/**`
  - `frontend/e2e/README.md`
  - `frontend/src/tests/README.md`
  - `docs/current-state/05-ops-and-ci.md`
  - `docs/repo-hardening/06-test-taxonomy.md`
- Remaining risk:
  - the committed Playwright coverage is still shallow and should expand by route family without turning into a flaky screenshot suite

### Historical inventory demotion
- Status: `FIXED`
- Changed because:
  - `docs/system-inventory/13-open-questions.txt` and `14-implementation-readiness.txt` were being read as live truth even when `docs/current-state/*` contradicted them
- Alternatives considered:
  - rewrite the entire inventory set immediately
- Why rejected:
  - too large for the first truth-reconciliation batch; the urgent need was to stop stale inventory from masquerading as live truth
- Files touched:
  - `docs/system-inventory/13-open-questions.txt`
  - `docs/system-inventory/14-implementation-readiness.txt`
- Remaining risk:
  - the historical inventory still contains stale detail until it is either refreshed or explicitly archived

### Docs/path validation automation
- Status: `FIXED`
- Changed because:
  - the repo already shipped real doc drift around missing paths and stale artifact references
- Alternatives considered:
  - rely on manual doc review
- Why rejected:
  - drift already happened repeatedly under manual review
- Files touched:
  - `scripts/check_docs_truth.py`
  - `.github/workflows/docs-validation.yml`
- Remaining risk:
  - the validator only checks repo-local path references and obvious links; it does not prove commands are executable

### Migration replay workflow
- Status: `FIXED`
- Changed because:
  - the repo explicitly carries migration replay uncertainty in the docs, but CI had no clean-replay gate
- Alternatives considered:
  - leave replay safety to pytest only
- Why rejected:
  - unit tests do not replace a clean Alembic replay on Postgres
- Files touched:
  - `.github/workflows/migration-safety.yml`
- Remaining risk:
  - replay still needs broader rollback/backfill documentation beyond the basic upgrade check

### Purpose-driven test taxonomy
- Status: `IMPLEMENTED`
- Changed because:
  - frontend tests were split across `__tests__` pockets with little ownership signal
  - backend migration, infra, security, and worker suites were still living under generic `unit/` buckets
- Alternatives considered:
  - leave file placement alone and only document the intended taxonomy
- Why rejected:
  - the repo already had enough historical sprawl that a doc-only taxonomy would immediately drift from the filesystem
- Files touched:
  - `frontend/src/tests/**`
  - `backend/tests/{contracts,infra,integration,migrations,security,unit,workers}/**`
  - `frontend/vitest.config.ts`
  - `.github/workflows/migration-safety.yml`
  - `frontend/src/tests/README.md`
  - `backend/tests/README.md`
  - `docs/repo-hardening/06-test-taxonomy.md`
- Remaining risk:
  - the taxonomy is now stable, but some broad lanes such as `backend/tests/unit/scraping/` and a few route-owned frontend suites are still intentionally coarse and should only be split further when a concrete ownership gain exists

### Adaptive parser fixture matrix and diagnosis API
- Status: `FIXED`
- Changed because:
  - the scraper stack already handled selectors, JSON-LD, embedded state, and anti-bot escalation, but failures still collapsed into a generic "no jobs" outcome when a fixture did not match
  - source-quality work needs to distinguish parser misses from JS-shell pages and Cloudflare-style blocks before further tuning is meaningful
- Alternatives considered:
  - add another scraper tier or broader fallback behavior
- Why rejected:
  - the stack already has the right runtime tiers; what was missing was an evidence-bearing diagnosis layer for the existing paths
- Files touched:
  - `backend/app/scraping/scrapers/adaptive_parser.py`
  - `backend/tests/unit/scraping/test_adaptive_parser_diagnostics.py`
  - `backend/tests/fixtures/career_pages/*`
  - `docs/current-state/04-data-and-scraping.md`
  - `docs/current-state/06-open-items.md`
  - `docs/repo-hardening/01-evidence-ledger.md`
- Remaining risk:
  - source-specific render recovery is still external to the parser itself; the harness only makes that boundary explicit

### Admin runtime summary for queue pressure and worker visibility
- Status: `FIXED`
- Changed because:
  - deployment follow-through needed a repo-owned way to inspect queue pressure, queue alerts, worker lane counts, and auth audit sink configuration without inventing a separate monitoring platform
  - the Admin page already existed as the operator surface, so the smallest useful fix was to add runtime visibility there rather than create a new dashboard silo
- Alternatives considered:
  - add a new standalone admin dashboard or depend entirely on deployment-side tooling
- Why rejected:
  - a new dashboard would duplicate the existing operator surface and push the real signal out of the repo
  - deployment-only tooling would leave the repo blind in local and CI contexts
- Files touched:
  - `backend/app/admin/service.py`
  - `backend/app/admin/router.py`
  - `backend/app/runtime/worker_metrics.py`
  - `frontend/src/api/admin.ts`
  - `frontend/src/pages/Admin.tsx`
  - `frontend/src/components/admin/AdminRuntimePanel.tsx`
  - `backend/tests/unit/admin/test_admin_service.py`
  - `backend/tests/integration/test_admin_api.py`
  - `frontend/src/tests/pages/Admin.page.test.tsx`
  - `docs/current-state/05-ops-and-ci.md`
  - `docs/current-state/06-open-items.md`
  - `docs/repo-hardening/07-observability-and-failure-map.md`
  - `docs/repo-hardening/09-final-gap-report.md`
- Remaining risk:
  - queue alert routing and long-window dashboarding are still deployment-owned follow-through, not repo-local monitoring

### Configurable Redis-backed auth audit sink
- Status: `FIXED`
- Changed because:
  - auth lifecycle events needed a dedicated sink that could be enabled without assuming deployment-owned logging existed
  - auth failures and state transitions should be visible as structured audit events rather than only as API responses
- Alternatives considered:
  - write auth events only to logs
  - make the sink always-on and require Redis in every environment
- Why rejected:
  - logs alone are easy to miss and hard to query for audit history
  - always-on Redis would turn a repo-owned observability path into an environment failure source
- Files touched:
  - `backend/app/config.py`
  - `backend/app/shared/audit_sink.py`
  - `backend/app/auth/router.py`
  - `backend/app/auth/service.py`
  - `backend/tests/unit/shared/test_audit_sink.py`
  - `backend/tests/unit/auth/test_auth_service.py`
  - `backend/tests/infra/test_runtime_config.py`
  - `docs/current-state/05-ops-and-ci.md`
  - `docs/current-state/06-open-items.md`
  - `docs/repo-hardening/07-observability-and-failure-map.md`
  - `docs/repo-hardening/09-final-gap-report.md`
- Remaining risk:
  - the sink is intentionally default-off, so deployments still need to opt in and route the stream to durable storage if they want long-term retention

### Queue telemetry history and alert transition routing
- Status: `FIXED`
- Changed because:
  - runtime observability needed more than the current queue snapshot and worker heartbeat state
  - the Admin page should expose recent queue history and queue alert changes without requiring a separate monitoring stack
- Alternatives considered:
  - keep queue observability as the latest snapshot only
  - push all history to deployment-side tooling and leave the repo blind
- Why rejected:
  - latest-snapshot-only view hides whether pressure or alerts are trending in the right direction
  - deployment-only tooling would leave local and CI runs without history
- Files touched:
  - `backend/app/runtime/telemetry.py`
  - `backend/app/runtime/scheduler.py`
  - `backend/app/admin/service.py`
  - `backend/app/config.py`
  - `frontend/src/components/admin/AdminRuntimePanel.tsx`
  - `frontend/src/api/admin.ts`
  - `docs/current-state/05-ops-and-ci.md`
  - `docs/current-state/06-open-items.md`
  - `docs/repo-hardening/07-observability-and-failure-map.md`
  - `docs/repo-hardening/09-final-gap-report.md`
- Remaining risk:
  - long-window retention and alert fanout beyond the repo-owned Redis history still need deployment routing if the operator wants durable monitoring outside the app

### Deployment ops runbook
- Status: `IMPLEMENTED`
- Changed because:
  - repo-owned observability is only useful if operators know how to read it, recover it, and validate it after a deploy or restore
- Alternatives considered:
  - leave deployment follow-through as implicit knowledge in docs scattered across current-state pages
- Why rejected:
  - restore and monitoring guidance need a single operator-facing entry point or they drift immediately
- Files touched:
  - `docs/repo-hardening/12-deployment-ops-runbook.md`
  - `docs/repo-hardening/00-index.md`
- Remaining risk:
  - external alert destinations and branch-protection enforcement still live outside the repo and must be set by the deployment/GitHub owner
