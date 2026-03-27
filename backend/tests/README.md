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
  contracts/      schema and adapter contract assertions
  edge_cases/     route-owned API edge cases and unusual input-path coverage
  fixtures/       shared test fixtures and factories
  infra/          config, database bootstrap, and operational CLI behavior
  integration/    API and cross-module integration coverage
    enrichment/   enrichment pipeline integration behavior
    scraping/     scraping orchestration integration behavior
  migrations/     Alembic and schema replay checks
  security/       auth, rate limiting, and security-focused behavior
  unit/           remaining subsystem unit suites still grouped by service/module
    auto_apply/   ATS detection, adapters, form extraction, and safety behavior
    dedup/        normalization-aware dedup behavior
    interview/    interview question/prep/evaluation service behavior
    search/       hybrid ranking, freshness, and normalization helpers
  workers/        background execution and scheduler behavior
    auto_apply/   auto-apply worker process behavior
```

## Notes
- `unit/` is still being normalized; new tests should prefer the more specific role-based directories when possible.
- `edge_cases/` should be split by route or subsystem, not collected into one umbrella suite.
- `integration/` should prefer subsystem folders once a domain owns more than one suite or has a service-specific name.
- `migrations/` is the canonical home for schema replay safety checks.
- `workers/` should cover lifecycle and retry semantics, not just helper functions.
- Scheduler and worker runtime entrypoint coverage belongs under `workers/` when it protects the dedicated process topology rather than pure selection logic.
- Contract suites are now split between provider adapters and model/schema assertions.
- `infra/` is the home for runtime/bootstrap/CLI checks; `database` bootstrap fits there rather than generic `unit/`.
