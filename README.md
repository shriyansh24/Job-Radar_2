# JobRadar V2

AI-powered job hunting assistant with direct-job scraping, enrichment, pipeline tracking, interview prep, resume tooling, compensation research, vault management, and auto-apply support.

## Start Here
- Current repo state: `docs/current-state/00-index.md`
- Audit ledger: `docs/audit/00-index.md`
- Agent preferences and frontend expectations: `AGENTS.md`
- Agent playbook and command surface: `CLAUDE.md`
- High-level project summary: `PROJECT_STATUS.md`

## Stack
- Backend: Python 3.12, FastAPI, SQLAlchemy async, PostgreSQL, Redis, Alembic, `uv`
- Frontend: React 19, Vite 6, TypeScript, Tailwind CSS v4, Zustand, React Query
- AI/LLM: OpenRouter-backed services for enrichment, interview prep, salary analysis, resume tailoring, cover letters, and copilot flows
- Scraping: ATS adapters, target scheduler, browser pool, page crawler, deduplication, telemetry
- UI system: reference-first neo-brutalist command-center shell with `Inter`, `JetBrains Mono`, Phosphor icons, and light/dark parity

## Quick Start

### Prerequisites
- Docker
- Node.js 22+
- Python 3.12+

### Infrastructure

```bash
docker start jobradar-postgres
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
uv run ruff check .
uv run pytest
```

### Frontend

```bash
cd frontend
npm run lint
npm run test -- --run
npm run build
```

### Browser QA
- Start the backend and frontend dev servers locally.
- Authenticate through `/login`.
- Sweep the routed app in desktop, tablet, and phone layouts.
- Store screenshots and other QA artifacts in `output/playwright/`.

## Current Verification Snapshot (2026-03-24)
- Frontend lint passed.
- Frontend Vitest suite passed: `24` test files, `39` tests.
- Frontend production build passed.
- Targeted backend auth/settings/admin/vault integration tests passed: `26` tests.
- Browser sweeps passed across all 21 authenticated routes on desktop, tablet, and phone, with representative screenshots written to `output/playwright/`.
- Local Postgres schema was upgraded to Alembic `head` during QA so the live settings/integration surfaces match the current code.

## Repo Layout

```text
jobradar-v2/
|-- backend/
|   |-- app/            # FastAPI application (domain modules)
|   |-- scripts/        # CLI utilities
|   `-- tests/          # pytest suite
|-- frontend/
|   |-- src/            # React 19 application
|   `-- system.md       # Frontend design-system source of truth
|-- docs/
|   |-- audit/          # Bug ledger (39 FIXED / 1 VERIFIED_CLEAN / 4 STALE)
|   |-- current-state/  # Canonical live state docs
|   `-- research/       # Future design research
|-- output/playwright/  # Browser QA artifacts when a local validation pass generates them
|-- .github/workflows/  # CI: lint, test, build, CodeQL
|-- AGENTS.md           # Agent preferences and frontend expectations
|-- CLAUDE.md           # Agent playbook and working commands
|-- DECISIONS.md        # Architectural decisions
|-- PROJECT_STATUS.md   # High-level project status
`-- README.md
```

## Notes
- Use `uv run` for backend commands and `npm` for frontend commands.
- The live frontend is a reference-first command-center UI while preserving the app's routed behavior and backend contracts.
- The current live product state is documented under `docs/current-state/`.
- `docs/research/` contains future-planning material, not current requirements.
