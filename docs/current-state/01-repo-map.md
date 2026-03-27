# Repo Map - JobRadar V2

## Monorepo Layout

```text
jobradar-v2/
|-- backend/      FastAPI app, workers, scripts, tests
|-- frontend/     React app, API clients, state, tests
|-- docs/         Audit, current-state, repo-hardening, research, historical plans
|-- infra/        Infrastructure support files
|-- .github/      CI, repo guardrails, templates, CODEOWNERS
|-- scripts/      Repo-level validation helpers
|-- CLAUDE.md     Agent playbook
|-- AGENTS.md     User preferences and workspace facts
|-- PROJECT_STATUS.md
`-- README.md
```

## Test Layout
- `frontend/src/tests/` is the live Vitest taxonomy:
  - `app/`, `api/`, `components/`, `hooks/`, `pages/`, `support/`
- `backend/tests/` is the live pytest taxonomy:
  - `contracts/`, `edge_cases/`, `fixtures/`, `infra/`, `integration/`, `migrations/`, `security/`, `unit/`, `workers/`
- The authoritative per-tree breadcrumbs live in:
  - `frontend/src/tests/README.md`
  - `backend/tests/README.md`

## Operational Read Order
1. `docs/current-state/00-index.md`
2. `docs/audit/00-index.md`
3. `AGENTS.md`
4. `CLAUDE.md`
5. `PROJECT_STATUS.md`
6. `README.md`

## Historical vs Current Docs
- Current:
  - `docs/current-state/`
  - `docs/audit/`
  - `CLAUDE.md`
  - `AGENTS.md`
- Future-looking:
  - `docs/research/`
- Historical:
  - `docs/system-inventory/`
  - `docs/repo-hardening/` while the hardening program is still in progress

## Important Local-Only Files
- `.claude/launch.json` is machine-local and should not be committed.
- `.claude/worktrees/` may contain old worktree mirrors and should not be used to infer live repo state.

## Primary Commands
- Backend commands run from `backend/` via `uv run`.
- Frontend commands run from `frontend/` via `npm`.
- Docker and workflow files live at repo root.
