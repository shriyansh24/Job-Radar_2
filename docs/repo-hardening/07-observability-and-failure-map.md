# Observability And Failure Map

## Purpose
Document where the major runtime flows log today, where failures surface, and where the repo is still blind.

## Source-Of-Truth Status
- Status: `DOCUMENTED_WORKING_SET`
- Scope: backend/runtime observability, failure handling, and blind spots
- Last validation basis: direct inspection of backend startup, middleware, worker scheduler, auth, and current CI/runtime docs on `2026-03-27`

## Runtime Flow Map

### API startup
- Entry: `backend/app/main.py`
- Logging:
  - `starting_up`
  - `scheduler_started`
  - `scheduler_stopped`
  - `shutting_down`
- Failure behavior:
  - `validate_runtime_settings(settings)` fails fast before the app fully serves requests
- Current gap:
  - scheduler startup is logged, but individual scheduled job registration and job execution outcomes are not

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
- Signals:
  - explicit token creation and cookie issuance
  - token version rotation on password change
- Current gap:
  - no explicit auth event logging for login success/failure, refresh, logout, or account deletion
  - cookie-based auth is used with `withCredentials` frontend calls, but there is no dedicated CSRF token flow today

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
  - `backend/app/workers/scheduler.py`
  - worker modules referenced there
- Signals:
  - scheduler start/stop logs at app lifecycle level
- Current gap:
  - no centralized worker heartbeat/completion/failure logging standard
  - scheduler remains coupled to the API process
  - several workers are inferred by schedule registration, but their execution success/failure is not surfaced here

## Current Blind Spots
- No committed browser/e2e signal even though browser QA is operationally important.
- No dedicated CSRF protection flow for cookie-authenticated state-changing requests.
- No explicit trusted-host boundary in the FastAPI middleware stack.
- No workflow that proves clean Alembic replay on every migration-affecting change.
- Scheduler job execution semantics are not described or monitored in one place.

## Existing Positive Controls
- `request_completed` structured logs exist.
- Request IDs are bound and echoed in response headers.
- Security headers are centralized in middleware.
- CI already runs `pip-audit`, `bandit`, `ruff`, `mypy`, `pytest`, `npm audit`, `eslint`, frontend tests, and builds.
- CodeQL and dependency review are already enabled.

## Hardening Direction
1. Add migration replay automation in GitHub Actions.
2. Add docs/path validation in GitHub Actions.
3. Treat CSRF and trusted-host posture as explicit hardening decisions, not implied protections.
4. Add job-level worker logging only where it improves diagnosis without flooding logs.
