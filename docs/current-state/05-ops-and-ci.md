# Ops And CI State - JobRadar V2

## Local Tooling
- Backend uses `uv`.
- Frontend uses `npm`.
- Infrastructure uses `docker compose`.

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

## GitHub Actions
- `ci.yml` now uses:
  - `actions/checkout@v6`
  - `actions/setup-python@v6`
  - `actions/setup-node@v6`
- Backend CI now runs:
  - `uv sync --frozen`
  - `uv run python -m pip check`
  - `uv export --frozen --format requirements-txt --no-emit-project -o .ci-requirements.txt`
  - `uv tool run pip-audit -r .ci-requirements.txt`
  - `uv tool run bandit -r app/ -c pyproject.toml --severity-level medium`
  - `uv run ruff check .`
  - `uv run mypy app/auth/service.py app/config.py app/shared/middleware.py app/scraping/deduplication.py app/scraping/port.py --ignore-missing-imports`
  - `uv run pytest --cov=app --cov-fail-under=60 tests/`
- Frontend CI now runs:
  - `npm ci`
  - `npm install --no-save @vitest/coverage-v8`
  - `npm audit --audit-level high`
  - `npm run lint`
  - `npm run test -- --run --coverage --coverage.thresholds.statements=40`
  - `npm run build`
- Additional workflows:
  - CodeQL
  - Dependency Review
  - Dependabot

## Security / Packaging Notes
- Redis is configured with auth in compose.
- Docker contexts use `.dockerignore` files.
- Backend test tooling is defined in `backend/pyproject.toml` under the `dev` dependency group.
- Incompatible scraper extras are declared as conflicts in `backend/pyproject.toml`.

## Current Assessment
- Local validation and GitHub workflow configuration are aligned with the current repo state.
