# JobRadar V2 - Project Status

> Last updated: 2026-03-23
> Canonical operational state lives in `docs/current-state/00-index.md`.

## Current Snapshot
- See `docs/current-state/00-index.md` for the canonical live state.
- Active branch in this workspace: `main`.
- `main` has PRs #15 (security hardening) and #16 (CodeQL + deps) merged.
- Backend: targeted settings/auth/admin integration tests pass, ruff clean, and the new settings/account contract is wired through the API.
- Frontend: lint clean, build clean, and the full Vitest suite passes.
- Audit status remains `39 FIXED / 1 VERIFIED_CLEAN / 4 STALE / 0 OPEN / 0 PARTIAL`.
- GitHub workflows are updated to current `actions/*@v6` releases.

## What Is Stable
- Cookie-based auth, refresh, revocation, rate limiting, and security headers
- Target-based scraping platform with ATS detection, tier routing, pagination crawling, and attempt telemetry
- Job enrichment, salary analysis, cover-letter generation, interview prep, resume tailoring, and application pipeline flows
- Frontend theme system with light mode and high-contrast dark mode
- Vault PATCH flows, admin cleanup, SSE credentialed transport, and current frontend build compatibility
- New frontend surfaces for copilot, networking, email signal logs, and outcomes
- Settings-backed saved-search updates, secret persistence, password change, account delete, and data clear actions

## Current Feature Status
The current shipped UI and backend contract are aligned for the Career OS overhaul:
- Shared design system and tokenized shell are in place
- `email`, `networking`, `outcomes`, and `copilot` are first-class frontend routes
- Settings now drives real backend flows for searches, integrations, password change, account delete, and data clear
- API keys are persisted through the dedicated integration endpoints

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
- Wire semantic search into Job Board UI
- Resume PDF generation end-to-end testing (WeasyPrint is optional dep)
- Saved-search alerts UI and scheduler UX
- Additional parser tuning for difficult JS-heavy career pages
- End-to-end Playwright coverage
