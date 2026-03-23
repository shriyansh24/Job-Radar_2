# CLAUDE.md - JobRadar V2 Agent Playbook

## Read Order
1. `docs/current-state/00-index.md`
2. `docs/audit/00-index.md`
3. `AGENTS.md`
4. `PROJECT_STATUS.md`
5. `README.md`

Use `docs/research/00-index.md` only for future-planning context.

## Repo Reality
- Monorepo root: `D:/jobradar-v2`
- Backend: Python 3.12, FastAPI, SQLAlchemy async, PostgreSQL, Redis, `uv`
- Frontend: React 19, Vite 6, TypeScript, Tailwind CSS v4, Zustand, React Query
- Auth: cookie-based access and refresh tokens
- Scraping: ATS registry, target-based scheduler, browser pool, tier router, page crawler
- CI: dependency checks, backend lint/tests, frontend audit/lint/tests/build

## Canonical Working Commands

### Backend
- Install: `cd backend && uv sync --frozen`
- Lint: `cd backend && uv run ruff check .`
- Tests: `cd backend && uv run pytest`
- Dependency health:
  - `cd backend && uv run python -m pip check`
  - `cd backend && uv export --frozen --format requirements-txt --no-emit-project -o .ci-requirements.txt`
  - `cd backend && uv tool run pip-audit -r .ci-requirements.txt`
- Migrate: `cd backend && uv run alembic upgrade head`
- Dev server: `cd backend && uv run uvicorn app.main:app --reload`

### Frontend
- Install: `cd frontend && npm ci`
- Lint: `cd frontend && npm run lint`
- Tests: `cd frontend && npm run test -- --run`
- Build: `cd frontend && npm run build`
- Dependency audit: `cd frontend && npm audit --audit-level high`
- Dev server: `cd frontend && npm run dev`

## Branch Context
- `main` has PRs #15 (security hardening) and #16 (CodeQL + deps) merged.
- `feat/p2-polish-advanced` has all P0/P1/P2 feature code (38 spec features). This is the active development branch.
- P0/P1/P2 features were built by Codex agents from a comprehensive spec; code quality is solid but integration wiring has gaps (see Known Structural Gaps below).

## Current State Summary (feat/p2-polish-advanced, 2026-03-23)
- Backend: **716 tests pass**, `ruff` clean, 23 routers mounted, 37 DB tables.
- Frontend: lint clean, build clean, 9 tests pass in 6 files.
- Backend and frontend dependency health checks pass locally.
- The audit ledger is closed at `39 FIXED / 5 STALE / 0 OPEN / 0 PARTIAL`.
- No known blocking reproducible bugs on the core platform.
- Alembic at revision `005` (consolidation migration for P2 tables).

## Remaining Frontend Gaps (feat/p2-polish-advanced)
- Frontend has no API modules or pages for: email, networking, outcomes, copilot chat.
- Settings stubs (change password, delete account, clear data) are frontend no-ops with no backend endpoint.
- API keys collected in Settings/Onboarding but not persisted to backend.
- Auto-apply run/pause/applySingle API functions defined but no UI triggers.

## Important Invariants
- `jobs.id` is a SHA-256 string key, not a UUID.
- Runtime `DateTime` columns should use `DateTime(timezone=True)`.
- Use `uv run` for backend commands; do not mix in ad hoc Python invocations when repo-managed commands exist.
- Use `npm` for frontend commands.
- The frontend theme system is driven by `useUIStore` and a `.dark` class on the root element.
- The frontend icon set is `@phosphor-icons/react`, not `lucide-react`.

## Infrastructure
- Docker container: `jobradar-postgres` (pgvector/pgvector:pg17) on port 5433.
- Start: `docker start jobradar-postgres`
- Connection: `postgresql+asyncpg://jobradar:jobradar220568@localhost:5433/jobradar`
- psql: `PGPASSWORD=jobradar220568 "C:/Program Files/PostgreSQL/18/bin/psql.exe" -h localhost -p 5433 -U jobradar -d jobradar`

## Agent Rules
- Read the current-state and audit docs before changing behavior.
- Prefer minimal, high-confidence fixes over refactors.
- Prove behavior changes with focused tests when possible.
- Do not treat old plan files or `docs/research/` as current product requirements.
- Do not commit `.claude/launch.json`; it is machine-local.
- Ignore `.claude/worktrees/` for live repo state unless you are explicitly working inside one.

## Known Residual Noise
- Frontend Vitest still prints a non-fatal `--localstorage-file` warning during test runs.
