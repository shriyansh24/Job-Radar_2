# Backend State - JobRadar V2

## Stack
- Python 3.12
- FastAPI
- SQLAlchemy 2.0 async
- PostgreSQL + Alembic
- Redis
- `uv` for dependency and command execution

## Key Runtime Areas
- Auth: cookie-based access and refresh flow with revocation and rate limiting
- Jobs: SHA-256 string IDs, enrichment fields, lifecycle tracking, application relationship via `selectin`
- Enrichment: HTML cleaning, markdown conversion, LLM extraction, salary/experience enrichment
- Interview: question generation, prep bundles, answer evaluation, persisted interview sessions
- Scraping: ATS registry, scheduler, tier routing, page crawling, adapter registry, browser pool
- Workers: scraping, enrichment, follow-up/notification support, scheduler wiring

## Runtime Invariants
- Runtime `DateTime` columns should be timezone-aware.
- LLM-driven JSON paths should fail explicitly on unusable payloads.
- Failed enrichment should not persist partial job mutations.
- Interview context should load `company_name` from jobs, not a non-existent `company` field.

## Recent Verified Fixes
- `Notification.created_at` is explicitly timezone-aware and matches the schema.
- Failed enrichment now restores job fields instead of persisting partial mutations.
- Interview generation no longer persists empty sessions when model output is empty.
- Interview prep now surfaces empty/failed model responses as a `502`.
- `ModelRouter.complete_json()` now raises when all candidate models return empty JSON.
- Interview job context now uses `company_name`.

## Validation
- `cd backend && uv run python -m pip check`
- `cd backend && uv export --frozen --format requirements-txt --no-emit-project -o .ci-requirements.txt`
- `cd backend && uv tool run pip-audit -r .ci-requirements.txt`
- `cd backend && uv tool run bandit -r app/ -c pyproject.toml --severity-level medium`
- `cd backend && uv run ruff check .`
- `cd backend && uv run mypy app/auth/service.py app/config.py app/shared/middleware.py app/scraping/deduplication.py app/scraping/port.py --ignore-missing-imports`
- `cd backend && uv run pytest --cov=app --cov-fail-under=60 tests/`
- Latest local result: `24 passed` for the targeted settings/auth/admin integration slice

## Entry Points
- App bootstrap: `backend/app/main.py`
- DB config: `backend/app/database.py`
- Settings: `backend/app/config.py`
- Auth routes: `backend/app/auth/router.py`
- Scraping routes: `backend/app/scraping/router.py`
- Workers: `backend/app/workers/`

## Current Assessment
- Backend is locally green for the targeted contract slice that was revalidated in this workspace.
- No known blocking backend or DB bugs remain after the latest verified pass.
- Bandit, pip-audit, pip check, backend Ruff, and the targeted backend mypy gate are green in the current branch.
- The revalidated backend slice covers auth, settings, admin, and vault contract changes used by the reference-first frontend migration.
