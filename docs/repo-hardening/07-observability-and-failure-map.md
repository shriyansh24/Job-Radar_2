# Observability And Failure Map

## Purpose
Document where the major runtime flows log today, where failures surface, and where the repo is still blind.

## Source-Of-Truth Status
- Status: `DOCUMENTED_WORKING_SET`
- Scope: backend/runtime observability, failure handling, and blind spots
- Last validation basis: direct inspection of backend startup, middleware, worker scheduler, auth, frontend API client behavior, and current CI/runtime docs on `2026-03-27`

## Runtime Flow Map

### API startup
- Entry: `backend/app/main.py`
- Logging:
  - `starting_up`
  - `shutting_down`
- Failure behavior:
  - `validate_runtime_settings(settings)` fails fast before the app fully serves requests
- Current gap:
  - API startup now logs only API lifecycle; migration start/completion still depends on Alembic and CI surfaces rather than first-class app-lifecycle events

### HTTP request lifecycle
- Files:
  - `backend/app/shared/middleware.py`
  - `backend/app/shared/logging.py`
- Signals:
  - request ID binding
  - response time header
  - `request_completed` structured log with method, path, route name, route path, authenticated user ID when available, status, and duration
  - security headers on every response
  - in-memory rate limiting and `429` response path
- Current gap:
  - login rate-limit JSON parsing errors are downgraded to debug logs without broader abuse context

### Auth lifecycle
- Files:
  - `backend/app/auth/service.py`
  - `backend/app/auth/router.py`
  - `backend/app/shared/middleware.py`
  - `frontend/src/api/client.ts`
- Signals:
  - explicit token creation and cookie issuance
  - readable CSRF cookie issuance and deletion
  - token version rotation on password change
  - structured lifecycle events for:
    - `auth_register_succeeded`
    - `auth_register_failed`
    - `auth_login_succeeded`
    - `auth_login_failed`
    - `auth_refresh_succeeded`
    - `auth_refresh_failed`
    - `auth_logout_succeeded`
    - `auth_account_deleted`
    - `auth_password_changed`
    - `auth_password_change_failed`
    - `auth_session_cleared`
- Current gap:
  - auth logs now inherit request IDs from middleware-bound contextvars and carry normalized `reason` codes, but there is still no separate security audit sink beyond the app log stream

### Migration lifecycle
- Files:
  - `backend/app/migrations/env.py`
  - `backend/tests/migrations/test_alembic_revisions.py`
  - `backend/tests/migrations/test_scrape_target_identity_migrations.py`
- Signals:
  - Alembic drives migrations from the configured DB URL
  - CI now records `alembic heads`, `alembic current`, and verbose `alembic history` when the migration safety lane runs
  - migration tests now cover both downgrade behavior and the ATS identity lineage through `scrape_targets.ats_vendor`, `scrape_targets.ats_board_token`, `idx_targets_ats`, and `jobs.source_target_id`
- Current gap:
  - migration start/completion is not logged by app startup
  - replay safety is stronger in CI now, but migration observability still depends on workflow artifacts rather than first-class runtime logs

### Scheduler and worker lifecycle
- Files:
  - `backend/app/runtime/scheduler.py`
  - `backend/app/workers/scheduler.py`
  - worker modules referenced there
- Signals:
  - `scheduler_starting`
  - `scheduler_configured`
  - `scheduler_dependencies_ready`
  - `scheduler_started`
  - `scheduler_ready`
  - `scheduler_shutdown_requested`
  - `scheduler_stopped`
  - `scheduler_job_enqueued`
  - `scheduler_job_dispatched`
  - `scheduler_job_failed`
  - `scheduler_job_missed`
  - `queue_pool_ready`
  - `queue_pool_stopped`
  - `arq_worker_booting`
  - `arq_worker_started`
  - `arq_worker_stopped`
  - `arq_worker_job_starting`
  - `arq_worker_job_finished`
  - `queue_job_started`
  - `queue_job_failed`
  - `queue_job_completed`
  - Redis-backed scheduler heartbeat state
  - ARQ worker `health_check_key` state
  - worker runtime metrics hash with queue depth, queue pressure, oldest-job age, queue alert, retry-scheduled totals, retry-exhausted totals, and completed/failed job counters
  - queue depth before and after enqueue
  - retry metadata including retryability, retry remaining, and scheduled backoff
  - truthful `retry_exhausted` logging for non-retryable or final failures
- Current gap:
  - scheduler and worker readiness now come from live runtime healthcheck probes instead of sentinel files, but there is still no sustained queue-depth alerting or long-window throughput view
  - queue lifecycle is now explicit and includes queue depth, queue alert state, worker counters, and retry metadata, but deployment-level dashboards and alert routing still live outside the repo

## Current Blind Spots
- Real external ATS/browser submission flows still depend on manual validation rather than deterministic in-repo browser tests.
- Scheduler job execution semantics are now explicit and health-backed, but queue throughput trend monitoring and alert routing are still deployment concerns.
- Auth logs are now explicit and request-correlated, but they are not separated into a dedicated audit sink.

## Existing Positive Controls
- `request_completed` structured logs exist.
- Request IDs are bound and echoed in response headers.
- Auth lifecycle events now cover register/login/refresh/logout/password/account-delete/session-clear paths, normalize common failure reasons, and keep sensitive payloads out of the structured log stream.
- Security headers are centralized in middleware.
- Queue enqueue and worker lifecycle logs now carry queue ownership, queue depth, retry metadata, scheduled retry backoff, truthful `retry_exhausted` outcomes, Redis heartbeat state, ARQ worker health surfaces, and worker runtime metrics hashes.
- CI already runs the reviewed backend dependency-audit policy, `bandit`, `ruff`, `mypy`, `pytest`, `npm audit`, `eslint`, frontend tests, and builds.
- CodeQL and dependency review are already enabled.

## Hardening Direction
1. Add job-level worker logging only where it improves diagnosis without flooding logs.
2. Keep scheduler process health separate from API readiness in docs, compose, and CI.
3. Keep normalized reason-code and request-correlation discipline consistent across future auth paths and queue-dispatched jobs, then add audit-sink discipline before claiming the auth surface is fully observable.
