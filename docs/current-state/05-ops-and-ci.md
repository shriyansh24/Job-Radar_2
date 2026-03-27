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
- `backend/app/runtime/worker.py` remains as a manual one-shot/debug runner, not the scheduled execution path.

## Validation Commands

### Backend
- `cd backend && uv run pytest tests/integration/test_auth_api.py tests/integration/test_settings_api.py tests/integration/test_admin_api.py tests/integration/test_vault_api.py`
- `cd backend && uv run pytest tests/infra/test_runtime_config.py tests/infra/test_queue_runtime_compose.py tests/workers/test_queue_runtime.py tests/workers/test_arq_worker_runtime.py tests/workers/test_job_registry_runtime.py tests/workers/test_scheduler_runtime.py tests/workers/scraping/test_scrape_scheduler.py`
- `cd backend && uv run pytest tests/workers/test_worker_runtime.py`

### Frontend
- `cd frontend && npm run lint`
- `cd frontend && npm run test -- --run`
- `cd frontend && npm run e2e`
- `cd frontend && npm run build`

### Browser QA
- Start backend and frontend locally.
- Start the dedicated scheduler and the queue-specific workers locally as well if you are not using compose.
- Log in through the real UI.
- Sweep the routed app on desktop, tablet, and phone.
- Write screenshots to `.claude/ui-captures/`.
- The latest authenticated sweep is current for the integrated frontend cleanup pass; treat further runs as incremental regression checks.
- The committed browser lane now covers shell/auth smoke, shell navigation, responsive shell behavior, a combined route-family outcomes flow for dashboard/jobs/pipeline/settings/targets, prepare/intelligence/outcomes flows, operations/admin/data flows, profile/settings/auth roundtrips, the recovered interview/search flow, and representative theme persistence/route-matrix assertions across all 8 theme combinations.

## GitHub Actions
- `ci.yml` uses:
  - `actions/checkout@v6`
  - `actions/setup-python@v6`
  - `actions/setup-node@v6`
- `frontend-e2e.yml` runs a dedicated browser check against the live backend API, the dedicated scheduler process, the queue-specific worker processes, and the Vite dev server.
- Backend quality job runs:
  - `uv sync --frozen`
  - `uv run python -m pip check`
  - `uv export --frozen --format requirements-txt --no-emit-project -o .ci-requirements.txt`
  - `uv tool run pip-audit -r .ci-requirements.txt`
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
- Route-family browser coverage now includes `frontend/e2e/smoke/auth-shell.spec.ts`, `frontend/e2e/flows/route-shell-navigation.spec.ts`, `frontend/e2e/flows/route-family-outcomes.spec.ts`, `frontend/e2e/flows/prepare-intelligence-outcomes.spec.ts`, `frontend/e2e/flows/operations-admin-data.spec.ts`, `frontend/e2e/flows/profile-settings-auth.spec.ts`, `frontend/e2e/flows/interview-search-recovered.spec.ts`, `frontend/e2e/flows/shell-responsive.spec.ts`, `frontend/e2e/theme-matrix/theme-persistence.spec.ts`, and `frontend/e2e/theme-matrix/route-theme-matrix.spec.ts`.
- `frontend-e2e.yml` emits one required check:
  - `Frontend E2E Smoke / frontend-e2e-smoke`
- `frontend-e2e.yml` also runs weekly as a drift-detection lane in addition to PR, `main` push, and manual runs.
- `docs-validation.yml` runs repo-local path/reference validation for live docs and workflow-linked files.
- `migration-safety.yml` replays Alembic on clean Postgres and runs `backend/tests/migrations/test_alembic_revisions.py`.
- `codeql.yml` and `dependency-review.yml` remain enabled.

## Branch Protection Assumptions
- Treat `main` as PR-only.
- Require repository validation, docs validation, migration safety, dependency review, CodeQL, and `Frontend E2E Smoke / frontend-e2e-smoke` before merge.
- Keep docs, tests, and runtime-truth updates in the same batch as behavior changes.
- Do not make the required browser workflow path-filtered or matrix-shaped while branch protection depends on that exact emitted check name.

## Current Assessment
- Local validation and GitHub workflow configuration are aligned with the current repo state.
- Frontend tests now live under `frontend/src/tests/`, browser suites live under `frontend/e2e/`, and backend tests use role-based directories under `backend/tests/`.
- Local browser QA now depends on a migrated schema; make sure the backend DB is at Alembic `head` before validating settings, integrations, and other current-schema surfaces.
- Compose-first local runtime is the repo default; older manual `jobradar-postgres` flows are now treated as legacy local overrides.
- Scheduler readiness now proves startup, DB reachability, and Redis/queue reachability; queue enqueue/dequeue logs also emit queue depth and retry metadata, but health is still not a substitute for sustained throughput monitoring.
- Worker isolation is queue-backed and compose-visible; the remaining runtime work is broader worker-lane coverage and alerting around queue depth / retry pressure rather than basic queue ownership.
