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
  contracts/      grouped contract assertions by responsibility
    models/       SQLAlchemy and schema-model contract coverage
    providers/    ATS/provider adapter contract coverage
  edge_cases/     route-owned API edge cases and unusual input-path coverage
  fixtures/       shared test fixtures and factories
  infra/          config, database bootstrap, and operational CLI behavior
  integration/    API and cross-module integration coverage
    analytics/    analytics API and operator pattern-surface coverage
    auto_apply/   live operator endpoints for profiles, runs, pause, and single-apply flows
    enrichment/   enrichment pipeline integration behavior
    resume/       resume API integration coverage for upload, template, preview, and export
    scraping/     scraping orchestration integration behavior
  migrations/     Alembic and schema replay checks
  security/       auth, rate limiting, and security-focused behavior
  unit/           role-based unit suites with no flat subsystem tests at the root
    admin/        admin service behavior
    analytics/    analytics service and pattern-detector behavior
    auto_apply/   ATS detection, adapters, form extraction, and safety behavior
    auth/         auth service behavior
    dedup/        normalization-aware dedup and feedback behavior
    email/        email parsing behavior
    intelligence/ embeddings, ML, model routing, GPU, and RAG behavior
    interview/    interview question/prep/evaluation service behavior
    jobs/         job model, lifecycle, and service behavior
    networking/   networking service behavior
    notifications/ notification service behavior
    pipeline/     pipeline service behavior
    profile/      profile service behavior
    resume/       archetypes, parser, validator, renderer, upload-service, and cover-letter prep behavior
    salary/       salary intelligence behavior
    scraping/     scraper internals that are still grouped under one lane
    search/       hybrid ranking, freshness, and normalization helpers
    settings/     settings service behavior
    shared/       shared events and pagination helpers
  workers/        background execution and scheduler behavior
    auto_apply/   auto-apply worker process behavior
```

## Notes
- `unit/` no longer has flat subsystem suites at the root; `__init__.py` is the only file left there.
- `edge_cases/` should be split by route or subsystem, not collected into one umbrella suite.
- `integration/` should prefer subsystem folders once a domain owns more than one suite or has a service-specific name.
- `migrations/` is the canonical home for schema replay safety checks.
- `workers/` should cover lifecycle and retry semantics, not just helper functions.
- Scheduler and worker runtime entrypoint coverage belongs under `workers/` when it protects the dedicated process topology rather than pure selection logic.
- `contracts/` is now split between provider adapters and model/schema assertions.
- `infra/` is the home for runtime/bootstrap/CLI checks; `database` bootstrap fits there rather than generic `unit/`.
- `unit/scraping/` is still the broadest remaining subsystem lane; if that subtree grows further, split it by browser/fetcher/model/registry responsibility rather than adding new flat suites.
