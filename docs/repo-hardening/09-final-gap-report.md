# Final Gap Report

## Purpose
Record the major unresolved risks and deferred work that remain after the current hardening batches so the repo does not over-claim cleanliness.

## Source-Of-Truth Status
- Status: `WORKING_GAP_REPORT`
- Scope: unresolved repo-hardening, runtime, security, testing, and selective feature-recovery gaps
- Last validation basis: evidence ledger, runtime truth matrix, traceability matrix, and local validation on `2026-03-27`

## Repo-Internal Closure State

### 1. Live repo scope is aligned
- Status: `CLOSED_FOR_REPO_SCOPE`
- Evidence:
  - `docs/repo-hardening/04-branch-disposition.md`
  - `docs/repo-hardening/05-implementation-traceability-matrix.md`
  - `docs/research/00-index.md`
- Why it matters:
  - the previously ambiguous `feat/p1-core-value` recovery story is now explicit: adopted slices are live on `codex/ui-changes`, and non-promoted branch-era variants are archived as historical alternatives rather than left as active live-scope ambiguity.

### 2. Runtime truth is aligned for repo-local operation
- Status: `CLOSED_FOR_REPO_SCOPE`
- Evidence:
  - `docs/repo-hardening/03-runtime-truth-matrix.md`
  - `README.md`
  - `CLAUDE.md`
  - `.env.example`
- Why it matters:
  - compose-first runtime, ARQ worker topology, health probes, queue pressure/alert semantics, and request/job correlation on queue-triggered operator paths are now reflected consistently in code and docs.

### 3. Test taxonomy and browser coverage are aligned to committed scope
- Status: `CLOSED_FOR_REPO_SCOPE`
- Evidence:
  - `docs/repo-hardening/06-test-taxonomy.md`
  - `frontend/src/tests/README.md`
  - `backend/tests/README.md`
  - `frontend/playwright.config.ts`
  - `frontend/e2e/README.md`
  - `docs/current-state/05-ops-and-ci.md`
- Why it matters:
  - the committed suite now has explicit route-family ownership, a deterministic resume preview/export flow, route-family 8-mode coverage across the routed app families, and filesystem breadcrumbs that match the actual test tree.

### 4. Migration operations are documented for repo-local recovery
- Status: `CLOSED_FOR_REPO_SCOPE`
- Evidence:
  - `.github/workflows/migration-safety.yml`
  - `docs/repo-hardening/10-migration-ops.md`
  - `backend/tests/migrations/test_alembic_revisions.py`
  - `backend/tests/migrations/test_job_ats_identity_migration.py`
  - `backend/tests/migrations/test_scrape_target_identity_migrations.py`
- Why it matters:
  - clean replay, targeted downgrade checks, and operator guidance now exist together rather than as a mix of implicit local knowledge and workflow folklore.

## External Or Deployment Follow-Through
- GitHub branch-protection enforcement for the documented required checks is configured outside the repo and is not proven by files alone.
- A dedicated auth audit sink, alert routing, and long-window queue monitoring depend on deployment and log-routing decisions in addition to the repo-local logging that now exists.
- Deployment-level queue alerting and dashboarding remain external even though the repo now emits healthier runtime signals and CI validates the queue-backed topology.
