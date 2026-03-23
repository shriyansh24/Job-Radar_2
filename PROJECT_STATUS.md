# JobRadar V2 - Project Status

> Last updated: 2026-03-23
> Canonical operational state lives in `docs/current-state/00-index.md`.

## Current Snapshot
- See `docs/current-state/00-index.md` for the canonical live state.
- Active development branch: `feat/p2-polish-advanced` (all P0/P1/P2 feature code).
- `main` has PRs #15 (security hardening) and #16 (CodeQL + deps) merged.
- Backend: **716 tests pass**, ruff clean, 23 routers mounted, 37 DB tables.
- Frontend: lint clean, build clean, 9 tests pass in 6 files.
- Audit status remains `39 FIXED / 5 STALE / 0 OPEN / 0 PARTIAL`.
- GitHub workflows are updated to current `actions/*@v6` releases.

## What Is Stable
- Cookie-based auth, refresh, revocation, rate limiting, and security headers
- Target-based scraping platform with ATS detection, tier routing, pagination crawling, and attempt telemetry
- Job enrichment, salary analysis, cover-letter generation, interview prep, resume tailoring, and application pipeline flows
- Frontend theme system with light mode and high-contrast dark mode
- Vault PATCH flows, admin cleanup, SSE credentialed transport, and current frontend build compatibility

## P0/P1/P2 Feature Status (feat/p2-polish-advanced)
All 38 spec features have backend code. Backend wiring is now complete:
- All 37 DB tables exist (10 P2 tables created via consolidation migration `005`)
- 23 routers mounted (email and outcomes added this session)
- Resume `ir_schema.py`, `renderer.py`, and `professional.html` template all present
- `users.created_at`/`updated_at` fixed to `timestamp with time zone`

Remaining frontend gaps:
- No API modules or pages for: email, networking, outcomes, copilot chat
- Settings stubs (change password, delete account, clear data) are no-ops
- API keys collected but not persisted to backend

## Where To Read Next
1. `docs/current-state/00-index.md`
2. `docs/audit/00-index.md`
3. `AGENTS.md`
4. `CLAUDE.md`
5. `README.md`

## Non-Blocking Residuals
- Repo-wide strict backend mypy remains deferred outside the current targeted CI scope.
- Vitest still emits non-fatal `--localstorage-file` warnings.

## Deferred Work (Not Current Bugs)
- Create frontend API modules and pages for: email, networking, outcomes, copilot chat
- Add backend endpoints for: change password, delete account, clear data
- Wire API key persistence from Settings/Onboarding to backend
- Wire semantic search into Job Board UI
- Resume PDF generation end-to-end testing (WeasyPrint is optional dep)
- Saved-search alerts UI and scheduler UX
- Additional parser tuning for difficult JS-heavy career pages
- End-to-end Playwright coverage
- Rebase feat/p2-polish-advanced onto current main
