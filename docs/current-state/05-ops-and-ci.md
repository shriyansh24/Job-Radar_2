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
- `docker compose up -d postgres redis`
- `docker compose up -d frontend backend` if you want the base compose app containers as well
- `docker compose -f docker-compose.yml -f docker-compose.dev.yml up frontend backend` for bind-mounted Vite/Uvicorn dev on top of the base compose services
- The dev overlay sets `VITE_API_PROXY_TARGET=http://backend:8000` so the frontend container can proxy `/api` traffic to the backend container instead of incorrectly looping back to itself.

## Validation Commands

### Backend
- `cd backend && uv run pytest tests/integration/test_auth_api.py tests/integration/test_settings_api.py tests/integration/test_admin_api.py tests/integration/test_vault_api.py`

### Frontend
- `cd frontend && npm run lint`
- `cd frontend && npm run test -- --run`
- `cd frontend && npm run build`

### Browser QA
- Start backend and frontend locally.
- Log in through the real UI.
- Sweep the routed app on desktop, tablet, and phone.
- Write screenshots to `.claude/ui-captures/`.
- The latest authenticated sweep is current for the integrated frontend cleanup pass; treat further runs as incremental regression checks.

## GitHub Actions
- `ci.yml` uses:
  - `actions/checkout@v6`
  - `actions/setup-python@v6`
  - `actions/setup-node@v6`
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
- `docs-validation.yml` runs repo-local path/reference validation for live docs and workflow-linked files.
- `migration-safety.yml` replays Alembic on clean Postgres and runs `backend/tests/migrations/test_alembic_revisions.py`.
- `codeql.yml` and `dependency-review.yml` remain enabled.

## Branch Protection Assumptions
- Treat `main` as PR-only.
- Require repository validation, docs validation, migration safety, dependency review, and CodeQL before merge.
- Keep docs, tests, and runtime-truth updates in the same batch as behavior changes.

## Current Assessment
- Local validation and GitHub workflow configuration are aligned with the current repo state.
- Frontend tests now live under `frontend/src/tests/`; backend tests use role-based directories under `backend/tests/`.
- Local browser QA now depends on a migrated schema; make sure the backend DB is at Alembic `head` before validating settings, integrations, and other current-schema surfaces.
- Compose-first local runtime is the repo default; older manual `jobradar-postgres` flows are now treated as legacy local overrides.
