# CLAUDE.md — JobRadar V2 Project Instructions

## Project Context
- **Repo:** D:/jobradar-v2 (monorepo: Python FastAPI backend + React/Vite frontend)
- **Status doc:** D:/jobradar-v2/PROJECT_STATUS.md (read this first every session)
- **Design spec:** docs/superpowers/specs/2026-03-19-scraper-platform-design.md
- **Implementation plans:** docs/superpowers/plans/00-index.md (master index) + chunk-1 through chunk-6 files

## Current Priority: Scraper Platform Build

### Execution Order (strict dependencies)
```
Sequential:  Chunk 1 (foundation) — MUST complete first
Parallel:    Chunk 2 (routing) + Chunk 3 (adapters)
Parallel:    Chunk 4 (browsers) + Chunk 5 (integration)
Sequential:  Chunk 6 (testing) — last, depends on everything
```

### Plan Files (one per chunk, self-contained)
- `docs/superpowers/plans/chunk-1-foundation.md` — Tasks 1-10
- `docs/superpowers/plans/chunk-2-routing.md` — Tasks 11-14
- `docs/superpowers/plans/chunk-3-adapters.md` — Tasks 15-19
- `docs/superpowers/plans/chunk-4-browsers.md` — Tasks 20-22
- `docs/superpowers/plans/chunk-5-integration.md` — Tasks 23-25
- `docs/superpowers/plans/chunk-6-testing.md` — Tasks 26-29

## Workflow Rules

### Use Superpowers Skills
- **superpowers:subagent-driven-development** for executing chunk tasks
- **superpowers:test-driven-development** — all implementation follows TDD
- **superpowers:verification-before-completion** — verify before claiming done
- **superpowers:requesting-code-review** — after completing a chunk

### Subagent Loop (REQUIRED for every task)
1. **IMPLEMENTER** subagent: reads task from chunk file, implements, tests, commits
2. **SPEC REVIEWER** subagent: checks code matches the task spec exactly
3. If spec fails → implementer fixes → spec re-review
4. **CODE QUALITY REVIEWER** subagent: checks readability, safety, performance
5. If quality fails → implementer fixes → quality re-review
6. Mark task complete in chunk file's status tracker

### Git Rules
- Work on `main` branch for sequential chunks
- For parallel chunks, use git worktrees:
  ```powershell
  # From D:/jobradar-v2 (main repo):
  git worktree add ../chunk-2-routing -b chunk-2-routing
  git worktree add ../chunk-3-adapters -b chunk-3-adapters
  ```
- Merge worktrees back after both parallel chunks pass all tests
- Never force-push or amend commits without asking

### Session Memory
- After completing work, update the chunk file's "Chunk Status" section
- After completing work, append to `docs/superpowers/plans/00-index.md` Session Log
- After completing work, update `PROJECT_STATUS.md` if major milestones reached

## Tech Stack
- Python 3.13, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Redis/Memurai
- React 18, Vite, TailwindCSS, React Query, Zustand
- Alembic migrations at `app/migrations/` (already initialized, do NOT run `alembic init`)
- Tests: pytest + pytest-asyncio, test DB: `jobradar_v2_test`

## Key Existing Patterns
- Scrapers implement `ScraperPort` (app/scraping/port.py)
- New fetchers implement `FetcherPort`, browsers implement `BrowserPort` (app/scraping/execution/)
- Rate limiting via token bucket + circuit breaker (app/scraping/rate_limiter.py)
- 3-layer dedup: MD5 hash, URL canonical, simhash (app/scraping/deduplication.py)
- SSE events via EventBus (app/shared/events.py)
- All datetime columns use `DateTime(timezone=True)`
- Job IDs are SHA-256 String(64), NOT UUID

## Environment
- Machine: 64GB RAM, 24 cores (Intel Core Ultra 9 275HX)
- Backend runs from: D:/jobradar-v2/backend
- Frontend runs from: D:/jobradar-v2/frontend
- .env at: D:/jobradar-v2/backend/.env
- API base URL: /api/v1 (relative, Vite proxies to backend)
- Dev servers: `preview_start backend` and `preview_start frontend` (see .claude/launch.json)

## Do NOT
- Run `alembic init` (already initialized at app/migrations/)
- Change jobs.id from String(64) to UUID
- Scrape behind login walls (LinkedIn auth, Glassdoor auth)
- Store API keys in code (use .env)
- Skip TDD — write test first, then implement
- Skip the subagent review loop
