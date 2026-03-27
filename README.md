# JobRadar V2

AI-powered job hunting assistant with direct-job scraping, enrichment, pipeline tracking, interview prep, resume tooling, compensation research, vault management, and auto-apply support.

## Start Here
- Current repo state: `docs/current-state/00-index.md`
- Audit ledger: `docs/audit/00-index.md`
- Repo hardening trail: `docs/repo-hardening/00-index.md`
- Agent preferences and frontend expectations: `AGENTS.md`
- Agent playbook and command surface: `CLAUDE.md`
- High-level project summary: `PROJECT_STATUS.md`

## Stack
- Backend: Python 3.12, FastAPI, SQLAlchemy async, PostgreSQL, Redis, Alembic, `uv`
- Frontend: React 19, Vite 6, TypeScript, Tailwind CSS v4, Zustand, React Query
- AI/LLM: OpenRouter-backed services for enrichment, interview prep, salary analysis, resume tailoring, cover letters, and copilot flows
- Scraping: ATS adapters, target scheduler, browser pool, page crawler, deduplication, telemetry
- UI system: reference-first command-center shell with `Inter`, `JetBrains Mono`, Phosphor icons, light/dark parity, and shadowless buttons

## Quick Start

### Prerequisites
- Docker
- Node.js 22+
- Python 3.12+

### Infrastructure

Canonical full-stack local runtime:

```bash
docker compose up -d
```

This base compose flow now starts Postgres, Redis, one-shot migrations, the API, the dedicated scheduler, and the frontend.
Host-local frontend/backend development is still supported, but it is an override on top of the compose infrastructure baseline rather than the canonical repo story.
If you already have a separate manual `jobradar-postgres` container, treat it as a legacy local override rather than the documented default.
Redis is still provisioned in the compose stack, but the current API and dedicated scheduler do not depend on it to reach their ready state.

### Backend

```bash
cd backend
uv sync --frozen
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Dedicated scheduler process:

```bash
cd backend
uv sync --frozen
uv run python -m app.runtime.scheduler
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`.

If you run the bind-mounted Docker dev overlay instead of host-local Vite, the checked-in `docker-compose.dev.yml` already sets `VITE_API_PROXY_TARGET=http://backend:8000` so the frontend container can proxy to the backend container correctly.

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
- Store screenshots and other QA artifacts in `.claude/ui-captures/`.
- Committed browser/e2e coverage now lives under `frontend/e2e/`.

## Repo Protections
- GitHub Actions currently cover repository validation, CodeQL, dependency review, docs/path validation, and migration replay safety.
- A dedicated `Frontend E2E Smoke / frontend-e2e-smoke` check now exercises the live login, authenticated shell navigation, and theme persistence flows against the real backend.
- The browser lane also runs weekly as a low-noise drift check for the dedicated scheduler/bootstrap/login path.
- Dependabot is enabled for GitHub Actions, frontend npm dependencies, and backend Python dependencies.
- Healthy branch-protection assumptions for this repo:
  - treat `main` as PR-only
  - require:
    - `Repository Validation / Backend quality and security checks`
    - `Repository Validation / Backend test suite`
    - `Repository Validation / Frontend audit and lint`
    - `Repository Validation / Frontend tests and build`
    - `Docs Validation / Docs truth and path validation`
    - `Migration Safety / Alembic replay on clean Postgres`
    - `Dependency Review / Dependency review`
    - `CodeQL / CodeQL (python)`
    - `CodeQL / CodeQL (javascript-typescript)`
    - `Frontend E2E Smoke / frontend-e2e-smoke`
    before merge
  - keep docs, tests, and runtime-truth updates in the same batch as behavior changes
  - do not turn the required browser workflow into a matrix or a path-filtered PR workflow, because the emitted check name must stay stable and always present

## Current Verification Snapshot (2026-03-27)
- Frontend lint passed.
- Frontend tests passed.
- Frontend production build passed.
- Targeted backend auth/settings/admin/vault integration tests passed: `26` tests.
- The integrated frontend sweep has current authenticated browser captures under `.claude/ui-captures/`.
- Local Postgres schema was upgraded to Alembic `head` during QA so the live settings/integration surfaces match the current code.

## Repo Layout

```text
jobradar-v2/
|-- backend/
|   |-- app/            # FastAPI application (domain modules)
|   |-- scripts/        # CLI utilities
|   |-- tests/          # pytest suite grouped by role (contracts/infra/integration/migrations/security/unit/workers)
|   `-- pyproject.toml  # backend tooling + pytest config
|-- frontend/
|   |-- src/            # React 19 application
|   |   `-- tests/      # Vitest suites grouped by app/api/components/hooks/pages/support
|   |-- e2e/            # Playwright smoke/flows/theme-matrix coverage
|   `-- system.md       # Frontend design-system source of truth
|-- docs/
|   |-- audit/          # Bug ledger (39 FIXED / 1 VERIFIED_CLEAN / 4 STALE)
|   |-- current-state/  # Canonical live state docs
|   |-- repo-hardening/ # Repository normalization and traceability artifacts
|   `-- research/       # Future design research
|-- scripts/           # Repo-level validation helpers
|-- .claude/ui-captures/ # Browser QA artifacts and route/theme capture packs
|-- .github/workflows/  # CI and repo guardrails
|-- AGENTS.md           # Agent preferences and frontend expectations
|-- CLAUDE.md           # Agent playbook and working commands
|-- DECISIONS.md        # Architectural decisions
|-- PROJECT_STATUS.md   # High-level project status
`-- README.md
```

## Notes
- Use `uv run` for backend commands and `npm` for frontend commands.
- The live frontend is a reference-first command-center UI while preserving the app's routed behavior and backend contracts.
- Buttons are intentionally shadowless; elevation is reserved for panels and structural surfaces.
- Test taxonomy now lives alongside the code: `frontend/src/tests/README.md` and `backend/tests/README.md`.
- Browser test taxonomy now lives in `frontend/e2e/README.md`.
- The current live product state is documented under `docs/current-state/`.
- `docs/repo-hardening/` is the active normalization trail while the repository hardening pass is in progress.
- `docs/research/` contains future-planning material, not current requirements.
- Cookie-authenticated unsafe requests are protected by the readable `jr_csrf_token` cookie plus the `X-CSRF-Token` header; FastAPI trusted hosts are enforced through `JR_TRUSTED_HOSTS`.
