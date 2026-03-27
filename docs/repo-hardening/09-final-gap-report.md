# Final Gap Report

## Purpose
Record the major unresolved risks and deferred work that remain after the current hardening batches so the repo does not over-claim cleanliness.

## Source-Of-Truth Status
- Status: `WORKING_GAP_REPORT`
- Scope: unresolved repo-hardening, runtime, security, testing, and selective feature-recovery gaps
- Last validation basis: evidence ledger, runtime truth matrix, traceability matrix, and local validation on `2026-03-27`

## Still Unresolved

### 1. Selective P1 feature recovery is not done
- Status: `DEFERRED_FOR_DECISION`
- Evidence:
  - `docs/repo-hardening/04-branch-disposition.md`
  - `docs/repo-hardening/05-implementation-traceability-matrix.md`
- Why it matters:
  - `feat/p1-core-value` still contains concrete capability work that the current branch does not ship, especially auto-apply form extraction, ATS adapters, deeper resume tooling, and interview-prep internals.
- Remaining risk:
  - if this branch is ignored, valuable partially implemented capability may be lost
  - if it is merged blindly, stale code and architectural drift will be reintroduced

### 2. Runtime truth is better aligned, but not fully finished
- Status: `PARTIAL`
- Evidence:
  - `docs/repo-hardening/03-runtime-truth-matrix.md`
  - `README.md`
  - `CLAUDE.md`
  - `.env.example`
- Why it matters:
  - the compose-first baseline is now documented, but legacy local assumptions still exist in developer muscle memory and some older historical docs.
- Remaining risk:
  - engineers can still follow stale local patterns if they ignore the current docs

### 3. Test taxonomy is only partially normalized
- Status: `PARTIAL`
- Evidence:
  - `docs/repo-hardening/06-test-taxonomy.md`
  - `frontend/src/tests/README.md`
  - `backend/tests/README.md`
- Why it matters:
  - the first filesystem move is complete, but several backend `unit/` and frontend umbrella suites still need second-pass splitting by behavior.
- Remaining risk:
  - role-based discoverability is improved, not complete

### 4. Browser/e2e coverage is still mostly manual
- Status: `DEFERRED`
- Evidence:
  - `docs/current-state/05-ops-and-ci.md`
  - `.claude/ui-captures/`
- Why it matters:
  - route sweeps and screenshots exist, but committed low-noise browser coverage is still missing.
- Remaining risk:
  - regressions in auth boot, theme switching, and route wiring can still slip past the committed suite

### 5. CSRF and trusted-host hardening are documented gaps, not fixed gaps
- Status: `DOCUMENTED`
- Evidence:
  - `SECURITY.md`
  - `docs/current-state/06-open-items.md`
- Why it matters:
  - cookie-based auth is live, but there is still no dedicated CSRF token flow and trusted-host enforcement is not explicit.
- Remaining risk:
  - the repo is safer because the gap is explicit, not because the protection exists yet

### 6. Scheduler / API coupling remains
- Status: `DOCUMENTED`
- Evidence:
  - `docs/system-inventory/14-implementation-readiness.txt`
  - `docs/repo-hardening/07-observability-and-failure-map.md`
- Why it matters:
  - the scheduler still runs inside the API process, which complicates scaling and operational isolation.
- Remaining risk:
  - worker or scheduler faults can still share failure domains with the API process

### 7. Migration replay has a gate now, but rollback/backfill guidance is still thin
- Status: `PARTIAL`
- Evidence:
  - `.github/workflows/migration-safety.yml`
  - `docs/repo-hardening/03-runtime-truth-matrix.md`
- Why it matters:
  - replay to `head` is now checked, but not every migration includes strong rollback or data-backfill guidance.
- Remaining risk:
  - operational confidence is improved for clean upgrades, not for all recovery scenarios

### 8. Observability is mapped, not comprehensively normalized
- Status: `PARTIAL`
- Evidence:
  - `docs/repo-hardening/07-observability-and-failure-map.md`
- Why it matters:
  - major blind spots are now documented, but structured logging and lifecycle event consistency still vary across modules.
- Remaining risk:
  - failure diagnosis is clearer on paper than it is uniformly in code

## What Would Count As The Next Credible Finish Line
1. Decide which `feat/p1-core-value` capabilities are being ported versus deferred.
2. Complete the second test-taxonomy pass for the broad `unit/` and umbrella page/component suites.
3. Add the first committed low-noise browser/e2e lane.
4. Either implement or explicitly defer CSRF/trusted-host hardening in the code, not just the docs.
5. Strengthen migration docs with rollback/backfill expectations where the risk is non-trivial.
