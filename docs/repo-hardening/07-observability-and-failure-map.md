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
- Current gap:
  - no explicit auth event logging for login success/failure, refresh, logout, or account deletion
  - cookie-auth now has CSRF enforcement, but auth event logging is still absent

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
  - `scheduler_job_completed`
  - `scheduler_job_failed`
  - `scheduler_job_missed`
- Current gap:
  - no centralized worker heartbeat/completion/failure logging standard
  - scheduler readiness is still represented by a sentinel file after startup + DB reachability; downstream dependency or per-job health can still drift after the marker is written
  - several workers are inferred by schedule registration, but they still do not emit a uniform completion/failure envelope beyond scheduler-level event hooks

## Current Blind Spots
- Browser/e2e now exists, but route-family coverage is still shallow.
- Scheduler job execution semantics are not described or monitored in one place.
- Auth success/failure, refresh, logout, and account-deletion events still do not emit structured auth lifecycle logs.

## Existing Positive Controls
- `request_completed` structured logs exist.
- Request IDs are bound and echoed in response headers.
- Security headers are centralized in middleware.
- CI already runs `pip-audit`, `bandit`, `ruff`, `mypy`, `pytest`, `npm audit`, `eslint`, frontend tests, and builds.
- CodeQL and dependency review are already enabled.

## Hardening Direction
1. Add job-level worker logging only where it improves diagnosis without flooding logs.
2. Keep scheduler process health separate from API readiness in docs, compose, and CI.
3. Add explicit auth lifecycle logging before claiming the auth surface is fully observable.
