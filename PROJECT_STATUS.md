# JobRadar V2 - Project Status

> Last updated: 2026-03-23
> Canonical operational state lives in `docs/current-state/00-index.md`.

## Current Snapshot
- See `docs/current-state/00-index.md` for the canonical live state.
- This pass combined stale-audit revalidation, CodeQL-style cleanup, CI hardening, and test-suite expansion.
- Local validation completed in this pass:
  - backend `539 passed`, coverage `60.10%`
  - frontend `23` test files, `35` tests, coverage `43.19%` statements
  - backend `pip check`, `pip-audit`, `bandit`, `ruff`, and targeted `mypy` all passed
  - frontend `npm audit`, lint, build, and coverage-gated tests all passed
- Audit status is now `39 FIXED / 1 VERIFIED_CLEAN / 4 STALE / 0 OPEN / 0 PARTIAL`.

## Verified In This Pass
- `.env` remains ignored by `.gitignore`, and this clone only tracks `.env.example`
- Circuit-breaker recovery behavior is covered by the passing rate-limiter unit tests
- `EventBus.publish()` still fans out through unbounded `asyncio.Queue()` subscribers, so the old full-queue claim does not match live code
- SimHash determinism and the current dedup threshold behavior pass targeted unit tests
- `ApifyScraper` remains wired into the live keyword-search scraping path via `ScrapingService.run_scrape()`
- CI now enforces backend Bandit, targeted backend mypy, backend coverage `>=60%`, and frontend coverage `>=40%`

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
- Resume PDF generation and template polish
- Saved-search alerts UI and scheduler UX
- Additional parser tuning for difficult JS-heavy career pages
- End-to-end Playwright coverage
- Longer-term scraper-library vendoring decisions
