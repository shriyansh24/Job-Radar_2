# Repository Hardening Execution Plan

## Purpose
Define the execution order, dependencies, and rollback-safe approach for the repository hardening program before structural edits.

## Source-Of-Truth Status
- Status: `DOCUMENTED`
- Scope: plan only
- Last validation basis: `01-evidence-ledger.md` on `2026-03-27`

## Workstreams

### Workstream A — Truth Reconciliation
Scope:
- reconcile runtime/env/docker truth
- reconcile current-state vs system-inventory vs top-level docs
- reconcile validation counts and browser artifact locations

Primary files:
- `README.md`
- `CLAUDE.md`
- `AGENTS.md`
- `.env.example`
- `docker-compose.yml`
- `docker-compose.dev.yml`
- `docs/current-state/*`
- `docs/system-inventory/*`

Dependencies:
- evidence ledger complete

Risks:
- picking one local runtime model without documenting the alternate manual-local flow
- breaking current-state authority by overfitting to stale system-inventory docs

### Workstream B — Branch And Phase Traceability
Scope:
- reconstruct P0/P1/P2 intended scope
- audit `feat/p1-core-value` commit-by-commit
- disposition retained branches into keep / port / defer / reject / archive

Primary evidence targets:
- PR #12
- PR #13
- PR #17
- `main`
- `feat/p1-core-value`
- `codex/ui-changes`
- `ui-overhaul-design`

Dependencies:
- none beyond Phase 0 evidence

Risks:
- treating phase PR text as truth without verifying the code tree
- losing track of cross-layer follow-through between backend, migrations, tests, and frontend

### Workstream C — Test Taxonomy And Coverage Hardening
Scope:
- redesign test layout and naming by protection goal
- identify missing e2e / migration / worker / infra categories
- improve CI readability and check granularity

Primary files:
- `backend/tests/**`
- `frontend/src/tests/**`
- `frontend/e2e/**`
- `frontend/vitest.config.ts`
- `.github/workflows/ci.yml`
- `.claude/agents/14-test.md`

Dependencies:
- truth reconciliation so docs and commands point to the correct paths

Risks:
- moving tests without preserving discoverability or import assumptions
- over-normalizing before deciding the final taxonomy

### Workstream D — Runtime / Observability / Safety Hardening
Scope:
- tighten startup and configuration truth
- review logging/failure handling for backend and workers
- inspect health checks, scheduler coupling, and migration safety

Primary files:
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/shared/logging.py`
- `backend/app/shared/middleware.py`
- `backend/app/workers/*`
- migration and startup surfaces
- GitHub workflows for automated safety checks

Dependencies:
- runtime truth matrix complete
- branch/phase matrix complete enough to avoid hardening dead features

Risks:
- silent changes to local runtime behavior
- noisy automation without operational value

### Workstream E — Documentation Front Door And State Hub
Scope:
- rewrite the root README
- expand/repair the current-state hub
- publish traceability, runtime truth, branch disposition, and final gap docs

Primary files:
- `README.md`
- `docs/current-state/*`
- `docs/repo-hardening/*`
- `PROJECT_STATUS.md`
- `DECISIONS.md`
- `AGENTS.md`
- `CLAUDE.md`

Dependencies:
- at least partial completion of workstreams A through D

Risks:
- writing docs ahead of reality
- leaving stale breadcrumbs after moving tests or changing commands

## Ordering
1. Phase 0: evidence ledger and plan docs
2. Truth reconciliation on runtime/docs contradictions
3. Branch/P0-P1-P2 traceability matrix
4. Test taxonomy proposal and safe migration plan
5. Runtime/observability/CI hardening
6. README and state-hub finalization
7. Final validation, gap report, commit, push

## Files Likely To Change
- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_STATUS.md`
- `DECISIONS.md`
- `.env.example`
- `docker-compose.yml`
- `docker-compose.dev.yml`
- `docs/current-state/*`
- `docs/system-inventory/*` or their index notes if kept as historical inventory
- `.github/workflows/*`
- `.github/dependabot.yml`
- test files and directories under `backend/tests/`, `frontend/src/tests/`, and `frontend/e2e/`
- supporting docs under `.claude/` if they describe the old layout or QA flow

## Test Migration Strategy
- do not move tests until the target taxonomy is documented
- move in bounded batches by boundary:
  - backend contracts
  - backend integration
  - backend security
  - backend migration/worker/infra
  - frontend route flows
  - frontend component/api contracts
  - e2e/browser if committed
- leave redirect breadcrumbs in docs and test guidance files during the migration batch

## Docs Migration Strategy
- promote only verified truth into `docs/current-state/`
- keep bug-only claims in `docs/audit/`
- explicitly mark `docs/system-inventory/` as inventory/historical if it remains stale relative to current-state
- keep this directory as the hardening audit trail until changes are promoted

## Rollback-Safe Approach
- small, reviewable batches
- no destructive branch resets
- no silent deletion of historical docs without either:
  - removal justification in commit message and docs
  - or a redirect/index note if humans would otherwise get lost
- run validation after every structural batch

## Done-When Gates For Phase 1
- a single runtime truth can be stated without contradiction
- current-state, README, AGENTS, and CLAUDE tell the same local startup story
- stale references to the removed superpowers doc set are removed or explicitly marked historical
- backend validation counts are reconciled
- system-inventory contradictions are either updated or explicitly marked as historical inventory
