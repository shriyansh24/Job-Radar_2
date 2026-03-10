# JobRadar — Personal Job Intelligence System

A locally-run, full-stack web application that scrapes jobs from multiple sources, deduplicates and enriches them with AI, and presents them in a polished dark dashboard UI with application tracking.

## Start Here

If you're new to this repo, begin with the curated entrypoints and default workflow loop:

- **Entrypoints:** `.agents/skills/entrypoints/` (curated "start here" stubs)
- **Router:** `.agents/skills/core/router/` (task → persona/workflow selection policy)
- **Default workflow:** `.agents/skills/workflows/plan-implement-review/`
- **Quick fix workflow:** `.agents/skills/workflows/quick-fix/`
- **Research workflow:** `.agents/skills/workflows/research-summarize-decide/`
- **Quality gate:** `.agents/skills/quality/gate/` (final verification)
- **Profiles:** `platforms/profiles/` (fast / safe / deep). Recommended default: `safe.yaml`
- **Map:** `docs/architecture/skill-map.md` (how the taxonomy fits together)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- pnpm (`npm install -g pnpm`)

### Installation

```bash
# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
cd frontend && pnpm install && cd ..
```

### Configuration

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

Required keys:
- `SERPAPI_KEY` — Google Jobs scraping ([serpapi.com](https://serpapi.com))
- `OPENROUTER_API_KEY` — LLM enrichment ([openrouter.ai/keys](https://openrouter.ai/keys))

Optional keys:
- `THEIRSTACK_KEY` — Additional job feed
- `APIFY_KEY` — Apify actor wrapper

### Running

```bash
# Start both servers (backend on :8000, frontend on :5173)
make dev

# Or start individually:
uvicorn backend.main:app --reload --port 8000
cd frontend && pnpm dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

## Architecture

### Backend (Python / FastAPI)

- **FastAPI** with async SQLAlchemy 2.0 + aiosqlite
- **SQLite** with WAL mode + FTS5 full-text search
- **7 scrapers**: SerpApi (Google Jobs), Greenhouse, Lever, Ashby, JobSpy (multi-board), TheirStack, Apify
- **AI enrichment** via OpenRouter (Claude 3.5 Haiku / GPT-4o-mini fallback)
- **Embeddings** via sentence-transformers for resume-job matching
- **Deduplication** via hash + rapidfuzz cross-source matching
- **APScheduler** for automated scraping + enrichment on configurable intervals
- **SSE** for real-time scraper event streaming

### Frontend (React / TypeScript)

- **React 19** + TypeScript + Vite 6
- **TailwindCSS 3.4** with custom dark design system (Geist font family)
- **Zustand** for state management
- **@tanstack/react-query** for server state
- **@tanstack/react-virtual** for virtualized job lists (50K+ items)
- **@dnd-kit** for drag-and-drop kanban
- **Recharts** for analytics charts

### Pages

| Page | Description |
|------|-------------|
| **Dashboard** | Stat cards, top matches, source/skills breakdown |
| **Job Board** | Filterable job list with detail panel, search, sorting |
| **Pipeline** | Kanban board for application tracking (drag-and-drop) |
| **Analytics** | Charts: jobs/day, experience levels, top companies, skills heatmap |
| **Settings** | API keys, scraper config, resume upload |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/jobs` | List jobs with 15+ filter params |
| GET | `/api/jobs/{id}` | Get single job |
| PATCH | `/api/jobs/{id}` | Update job status/notes/tags |
| GET | `/api/search/semantic` | Semantic search via embeddings |
| POST | `/api/scraper/run` | Trigger scraper run |
| GET | `/api/scraper/status` | Get scraper run history |
| GET | `/api/scraper/stream` | SSE stream of scraper events |
| GET | `/api/stats` | Aggregated statistics |
| POST | `/api/copilot` | AI copilot (cover letter, interview prep) |
| GET/POST | `/api/settings` | App configuration |
| POST | `/api/resume/upload` | Upload resume for matching |

## Data Flow

1. **Scrape** — Scrapers fetch jobs on schedule from multiple sources
2. **Deduplicate** — Hash + fuzzy matching prevents duplicates across sources
3. **Store** — Jobs saved to SQLite with FTS5 indexing
4. **Enrich** — LLM extracts skills, tech stack, scores, flags (every 15min)
5. **Match** — Embedding similarity scores jobs against uploaded resume
6. **Display** — Dashboard shows enriched data with real-time updates via SSE

## Project Structure

```
backend/
  main.py              # FastAPI app entry point
  config.py            # Environment settings
  database.py          # SQLAlchemy async engine + FTS5
  models.py            # ORM: Job, SavedSearch, ScraperRun, UserProfile
  schemas.py           # Pydantic v2 schemas
  scheduler.py         # APScheduler + SSE broadcasting
  scrapers/            # 7 scraper implementations
  enrichment/          # LLM enricher, embeddings, deduplicator
  routers/             # API route handlers

frontend/
  src/
    pages/             # Dashboard, JobBoard, Pipeline, Analytics, Settings
    components/        # Layout, jobs, pipeline, scraper, stats, settings
    api/client.ts      # Typed API client
    store/             # Zustand store
    lib/               # Utils, constants
```

## License

Personal use. Not for distribution.
