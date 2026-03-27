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
- Current UI: reference-first command-center shell with shared primitives under `frontend/src/components/system`, a `frontend/system.md` design source of truth, shadowless buttons, and routed workspace groupings for `Home`, `Discover`, `Execute`, `Prepare`, `Intelligence`, and `Operations`
- Test layout: frontend Vitest suites live under `frontend/src/tests/`; backend pytest suites are moving toward explicit `contracts/`, `infra/`, `migrations/`, `security/`, and `workers/` lanes

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
- Containerized dev proxy override: `VITE_API_PROXY_TARGET=http://backend:8000`

## Branch Context
- Active migration branch in this workspace: `codex/ui-changes`.

## Current State Summary (2026-03-27)
- Frontend: reference-first UI migration is implemented, the shared system is flatter and shadowless on controls, the largest routed pages have been broken into smaller component groups, and the slop-copy cleanup pass is already integrated into login, settings, dashboard, jobs, pipeline, and copilot.
- Backend: targeted auth/settings/admin/vault integration tests pass locally.
- Browser QA: the latest authenticated route sweep is current and representative captures live under `.claude/ui-captures/`.
- Local Postgres schema was upgraded from Alembic revision `005` to `head` during QA so the settings/integration surfaces match the live schema.
- The audit ledger remains at `39 FIXED / 1 VERIFIED_CLEAN / 4 STALE / 0 OPEN / 0 PARTIAL`.

## Remaining Frontend Gaps
- No blocking frontend gaps are currently known from the verified local pass.
- Remaining work is iterative polish on the remaining larger routed surfaces and deeper route-by-route theme review, not a known blocker.

## Important Invariants
- `jobs.id` is a SHA-256 string key, not a UUID.
- Runtime `DateTime` columns should use `DateTime(timezone=True)`.
- Use `uv run` for backend commands; do not mix in ad hoc Python invocations when repo-managed commands exist.
- Use `npm` for frontend commands.
- The frontend theme system is driven by `useUIStore`, stores theme family plus mode, and applies a `.dark` class on the root element for dark variants.
- The frontend icon set is `@phosphor-icons/react`, not `lucide-react`.
- Buttons should not carry drop shadows; elevation belongs to surfaces and containers, not interactive controls.
- Keep `frontend/system.md` aligned with any new visual or layout rule.

## Infrastructure
- Canonical local runtime: `docker compose up -d postgres redis`
- Canonical compose DB: `postgresql+asyncpg://jobradar:jobradar@localhost:5432/jobradar`
- Canonical compose Redis: `redis://:jobradar-redis@localhost:6379/0`
- `docker-compose.dev.yml` is an overlay for bind-mounted frontend/backend dev on top of the base compose services, and it sets `VITE_API_PROXY_TARGET=http://backend:8000` so Vite can reach the backend from inside the frontend container.
- Legacy/manual local container setups on `5433` are workspace-specific overrides and should not be treated as the repo default.

## GitHub Guardrails
- Repository validation workflow: backend quality, backend tests, frontend quality, and frontend tests/build.
- Docs validation workflow: checks repo-local doc/path references.
- Migration safety workflow: replays Alembic on clean Postgres and runs targeted migration tests.
- CodeQL and dependency review remain enabled.

## Agent Rules
- Read the current-state and audit docs before changing behavior.
- Preserve the reference-first shell, typography, color system, and responsive grammar across all new surfaces.
- Prove behavior changes with focused tests when possible.
- Do not treat old plan files or `docs/research/` as current product requirements.
- Do not commit `.claude/launch.json`; it is machine-local.
- Ignore `.claude/worktrees/` for live repo state unless you are explicitly working inside one.

## Known Residual Noise
- Browser QA is current for the latest integrated sweep; additional captures should be treated as incremental visual regression checks, not as a missing validation step.
