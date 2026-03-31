# Open Items - JobRadar V2

## Blocking Bugs
- None verified in the current `2026-03-27` cleanup pass.

## Fixed Structural Gaps (2026-03-27)
- Reference-first frontend migration shipped across all routed pages.
- Shared shell, navigation, tokens, and page grammar now follow the reference-first command-center system.
- `SearchExpansion`, `Resume Studio`, `Compensation`, `Settings`, `Admin`, and `Targets` now align to the live backend contracts used by the app.
- Vault update integration coverage was added and passes in the targeted backend suite.
- Local Postgres schema was upgraded to Alembic `head` so the settings/integration surfaces match the current app.

## Repo-Local Closure
- The reference-first frontend, queue-backed runtime, recovered auto-apply execution path, persisted operator review diagnostics, resume preview/export flow, interview prep bundles, analytics patterns, and hybrid search path are all live and validated in repo-local scope.
- Branch-era variants that were not promoted are archived as historical alternatives rather than left as active live-scope gaps.

## Non-Blocking Residuals
- No blocking residual is currently tied to the frontend sweep; additional browser captures are incremental QA rather than a missing validation gate.
- Migration replay now has a dedicated GitHub workflow and a canonical migration-ops runbook, and targeted downgrade coverage now exists for the base `002` lineage, the ATS-identity migration slice, and the focused `005_create_p2_tables` regression suite.
- Scheduler isolation is now queue-backed through ARQ, and queue telemetry now includes depth, oldest-job age, alert state, truthful `retry_exhausted` final-failure logs, and request/job correlation on queue-triggered operator paths.
- The latest coverage-bearing backend validation run keeps every `app/` module at or above `50%` coverage and brings overall backend coverage to `71.24%`; the latest full-suite rerun now sits at `1094 passed, 1 skipped`.
- Auth lifecycle logging now carries request correlation and normalized reason codes through the main app log stream; dedicated audit routing is deployment-specific follow-through rather than a missing repo-local feature.
- Target-batch scraping now applies conditional requests, enforces `robots.txt` policy on non-ATS targets, falls back cleanly when pagination times out, and has deterministic parser fixtures for selector-based, JSON-LD, embedded-state, and JS-shell career pages.
- Google OAuth credentials are now split from general JWT signing through `JR_CREDENTIAL_ENCRYPTION_KEY` and `JR_JWT_SIGNING_KEY`, Gmail sync persists partial-message failure state instead of reporting false health, and targets with scrape history can no longer be destructively deleted from the operator UI.

## External Or Non-Goal Follow-Through
- Provider-backed ATS submission flows, destructive admin operations, and seeded-data-heavy PDF fidelity remain environment-specific validation concerns rather than missing repo-local implementation.
- Further parser tuning for difficult JS-heavy career pages remains an ongoing source-specific quality-improvement area, not a missing base execution feature. The remaining work is render/anti-bot recovery on specific sites rather than absent conditional requests, robots policy, target-batch persistence, or baseline adaptive-parser support for structured/hydrated job data.
- Long-window queue alert routing, dashboards, and dedicated auth audit sinks depend on deployment/log-routing infrastructure outside this repository.
- Gmail-first integration is now live in repo scope. Remaining Google follow-through is explicitly out of current live scope: Calendar integration, Drive integration, and any `googleworkspace/cli`/`gws`-based workflow.

## Historical Planning Material
- Future design notes live in `docs/research/`.
- Feature spec reference is preserved in Claude memory.
