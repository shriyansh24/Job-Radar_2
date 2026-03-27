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
| Frontend port | `5173` for local dev | `npm run dev` only | n/a | `3000:80` in base compose | `5173:5173` in dev overlay | host-local Vite uses `5173`; base compose serves Nginx on `3000` | `DOCUMENTED_CONFLICT`: dual startup modes need one explicit hierarchy |
| Postgres host/port | manual `docker start jobradar-postgres` | `5433` manual container | `5432` localhost | `5432:5432` | inherits base compose | `backend/app/config.py` default is `5432` | `DOCUMENTED_CONFLICT` |
| Postgres credentials | not explicit in quick start | `jobradar220568` | `jobradar` / `jobradar` | `jobradar` / `jobradar` | inherits base compose | `backend/app/config.py` default is `jobradar` / `jobradar` | `DOCUMENTED_CONFLICT` |
| Redis URL/password | not explicit | implied Docker Redis | no password | requires `jobradar-redis` | inherits base compose | `backend/app/config.py` default expects password | `DOCUMENTED_CONFLICT` |
| Redis TLS | not described | not clearly described | not described | conditional TLS if certs exist | inherits base compose | `redis_use_tls=False` by default in code | `DOCUMENTED_GAP` |
| Cookie auth model | says cookie-based auth | says cookie-based auth | n/a | n/a | n/a | `backend/app/auth/service.py` sets httpOnly access/refresh cookies | `ALIGNED_BUT_UNDERDOCUMENTED` |
| Cookie security flags | not described | not described | n/a | n/a | n/a | `cookie_secure=False`, `SameSite=lax` by default | `DOCUMENTED_GAP` |
| Scheduler process model | not described clearly | mentions runtime but not coupling | n/a | n/a | n/a | `backend/app/main.py` starts APScheduler inside FastAPI lifespan | `DOCUMENTED_GAP` |
| Frontend API proxy | host-local Vite on `localhost:8000`; containerized Vite must override target | not previously explicit | `VITE_API_PROXY_TARGET=http://localhost:8000` | base compose uses built frontend container | dev overlay now sets `VITE_API_PROXY_TARGET=http://backend:8000` | `frontend/vite.config.ts` reads `VITE_API_PROXY_TARGET` with `http://localhost:8000` fallback | `FIXED_IN_CODE_AND_DOCS` |
| Browser QA artifact path | `.claude/ui-captures/` | `.claude/ui-captures/` | n/a | n/a | n/a | current branch stores captures there | `ALIGNED` |
| Frontend theme model | high-level light/dark wording | high-level theme wording | n/a | n/a | n/a | `useUIStore` persists theme family + mode | `DOCUMENTED_GAP` |

## Actual Local Runtime Baseline From Code
- Backend config source: `backend/app/config.py`
- Backend startup and scheduler coupling: `backend/app/main.py`
- Database engine/session: `backend/app/database.py`
- Frontend dev proxy: `frontend/vite.config.ts`
- Base container topology: `docker-compose.yml`
- Dev overlay topology: `docker-compose.dev.yml`

## Reconciliation Direction
1. Pick one primary local-dev story and explicitly label the alternate story as legacy or optional.
2. Rewrite `.env.example` so it matches the chosen DB and Redis baseline.
3. Decide whether containerized Vite dev is actually supported; if yes, fix the proxy target.
4. Document cookie names and local security flags in one place.
5. Document scheduler/API-process coupling as an explicit limitation, not an implied detail.
