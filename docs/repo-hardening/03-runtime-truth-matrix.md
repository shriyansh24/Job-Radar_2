# Runtime Truth Matrix

## Purpose
Crosswalk the actual runtime behavior against the docs that currently describe it.

## Source-Of-Truth Status
- Status: `DOCUMENTED`
- Scope: local/runtime/development truth
- Last validation basis: direct reads of config, compose, startup, and doc files on `2026-03-27`

| Topic | README.md | CLAUDE.md | .env.example | docker-compose.yml | docker-compose.dev.yml | Code Reality | Current Verdict |
|---|---|---|---|---|---|---|---|
| Backend port | implies `8000` | implies `8000` | n/a | `8000:8000` | backend command binds `8000` | `backend/app/main.py` serves via Uvicorn on configured host/port | `FIXED_IN_CODE`, docs broadly aligned |
| Frontend port | `5173` for host-local dev | `npm run dev` only | n/a | `3000:80` in base compose | `5173:5173` in dev overlay | host-local Vite uses `5173`; base compose serves Nginx on `3000` | `ALIGNED_WITH_EXPLICIT_DUAL_MODE` |
| Postgres host/port | `5432` compose baseline | `5432` compose baseline | `5432` localhost | `5432:5432` | inherits base compose | `backend/app/config.py` default is `5432` | `ALIGNED` |
| Postgres credentials | compose baseline | compose baseline | `jobradar` / `jobradar` | `jobradar` / `jobradar` | inherits base compose | `backend/app/config.py` default is `jobradar` / `jobradar` | `ALIGNED` |
| Redis URL/password | compose baseline with password | compose baseline with password | compose password baseline | ships a passworded Redis service | inherits base compose | `backend/app/config.py` still has a compose-friendly default; Redis is now on the scheduler/worker critical path as the ARQ queue backbone | `ALIGNED_WITH_LIVE_QUEUE_RUNTIME` |
| Redis TLS | not described | not clearly described | not described | conditional TLS if certs exist | inherits base compose | `redis_use_tls=False` by default in code | `DOCUMENTED_GAP` |
| Cookie auth model | says cookie-based auth and CSRF echo header | says cookie-based auth and CSRF echo header | n/a | n/a | n/a | `backend/app/auth/service.py` sets httpOnly access/refresh cookies plus a readable CSRF cookie; `frontend/src/api/client.ts` echoes `X-CSRF-Token` on unsafe methods | `ALIGNED` |
| Cookie security flags | local dev flags documented | local dev flags documented | n/a | n/a | n/a | `cookie_secure=False`, `SameSite=lax` by default for local-only dev; runtime validation rejects `SameSite=None` without secure cookies | `ALIGNED_WITH_LOCAL_ONLY_DEFAULTS` |
| Auth request correlation and reason codes | high-level auth wording only | high-level auth wording only | n/a | n/a | n/a | `backend/app/shared/middleware.py` binds `request_id`; auth lifecycle logs in `backend/app/auth/service.py` and `backend/app/auth/router.py` now emit normalized `reason` codes without sensitive payloads | `DOCUMENTED_IN_HARDENING_ONLY` |
| Trusted hosts | branch-protection/runtime docs now mention trusted hosts | branch-protection/runtime docs now mention trusted hosts | explicit example now present | compose and dev overlay include `backend` for containerized proxying | dev overlay includes `backend` | `backend/app/main.py` installs `TrustedHostMiddleware`; `backend/app/config.py` validates `JR_TRUSTED_HOSTS` and defaults now include `backend` | `ALIGNED` |
| Scheduler process model | explicit dedicated scheduler command | explicit dedicated scheduler command | queue-backed scheduler env documented via compose/runtime only | dedicated `scheduler` service with healthcheck plus queue-specific worker services | bind-mounted `scheduler` and worker overlay services | `backend/app/main.py` no longer owns APScheduler; `backend/app/runtime/scheduler.py` is the runtime entrypoint, withholds readiness until DB and Redis reachability are proven, writes a Redis-backed heartbeat key, schedules `daily_digest`, and enqueues scheduled work onto ARQ queues consumed by `backend/app/runtime/arq_worker.py` | `ALIGNED_WITH_LIVE_QUEUE_RUNTIME` |
| Queue telemetry | high-level queue wording only | queue topology described | n/a | queue-specific workers documented | queue-specific workers documented | `backend/app/runtime/queue.py`, `job_registry.py`, and `arq_worker.py` now log queue depth, retry metadata, queue names, stable worker-role health keys, real ARQ retry/backoff behavior, and truthful `retry_exhausted` final-failure logging | `ALIGNED_WITH_NARROW_REMAINING_GAPS` |
| Frontend API proxy | host-local Vite on `localhost:8000`; containerized Vite must override target | explicit compose-first wording | `VITE_API_PROXY_TARGET=http://localhost:8000` | base compose uses built frontend container | dev overlay sets `VITE_API_PROXY_TARGET=http://backend:8000`, publishes only `5173:5173`, and health-checks Vite on `5173` | `frontend/vite.config.ts` reads `VITE_API_PROXY_TARGET` with `http://localhost:8000` fallback | `FIXED_IN_CODE_AND_DOCS` |
| Frontend base URL | not previously called out | not previously called out | `JR_FRONTEND_BASE_URL=http://localhost:5173` | n/a | n/a | `backend/app/config.py` now uses `frontend_base_url` to build post-OAuth callback redirects from the backend Google callback route | `NEW_LIVE_RUNTIME_TRUTH` |
| Google OAuth client configuration | not previously called out | not previously called out | `JR_GOOGLE_OAUTH_CLIENT_ID`, `JR_GOOGLE_OAUTH_CLIENT_SECRET`, `JR_GOOGLE_OAUTH_REDIRECT_URI` | n/a | n/a | `backend/app/integrations/google_oauth.py` fails fast when these are unset and the Google connect flow is invoked | `NEW_LIVE_RUNTIME_TRUTH` |
| Gmail sync runtime knobs | not previously called out | not previously called out | `JR_GOOGLE_GMAIL_SYNC_QUERY`, `JR_GOOGLE_GMAIL_SYNC_MAX_MESSAGES` | n/a | n/a | `backend/app/settings/service.py`, `backend/app/email/gmail_sync.py`, and `backend/app/workers/gmail_worker.py` use these values for manual and scheduled Gmail sync execution | `NEW_LIVE_RUNTIME_TRUTH` |
| Settings integration auth model | API-key providers only implied | high-level integrations wording only | n/a | n/a | n/a | `backend/app/settings/models.py` and `backend/app/settings/schemas.py` now represent both `api_key` and `oauth` integration types; Google is OAuth-backed with sync metadata rather than an API-key provider | `NEW_LIVE_RUNTIME_TRUTH` |
| Gmail sync scheduler ownership | not described | not described | n/a | runtime implied only through code | runtime implied only through code | `backend/app/workers/scheduler.py` schedules `gmail_sync` every 30 minutes and `backend/app/runtime/job_registry.py` registers it on the `ops` queue | `NEW_LIVE_RUNTIME_TRUTH` |
| Browser QA artifact path | `.claude/ui-captures/` | `.claude/ui-captures/` | n/a | n/a | n/a | current branch stores captures there | `ALIGNED` |
| Browser e2e tree | committed `frontend/e2e/` | committed `frontend/e2e/` | n/a | n/a | n/a | Playwright config and suites now live under `frontend/e2e/` | `ALIGNED` |
| Frontend theme model | high-level light/dark wording | high-level theme wording | n/a | n/a | n/a | `useUIStore` persists theme family + mode | `DOCUMENTED_GAP` |

## Actual Local Runtime Baseline From Code
- Backend config source: `backend/app/config.py`
- API startup: `backend/app/main.py`
- Dedicated scheduler runtime: `backend/app/runtime/scheduler.py`
- Database engine/session: `backend/app/database.py`
- Frontend dev proxy: `frontend/vite.config.ts`
- Base container topology: `docker-compose.yml`
- Dev overlay topology: `docker-compose.dev.yml`

## Live Background Runtime Topology
- Scheduler remains its own runtime entrypoint.
- Scheduled jobs enqueue onto ARQ queues: `scraping`, `analysis`, and `ops`.
- Career-page scheduling now flows only through `target_batch_career_page`; the older standalone `career_page_scrape` path is no longer part of the active runtime.
- The scheduler writes a Redis-backed heartbeat key and owns the `daily_digest` schedule on the ops lane.
- Queue-specific worker services consume those queues instead of the scheduler spawning one-shot worker subprocesses directly.
- Worker health is exposed through ARQ `health_check_key` surfaces, and compose plus CI now probe those runtime healthcheck commands instead of relying on sentinel files.
- Enqueue and worker lifecycle logs now record queue depth, retry metadata, queue ownership, scheduled retry backoff, and truthful `retry_exhausted` final-failure outcomes at the dispatch and execution boundaries.
- Google OAuth callback redirects now depend on `JR_FRONTEND_BASE_URL`, and the `ops` worker lane now owns Gmail sync traffic against Google OAuth and Gmail APIs when Google is connected.
- Redis moves from a merely reserved compose dependency to the queue backbone for background execution.
- `backend/app/runtime/worker.py` remains available as the manual one-shot/debug runner.
- Migration operations guidance now has one canonical runbook at `docs/repo-hardening/10-migration-ops.md`.

## Reconciliation Direction
1. Keep base compose as the canonical runtime baseline and host-local frontend/backend as an explicit override.
2. Keep `.env.example` aligned to the compose DB and Redis baseline.
3. Keep containerized Vite dev as the checked-in overlay story and document it as an overlay, not the default runtime.
4. Keep cookie names, CSRF behavior, and local security flags in one place.
5. Keep the trusted-host list explicit in runtime docs whenever local or CI hostnames change.
6. Keep queue telemetry and auth request-correlation facts in hardening docs until they are promoted into a stable front-door summary.
7. Treat the remaining queue-runtime gaps as narrow: alerting on queue depth and retry pressure, stronger request-to-job correlation, and richer lane validation rather than baseline scheduler or worker ownership.
