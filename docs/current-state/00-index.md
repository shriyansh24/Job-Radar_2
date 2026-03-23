# Current State Index - JobRadar V2

> Last updated: 2026-03-23

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
- `SEC-01`, `SC-03`, `SC-05`, `SC-07`, and `SC-14` were rechecked against live code on `2026-03-23`.
- Full backend and frontend validation was rerun after the latest security, test, and CI hardening changes.
- `ApifyScraper` remains part of the live `ScrapingService.run_scrape()` path, so the old "dead code" audit claim is stale.
- The audit ledger is now `39 FIXED / 1 VERIFIED_CLEAN / 4 STALE / 0 OPEN / 0 PARTIAL`.
- CI is aligned to the current branch state: backend coverage gate `60%`, frontend coverage gate `40%`, Bandit, targeted mypy, pip-audit, and CodeQL v4.

## Latest Validation Snapshot

### Full Validation
- `cd backend && uv run python -m pip check`
- `cd backend && uv export --frozen --format requirements-txt --no-emit-project -o .ci-requirements.txt`
- `cd backend && uv tool run pip-audit -r .ci-requirements.txt`
- `cd backend && uv tool run bandit -r app/ -c pyproject.toml --severity-level medium`
- `cd backend && uv run ruff check .`
- `cd backend && uv run mypy app/auth/service.py app/config.py app/shared/middleware.py app/scraping/deduplication.py app/scraping/port.py --ignore-missing-imports`
- `cd backend && uv run pytest --cov=app --cov-fail-under=60 tests/`
- `cd frontend && npm audit --audit-level high`
- `cd frontend && npm run lint`
- `cd frontend && npm run test -- --run`
- `cd frontend && npm install --no-save @vitest/coverage-v8`
- `cd frontend && npm run test -- --run --coverage --coverage.thresholds.statements=40`
- `cd frontend && npm run build`
- Latest local results:
  - backend: `539 passed`, coverage `60.10%`
  - frontend: `23` test files, `35` tests, coverage `43.19%` statements

### Verified Clean / Stale-Item Recheck
- `git ls-files '.env' 'backend/.env' '.env.*' 'backend/.env.*'`
- `Get-ChildItem -Force .env*`
- `Get-ChildItem -Force backend\\.env*`
- `git grep -n "ApifyScraper|run_scrape|EventBus|DeduplicationService" backend/app backend/tests`
- `cd backend && uv run pytest tests/unit/test_rate_limiter.py tests/unit/test_deduplication.py tests/unit/scraping/test_simhash_deterministic.py`
- Latest local result: `29 passed`

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
