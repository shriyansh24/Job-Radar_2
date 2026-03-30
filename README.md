# JobRadar V2

JobRadar V2 is a full-stack job-search and career-operations workspace. It combines direct job scraping, enrichment, pipeline tracking, interview prep, resume tooling, compensation analysis, vault management, and auto-apply support behind a single React frontend and FastAPI backend.

## Start Here
- Live repo state: `docs/current-state/00-index.md`
- Bug ledger: `docs/audit/00-index.md`
- Hardening and traceability trail: `docs/repo-hardening/00-index.md`
- Operator/agent command surface: `CLAUDE.md`
- Workspace-specific preferences and facts: `AGENTS.md`
- High-level status summary: `PROJECT_STATUS.md`

## Documentation Hierarchy
- `docs/current-state/` is the live operational source of truth.
- `docs/audit/` is the bug ledger.
- `docs/research/` is exploratory roadmap material, not shipped scope by default.
- `docs/repo-hardening/` is the repository normalization and traceability trail while the hardening program is active.

## Architecture At A Glance
- Frontend: React 19, Vite 6, TypeScript, Tailwind CSS v4, Zustand, React Query
- Backend: FastAPI, SQLAlchemy async, PostgreSQL, Alembic, `uv`
- Runtime: compose-first local stack with Postgres, Redis, one-shot migrations, API, dedicated scheduler, queue-specific ARQ workers (`scraping`, `analysis`, `ops`), and frontend
- Browser validation: committed Playwright coverage under `frontend/e2e/` plus broader screenshot sweeps under `.claude/ui-captures/`
- Selective P1 recovery is now live on `main`: queue-backed worker runtime, ATS identity persistence on scraped jobs, recovered auto-apply execution and operator controls, richer interview prep bundles, bounded hybrid semantic search, live analytics pattern surfaces, resume preview/export flows, and the digest-worker follow-through on the ops lane

## Current Branch Strategy
- `main` is the canonical active and default branch.
- `codex/ui-changes` was the final broad integration branch and is now merged into `main`.
- `feat/p1-core-value` is a selective recovery source, not a blind-merge target.
- Historical and retained branch decisions are tracked in `docs/repo-hardening/04-branch-disposition.md`.

## Local Runtime Baseline

Canonical full-stack local runtime:

```bash
docker compose up -d
```

This compose baseline starts:
- Postgres on `5432`
- Redis on `6379`
- one-shot migrations
- backend API on `8000`
- dedicated scheduler runtime
- `worker-scraping`
- `worker-analysis`
- `worker-ops`
- frontend container on `3000`

Host-local development is still supported, but it is an override on top of the compose baseline rather than the canonical repo story.

### Host-Local Backend
```bash
cd backend
uv sync --frozen
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

### Dedicated Scheduler
```bash
cd backend
uv sync --frozen
uv run python -m app.runtime.scheduler
```

### Dedicated Queue Workers
```bash
cd backend
uv sync --frozen
uv run python -m app.runtime.arq_worker scraping
uv run python -m app.runtime.arq_worker analysis
uv run python -m app.runtime.arq_worker ops
```

The scheduler now enqueues named jobs onto ARQ queues `scraping`, `analysis`, and `ops`. Queue-specific worker services consume those queues directly instead of the scheduler spawning one-shot worker subprocesses. Treat [05-ops-and-ci.md](D:/jobradar-v2/docs/current-state/05-ops-and-ci.md) as the authoritative runtime-status page for current worker ownership, runtime health probes, and validation commands.
Migration replay, rollback stance, and backfill guidance for the current tree are documented in [10-migration-ops.md](D:/jobradar-v2/docs/repo-hardening/10-migration-ops.md).

### Host-Local Frontend
```bash
cd frontend
npm ci
npm run dev
```

Host-local frontend runs on `http://localhost:5173`.

If you use the bind-mounted dev overlay instead, `docker-compose.dev.yml` already sets `VITE_API_PROXY_TARGET=http://backend:8000` for the frontend container.

## Validation

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
npm run e2e
npm run build
```

### Browser QA
- Keep broader screenshot captures in `.claude/ui-captures/`
- Keep committed browser coverage in `frontend/e2e/`
- The committed browser lane currently covers auth/shell smoke, shell navigation, responsive shell behavior, route-family outcomes for `dashboard/jobs/pipeline/settings/targets`, communications/setup flows, prepare/intelligence/outcomes flows, operations/admin/data surfaces including the Auto Apply operator controls, the recovered interview/search flow, profile/settings/auth roundtrips, resume template preview/export, and route-family 8-mode theme checks across the routed families the app exposes. The live frontend also now exposes analytics pattern panels and backend-backed resume preview/export flows on the main routed surfaces.
- Treat `docs/current-state/05-ops-and-ci.md` as the authoritative validation and CI reference

## Test Taxonomy
- Frontend unit and route tests: `frontend/src/tests/`
- Frontend browser/e2e tests: `frontend/e2e/`
- Backend tests: `backend/tests/{contracts,edge_cases,fixtures,infra,integration,migrations,security,unit,workers}`

Per-tree guidance lives in:
- `frontend/src/tests/README.md`
- `frontend/e2e/README.md`
- `backend/tests/README.md`

## Repo Layout

```text
jobradar-v2/
|-- backend/              FastAPI app, migrations, workers, backend tests
|-- frontend/             React app, Vitest suites, Playwright suites
|-- docs/                 current-state, audit, research, repo-hardening
|-- infra/                minimal runtime support assets
|-- scripts/              repo-level validation helpers
|-- .github/              workflows, templates, CODEOWNERS
|-- .claude/ui-captures/  browser QA artifacts
|-- README.md
|-- CLAUDE.md
|-- AGENTS.md
|-- PROJECT_STATUS.md
`-- DECISIONS.md
```

## GitHub And Safety
- GitHub Actions currently cover `Repository Validation`, `Docs Validation`, `Migration Safety`, `Dependency Review`, `CodeQL`, and the dedicated browser check `Frontend E2E Smoke / frontend-e2e-smoke`.
- Backend dependency auditing runs through `scripts/run_backend_dependency_audit.py` and the reviewed exception policy in `backend/pip-audit-policy.json` so CVE exceptions are explicit, dated, and checked in instead of hidden inside workflow YAML.
- Treat `main` as PR-only.
- Keep docs, tests, and runtime-truth updates in the same batch as behavior changes.
- Keep ARQ queue-topology claims, worker-service claims, and retry-policy changes in `docs/current-state/05-ops-and-ci.md`.
- Do not treat `docs/research/` as committed scope unless it is explicitly promoted into `docs/current-state/` and the relevant front-door docs.

## Read Next
- `docs/current-state/00-index.md`
- `docs/current-state/05-ops-and-ci.md`
- `docs/repo-hardening/04-branch-disposition.md`
- `docs/repo-hardening/05-implementation-traceability-matrix.md`
