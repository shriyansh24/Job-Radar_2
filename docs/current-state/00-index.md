# Current State Index - JobRadar V2

> Last updated: 2026-03-22

## Read Order
1. `00-index.md`
2. `01-repo-map.md`
3. `02-backend.md`
4. `03-frontend.md`
5. `04-data-and-scraping.md`
6. `05-ops-and-ci.md`
7. `06-open-items.md`
8. `../audit/00-index.md`

## Current Status At A Glance
- No known blocking reproducible bugs remain after the latest fix pass.
- Backend lint, tests, and dependency-health checks pass locally.
- Frontend audit, lint, tests, and build pass locally.
- GitHub Actions workflows are updated to current `actions/*@v6` releases.
- The audit ledger is closed at `39 FIXED / 5 STALE / 0 OPEN / 0 PARTIAL`.

## Latest Validation Snapshot

### Backend
- `cd backend && uv run python -m pip check`
- `cd backend && uv export --frozen --format requirements-txt --no-emit-project -o .ci-requirements.txt`
- `cd backend && uv tool run pip-audit -r .ci-requirements.txt`
- `cd backend && uv run ruff check .`
- `cd backend && uv run pytest`
- Latest local result: `493 passed`

### Frontend
- `cd frontend && npm audit --audit-level high`
- `cd frontend && npm run lint`
- `cd frontend && npm run test -- --run`
- `cd frontend && npm run build`
- Latest local result: `9 passed` in `6` test files

## Documentation Map

| File | Purpose |
|------|---------|
| `01-repo-map.md` | Repo layout, doc map, and onboarding order |
| `02-backend.md` | Backend stack, runtime behavior, and recent fixes |
| `03-frontend.md` | Frontend stack, theme system, and UI/runtime state |
| `04-data-and-scraping.md` | Data model, scraper platform, and scheduler state |
| `05-ops-and-ci.md` | Local commands, Docker, CI, dependency checks, workflow state |
| `06-open-items.md` | Deferred work and non-bug residuals |
| `../audit/00-index.md` | Verified bug ledger and stale-audit tracking |
| `../research/00-index.md` | Future design and roadmap material |
| `../superpowers/` | Historical scraper-platform design and implementation plans |

## Notes For Agents
- Treat this directory plus `docs/audit/` as the current source of truth.
- Treat `docs/research/` as future-looking reference material.
- Treat `docs/superpowers/` as historical implementation planning, not the live priority queue.
- Use `CLAUDE.md` and `AGENTS.md` for working conventions, not product-state discovery.
