# Deployment Ops Runbook

## Purpose
This runbook is the operator-facing entry point for the repo-owned runtime history and recovery surfaces.

Use it for:
- reading queue pressure and queue alert history
- checking auth audit history
- verifying alert routing and queue telemetry after deploys
- restoring the stack after a schema or runtime incident

Do not use this file as the live product-state source of truth. Live behavior still lives in:
- `docs/current-state/05-ops-and-ci.md`
- `docs/current-state/06-open-items.md`

## Source-Of-Truth Status
- Status: `DOCUMENTED_WORKING_SET`
- Scope: runtime history, alert routing, and restore guidance for the current repo-owned observability slice
- Last validation basis: direct inspection of the admin/runtime stack, queue telemetry storage, auth audit sink support, and current-state docs on `2026-03-31`

## What The Runtime Now Exposes

### Queue history
- The scheduler records queue telemetry samples into Redis-backed history.
- The Admin runtime summary reads those samples back so operators can inspect recent queue pressure and oldest-job age without leaving the app.
- Queue alert transitions are stored separately so alert changes are visible as events, not just as the latest status.

### Auth history
- Auth lifecycle events can be written to a Redis-backed audit stream when configured.
- The Admin runtime summary reads recent auth audit events back from that stream.
- The sink is best-effort and should not be treated as the only retention layer for a production deployment.

### Queue alert routing
- Queue alert transitions can be routed to an optional webhook URL when configured.
- The webhook is a deployment-owned destination; the repo only emits the alert event and performs a best-effort POST.

## Operating Procedure

### 1. Validate the runtime is healthy
- Confirm the API, scheduler, and worker lanes are up.
- Open Admin and verify:
  - Redis connected
  - queue pressure state
  - queue alert state
  - recent queue telemetry samples
  - recent queue alert transitions
  - recent auth audit events

### 2. Inspect queue behavior
- If queue pressure is elevated or saturated, compare the latest queue snapshot to the recent telemetry samples.
- Look for a transition from `clear` to `watch`, `backlog`, or `stalled`.
- If there is no history, confirm Redis connectivity and the queue telemetry stream settings.

### 3. Inspect auth/audit behavior
- If auth failures or admin account actions are being investigated, read the recent auth audit events from Admin first.
- Confirm the configured stream key matches the deployment environment.
- If the stream is disabled, rely on the structured log stream and enable the sink only when a deployment wants durable auth history.

### 4. Handle queue alerts
- Queue alerts are repo-owned history events plus optional deployment webhook routing.
- If the webhook is configured, treat webhook failures as best-effort routing failures, not runtime corruption.
- If a deployment needs durable long-window alerting, route the Redis stream into the external monitoring stack.

### 5. Restore after incident
- Replay migrations from a clean database before validating the runtime.
- Bring up Postgres and Redis first.
- Start the scheduler and workers after DB replay succeeds.
- Confirm the Admin runtime summary and recent history views repopulate after the scheduler records a fresh sample.

## Validation Checklist
- `python scripts/check_docs_truth.py`
- `docker compose -f docker-compose.yml config`
- `docker compose -f docker-compose.yml -f docker-compose.dev.yml config`
- backend runtime and migration tests
- frontend Admin page smoke against the live runtime

## Known Limits
- Long-window monitoring and dashboarding are still deployment-owned.
- Branch protection is still configured outside the repo.
- The queue and auth histories are Redis-backed and therefore not a substitute for a durable monitoring warehouse if the deployment needs one.
