# CLAUDE.md — JobRadar Development Guide

This file provides context for AI assistants working on the JobRadar codebase.

## What is JobRadar?

A locally-run, full-stack personal job intelligence system that scrapes jobs from multiple sources, deduplicates and enriches them with AI, and presents them in a dark-themed dashboard with drag-and-drop application tracking. Runs exclusively on localhost — no deployment, no auth, no public users.

## Quick Start

```bash
# Install dependencies
pip install -r backend/requirements.txt
cd frontend && pnpm install

# Run development servers
uvicorn backend.main:app --reload --port 8000   # Backend at localhost:8000
cd frontend && pnpm dev                          # Frontend at localhost:5173

# Or use the Makefile
make install   # Install all deps
make dev       # Start both servers
make reset     # Delete DB and restart
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI 0.115, SQLAlchemy 2.0 (async) |
| Database | SQLite with WAL mode + FTS5 full-text search |
| Scheduler | APScheduler 3.10 (AsyncIOScheduler) |
| Frontend | React 19, TypeScript 5.6, Vite 6, TailwindCSS 3.4 |
| State | Zustand 5 (client), React Query 5 (server) |
| LLM | OpenRouter API via OpenAI SDK (`base_url` swap) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) + sqlite-vec |
| Package mgmt | pip/uv (Python), pnpm (frontend) |

## Project Structure

```
backend/
├── main.py              # FastAPI app, lifespan, CORS, router registration
├── config.py            # Pydantic Settings from .env
├── database.py          # Async SQLAlchemy engine, FTS5 triggers, WAL mode
├── models.py            # ORM: Job, SavedSearch, ScraperRun, UserProfile
├── schemas.py           # Pydantic v2 request/response schemas
├── scheduler.py         # APScheduler + SSE event broadcasting
├── scrapers/
│   ├── base.py          # Abstract BaseScraper (fetch_jobs, normalize, compute_job_id)
│   ├── serpapi_scraper.py      # Google Jobs via SerpApi (PRIMARY, requires key)
│   ├── greenhouse_scraper.py   # Free ATS API
│   ├── lever_scraper.py        # Free ATS API
│   ├── ashby_scraper.py        # Free ATS API
│   ├── jobspy_scraper.py       # Free multi-board (LinkedIn, Indeed, Glassdoor, Google, ZipRecruiter)
│   ├── theirstack_scraper.py   # Optional paid feed
│   └── apify_scraper.py        # Optional Apify actor wrapper
├── enrichment/
│   ├── llm_enricher.py  # OpenRouter LLM enrichment (skills, flags, scores)
│   ├── embedding.py     # sentence-transformers resume matching
│   └── deduplicator.py  # Hash + rapidfuzz cross-source dedup
└── routers/
    ├── jobs.py          # GET/PATCH /api/jobs
    ├── scraper.py       # POST /api/scraper/run, GET /api/scraper/status/stream
    ├── search.py        # GET /api/search/semantic
    ├── stats.py         # GET /api/stats
    ├── copilot.py       # POST /api/copilot (streaming LLM proxy)
    └── settings.py      # GET/POST /api/settings, POST /api/resume/upload

frontend/src/
├── main.tsx             # React entry
├── App.tsx              # Routing, SSE connection
├── api/client.ts        # Axios instance, typed API client
├── store/useJobStore.ts # Zustand store (filters, view mode, scraper state)
├── pages/
│   ├── Dashboard.tsx    # Stat cards, top matches, source/skills charts
│   ├── JobBoard.tsx     # Filter panel + virtualized list + detail panel
│   ├── Pipeline.tsx     # Kanban board (dnd-kit)
│   ├── Analytics.tsx    # Area/pie/bar charts, skills heatmap, funnel
│   └── Settings.tsx     # API keys, scraper config, resume upload
├── components/
│   ├── layout/          # Layout.tsx, Sidebar.tsx, TopBar.tsx
│   ├── jobs/            # JobCard, JobList (virtualized), JobDetailPanel, JobFilters, ScoreRing
│   ├── pipeline/        # KanbanBoard.tsx, KanbanCard.tsx
│   ├── scraper/         # ScraperControlPanel.tsx, ScraperLog.tsx (SSE terminal)
│   ├── stats/           # StatsOverview.tsx, SourceBreakdownChart.tsx
│   └── settings/        # SettingsPage.tsx, ResumeUpload.tsx
└── lib/
    ├── utils.ts         # Helper functions
    └── constants.ts     # Colors, status enums, source badges
```

## Key Architecture Patterns

### Data Flow
1. **Scrape** — Scrapers fetch jobs from 7 sources on configurable schedules
2. **Deduplicate** — Hash match + rapidfuzz (>0.92 ratio) prevents cross-source dupes
3. **Store** — SQLite with FTS5 indexing (auto-maintained via triggers)
4. **Enrich** — LLM extracts skills, tech stack, scores, flags (every 15min, batches of 10)
5. **Match** — Embedding similarity scores jobs against uploaded resume (every 20min)
6. **Display** — Dashboard shows enriched data with real-time SSE updates

### Database
- SQLite with WAL mode for concurrent reads
- FTS5 virtual table `jobs_fts` indexes: job_id, title, company_name, description_clean, skills_required, tech_stack
- Triggers auto-sync FTS on INSERT/UPDATE/DELETE — do not manually manage FTS
- Primary key for jobs is `job_id` — a SHA256 hash of `{source}:{company}:{title}`

### LLM Integration
- All LLM calls go through OpenRouter via OpenAI SDK with `base_url="https://openrouter.ai/api/v1"`
- Primary model: `anthropic/claude-3-5-haiku` — Fallback: `openai/gpt-4o-mini`
- Frontend NEVER calls OpenRouter directly — always via `POST /api/copilot`
- Enrichment uses `response_format={"type": "json_object"}` with `temperature=0.1`

### Frontend Patterns
- Virtualized lists via `@tanstack/react-virtual` for 50K+ items
- Drag-and-drop via `@dnd-kit/core` + `@dnd-kit/sortable`
- Optimistic updates on status changes — PATCH then revert on error
- SSE connection to `/api/scraper/stream` for real-time scraper logs
- All filters sync to URL query params

### Scraper Pattern
All scrapers extend `BaseScraper` with:
- `source_name: str` — identifier
- `rate_limit_delay: float` — seconds between requests
- `async fetch_jobs(query, location, limit) -> list[dict]` — main method
- `normalize(raw) -> dict` — standardize to Job schema
- `compute_job_id(source, company, title) -> str` — SHA256 hash

## API Endpoints

```
GET    /api/jobs?page=&limit=&q=&source=&status=&experience_level=&remote_type=&sort_by=&sort_dir=
GET    /api/jobs/{job_id}
PATCH  /api/jobs/{job_id}          # { status?, notes?, tags?, is_starred? }
GET    /api/search/semantic?q=&limit=
POST   /api/scraper/run            # { source: "all"|"serpapi"|"greenhouse"|... }
GET    /api/scraper/status
GET    /api/scraper/stream         # SSE endpoint
GET    /api/stats
POST   /api/copilot                # { tool: "coverLetter"|"interviewPrep"|"gapAnalysis", job_id }
GET    /api/settings
POST   /api/settings
POST   /api/resume/upload          # Multipart PDF/TXT
GET    /api/saved-searches
POST   /api/saved-searches
DELETE /api/saved-searches/{id}
GET    /api/health
```

CORS allows `http://localhost:5173` and `http://127.0.0.1:5173`.
Error format: `{"error": "message", "detail": "..."}`.
FastAPI docs: `http://localhost:8000/docs`.

## Environment Variables

Required in `.env` (see `.env.example`):
- `SERPAPI_KEY` — Google Jobs scraping (required for SerpApi scraper)
- `OPENROUTER_API_KEY` — LLM enrichment (required)
- `OPENROUTER_PRIMARY_MODEL` — default: `anthropic/claude-3-5-haiku`
- `OPENROUTER_FALLBACK_MODEL` — default: `openai/gpt-4o-mini`
- `DATABASE_URL` — default: `sqlite+aiosqlite:///./data/jobradar.db`

Optional: `THEIRSTACK_KEY`, `APIFY_KEY`, `SCRAPINGBEE_KEY`

## Design System

- Dark theme — `#000000` base, `#0a0a0a` surface, `#111111` elevated
- Accent: `#0070F3` (Vercel blue), green `#10B981`, amber `#F5A623`, red `#E00000`
- Fonts: Geist (UI), Geist Mono (data/code) — loaded via Google Fonts
- 8px base grid, `rounded-lg` cards, `rounded-xl` panels, `rounded-full` badges
- Source badges: greenhouse=emerald, lever=violet, ashby=orange, serpapi=red, jobspy=slate
- Status colors: new=green, saved=amber, applied=cyan, interviewing=purple, offer=pink, rejected=red, ghosted=slate

## Critical Rules

1. **No ProxyCurl** — shut down July 2025. Never reference or build integrations for it.
2. **No Ollama/local LLM** — use OpenRouter API exclusively. No `ollama` imports.
3. **No mock data in production** — every component must use real API data.
4. **API keys stay server-side** — frontend calls `/api/copilot`, never OpenRouter directly.
5. **JobSpy is the free fallback** — `python-jobspy` for LinkedIn/Indeed/Glassdoor without API keys.
6. **SQLite only** — no Postgres, no Redis, no Celery. APScheduler handles scheduling.
7. **Localhost only** — no deployment, no auth, no Docker (except optional Phase 6).

## Document Hierarchy

When documents conflict, follow this priority order:
1. `AGENT_OVERRIDES.md` — ground truths, always wins
2. `CLAUDE.md` (this file) — development guide
3. `Claude.md` — original build specification
4. `README.md` — project documentation

## Scheduler Configuration

```
serpapi:     every 6h    |  greenhouse: every 3h  |  lever: every 3h
ashby:      every 3h    |  jobspy:     every 12h
enrichment: every 15min |  scoring:    every 20min
```

All intervals are user-configurable via `/api/settings`.
