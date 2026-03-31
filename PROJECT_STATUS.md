# JobRadar V2 - Project Status

> Last updated: 2026-03-31
> Canonical live state lives in `docs/current-state/00-index.md`.

## Snapshot
- Canonical active branch: `main`
- Current implementation branch for the forward-program follow-through: `codex/forward-program`
- Compose-first local runtime is the current repo baseline
- Dedicated scheduler runtime is live alongside the API process
- Queue-backed ARQ worker services are now live for `scraping`, `analysis`, and `ops`
- ATS identity persistence is now live on scraped jobs with migration coverage
- Auto Apply now exposes run/pause/refresh operator controls and has API integration coverage
- Settings integrations now support Google OAuth, and Gmail-first sync feeds the live email and pipeline surfaces
- Resume Studio now supports live template preview and PDF export against the backend API
- Analytics now includes live application-pattern surfaces on top of the overview and chart stack
- Interview prep now returns richer company/role context, and Job Board semantic mode now runs through the live hybrid-search backend path
- Pipeline now renders `rejected` and `withdrawn` stages and supports bounded drag/drop transitions
- Frontend test taxonomy lives under `frontend/src/tests/`
- Browser/e2e coverage lives under `frontend/e2e/`
- Backend pytest lanes now use explicit role-based directories under `backend/tests/`
- Representative browser captures live under `.claude/ui-captures/`

## What Is Currently True
- The reference-first frontend is the active UI direction on `main`.
- The main routed app is validated locally through frontend lint, frontend tests, frontend build, full backend pytest, and the committed browser/e2e suite against the Docker-backed stack.
- `docs/current-state/` and `docs/audit/` are the live authority layers.
- `docs/repo-hardening/` is the active normalization and traceability trail.
- `feat/p1-core-value` remains a selective recovery source rather than a merge target.
- `codex/ui-changes` is merged and closed; its adopted frontend/runtime/test/doc work now lives on `main`.

## External Or Optional Follow-Through
- Repo-wide backend mypy remains a targeted CI gate rather than a full-program strict-type contract.
- Browser/e2e coverage is committed and representative; destructive provider-backed flows and seeded-data-heavy workflows still rely on targeted or manual validation.
- Queue-backed runtime is live with queue pressure, alert state, oldest-job age, and request/job correlation on queue-triggered operator paths. Long-window alert routing and dashboards still depend on deployment infrastructure outside the repo.
- Gmail sync is now both operator-triggered from Settings and scheduler-triggered on the `ops` worker lane; broader Google Workspace surfaces such as Calendar, Drive, and `googleworkspace/cli` remain out of live scope.
- Migration replay, targeted rollback coverage, and the migration-ops runbook are live; full production restore strategy remains an operator concern outside the codebase.

## Read Order
1. `docs/current-state/00-index.md`
2. `docs/audit/00-index.md`
3. `docs/repo-hardening/00-index.md`
4. `README.md`
5. `CLAUDE.md`

## Where Each Question Goes
- "What is live?" -> `docs/current-state/`
- "What was broken or fixed?" -> `docs/audit/`
- "What is still being normalized or traced?" -> `docs/repo-hardening/`
- "What is exploratory?" -> `docs/research/`

## Current Hardening Posture
- Runtime/doc truth is materially reconciled around the compose-first baseline.
- Current docs now distinguish the live queue-backed runtime from deployment-only follow-through instead of treating ARQ as a future-only target.
- GitHub protections now include `Repository Validation`, `Docs Validation`, `Migration Safety`, `Dependency Review`, `CodeQL`, and `Frontend E2E Smoke / frontend-e2e-smoke`.
- Remaining branch-era `feat/p1-core-value` variants are now treated as explicit adopt-or-archive decisions rather than open-ended live-scope ambiguity.

## Intentional Non-Goals In Live Scope
- Branch-era `feat/p1-core-value` variants that were not promoted are now historical/archive material, not active committed work.
- Provider-backed ATS submission flows, destructive admin actions, and seeded-data-heavy PDF fidelity remain environment-specific validation concerns rather than missing repo-local implementation.
