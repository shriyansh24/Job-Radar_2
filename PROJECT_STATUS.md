# JobRadar V2 - Project Status

> Last updated: 2026-03-22
> Canonical operational state lives in `docs/current-state/00-index.md`.

## Current Snapshot
- See `docs/current-state/00-index.md` for the canonical live state.
- Local validation is green for backend lint/tests/dependency checks and frontend audit/lint/tests/build.
- Audit status remains `39 FIXED / 5 STALE / 0 OPEN / 0 PARTIAL`.
- GitHub workflows are updated to current `actions/*@v6` releases and enforce lock-aware dependency checks in CI.

## What Is Stable
- Cookie-based auth, refresh, revocation, rate limiting, and security headers
- Target-based scraping platform with ATS detection, tier routing, pagination crawling, and attempt telemetry
- Job enrichment, salary analysis, cover-letter generation, interview prep, resume tailoring, and application pipeline flows
- Frontend theme system with light mode and high-contrast dark mode
- Vault PATCH flows, admin cleanup, SSE credentialed transport, and current frontend build compatibility

## Recent Fixes In The Latest Pass
- Cleared the backend Ruff backlog that was failing GitHub Actions
- Updated GitHub Actions runtimes and added dependency-health checks to CI
- Hardened enrichment so failed LLM enrichment does not persist partial job mutations
- Hardened interview generation and prep so empty model payloads fail explicitly
- Fixed interview job-context loading to use `company_name`
- Hardened router JSON fallback so all-empty model responses raise instead of silently returning `{}`
- Aligned `Notification.created_at` with the timezone-aware database schema
- Hardened scraper circuit-breaker timing for Windows/high-resolution clock behavior

## Where To Read Next
1. `docs/current-state/00-index.md`
2. `docs/audit/00-index.md`
3. `AGENTS.md`
4. `CLAUDE.md`
5. `README.md`

## Non-Blocking Residuals
- Vitest prints a non-fatal `--localstorage-file` warning during frontend tests.

## Deferred Work (Not Current Bugs)
- Resume PDF generation and template polish
- Saved-search alerts UI and scheduler UX
- Additional parser tuning for difficult JS-heavy career pages
- End-to-end Playwright coverage
- Longer-term scraper-library vendoring decisions
