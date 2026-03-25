# Current State Index - JobRadar V2

> Last updated: 2026-03-24

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
- Reference-first UI migration is implemented in this workspace using the external UI repo as the visual authority and the current repo as the behavior authority.
- Active branch in this workspace: `codex/ui-changes`.
- Backend targeted auth/settings/admin/vault integration tests pass locally.
- Frontend lint, tests, and build pass locally.
- Browser sweeps passed across all 21 authenticated frontend routes on desktop, tablet, and phone.
- Representative screenshot artifacts for the current pass were written to `output/playwright/`.
- Local Postgres schema was upgraded from Alembic revision `005` to `head` during QA so the settings/integration surfaces match the current schema.
- The audit ledger remains `39 FIXED / 1 VERIFIED_CLEAN / 4 STALE / 0 OPEN / 0 PARTIAL`.

## Latest Validation Snapshot

### Backend
- `cd backend && uv run pytest tests/integration/test_auth_api.py tests/integration/test_settings_api.py tests/integration/test_admin_api.py tests/integration/test_vault_api.py`
- `cd backend && uv run alembic current`
- `cd backend && uv run alembic upgrade head`
- Latest local result: `26 passed`

### Frontend
- `cd frontend && npm run lint`
- `cd frontend && npm run test -- --run`
- `cd frontend && npm run build`
- Latest local result: `24` test files, `39` tests

### Browser QA
- Start the local backend and frontend dev servers.
- Authenticate through `/login`.
- Sweep every authenticated route on desktop, tablet, and phone.
- Capture representative screenshots into `output/playwright/`.

## Documentation Map

| File | Purpose |
|------|---------|
| `01-repo-map.md` | Repo layout, doc map, and onboarding order |
| `02-backend.md` | Backend stack, runtime behavior, and recent fixes |
| `03-frontend.md` | Frontend stack, visual system, contract alignments, and QA state |
| `04-data-and-scraping.md` | Data model, scraper platform, and scheduler state |
| `05-ops-and-ci.md` | Local commands, Docker, CI, dependency checks, workflow state |
| `06-open-items.md` | Deferred work, structural gaps, and non-bug residuals |
| `../audit/00-index.md` | Verified bug ledger and stale-audit tracking |
| `../research/00-index.md` | Future design and roadmap material |

## Notes For Agents
- Treat this directory plus `docs/audit/` as the current source of truth.
- Treat `docs/research/` as future-looking reference material.
- Use `CLAUDE.md` and `AGENTS.md` for working conventions, not product-state discovery.
- The current workspace includes the reference-first frontend migration: shared shell, responsive navigation, light/dark parity, backend-aligned settings/admin/resume/salary/search-expansion surfaces, and browser QA artifacts.
