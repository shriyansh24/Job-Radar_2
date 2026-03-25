# JobRadar V2 - Project Status

> Last updated: 2026-03-24
> Canonical operational state lives in `docs/current-state/00-index.md`.

## Current Snapshot
- See `docs/current-state/00-index.md` for the canonical live state.
- Active branch in this workspace: `codex/ui-changes`.
- Frontend: reference-first UI migration is in place, and lint, tests, and build pass locally.
- Backend: targeted auth/settings/admin/vault integration tests pass locally.
- Browser QA: desktop, tablet, and phone sweeps passed across all routed frontend surfaces, and representative screenshots were written to `output/playwright/`.
- Audit status remains `39 FIXED / 1 VERIFIED_CLEAN / 4 STALE / 0 OPEN / 0 PARTIAL`.

## What Is Stable
- Cookie-based auth, refresh, revocation, rate limiting, and security headers
- Target-based scraping platform with ATS detection, tier routing, pagination crawling, and attempt telemetry
- Job enrichment, salary analysis, cover-letter generation, interview prep, resume tailoring, and application pipeline flows
- Reference-first frontend shell with fixed header, responsive desktop rail, mobile drawer, mobile bottom nav, and light/dark parity
- Search expansion, resume tailoring, salary research/evaluation, settings integrations, vault editing, and target/scraper surfaces aligned to live backend contracts
- Local browser QA artifacts for the current migration pass under `output/playwright/`

## Current Feature Status
The current shipped UI and backend contract are aligned for the reference-first migration:
- all routed frontend pages use the shared command-center shell
- `/resume`, `/interview`, `/salary`, `/vault`, `/copilot`, `/analytics`, `/outcomes`, `/targets`, `/search-expansion`, `/admin`, and `/settings` are running against the current contract layer
- settings and integrations persist against the live backend once the local schema is migrated to `head`

## Where To Read Next
1. `docs/current-state/00-index.md`
2. `docs/audit/00-index.md`
3. `AGENTS.md`
4. `CLAUDE.md`
5. `README.md`

## Non-Blocking Residuals
- Repo-wide strict backend mypy remains deferred outside the targeted CI scope.
- Vitest still emits non-fatal `--localstorage-file` warnings.
- Vite still emits a chunk-size warning during production builds.
- Browser-level QA still surfaces non-fatal password `autocomplete` hints on Settings inputs and Recharts width warnings when charts mount in hidden or zero-sized containers during automated sweeps.

## Deferred Work (Not Current Bugs)
- Wire semantic search into the Job Board as a richer interactive filter flow
- Resume PDF generation end-to-end testing
- Saved-search alerts UI and scheduler UX
- Additional parser tuning for difficult JS-heavy career pages
- Broader end-to-end Playwright coverage beyond the current smoke and screenshot pass
