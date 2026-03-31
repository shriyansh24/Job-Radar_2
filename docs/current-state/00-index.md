# Current State Index - JobRadar V2

> Last updated: 2026-03-30

## Read Order
1. `00-index.md`
2. `01-repo-map.md`
3. `02-backend.md`
4. `03-frontend.md`
5. `04-data-and-scraping.md`
6. `05-ops-and-ci.md`
7. `06-open-items.md`
8. `07-system-analysis.md`
9. `../audit/00-index.md`

## Current Status At A Glance
- Reference-first UI migration is implemented in this workspace using the external UI repo as the visual authority and the current repo as the behavior authority.
- Active branch in this workspace: `main`.
- Full backend pytest now passes locally with coverage on the current branch.
- Frontend lint, test, and build pass locally after the latest frontend decomposition and copy cleanup pass.
- Committed browser coverage now includes auth/shell smoke, shell navigation, responsive shell behavior, route-family outcomes, communications/setup flows, prepare/intelligence/outcomes flows, operations/admin/data flows, profile/settings/auth roundtrips, resume preview/export, and route-family 8-mode theme assertions under `frontend/e2e/`.
- The current authenticated browser sweep is up to date, and representative screenshots now live in `.claude/ui-captures/`.
- Local Postgres schema was upgraded from Alembic revision `005` to `head` during QA so the settings/integration surfaces match the current schema.
- Settings integrations are no longer API-key-only: Google OAuth is now a live provider, and Gmail-first sync feeds the existing email and pipeline modules through both operator-triggered sync and the scheduled `gmail_sync` job on the `ops` worker lane.
- The audit ledger remains `39 FIXED / 1 VERIFIED_CLEAN / 4 STALE / 0 OPEN / 0 PARTIAL`.

## Latest Validation Snapshot

### Backend
- `cd backend && uv run pytest --cov=app --cov-report=json:coverage.json tests/`
- `cd backend && uv run alembic current`
- `cd backend && uv run alembic upgrade head`
- Latest local result on `2026-03-27`: `1025 passed, 1 skipped` with backend coverage at `71.24%`

### Frontend
- `cd frontend && npm run lint`
- `cd frontend && npm run test -- --run`
- `cd frontend && npm run e2e`
- `cd frontend && npm run build`
- Latest local result: lint, full test suite, and production build pass after the current frontend decomposition and copy cleanup pass. The committed Playwright lane now owns backend API startup as well, reusing `127.0.0.1:8000` when an API is already running and otherwise failing fast if the local Postgres/Redis contract is not reachable.

### Browser QA
- Start the local frontend dev server for manual sweeps; the committed Playwright lane now boots or reuses the backend API on its own.
- Authenticate through `/login`.
- Sweep every authenticated route on desktop, tablet, and phone.
- Capture representative screenshots into `.claude/ui-captures/`.
- Committed browser/e2e coverage now lives under `frontend/e2e/` and covers auth/shell smoke, shell navigation, responsive shell behavior, route-family outcomes, communications/setup flows, prepare/intelligence/outcomes flows, operations/admin/data flows, profile/settings/auth roundtrips, resume preview/export, and route-family 8-mode theme assertions; the screenshot sweep is still useful as a broader operator QA lane, not the only browser signal.

## Documentation Map

| File | Purpose |
|------|---------|
| `01-repo-map.md` | Repo layout, doc map, and onboarding order |
| `02-backend.md` | Backend stack, runtime behavior, and recent fixes |
| `03-frontend.md` | Frontend stack, visual system, contract alignments, and QA state |
| `04-data-and-scraping.md` | Data model, scraper platform, and scheduler state |
| `05-ops-and-ci.md` | Local commands, Docker, CI, dependency checks, workflow state |
| `06-open-items.md` | Deferred work, structural gaps, and non-bug residuals |
| `07-system-analysis.md` | Reference snapshot of the repository/system layout and branch deltas; defer to `01-repo-map.md` and `../repo-hardening/06-test-taxonomy.md` for live filesystem ownership |
| `../audit/00-index.md` | Verified bug ledger and stale-audit tracking |
| `../research/00-index.md` | Future design and roadmap material |

## Notes For Agents
- Treat this directory plus `docs/audit/` as the current source of truth.
- Treat `docs/research/` as future-looking reference material.
- Treat `docs/repo-hardening/` as the normalization and traceability audit trail while the hardening pass is in progress, not as a replacement for current-state.
- Use `CLAUDE.md` and `AGENTS.md` for working conventions, not product-state discovery.
- Treat `05-ops-and-ci.md` as the canonical runtime-status page for the live ARQ queue topology, worker services, and deployment-facing follow-through.
- The current workspace includes the reference-first frontend migration: shared shell, responsive navigation, light/dark parity, backend-aligned settings/admin/resume/salary/search-expansion surfaces, decomposed page families, and a completed browser-verified cleanup pass over the main routed surfaces.
- The current routed app now includes live analytics pattern panels plus backend-backed resume template preview and PDF export flows on the main branch, not just branch-only recovery code.
- Gmail-first Google integration is part of the current live scope; Calendar, Drive, and `googleworkspace/cli` are not.
