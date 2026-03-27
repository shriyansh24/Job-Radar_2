# Final Gap Report

## Purpose
Record the major unresolved risks and deferred work that remain after the current hardening batches so the repo does not over-claim cleanliness.

## Source-Of-Truth Status
- Status: `WORKING_GAP_REPORT`
- Scope: unresolved repo-hardening, runtime, security, testing, and selective feature-recovery gaps
- Last validation basis: evidence ledger, runtime truth matrix, traceability matrix, and local validation on `2026-03-27`

## Still Unresolved

### 1. Selective P1 feature recovery is not done
- Status: `PARTIAL_PROGRESS`
- Evidence:
  - `docs/repo-hardening/04-branch-disposition.md`
  - `docs/repo-hardening/05-implementation-traceability-matrix.md`
- Why it matters:
  - the backend auto-apply execution slice is live, interview/hybrid-search/normalization/freshness plus the current tailoring/rendering family are partially recovered, ATS identity persistence now exists on the live branch, and the digest worker plus initial pipeline ergonomics are no longer branch-only; `feat/p1-core-value` still contains deeper resume/export/operator and worker/search follow-through that the current branch does not ship.
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
  - the compose-first baseline is now documented, the repo now runs through the live ARQ queue topology, scheduler and worker health is probeable through runtime healthchecks, the scheduler heartbeat lives in Redis, and retry semantics now reflect real ARQ backoff behavior.
- Remaining risk:
  - engineers can still under-test queue behavior if they treat runtime health as full proof of sustained throughput, queue-depth pressure, and end-to-end request correlation

### 3. Test taxonomy is only partially normalized
- Status: `PARTIAL`
- Evidence:
  - `docs/repo-hardening/06-test-taxonomy.md`
  - `frontend/src/tests/README.md`
  - `backend/tests/README.md`
- Why it matters:
  - the first filesystem move is complete, and the current interview/search/dedup slices are now bucketed by subsystem, but several backend `unit/` and frontend umbrella suites still need second-pass splitting by behavior.
- Remaining risk:
  - role-based discoverability is improved, not complete

### 4. Browser/e2e coverage is committed, but still shallow
- Status: `PARTIAL_PROGRESS`
- Evidence:
  - `frontend/playwright.config.ts`
  - `frontend/e2e/README.md`
  - `docs/current-state/05-ops-and-ci.md`
  - `.claude/ui-captures/`
- Why it matters:
  - a committed low-noise browser lane now exists, including auth/shell smoke, shell navigation, responsive shell behavior, route-family outcomes for dashboard/jobs/pipeline/settings/targets, prepare/intelligence/outcomes and operations/admin/data slices, recovered interview/search flow coverage, profile/settings/auth roundtrips, and representative 8-mode route-theme checks, but it still covers only part of the routed app.
- Remaining risk:
  - regressions deeper in route families, richer page workflows, and cross-route state transitions can still slip past the committed suite

### 5. Auth lifecycle logging is explicit, but still not a full audit stream
- Status: `PARTIAL_PROGRESS`
- Evidence:
  - `backend/app/auth/service.py`
  - `backend/app/auth/router.py`
  - `backend/tests/integration/test_auth_api.py`
  - `backend/tests/unit/test_auth_service.py`
  - `docs/repo-hardening/07-observability-and-failure-map.md`
- Why it matters:
  - login/refresh/logout/password-change/account-delete/session-clear events now emit structured logs without token or credential payloads and inherit request correlation, but they still share the main app log stream instead of a dedicated audit sink.
- Remaining risk:
  - auth diagnosis is materially better, but not yet at the level of a distinct audit trail

### 6. Dedicated scheduler runtime exists, but queue telemetry and worker validation are still incomplete
- Status: `PARTIAL_PROGRESS`
- Evidence:
  - `docs/repo-hardening/03-runtime-truth-matrix.md`
  - `docs/repo-hardening/07-observability-and-failure-map.md`
- Why it matters:
  - the scheduler now has its own runtime entrypoint, writes a Redis-backed heartbeat key, schedules `daily_digest`, and the live topology is scheduler -> ARQ queues (`scraping`, `analysis`, `ops`) -> queue-specific worker services with ARQ health surfaces.
- Remaining risk:
  - background execution ownership is explicit, retry semantics are now honest, and queue telemetry is richer, but alerting, queue-pressure monitoring, request/job correlation, and richer lane validation are still only partially validated end to end

### 7. Migration replay has a gate now, but rollback/backfill guidance is still thin
- Status: `PARTIAL`
- Evidence:
  - `.github/workflows/migration-safety.yml`
  - `docs/repo-hardening/03-runtime-truth-matrix.md`
  - `docs/repo-hardening/10-migration-ops.md`
- Why it matters:
  - replay to `head` is now checked and there is now a canonical migration-ops runbook, but not every migration includes strong rollback or data-backfill guidance in-file.
- Remaining risk:
  - operational confidence is improved for clean upgrades, not for all recovery scenarios

### 8. Observability is mapped, not comprehensively normalized
- Status: `PARTIAL`
- Evidence:
  - `docs/repo-hardening/07-observability-and-failure-map.md`
- Why it matters:
  - major blind spots are now documented, but structured logging and lifecycle event consistency still vary across modules.
- Remaining risk:
  - failure diagnosis is clearer in queue/auth paths than before, but queue-depth alerting and request-to-job correlation are still not uniformly first-class

## What Would Count As The Next Credible Finish Line
1. Continue selective P1 recovery beyond the recovered backend auto-apply, ATS identity, interview prep, hybrid-search, freshness, normalization, digest-worker, and pipeline-state slices.
2. Complete the second test-taxonomy pass for the broad `unit/` and umbrella page/component suites.
3. Extend queue validation to cover alerting, back-pressure, request-to-job correlation, and richer worker-lane behavior beyond the current queue-depth, retry, and health probes.
4. Expand the committed browser/e2e lane by route family and deeper workflow outcomes.
5. Add a dedicated audit-stream strategy for the auth lifecycle logs.
6. Strengthen in-file migration docs with rollback/backfill expectations where the risk is non-trivial.
