# Repo Map - JobRadar V2

## Monorepo Layout

```text
jobradar-v2/
|-- backend/      FastAPI app, workers, scripts, tests
|-- frontend/     React app, API clients, state, tests
|-- docs/         Audit, current-state, research, historical plans
|-- infra/        Infrastructure support files
|-- .github/      CI, CodeQL, dependency review, Dependabot
|-- CLAUDE.md     Agent playbook
|-- AGENTS.md     User preferences and workspace facts
|-- PROJECT_STATUS.md
`-- README.md
```

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
  - `docs/superpowers/`

## Important Local-Only Files
- `.claude/launch.json` is machine-local and should not be committed.
- `.claude/worktrees/` may contain old worktree mirrors and should not be used to infer live repo state.

## Primary Commands
- Backend commands run from `backend/` via `uv run`.
- Frontend commands run from `frontend/` via `npm`.
- Docker and workflow files live at repo root.
