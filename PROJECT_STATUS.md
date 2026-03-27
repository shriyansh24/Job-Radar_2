# JobRadar V2 - Project Status

> Last updated: 2026-03-27
> Canonical operational state lives in `docs/current-state/00-index.md`.

## Current Snapshot
- See `docs/current-state/00-index.md` for the canonical live state.
- Active branch in this workspace: `codex/ui-changes`.
- Frontend: reference-first UI migration is in place, major routed pages have been decomposed into smaller component groups, generated shell/page copy has been stripped from the main surfaces, and lint/test/build are green.
- Backend: targeted auth/settings/admin/vault integration tests pass locally.
- Browser QA: the latest authenticated sweep is current, and representative screenshots are stored in `.claude/ui-captures/`.
- Audit status remains `39 FIXED / 1 VERIFIED_CLEAN / 4 STALE / 0 OPEN / 0 PARTIAL`.

## What Is Stable
- Cookie-based auth, refresh, revocation, rate limiting, and security headers
- Target-based scraping platform with ATS detection, tier routing, pagination crawling, and attempt telemetry
- Job enrichment, salary analysis, cover-letter generation, interview prep, resume tailoring, and application pipeline flows
- Reference-first frontend shell with fixed header, responsive desktop rail, mobile drawer, mobile bottom nav, shadowless buttons, and light/dark parity
- Search expansion, resume tailoring, salary research/evaluation, settings integrations, vault editing, and target/scraper surfaces aligned to live backend contracts
- Current browser QA artifacts under `.claude/ui-captures/`

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
- Further route-by-route visual polish and decomposition are still worthwhile, but the current frontend/browser verification set is already current.

## Deferred Work (Not Current Bugs)
- Wire semantic search into the Job Board as a richer interactive filter flow
- Resume PDF generation end-to-end testing
- Saved-search alerts UI and scheduler UX
- Additional parser tuning for difficult JS-heavy career pages
- Broader end-to-end Playwright coverage beyond the current smoke and screenshot pass
- Continued route-by-route visual cleanup and decomposition for the remaining larger frontend surfaces
