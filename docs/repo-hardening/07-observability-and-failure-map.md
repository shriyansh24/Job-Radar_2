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
  - API startup now logs only API lifecycle; request-scoped failures still do not identify authenticated user context

### HTTP request lifecycle
- Files:
  - `backend/app/shared/middleware.py`
  - `backend/app/shared/logging.py`
- Signals:
  - request ID binding
  - response time header
  - `request_completed` structured log with method, path, status, duration
  - security headers on every response
  - in-memory rate limiting and `429` response path
- Current gap:
  - request logs do not include authenticated user identifiers or router/module ownership
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
- Signals:
  - Alembic drives migrations from the configured DB URL
- Current gap:
  - migration start/completion is not logged by app startup
  - replay safety is only partially covered by unit tests and manual/operator discipline

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
  - queue depth before and after enqueue
  - retry metadata including retryability and retry remaining
- Current gap:
  - scheduler and worker readiness are still represented by sentinel files after startup probes; downstream dependency or per-job health can still drift after the markers are written
  - queue lifecycle is now explicit and includes queue depth plus retry metadata, but there is still no alerting or sustained throughput view

## Current Blind Spots
- Browser/e2e now exists, but route-family coverage is still shallow.
- Scheduler job execution semantics are now explicit, but queue throughput and retry pressure are not yet monitored in one place.
- Auth logs are now explicit and request-correlated, but they are not separated into a dedicated audit sink.

## Existing Positive Controls
- `request_completed` structured logs exist.
- Request IDs are bound and echoed in response headers.
- Auth lifecycle events now normalize common failure reasons and keep sensitive payloads out of the structured log stream.
- Security headers are centralized in middleware.
- Queue enqueue and worker lifecycle logs now carry queue ownership, queue depth, and retry metadata.
- CI already runs `pip-audit`, `bandit`, `ruff`, `mypy`, `pytest`, `npm audit`, `eslint`, frontend tests, and builds.
- CodeQL and dependency review are already enabled.

## Hardening Direction
1. Add job-level worker logging only where it improves diagnosis without flooding logs.
2. Keep scheduler process health separate from API readiness in docs, compose, and CI.
3. Keep normalized reason-code and request-correlation discipline consistent across future auth paths, then add audit-sink discipline before claiming the auth surface is fully observable.
