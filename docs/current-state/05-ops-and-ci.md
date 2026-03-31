# Ops And CI State - JobRadar V2

## Local Tooling
- Backend uses `uv`.
- Frontend uses `npm`.
- Infrastructure uses Docker / `docker compose`.

## Core Local Commands

### Backend
- `cd backend && uv sync --frozen`
- `cd backend && uv run alembic upgrade head`
- `cd backend && uv run uvicorn app.main:app --reload`

### Frontend
- `cd frontend && npm ci`
- `cd frontend && npm run dev`
- `VITE_API_PROXY_TARGET=http://backend:8000 cd frontend && npm run dev` only when running Vite inside the frontend container rather than on the host

### Infrastructure
- `docker compose up -d` is the canonical full-stack compose runtime
- Base compose now owns `postgres`, `redis`, `migrate`, `backend`, `scheduler`, `worker-scraping`, `worker-analysis`, `worker-ops`, and `frontend`
- `docker compose -f docker-compose.yml -f docker-compose.dev.yml up backend scheduler worker-scraping worker-analysis worker-ops frontend` is the bind-mounted dev overlay for Uvicorn, the dedicated scheduler process, queue-specific ARQ workers, and Vite on top of the base compose services
- The dev overlay now publishes only `5173:5173`, health-checks `http://127.0.0.1:5173/`, and sets `VITE_API_PROXY_TARGET=http://backend:8000` so the frontend container can proxy `/api` traffic to the backend container instead of incorrectly looping back to itself.
- Redis is provisioned in the compose baseline and is now the active queue backbone for background execution.
- The live runtime shape is: scheduler enqueues named jobs to ARQ queues `scraping`, `analysis`, and `ops`; queue-specific worker services consume those queues.
- The scheduler now writes a Redis-backed heartbeat key and owns the `daily_digest`, `saved_search_alerts`, and `gmail_sync` schedules on the ops lane.
- Career-page targets now run only through the `target_batch_career_page` ARQ job on the scraping lane; the older standalone `career_page_scrape` scheduler path was removed so conditional requests, robots policy, and adaptive parsing all share one authoritative execution path.
- Compose healthchecks now use runtime healthcheck commands against the live scheduler and worker surfaces rather than ready-marker files.
- `backend/app/runtime/worker.py` remains as a manual one-shot/debug runner, not the scheduled execution path.
- Gmail-first integration is disabled unless the Google OAuth env vars are configured. The repo-local runtime knobs are:
  - `JR_FRONTEND_BASE_URL`
  - `JR_GOOGLE_OAUTH_CLIENT_ID`
  - `JR_GOOGLE_OAUTH_CLIENT_SECRET`
  - `JR_GOOGLE_OAUTH_REDIRECT_URI`
  - `JR_GOOGLE_GMAIL_SYNC_QUERY`
  - `JR_GOOGLE_GMAIL_SYNC_MAX_MESSAGES`
- Operator-owned Gmail sync paths are:
  - Settings > Integrations > `Connect Google`
  - Settings > Integrations > `Sync Gmail`
  - the scheduled `gmail_sync` worker job on the `ops` lane
- The `worker-ops` lane now owns outbound Google OAuth + Gmail API traffic in addition to digest, alert, cleanup, and operator-support jobs.

## Validation Commands

### Backend
- `cd backend && uv run pytest tests/integration/test_auth_api.py tests/integration/test_settings_api.py tests/integration/test_admin_api.py tests/integration/test_vault_api.py`
- `cd backend && uv run pytest tests/integration/test_settings_api.py tests/unit/settings/test_settings_service.py tests/unit/email/test_email_service_gmail.py tests/unit/email/test_gmail_sync.py tests/unit/email/test_google_oauth.py tests/unit/email/test_gmail_client.py`
- `cd backend && uv run pytest tests/infra/test_runtime_config.py tests/infra/test_queue_runtime_compose.py tests/workers/test_queue_runtime.py tests/workers/test_arq_worker_runtime.py tests/workers/test_job_registry_runtime.py tests/workers/test_scheduler_runtime.py tests/workers/scraping/test_scrape_scheduler.py`
- `cd backend && uv run pytest tests/workers/test_worker_runtime.py`
- `cd backend && uv run pytest tests/integration/auto_apply/test_auto_apply_api.py tests/integration/scraping/test_scraping_identity.py tests/workers/test_digest_worker.py tests/migrations/test_job_ats_identity_migration.py tests/migrations/test_scrape_target_identity_migrations.py`

### Frontend
- `cd frontend && npm run lint`
- `cd frontend && npm run test -- --run`
- `cd frontend && npm run e2e`
- `cd frontend && npm run build`
- `cd frontend && npm run e2e` now reuses a live backend on `127.0.0.1:8000` when present; otherwise `frontend/playwright.config.ts` invokes `scripts/start_playwright_backend.py`, which runs `alembic upgrade head`, boots the API, and fails early if Postgres or Redis are unreachable or misconfigured.

### Browser QA
- Start backend and frontend locally.
- Start the dedicated scheduler and the queue-specific workers locally as well if you are not using compose.
- Log in through the real UI.
- Sweep the routed app on desktop, tablet, and phone.
- Write screenshots to `.claude/ui-captures/`.
- The latest authenticated sweep is current for the integrated frontend cleanup pass; treat further runs as incremental regression checks.
- The committed browser lane now covers shell/auth smoke, shell navigation, responsive shell behavior, a combined route-family outcomes flow for dashboard/jobs/pipeline/settings/targets, communications/setup flows, prepare/intelligence/outcomes flows, operations/admin/data flows, profile/settings/auth roundtrips, the recovered interview/search flow, the live analytics patterns surface, resume template preview/export, and route-family theme persistence/route-matrix assertions across all 8 theme combinations.

## GitHub Actions
- `ci.yml` uses:
  - `actions/checkout@v6`
  - `actions/setup-python@v6`
  - `actions/setup-node@v6`
- `frontend-e2e.yml` runs a dedicated browser check against the live backend API, the dedicated scheduler process, the queue-specific worker processes, and the Vite dev server.
- `frontend-e2e.yml` now waits on runtime healthcheck probes for the scheduler and workers rather than file markers.
- Backend quality job runs:
  - `uv sync --frozen`
  - `uv run python -m pip check`
  - `uv export --frozen --format requirements-txt --no-emit-project -o .ci-requirements.txt`
  - `python ../scripts/run_backend_dependency_audit.py --requirements .ci-requirements.txt`
  - `uv tool run bandit -r app/ -c pyproject.toml --severity-level medium`
  - `uv run ruff check .`
  - targeted `mypy`
- Backend test job runs:
  - `uv run pytest --cov=app --cov-fail-under=60 tests/`
- Frontend quality job runs:
  - `npm ci`
  - `npm audit --audit-level high`
  - `npm run lint`
- Frontend test/build job runs:
  - `npm run test -- --run --coverage --coverage.thresholds.statements=40`
  - `npm run build`
- Browser/e2e coverage now has a committed Playwright tree under `frontend/e2e/`; CI wiring for that lane should be kept separate from the fast PR lint/unit/build gates.
- Route-family browser coverage now includes `frontend/e2e/smoke/auth-shell.spec.ts`, `frontend/e2e/flows/route-shell-navigation.spec.ts`, `frontend/e2e/flows/route-family-outcomes.spec.ts`, `frontend/e2e/flows/communications-setup.spec.ts`, `frontend/e2e/flows/prepare-intelligence-outcomes.spec.ts`, `frontend/e2e/flows/operations-admin-data.spec.ts`, `frontend/e2e/flows/profile-settings-auth.spec.ts`, `frontend/e2e/flows/interview-search-recovered.spec.ts`, `frontend/e2e/flows/resume-template-preview.spec.ts`, `frontend/e2e/flows/shell-responsive.spec.ts`, `frontend/e2e/theme-matrix/theme-persistence.spec.ts`, and `frontend/e2e/theme-matrix/route-theme-matrix.spec.ts`.
- `frontend-e2e.yml` emits one required check:
  - `Frontend E2E Smoke / frontend-e2e-smoke`
- `frontend-e2e.yml` also runs weekly as a drift-detection lane in addition to PR, `main` push, `codex/*` push, and manual runs.
- `docs-validation.yml` runs repo-local path/reference validation for live docs and workflow-linked files.
- `migration-safety.yml` replays Alembic on clean Postgres and runs the full `backend/tests/migrations/` lane.
- `migration-safety.yml` now runs the full `backend/tests/migrations/` lane and uploads `alembic history --verbose` output on failure for replay debugging.
- `codeql.yml` and `dependency-review.yml` remain enabled.

## Branch Protection Assumptions
- Treat `main` as PR-only.
- Require repository validation, dependency review, CodeQL, and `Frontend E2E Smoke / frontend-e2e-smoke` before merge.
- Treat `Docs Validation` and `Migration Safety` as required path-scoped checks for doc/workflow/runtime and backend/migration changes respectively; if they must become unconditional required checks, convert them to always-run wrappers before tightening branch protection.
- Keep docs, tests, and runtime-truth updates in the same batch as behavior changes.
- Do not make the required browser workflow path-filtered or matrix-shaped while branch protection depends on that exact emitted check name.

## Current Assessment
- Local validation and GitHub workflow configuration are aligned with the current repo state.
- Frontend tests now live under `frontend/src/tests/`, browser suites live under `frontend/e2e/`, and backend tests use role-based directories under `backend/tests/`.
- Local browser QA now depends on a migrated schema; make sure the backend DB is at Alembic `head` before validating settings, integrations, and other current-schema surfaces.
- Compose-first local runtime is the repo default; older manual `jobradar-postgres` flows are now treated as legacy local overrides.
- Scheduler and worker readiness now come from runtime healthcheck probes against the live queue surfaces rather than ready-marker files; the scheduler heartbeat also lives in Redis so compose and CI can probe the real runtime state.
- Queue enqueue/dequeue logs now emit queue depth and retry metadata, retryable jobs raise real ARQ `Retry` with scheduled backoff, and non-retryable or final failures log `retry_exhausted` truthfully.
- Gmail sync now emits repo-local lifecycle logs through `google_integration_connected`, `gmail_worker_started`, `gmail_worker_skipped`, `gmail_worker_user_failed`, `gmail_worker_completed`, `gmail_sync_completed`, and `email_duplicate_skipped`. Alert routing for those signals is still deployment-owned.
- Worker isolation is queue-backed and compose-visible; queue telemetry now includes depth, oldest-job age, pressure, alert state, truthful retry exhaustion, worker-lane counters, and request/job correlation on queue-triggered operator paths. Request lifecycle logs also now carry route identity and authenticated user context when available. The remaining follow-through is mostly deployment-level alert routing and dashboards rather than missing repo-local runtime ownership.
- The latest full local backend validation run on `2026-03-27` completed at `1025 passed, 1 skipped` with backend coverage at `71.24%` and no `app/` module below `50%` coverage.
- Backend dependency auditing now runs through `scripts/run_backend_dependency_audit.py`, which applies the checked-in reviewed exception policy from `backend/pip-audit-policy.json` instead of burying CVE ignores inline in workflow YAML.
