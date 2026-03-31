# Backend State - JobRadar V2

## Stack
- Python 3.12
- FastAPI
- SQLAlchemy 2.0 async
- PostgreSQL + Alembic
- Redis
- `uv` for dependency and command execution

## Key Runtime Areas
- Auth: cookie-based access and refresh flow with revocation, CSRF protection on unsafe cookie-auth requests, trusted-host enforcement, rate limiting, request-correlated lifecycle logs, route-aware request completion logs, and normalized reason codes for register/login/refresh/logout/password-change/session-clear/account-delete paths
- Auto-apply: field learning, Workday adapter, recovered form extraction, Greenhouse/Lever adapters, a pre-flight safety layer, live batch/single service wiring, worker-level batch execution, operator-facing run/pause/list/stats API coverage, and persisted run-level `review_items` / `review_required` diagnostics are all part of the live repo-local flow
- Settings and integrations: saved-search CRUD plus alert metadata, API-key-backed providers (`openrouter`, `serpapi`, `theirstack`, `apify`), and Google OAuth-backed Gmail integration with account email, scopes, sync status, last-validated, last-synced, and last-error state
- Resume: upload parsing supports `.pdf`, `.docx`, `.tex`, and `.txt` into persisted structured IR payloads; tailoring, ATS validation, council review, cover-letter generation, HTML/PDF rendering, template preview, and PDF export are live on the branch
- Jobs: SHA-256 string IDs, enrichment fields, lifecycle tracking, application relationship via `selectin`
- Enrichment: HTML cleaning, markdown conversion, LLM extraction, salary/experience enrichment, a live single-job enrichment API path, and a queue-backed batch trigger on the analysis lane
- Interview: question generation, stage-aware prep bundles, company research / role analysis, answer evaluation, persisted interview sessions
- Search and dedup: hybrid semantic ranking via `backend/app/search/hybrid.py`, freshness scoring via `backend/app/enrichment/freshness.py`, normalization-aware dedup via `backend/app/scraping/normalization.py` + `deduplication.py`, and ATS identity persistence on `jobs` via `ats_job_id`, `ats_provider`, and `ats_composite_key`
- Scraping: ATS registry, scheduler, tier routing, page crawling, conditional request cache handling, Protego-based `robots.txt` policy, adapter registry, browser pool, and target-batch persistence across ATS/fetch/browser paths
- Runtime topology: API process via `backend/app/main.py`, dedicated scheduler process via `backend/app/runtime/scheduler.py`, ARQ queue services via `backend/app/runtime/arq_worker.py`, and compose-managed Postgres/Redis; scheduler now enqueues jobs onto `scraping`, `analysis`, and `ops`
- Email: webhook and Gmail-synced inbound messages both flow through a shared inbound abstraction, duplicate suppression now prefers provider/message identity when available, email logs persist source provenance (`source_provider`, `source_message_id`, `source_thread_id`, `source_received_at`), and low-confidence Gmail signals downgrade to review-required notifications instead of silently transitioning pipeline state
- Workers: scraping, enrichment, follow-up/notification support, scheduled job registration, queue registry ownership, queue-specific ARQ worker services, retry-aware queue lifecycle logging, and live `daily_digest` plus `gmail_sync` jobs on the `ops` lane

## Runtime Invariants
- Runtime `DateTime` columns should be timezone-aware.
- LLM-driven JSON paths should fail explicitly on unusable payloads.
- Failed enrichment should not persist partial job mutations.
- Interview context should load `company_name` from jobs, not a non-existent `company` field.

## Recent Verified Fixes
- `Notification.created_at` is explicitly timezone-aware and matches the schema.
- Failed enrichment now restores job fields instead of persisting partial mutations.
- Interview generation no longer persists empty sessions when model output is empty.
- Interview prep now surfaces empty/failed model responses as a `502`.
- `ModelRouter.complete_json()` now raises when all candidate models return empty JSON.
- Interview job context now uses `company_name`.

## Validation
- `cd backend && uv run python -m pip check`
- `cd backend && uv export --frozen --format requirements-txt --no-emit-project -o .ci-requirements.txt`
- `cd backend && uv export --frozen --format requirements-txt --no-emit-project -o .ci-requirements.txt`
- `cd backend && python ../scripts/run_backend_dependency_audit.py --requirements .ci-requirements.txt`
- `cd backend && uv tool run bandit -r app/ -c pyproject.toml --severity-level medium`
- `cd backend && uv run ruff check .`
- `cd backend && uv run mypy app/auth/service.py app/config.py app/shared/middleware.py app/scraping/deduplication.py app/scraping/port.py --ignore-missing-imports`
- `cd backend && uv run pytest --cov=app --cov-fail-under=60 tests/`
- Latest full local result on `2026-03-27`: `1025 passed, 1 skipped` with backend coverage at `71.24%`
- Latest targeted local result on `2026-03-27`: `117 passed` across auth, jobs semantic search, interview prep, dedup/normalization/freshness, queue runtime, and auto-apply worker slices
- Additional targeted local results on `2026-03-27`: `37 passed` across ATS identity persistence, auto-apply operator API coverage, digest worker runtime, and migration lineage checks, plus `5 passed` across direct `alert_worker` / `phase7a_worker` coverage and the focused `005_create_p2_tables` migration regression suite
- Additional targeted local result on `2026-03-30`: `138 passed` across the full `unit/auto_apply` and `integration/auto_apply` suites plus Alembic revision-lineage checks after the persisted review-diagnostics slice landed
- Backend tests now use explicit `contracts/`, `infra/`, `integration/`, `migrations/`, `security/`, `unit/`, and `workers/` directories under `backend/tests/`.
- Auth lifecycle events now emit structured logs without credential/token payloads and inherit request correlation from middleware-bound request IDs.
- Dirty-worktree recovery coverage now also exists for `backend/tests/unit/search/test_hybrid_search.py`, `backend/tests/unit/search/test_freshness.py`, `backend/tests/unit/search/test_normalization.py`, `backend/tests/unit/interview/test_interview_contextual_service.py`, `backend/tests/workers/test_queue_runtime.py`, and `backend/tests/workers/test_arq_worker_runtime.py`.
- Gmail-first integration coverage now exists for Google OAuth helper behavior, settings/integration connect+sync routes, Gmail client parsing, Gmail sync refresh/retry handling, Gmail email-provenance/duplicate semantics, and `gmail_sync` scheduler/worker registration under `backend/tests/integration/test_settings_api.py`, `backend/tests/unit/settings/test_settings_service.py`, `backend/tests/unit/email/test_email_service_gmail.py`, `backend/tests/unit/email/test_gmail_sync.py`, `backend/tests/unit/email/test_google_oauth.py`, `backend/tests/unit/email/test_gmail_client.py`, and the worker runtime suites.

## Entry Points
- App bootstrap: `backend/app/main.py`
- Scheduler bootstrap: `backend/app/runtime/scheduler.py`
- DB config: `backend/app/database.py`
- Settings: `backend/app/config.py`
- Auth routes: `backend/app/auth/router.py`
- Scraping routes: `backend/app/scraping/router.py`
- Workers: `backend/app/workers/`

## Current Assessment
- Backend is locally green for the full repo-local test suite that was revalidated in this workspace.
- No known blocking backend or DB bugs remain after the latest verified pass.
- Bandit, pip-audit with the checked-in reviewed exception policy, pip check, backend Ruff, and the targeted backend mypy gate are green in the current branch.
- The latest full backend validation run keeps every `app/` module at or above `50%` coverage and brings overall backend coverage to `71.24%`.
- The revalidated backend slice covers auth, settings, admin, and vault contract changes used by the reference-first frontend migration.
- Auto-apply backend foundations are broader than the older branch-era recovery slices, and the live API/service execution path now includes recovered form extraction, Greenhouse/Lever adapters, safety gating, worker-triggered batch execution, operator-facing API coverage, and persisted manual-review diagnostics on each run. Provider-backed ATS submission remains environment-specific validation rather than a missing repo-local implementation.
- Resume capability is now part of `main`: structured IR extraction, tailoring, ATS validation, council review, renderer/template coverage, backend-backed preview, and PDF export are live in the merged branch tip. The branch-era proposal/session model is not part of the committed live flow.
- Cookie-authenticated unsafe requests now require the readable `jr_csrf_token` cookie to be echoed via `X-CSRF-Token`, and `TrustedHostMiddleware` is part of the live middleware stack.
- Scheduler isolation is now queue-backed: APScheduler enqueues named jobs, worker services consume queue-owned jobs directly, and Redis is part of the active background-execution critical path.
- Interview prep and semantic job search are now part of `main`: prep bundles return company research and role analysis, and semantic search uses the live hybrid ranking path rather than branch-only scaffolding.
- Hybrid search, freshness scoring, normalization, and ATS identity persistence are no longer branch-only research slices: they now exist on `main` as backend ranking and dedup foundations.
