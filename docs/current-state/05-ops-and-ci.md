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

### Infrastructure
- `docker compose up -d postgres redis`

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
- Backend CI runs:
  - `uv sync --frozen`
  - `uv run python -m pip check`
  - `uv export --frozen --format requirements-txt --no-emit-project -o .ci-requirements.txt`
  - `uv tool run pip-audit -r .ci-requirements.txt`
  - `uv tool run bandit -r app/ -c pyproject.toml --severity-level medium`
  - `uv run ruff check .`
  - targeted `mypy`
  - `uv run pytest --cov=app --cov-fail-under=60 tests/`
- Frontend CI runs:
  - `npm ci`
  - `npm install --no-save @vitest/coverage-v8`
  - `npm audit --audit-level high`
  - `npm run lint`
  - `npm run test -- --run --coverage --coverage.thresholds.statements=40`
  - `npm run build`

## Current Assessment
- Local validation and GitHub workflow configuration are aligned with the current repo state.
- Local browser QA now depends on a migrated schema; make sure the backend DB is at Alembic `head` before validating settings, integrations, and other current-schema surfaces.
