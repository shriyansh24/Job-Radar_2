# JobRadar V2 - Project Status

> Last updated: 2026-03-27
> Canonical live state lives in `docs/current-state/00-index.md`.

## Snapshot
- Active workspace branch: `codex/ui-changes`
- Compose-first local runtime is the current repo baseline
- Dedicated scheduler runtime is live alongside the API process
- Queue-backed ARQ worker services are now live for `scraping`, `analysis`, and `ops`
- Interview prep now returns richer company/role context, and Job Board semantic mode now runs through the live hybrid-search backend path
- Frontend test taxonomy lives under `frontend/src/tests/`
- Browser/e2e coverage lives under `frontend/e2e/`
- Backend pytest lanes now use explicit role-based directories under `backend/tests/`
- Representative browser captures live under `.claude/ui-captures/`

## What Is Currently True
- The reference-first frontend is the active UI direction on `codex/ui-changes`.
- The main routed app is validated locally through frontend lint, frontend tests, browser/e2e, frontend build, and targeted backend integration coverage.
- `docs/current-state/` and `docs/audit/` are the live authority layers.
- `docs/repo-hardening/` is the active normalization and traceability trail.
- `feat/p1-core-value` remains a selective recovery source rather than a merge target.

## What Is Not Finished
- Selective P1 recovery is still in progress and must stay evidence-based.
- Repo-wide backend mypy is still narrower than a full-program strict pass.
- Browser/e2e coverage now protects auth/shell smoke, responsive shell behavior, route-family outcomes for `dashboard/jobs/pipeline/settings/targets`, and representative 8-mode route checks, but it is still shallower than full route-family coverage.
- Queue-backed runtime is live, but retry/back-pressure policy validation and worker-lane coverage still need hardening.
- Migration rollback/backfill guidance still needs hardening.

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
- Current docs now distinguish the live queue-backed runtime from the remaining migration/coverage hardening work instead of treating ARQ as a future-only target.
- GitHub protections now include repo validation, docs validation, migration safety, dependency review, CodeQL, and a dedicated frontend browser smoke lane.
- Test taxonomy is improved but still not fully normalized.

## Deferred Work
- Resume PDF generation and related template flows
- Saved-search alerts UI and scheduler UX
- Additional parser tuning for difficult JS-heavy career pages
- Broader route-family browser coverage beyond the current smoke/responsive/theme/dashboard-jobs-pipeline/settings-targets baseline
- Remaining second-pass frontend decomposition and copy cleanup on larger surfaces
