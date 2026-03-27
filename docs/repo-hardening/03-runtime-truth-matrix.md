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
| Redis URL/password | compose baseline with password | compose baseline with password | compose password baseline | requires `jobradar-redis` | inherits base compose | `backend/app/config.py` default expects password | `ALIGNED` |
| Redis TLS | not described | not clearly described | not described | conditional TLS if certs exist | inherits base compose | `redis_use_tls=False` by default in code | `DOCUMENTED_GAP` |
| Cookie auth model | says cookie-based auth and CSRF echo header | says cookie-based auth and CSRF echo header | n/a | n/a | n/a | `backend/app/auth/service.py` sets httpOnly access/refresh cookies plus a readable CSRF cookie; `frontend/src/api/client.ts` echoes `X-CSRF-Token` on unsafe methods | `ALIGNED` |
| Cookie security flags | local dev flags documented | local dev flags documented | n/a | n/a | n/a | `cookie_secure=False`, `SameSite=lax` by default for local-only dev; runtime validation rejects `SameSite=None` without secure cookies | `ALIGNED_WITH_LOCAL_ONLY_DEFAULTS` |
| Trusted hosts | branch-protection/runtime docs now mention trusted hosts | branch-protection/runtime docs now mention trusted hosts | n/a | n/a | n/a | `backend/app/main.py` installs `TrustedHostMiddleware`; `backend/app/config.py` validates `JR_TRUSTED_HOSTS` | `ALIGNED` |
| Scheduler process model | explicit dedicated scheduler command | explicit dedicated scheduler command | marker env documented via compose only | dedicated `scheduler` service with healthcheck | bind-mounted `scheduler` overlay service | `backend/app/main.py` no longer owns APScheduler; `backend/app/runtime/scheduler.py` is the runtime entrypoint | `ALIGNED` |
| Frontend API proxy | host-local Vite on `localhost:8000`; containerized Vite must override target | not previously explicit | `VITE_API_PROXY_TARGET=http://localhost:8000` | base compose uses built frontend container | dev overlay now sets `VITE_API_PROXY_TARGET=http://backend:8000` | `frontend/vite.config.ts` reads `VITE_API_PROXY_TARGET` with `http://localhost:8000` fallback | `FIXED_IN_CODE_AND_DOCS` |
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

## Reconciliation Direction
1. Keep base compose as the canonical runtime baseline and host-local frontend/backend as an explicit override.
2. Keep `.env.example` aligned to the compose DB and Redis baseline.
3. Keep containerized Vite dev as the checked-in overlay story and document it as an overlay, not the default runtime.
4. Keep cookie names, CSRF behavior, and local security flags in one place.
5. Keep the trusted-host list explicit in runtime docs whenever local or CI hostnames change.
