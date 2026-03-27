# Backend Test Taxonomy

## Purpose
Document the backend test layout so runtime, migration, contract, worker, and service coverage can be extended without turning `backend/tests/` into another mixed bucket.

## Source-Of-Truth Status
- Status: `LIVE_LAYOUT`
- Scope: backend test taxonomy under `backend/tests/`
- Last validation basis: taxonomy move plus targeted pytest runs on `2026-03-27`

## Layout
```text
backend/tests/
  contracts/   schema and adapter contract assertions
  edge_cases/  unusual cross-cutting API behaviors still awaiting split
  fixtures/    shared test fixtures and factories
  infra/       config, database bootstrap, and operational CLI behavior
  integration/ API and cross-module integration coverage
  migrations/  Alembic and schema replay checks
  security/    auth, rate limiting, and security-focused behavior
  unit/        remaining subsystem unit suites still grouped by service/module
  workers/     background execution and scheduler behavior
```

## Notes
- `unit/` is still being normalized; new tests should prefer the more specific role-based directories when possible.
- `migrations/` is the canonical home for schema replay safety checks.
- `workers/` should cover lifecycle and retry semantics, not just helper functions.
