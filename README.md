# JobRadar V2

AI-powered job hunting assistant with direct-job scraping, enrichment, pipeline tracking, interview prep, resume tooling, and auto-apply support.

## Start Here
- Current repo state: `docs/current-state/00-index.md`
- Audit ledger: `docs/audit/00-index.md`
- Agent preferences and frontend expectations: `AGENTS.md`
- Agent playbook and command surface: `CLAUDE.md`
- High-level project summary: `PROJECT_STATUS.md`

## Stack
- Backend: Python 3.12, FastAPI, SQLAlchemy async, PostgreSQL, Redis, Alembic, `uv`
- Frontend: React 19, Vite 6, TypeScript, Tailwind CSS v4, Zustand, React Query
- AI/LLM: OpenRouter-backed services for enrichment, interview prep, salary analysis, resume tailoring, and cover letters
- Scraping: ATS adapters, target scheduler, browser pool, page crawler, deduplication, telemetry

## Quick Start

### Prerequisites
- Docker
- Node.js 22+
- Python 3.12+

### Infrastructure

```bash
docker compose up -d postgres redis
```

### Backend

```bash
cd backend
uv sync --frozen
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`.

## Validation Commands

### Backend

```bash
cd backend
uv run python -m pip check
uv export --frozen --format requirements-txt --no-emit-project -o .ci-requirements.txt
uv tool run pip-audit -r .ci-requirements.txt
uv tool run bandit -r app/ -c pyproject.toml --severity-level medium
uv run ruff check .
uv run mypy app/auth/service.py app/config.py app/shared/middleware.py app/scraping/deduplication.py app/scraping/port.py --ignore-missing-imports
uv run pytest --cov=app --cov-fail-under=60 tests/
```

### Frontend

```bash
cd frontend
npm audit --audit-level high
npm run lint
npm run test -- --run
npm install --no-save @vitest/coverage-v8
npm run test -- --run --coverage --coverage.thresholds.statements=40
npm run build
```

## Common Make Targets

```bash
make dev
make test
make lint
make migrate
```

## Repo Layout

```text
jobradar-v2/
|-- backend/
|   |-- app/
|   |-- scripts/
|   `-- tests/
|-- frontend/
|   |-- src/
|   `-- dist/
|-- docs/
|   |-- audit/
|   |-- current-state/
|   |-- research/
|   `-- superpowers/
|-- infra/
|-- .github/workflows/
|-- AGENTS.md
|-- CLAUDE.md
|-- PROJECT_STATUS.md
`-- README.md
```

## Notes
- Use `uv run` for backend commands and `npm` for frontend commands.
- The current live product state is documented under `docs/current-state/`.
- `docs/superpowers/` contains historical scraper-build planning, not the current execution queue.
