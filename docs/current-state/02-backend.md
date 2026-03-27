# Backend State - JobRadar V2

## Stack
- Python 3.12
- FastAPI
- SQLAlchemy 2.0 async
- PostgreSQL + Alembic
- Redis
- `uv` for dependency and command execution

## Key Runtime Areas
- Auth: cookie-based access and refresh flow with revocation, CSRF protection on unsafe cookie-auth requests, trusted-host enforcement, rate limiting, request-correlated lifecycle logs, and normalized reason codes for login/refresh/logout/password-change/session-clear/account-delete paths
- Auto-apply: field learning, Workday adapter, recovered form extraction, Greenhouse/Lever adapters, a pre-flight safety layer, live batch/single service wiring, and worker-level batch execution; broader operator tooling and end-to-end coverage still remain partial
- Resume: upload parsing supports `.pdf`, `.docx`, `.tex`, and `.txt` into persisted structured IR payloads; tailoring, ATS validation, council review, cover-letter generation, and HTML/PDF rendering modules are live on the branch, with preview/export/operator depth still the main remaining gap
- Jobs: SHA-256 string IDs, enrichment fields, lifecycle tracking, application relationship via `selectin`
- Enrichment: HTML cleaning, markdown conversion, LLM extraction, salary/experience enrichment
- Interview: question generation, stage-aware prep bundles, company research / role analysis, answer evaluation, persisted interview sessions
- Search and dedup: hybrid semantic ranking via `backend/app/search/hybrid.py`, freshness scoring via `backend/app/enrichment/freshness.py`, and normalization-aware dedup via `backend/app/scraping/normalization.py` + `deduplication.py`
- Scraping: ATS registry, scheduler, tier routing, page crawling, adapter registry, browser pool
- Runtime topology: API process via `backend/app/main.py`, dedicated scheduler process via `backend/app/runtime/scheduler.py`, ARQ queue services via `backend/app/runtime/arq_worker.py`, and compose-managed Postgres/Redis; scheduler now enqueues jobs onto `scraping`, `analysis`, and `ops`
- Workers: scraping, enrichment, follow-up/notification support, scheduled job registration, queue registry ownership, queue-specific ARQ worker services, and retry-aware queue lifecycle logging

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
- `cd backend && uv tool run pip-audit -r .ci-requirements.txt`
- `cd backend && uv tool run bandit -r app/ -c pyproject.toml --severity-level medium`
- `cd backend && uv run ruff check .`
- `cd backend && uv run mypy app/auth/service.py app/config.py app/shared/middleware.py app/scraping/deduplication.py app/scraping/port.py --ignore-missing-imports`
- `cd backend && uv run pytest --cov=app --cov-fail-under=60 tests/`
- Latest targeted local result on `2026-03-27`: `117 passed` across auth, jobs semantic search, interview prep, dedup/normalization/freshness, queue runtime, and auto-apply worker slices
- Backend tests now use explicit `contracts/`, `infra/`, `integration/`, `migrations/`, `security/`, `unit/`, and `workers/` directories under `backend/tests/`.
- Auth lifecycle events now emit structured logs without credential/token payloads and inherit request correlation from middleware-bound request IDs.
- Dirty-worktree recovery coverage now also exists for `backend/tests/unit/search/test_hybrid_search.py`, `backend/tests/unit/search/test_freshness.py`, `backend/tests/unit/search/test_normalization.py`, `backend/tests/unit/interview/test_interview_contextual_service.py`, `backend/tests/workers/test_queue_runtime.py`, and `backend/tests/workers/test_arq_worker_runtime.py`.

## Entry Points
- App bootstrap: `backend/app/main.py`
- Scheduler bootstrap: `backend/app/runtime/scheduler.py`
- DB config: `backend/app/database.py`
- Settings: `backend/app/config.py`
- Auth routes: `backend/app/auth/router.py`
- Scraping routes: `backend/app/scraping/router.py`
- Workers: `backend/app/workers/`

## Current Assessment
- Backend is locally green for the targeted contract slice that was revalidated in this workspace.
- No known blocking backend or DB bugs remain after the latest verified pass.
- Bandit, pip-audit, pip check, backend Ruff, and the targeted backend mypy gate are green in the current branch.
- The revalidated backend slice covers auth, settings, admin, and vault contract changes used by the reference-first frontend migration.
- Auto-apply backend foundations are broader than `main`, and the live API/service execution path now includes recovered form extraction, Greenhouse/Lever adapters, safety gating, and worker-triggered batch execution, but operator-facing UI and broader integration coverage are still not end to end.
- Resume capability is broader than `main`: structured IR extraction, tailoring, ATS validation, council review, and renderer/template coverage are live on `codex/ui-changes`, but richer preview/export/operator follow-through is still not end to end.
- Cookie-authenticated unsafe requests now require the readable `jr_csrf_token` cookie to be echoed via `X-CSRF-Token`, and `TrustedHostMiddleware` is part of the live middleware stack.
- Scheduler isolation is now queue-backed: APScheduler enqueues named jobs, worker services consume queue-owned jobs directly, and Redis is part of the active background-execution critical path.
- Interview prep and semantic job search are broader than `main`: prep bundles now return company research and role analysis, and semantic search now uses the live hybrid ranking path rather than branch-only scaffolding.
- Hybrid search, freshness scoring, and normalization are no longer branch-only research slices: they now exist on `codex/ui-changes` as backend ranking and dedup foundations, but they still need broader product follow-through and tuning.
