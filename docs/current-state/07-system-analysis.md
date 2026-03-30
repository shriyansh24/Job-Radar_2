# System Analysis Snapshot

> Last updated: 2026-03-30
> Status: `REFERENCE_SNAPSHOT`

## Purpose
This file is a repository-wide orientation snapshot that was merged from `origin/main` during final branch integration.

It is useful for:
- high-level subsystem mapping
- branch-delta context
- repository-wide risk review

It is not the primary source of truth for:
- live runtime commands
- exact filesystem ownership
- test layout details
- current validation status

For those, use:
1. `01-repo-map.md`
2. `02-backend.md`
3. `03-frontend.md`
4. `05-ops-and-ci.md`
5. `06-open-items.md`
6. `../repo-hardening/06-test-taxonomy.md`

## Scope
This snapshot covers:
- repository structure by major subsystem
- execution-flow summary
- core design patterns
- broad bottlenecks and constraints
- historical branch notes that matter for repo navigation

It intentionally avoids a file-by-file inventory because that level of detail drifted faster than the normalized current-state and test-taxonomy docs.

## Major Subsystems

### Backend
- `backend/app/` contains the FastAPI application, domain modules, runtime queue entrypoints, and worker orchestration.
- Major domains include auth, jobs, scraping, resume, interview, analytics, salary, networking, outcomes, vault, and admin/ops surfaces.
- `backend/app/migrations/` contains Alembic environment and schema revisions.
- `backend/tests/` is organized by protection goal: contracts, edge cases, infra, integration, migrations, security, unit, and workers.

### Frontend
- `frontend/src/` contains the React application, route pages, API clients, stores, shared components, and hooks.
- `frontend/src/tests/` holds the normalized Vitest suites by app/api/components/hooks/pages/support responsibility.
- `frontend/e2e/` holds committed Playwright coverage for smoke, route flows, responsive shell behavior, and theme-matrix assertions.
- The live shell is the reference-first command center documented in `03-frontend.md` and `frontend/system.md`.

### Runtime and Infra
- `docker-compose.yml` and `docker-compose.dev.yml` define the canonical local topology.
- Redis is now part of the active background-execution path through the ARQ queue model.
- Queue lanes are documented as `scraping`, `analysis`, and `ops`.
- Dedicated scheduler and worker roles are part of the runtime contract; the API process is no longer treated as the scheduler owner.

### Documentation Layers
- `docs/current-state/` is the live operational truth.
- `docs/audit/` is the bug ledger.
- `docs/research/` is exploratory or archived research only.
- `docs/repo-hardening/` is the repository traceability and hardening evidence layer.

## Execution Flow Summary
1. Backend boot validates config, installs middleware, mounts routers, and exposes health/auth/domain APIs.
2. Frontend boot mounts the routed React shell, auth guards, query client, and lazy route families.
3. Auth flows use the backend cookie/session path and frontend auth store/API client integration.
4. Scheduler enqueues named jobs onto Redis-backed ARQ queues.
5. Queue-specific workers execute scraping, analysis, and ops jobs with structured lifecycle logging.
6. Domain services persist through SQLAlchemy models and expose routed API boundaries to the frontend.
7. Frontend route pages consume typed API clients and render with shared component/system primitives.

## Core Design Patterns
- Layered backend domains: `models.py`, `schemas.py`, `service.py`, `router.py`
- Queue-backed background processing with explicit job registry and worker lanes
- Adapter and registry patterns across scraping and ATS-specific execution
- React route-family composition with reusable primitives, Zustand stores, and TanStack Query
- Structured logging and explicit health/readiness surfaces across critical backend/runtime paths

## Known Pressure Points
- Browser-heavy scraping remains the most resource-intensive backend path.
- Enrichment and LLM-adjacent flows remain throughput-sensitive compared with pure CRUD APIs.
- Queue telemetry and deployment-side alerting still matter operationally even after repo-local hardening.
- External ATS/browser/provider behavior cannot be fully made deterministic in local automated coverage.

## Branch Context
- `main` is the stable branch to merge back into and becomes the canonical active branch once the final PR lands.
- `codex/ui-changes` is the audited broad integration branch carrying frontend, backend, docs, runtime, test, and CI hardening work.
- `feat/p1-core-value` is not a merge target; it remains a capability-recovery source that has already been mined selectively.

## Validation Note
This snapshot is intentionally high-level so it remains truthful alongside:
- path-sensitive docs validation
- the normalized test taxonomy
- the current-state runtime pages

If deeper forensic detail is needed, use `docs/repo-hardening/` instead of re-expanding this file into another stale file-by-file dump.
