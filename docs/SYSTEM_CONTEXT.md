# JobRadar System Overview

## Executive Summary

JobRadar is a locally-run, full-stack job intelligence system that aggregates job postings from 7 sources (SerpApi/Google Jobs, Greenhouse, Lever, Ashby, JobSpy multi-board, TheirStack, Apify), deduplicates them via hash + fuzzy matching, stores them in SQLite with FTS5 full-text search, and enriches each posting with AI-generated metadata (skills extraction, scoring, red/green flags) via OpenRouter's LLM API. The system runs entirely on localhost with no authentication, no deployment, and no public users.

The frontend is a polished dark-themed dashboard (React 19, TypeScript, Tailwind) with 5 pages: a stats dashboard, filterable job board with virtualized lists, drag-and-drop kanban pipeline for application tracking, analytics with Recharts, and a settings panel. Real-time scraper events stream to the UI via Server-Sent Events (SSE). An AI copilot provides cover letter generation, interview prep, and gap analysis directly in the job detail panel.

The backend orchestrates everything through APScheduler with 7 scheduled jobs running scraping (configurable 3-12h intervals), LLM enrichment (every 15 minutes in batches of 10), and resume-based match scoring (every 20 minutes in batches of 50). All scraper intervals, search queries, target locations, and company watchlists are user-configurable through the settings API.

---

## Architecture

```
                              JobRadar Architecture
 +-----------------------------------------------------------------+
 |                        FRONTEND (:5173)                          |
 |  React 19 + TypeScript + Vite 6 + TailwindCSS 3.4              |
 |                                                                  |
 |  [Dashboard] [Job Board] [Pipeline] [Analytics] [Settings]      |
 |       |           |          |           |           |           |
 |  Zustand Store + TanStack React Query v5 + SSE Client           |
 +-----------------------------+------------------------------------+
                               | axios / SSE
                               v
 +-----------------------------------------------------------------+
 |                     BACKEND API (:8000)                          |
 |  FastAPI + SQLAlchemy 2.0 async + APScheduler                   |
 |                                                                  |
 |  Routers:                                                        |
 |  /api/jobs      /api/scraper     /api/search    /api/stats      |
 |  /api/copilot   /api/settings    /api/resume    /api/health     |
 +--------+----------------+------------------+--------------------+
          |                |                  |
          v                v                  v
 +----------------+ +----------------+ +------------------+
 |   SCRAPERS     | |  ENRICHMENT    | |   SCHEDULER      |
 |                | |                | |                   |
 | SerpApi        | | LLM Enricher   | | serpapi: 6h       |
 | Greenhouse     | |  Claude Haiku  | | greenhouse: 3h    |
 | Lever          | |  GPT-4o-mini   | | lever: 3h         |
 | Ashby          | | Embedding      | | ashby: 3h         |
 | JobSpy         | |  MiniLM-L6-v2  | | jobspy: 12h       |
 | TheirStack     | | Deduplicator   | | enrichment: 15m   |
 | Apify          | |  rapidfuzz     | | scoring: 20m      |
 +-------+--------+ +-------+--------+ +---------+---------+
         |                  |                     |
         v                  v                     v
 +-----------------------------------------------------------------+
 |                     SQLite + WAL + FTS5                          |
 |  Tables: jobs, saved_searches, scraper_runs, user_profile       |
 |  FTS5: jobs_fts (title, company, description, skills, tech)     |
 |  Path: data/jobradar.db                                         |
 +-----------------------------------------------------------------+
```

### Data Flow (5 Phases)

**Phase 1: Data Collection** — Scrapers fetch jobs from external APIs on schedule
**Phase 2: Deduplication** — Hash-based exact match + rapidfuzz cross-source (>92% title similarity within 7 days)
**Phase 3: Storage** — Jobs inserted into SQLite with FTS5 triggers for automatic search indexing
**Phase 4: AI Enrichment** — LLM extracts structured metadata; embeddings compute resume match scores
**Phase 5: Presentation** — Dashboard renders enriched data with real-time SSE updates

### Checkpoints

1. **Pre-Insert Checkpoint** — Deduplicator validates before any job enters the database
2. **Enrichment Checkpoint** — LLM responses validated as JSON; fallback model on primary failure
3. **User Checkpoint** — All status changes (saved/applied/rejected) require explicit user action

---

## Tech Stack

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12 | Runtime |
| FastAPI | 0.115.0 | API framework |
| SQLAlchemy | 2.0.36 (async) | ORM + database |
| aiosqlite | 0.20.0 | Async SQLite driver |
| APScheduler | 3.10.4 | Job scheduling |
| Pydantic | 2.9.0 | Schema validation |
| httpx | 0.27.0 | Async HTTP client |
| sentence-transformers | 3.3.0 | Embedding model |
| rapidfuzz | 3.10.0 | Fuzzy string matching |
| python-jobspy | 1.1.82 | Multi-board scraping |
| openai (SDK) | 1.57.0 | OpenRouter API client |
| beautifulsoup4 | 4.12.3 | HTML parsing |
| html2text | 2024.2.26 | HTML to markdown |

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| React | 19.0.0 | UI framework |
| TypeScript | 5.6+ | Type safety |
| Vite | 6.0.0 | Build tool + dev server |
| TailwindCSS | 3.4.0 | Utility-first CSS |
| Zustand | 5.0.0 | State management |
| @tanstack/react-query | 5.0.0 | Server state |
| @tanstack/react-virtual | 3.0.0 | Virtualized lists |
| @dnd-kit/core + sortable | 6.0 / 8.0 | Drag-and-drop kanban |
| Recharts | 2.13.0 | Charts and analytics |
| lucide-react | 0.460.0 | Icons |
| axios | 1.7.0 | HTTP client |

### LLM Integration
| Provider | Model | Use Case | Cost |
|----------|-------|----------|------|
| OpenRouter | anthropic/claude-3-5-haiku | Primary enrichment | ~$0.25/MTok input |
| OpenRouter | openai/gpt-4o-mini | Fallback enrichment | ~$0.15/MTok input |
| Local | all-MiniLM-L6-v2 (384-dim) | Resume match scoring | Free (CPU) |

---

## Current Implementation Status

- [x] Tech stack finalized
- [x] Project structure and build system (Makefile, Vite, pip)
- [x] Database models with FTS5 full-text search
- [x] All 7 scraper implementations
- [x] Deduplication engine (hash + fuzzy)
- [x] LLM enrichment pipeline with fallback
- [x] Embedding-based resume matching
- [x] APScheduler with 7 scheduled jobs
- [x] All FastAPI routers (19 endpoints)
- [x] SSE streaming for real-time scraper events
- [x] Frontend design system (Geist dark theme)
- [x] Dashboard page with stat cards and charts
- [x] Job Board with filters, virtualized list, detail panel
- [x] Pipeline kanban with drag-and-drop
- [x] Analytics page with 5 chart types
- [x] Settings page (API keys, scraper config, resume upload)
- [x] Scraper log drawer with terminal-style output
- [x] AI Copilot tools (cover letter, interview prep, gap analysis)
- [x] Full backend-frontend integration
- [ ] Docker Compose deployment
- [ ] CSV/JSON export from job board
- [ ] Email alerts for saved searches

---

## Key APIs/Integrations

### Job Scraping Sources

| Source | Endpoint | Auth | Rate Limit | Data Quality |
|--------|----------|------|------------|-------------|
| **SerpApi** | `serpapi.com/search.json?engine=google_jobs` | API key | 1s/page, 20% hourly cap | High (salary, apply links) |
| **Greenhouse** | `boards-api.greenhouse.io/v1/boards/{slug}/jobs` | None | 0.5s/slug | High (full HTML content) |
| **Lever** | `api.lever.co/v0/postings/{slug}?mode=json` | None | 0.5s/slug | Medium (plain + HTML desc) |
| **Ashby** | `api.ashbyhq.com/posting-api/job-board/{slug}` | None | 0.5s/slug | High (compensation data) |
| **JobSpy** | Local python-jobspy library | None | 2s/run | Medium (aggregates 5 boards) |
| **TheirStack** | `api.theirstack.com/v1/jobs/search` | Bearer token | 0.5s, 2 req/sec free | Medium |
| **Apify** | `api.apify.com/v2/acts/{id}/runs` | Bearer token | 1s, 120s poll timeout | Varies by actor |

### OpenRouter LLM Endpoint
- **Base URL**: `https://openrouter.ai/api/v1`
- **Client**: OpenAI Python SDK with `base_url` override
- **Rate Limits**: Varies by model, enforced by OpenRouter
- **Batch Size**: 10 jobs per enrichment cycle
- **Max Tokens**: 1000 per enrichment call
- **Temperature**: 0.1 (near-deterministic)
- **Response Format**: `{"type": "json_object"}` enforced

### Database Schema (Core Tables)

```sql
-- Primary table: 65+ columns covering identity, company, role,
-- compensation, content, AI enrichment, and user state
jobs (
    job_id       TEXT(64) PRIMARY KEY,  -- SHA256 hash
    source       TEXT(32),
    title        TEXT(500),
    company_name TEXT(255),
    status       TEXT(32) DEFAULT 'new',
    match_score  REAL,                  -- 0-100, resume-based
    is_enriched  BOOLEAN DEFAULT FALSE,
    -- ... 60+ more columns
)

-- Full-text search shadow table
jobs_fts USING fts5(job_id UNINDEXED, title, company_name,
    description_clean, skills_required, tech_stack)

-- Scraper execution history
scraper_runs (id, source, started_at, completed_at,
    jobs_found, jobs_new, jobs_updated, error_message, status)

-- User preferences (singleton, id=1)
user_profile (id, resume_filename, resume_text,
    default_queries JSON, default_locations JSON, company_watchlist JSON)

-- Saved filter configurations
saved_searches (id, name, query_params JSON, alert_enabled, created_at)
```

---

## Agent Specifications

### Phase 1: Data Collection (Scrapers)

| Agent | Source | Trigger | Search Strategy |
|-------|--------|---------|----------------|
| **SerpApiScraper** | Google Jobs | Every 6h | Query x Location combos from UserProfile |
| **GreenhouseScraper** | Greenhouse ATS | Every 3h | Company watchlist slugs |
| **LeverScraper** | Lever ATS | Every 3h | Company watchlist slugs |
| **AshbyScraper** | Ashby ATS | Every 3h | Company watchlist slugs |
| **JobSpyScraper** | LinkedIn+Indeed+Glassdoor+Google+ZipRecruiter | Every 12h | Query x Location combos |
| **TheirStackScraper** | TheirStack API | Manual / Optional | Query x Location combos |
| **ApifyScraper** | Apify Actors | Manual / Optional | Actor-specific params |

### Phase 2: Deduplication
- **Agent**: `Deduplicator`
- **Trigger**: Before every job insert (inline, not batched)
- **Strategy**: SHA256 hash match → cross-source fuzzy match (same company + >92% title + 7-day window)
- **Output**: `duplicate_of` field set on newer record; original preserved

### Phase 3: AI Enrichment
- **Agent**: `LLMEnricher`
- **Trigger**: Every 15 minutes (APScheduler)
- **Input**: Unenriched jobs (`is_enriched=False`), batch of 10
- **Output**: skills, tech_stack, scores, summary, flags
- **Fallback**: Primary model failure → fallback model → mark as failed

### Phase 4: Resume Matching
- **Agent**: `EmbeddingMatcher`
- **Trigger**: Every 20 minutes (APScheduler), or on resume upload
- **Input**: Jobs without match_score + cached resume embedding
- **Output**: `match_score` (0-100, cosine similarity)
- **Model**: all-MiniLM-L6-v2 (384-dim, CPU-only)

### Phase 5: Presentation & Interaction
- **Agent**: Frontend SSE consumer
- **Trigger**: Real-time (SSE stream)
- **Events**: `scraper_started`, `job_found`, `scraper_progress`, `scraper_completed`, `scraper_error`
- **AI Copilot**: On-demand cover letter / interview prep / gap analysis via `POST /api/copilot`

---

## Constraints & Decisions

| Constraint | Decision | Rationale |
|-----------|----------|-----------|
| Must run locally | SQLite + localhost only | Privacy-first, no cloud dependency |
| No authentication | Single-user design | Personal tool, no public access |
| Token efficiency | Claude 3.5 Haiku primary | $0.25/MTok vs $3/MTok for Sonnet |
| Parallel execution | APScheduler async + SSE | Non-blocking scraper runs, real-time UI |
| 50K+ job handling | @tanstack/react-virtual | Virtualized rendering, no DOM bloat |
| Cross-source dedup | Hash + rapidfuzz | Exact match first (fast), fuzzy second (accurate) |
| No Ollama | OpenRouter API only | User preference for cloud LLM (AGENT_OVERRIDES.md) |
| No ProxyCurl | JobSpy replacement | ProxyCurl deprecated / dead service |
| Resume on CPU | MiniLM-L6-v2 (384-dim) | Fast enough for single-user, no GPU required |
| API keys server-side | Copilot proxied via `/api/copilot` | Never expose OpenRouter key to browser |

---

## File Structure

```
jobradar/
├── backend/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app + lifespan
│   ├── config.py                  # Pydantic Settings from .env
│   ├── database.py                # Async engine + FTS5 setup
│   ├── models.py                  # ORM: Job, SavedSearch, ScraperRun, UserProfile
│   ├── schemas.py                 # Pydantic v2 request/response schemas
│   ├── scheduler.py               # APScheduler + SSE broadcast
│   ├── requirements.txt
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract BaseScraper
│   │   ├── serpapi_scraper.py     # Google Jobs via SerpApi
│   │   ├── greenhouse_scraper.py  # Free ATS API
│   │   ├── lever_scraper.py       # Free ATS API
│   │   ├── ashby_scraper.py       # Free ATS API
│   │   ├── jobspy_scraper.py      # Multi-board (5 sites)
│   │   ├── theirstack_scraper.py  # Paid API (optional)
│   │   └── apify_scraper.py       # Actor wrapper (optional)
│   ├── enrichment/
│   │   ├── __init__.py
│   │   ├── llm_enricher.py        # OpenRouter Claude/GPT enrichment
│   │   ├── embedding.py           # sentence-transformers matching
│   │   └── deduplicator.py        # Hash + fuzzy dedup
│   └── routers/
│       ├── __init__.py
│       ├── jobs.py                # CRUD + filtering + FTS5
│       ├── scraper.py             # Run/status/SSE stream
│       ├── search.py              # Semantic search
│       ├── stats.py               # Aggregated analytics
│       ├── copilot.py             # AI tools proxy
│       └── settings.py            # Config + resume + saved searches
├── frontend/
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.cjs
│   ├── postcss.config.cjs
│   ├── tsconfig.json
│   └── src/
│       ├── index.css              # Design system CSS variables
│       ├── main.tsx               # React root + QueryClient
│       ├── App.tsx                # Page router + SSE connection
│       ├── api/client.ts          # Typed API client (axios)
│       ├── store/useJobStore.ts   # Zustand global state
│       ├── lib/
│       │   ├── constants.ts       # Colors, statuses, config
│       │   └── utils.ts           # cn(), formatTimeAgo, etc.
│       ├── components/
│       │   ├── layout/            # Sidebar, TopBar, Layout
│       │   ├── jobs/              # JobCard, JobList, JobDetailPanel,
│       │   │                      # JobFilters, JobStatusBadge, ScoreRing
│       │   ├── pipeline/          # KanbanBoard, KanbanCard
│       │   ├── scraper/           # ScraperLog, ScraperControlPanel
│       │   ├── stats/             # StatsOverview, SourceBreakdownChart
│       │   └── settings/          # SettingsPage, ResumeUpload
│       └── pages/
│           ├── Dashboard.tsx
│           ├── JobBoard.tsx
│           ├── Pipeline.tsx
│           ├── Analytics.tsx
│           └── Settings.tsx
├── data/
│   └── jobradar.db                # SQLite database (gitignored)
├── docs/
│   └── SYSTEM_CONTEXT.md          # This file
├── .env                           # API keys (gitignored)
├── .env.example                   # Template
├── .gitignore
├── Makefile
└── README.md
```

---

## Known Issues / Open Questions

### Known Limitations
1. **PDF parsing**: Falls back to raw UTF-8 decode if `pypdf` import fails (less accurate for complex PDFs)
2. **Enrichment timeout**: 1000 max_tokens may truncate responses for very complex job postings
3. **Resume re-embedding**: Blocking operation on upload (no background task queue)
4. **Apify polling**: Hard-coded 120-second max wait (60 iterations x 2s)
5. **JobSpy sync execution**: Runs in thread executor since the library is synchronous
6. **No pagination for scraper logs**: SSE stream holds last 200 entries in memory only

### Open Questions
1. Should TheirStack/Apify be auto-scheduled or remain manual-trigger only?
2. Should CSV/JSON export be added to the job board toolbar?
3. Should saved search alerts trigger browser notifications or email?
4. Should the skills heatmap include a time-range selector?

---

## Integration Points (Ready for New Features)

### Adding a New Scraper
1. Create `backend/scrapers/newscraper.py` extending `BaseScraper`
2. Register in `SCRAPERS` dict in `backend/scheduler.py`
3. Add scheduler job in `create_scheduler()`
4. Optionally add source color to `frontend/src/lib/constants.ts`

### Adding a New AI Tool
1. Add prompt template to `TOOL_PROMPTS` dict in `backend/routers/copilot.py`
2. Add tool name to `CopilotRequest` schema in `backend/schemas.py`
3. Add UI button in `frontend/src/components/jobs/JobDetailPanel.tsx`

### Adding a New Analytics Chart
1. Add data aggregation to `GET /api/stats` in `backend/routers/stats.py`
2. Add Recharts component in `frontend/src/components/stats/`
3. Import and render in `frontend/src/pages/Analytics.tsx`

### Database Extension Points
- Add columns to `Job` model in `backend/models.py` (auto-migrated on restart)
- Update `jobs_fts` triggers if new searchable columns added
- Add new models for features like user tags, application timeline, etc.

### Frontend Component Slots
- **Dashboard right column**: Add cards below "Top Skills in Market"
- **Job detail panel tabs**: Add new tab alongside "Details" and "AI"
- **Settings tabs**: Add new tab (e.g., "Notifications", "Integrations")
- **Sidebar nav**: Add new page entry below Settings

---

## Prompt Template for AI Agents

```
# JobRadar Context Brief

## System Overview
JobRadar is a locally-run job intelligence system that scrapes 7 sources,
deduplicates via hash+fuzzy matching, enriches with Claude 3.5 Haiku via
OpenRouter, and presents in a React 19 dark dashboard with kanban tracking.

## Current Architecture
- 7 scrapers (SerpApi, Greenhouse, Lever, Ashby, JobSpy, TheirStack, Apify)
- 3 enrichment agents (LLM enricher, embedding matcher, deduplicator)
- APScheduler with 7 scheduled jobs
- FastAPI backend (19 endpoints) + React frontend (5 pages)
- SQLite + FTS5, SSE streaming, Zustand + React Query

## Tech Stack
- Backend: Python 3.12, FastAPI 0.115, SQLAlchemy 2.0 async, APScheduler 3.10
- Frontend: React 19, TypeScript 5, Vite 6, TailwindCSS 3.4, Recharts 2
- LLM: OpenRouter (claude-3-5-haiku primary, gpt-4o-mini fallback)
- Embeddings: all-MiniLM-L6-v2 (384-dim, CPU)
- Database: SQLite WAL + FTS5

## Your Task
[Specific task description]

## Key Constraints
- Must work with local-first design (localhost only, no auth)
- Token efficiency matters (using Haiku at $0.25/MTok)
- All scraper intervals user-configurable via settings API
- API keys never exposed to frontend (server-side proxy)
- No Ollama, no ProxyCurl (per AGENT_OVERRIDES.md)

## Relevant Code Context
[Paste the CONTEXT.md file for affected modules]

## Success Criteria
[Measurable outcomes]
```
