# JobRadar — Comprehensive Context Summary

> **Purpose**: This document consolidates all reference materials for the JobRadar project to serve as context for subsequent research on multi-agent build systems.

---

## 1. Complete Tech Stack

### Backend
| Component | Technology | Version/Notes |
|-----------|------------|---------------|
| Runtime | Python 3.12 | FastAPI 0.115+ |
| Framework | FastAPI | Async, high-performance |
| ORM | SQLAlchemy 2.0 | Async mode with `aiosqlite` |
| HTTP Client | httpx 0.27.0 | Async requests |
| HTML Parsing | BeautifulSoup 4.12.3 | Job description parsing |
| Text Processing | html2text 2024.2.26 | HTML → Markdown conversion |
| Fuzzy Matching | rapidfuzz 3.10.0 | Cross-source deduplication |
| Data Processing | pandas 2.2.0 | DataFrame operations |

### Database
| Component | Technology | Notes |
|-----------|------------|-------|
| Primary DB | SQLite | WAL mode for concurrency |
| Full-Text Search | FTS5 | Virtual table with triggers |
| Vector Storage | sqlite-vec 0.1.6 | SIMD-accelerated, 384-dim vectors |

### Scheduler
| Component | Technology | Notes |
|-----------|------------|-------|
| Scheduler | APScheduler 3.10.4 | AsyncIOScheduler |
| Job Store | SQLAlchemyJobStore | Persists to same SQLite DB |
| Triggers | Interval-based | Configurable per-source |

### LLM / AI Enrichment
| Component | Technology | Notes |
|-----------|------------|-------|
| API Provider | **OpenRouter** | OpenAI SDK-compatible via `base_url` |
| Primary Model | `anthropic/claude-3-5-haiku` | Best JSON schema adherence |
| Fallback Model | `openai/gpt-4o-mini` | Lower cost fallback |
| SDK | `openai==1.57.0` | Handles OpenRouter via base_url swap |
| Embeddings | sentence-transformers 3.3.0 | `all-MiniLM-L6-v2` (384-dim) |

**⚠️ CRITICAL**: No local LLM (Ollama) — user explicitly chose OpenRouter API.

### Scrapers
| Source | Type | Auth | Notes |
|--------|------|------|-------|
| **SerpApi** | Google Jobs SERP | API Key | PRIMARY source, aggregates LinkedIn/Indeed/Glassdoor |
| **Greenhouse** | ATS API | None | Free, public JSON API |
| **Lever** | ATS API | None | Free, public JSON API |
| **Ashby** | ATS API | None | Free, includes compensation data |
| **JobSpy** | Multi-board scraper | None | FREE fallback, no API key needed |
| TheirStack | Job data API | Bearer | Optional paid source |
| Apify | Actor platform | API Token | Optional for specialized scraping |

**⚠️ DEAD SERVICE**: ProxyCurl shut down July 4, 2025 — do NOT implement.

### Frontend
| Component | Technology | Version |
|-----------|------------|---------|
| Framework | React | 19.0.0 |
| Build Tool | Vite | 6.0.0 |
| Styling | TailwindCSS | 3.4.0 |
| State (UI) | Zustand | 5.0.0 |
| State (Server) | @tanstack/react-query | 5.0.0 |
| Virtualization | @tanstack/react-virtual | 3.0.0 |
| Drag & Drop | @dnd-kit/core + sortable | 6.0.0 / 8.0.0 |
| Charts | Recharts | 2.13.0 |
| Icons | lucide-react | 0.460.0 |
| Dates | date-fns | 4.0.0 |
| Notifications | react-hot-toast | 2.4.0 |
| HTTP | axios | 1.7.0 |

### Package Management
| Tool | Purpose |
|------|---------|
| uv | Python package management (10-100× faster than pip) |
| pnpm | Frontend package management |
| Makefile | Unified task runner |

---

## 2. Key Architectural Decisions & Constraints

### Core Architecture Principles
1. **Localhost-only** — No deployment, no authentication, no public users
2. **Single SQLite file** — All data in `data/jobradar.db`
3. **No external services** — No Redis, no PostgreSQL, no Docker (until Phase 6)
4. **Real data only** — No mock data, no placeholders, no lorem ipsum
5. **API keys server-side only** — Frontend never holds API keys

### Database Architecture
```sql
-- WAL mode for concurrent reads during scraper writes
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;  -- 64MB cache
```

- **FTS5 virtual table** with triggers for automatic sync
- **sqlite-vec** for vector similarity search (resume matching)
- **Deterministic job_id**: `SHA-256(source:company:title)[:64]`

### Scraper Architecture
- **Adapter pattern**: Abstract `BaseScraper` class with per-source implementations
- **Deduplication**: 3-layer approach:
  1. Exact `job_id` hash match
  2. URL normalization and comparison
  3. Cross-source fuzzy matching (rapidfuzz > 0.92 + same company + 7-day window)
- **Rate limiting**: Per-source delays, exponential backoff on 429/403

### Enrichment Pipeline
- **Batch processing**: APScheduler job every 15 minutes
- **Batch size**: 10 jobs per enrichment run
- **Fallback chain**: claude-3-5-haiku → gpt-4o-mini → mark as `enrichment_failed`
- **Embedding**: Batch in groups of 50, cosine similarity × 100 = `match_score`

### Frontend Architecture
- **Layout**: Fixed 240px sidebar + 56px top bar + scrollable main
- **Job Detail Panel**: 480px slide-in from right (no page navigation)
- **Filter Panel**: 280px collapsible left sidebar
- **Virtualization**: Required for 50K+ job lists
- **Real-time**: SSE for scraper progress updates

---

## 3. Ground Truths from AGENT_OVERRIDES.md

### ❌ Dead Services — Do NOT Build
- **ProxyCurl** — Shut down July 4, 2025 (LinkedIn lawsuit)
- **Ollama / Local LLM** — User chose OpenRouter API instead

### ✅ Critical Additions Not in Research Docs
- **JobSpy** (`python-jobspy==1.1.82`) — Free multi-board scraper, ~2,800 GitHub stars
  - Scrapes LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter concurrently
  - Returns pandas DataFrames — no parsing needed
  - Use as fallback when SerpApi quota exhausted or no API key

### 🤖 LLM Configuration
```python
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "JobRadar"
    }
)
```

### 💰 Corrected Pricing (Feb 2026)
| Model | Input/1M tokens | Output/1M tokens | Cost/job |
|-------|-----------------|------------------|----------|
| claude-3-5-haiku | $0.80 | $4.00 | ~$0.004 |
| gpt-4o-mini | $0.15 | $0.60 | ~$0.0006 |

### ⚖️ Conflict Resolution Priority
1. **AGENT_OVERRIDES.md** — Always wins
2. **research-claude.md** — Architecture, stack, roadmap
3. **research-perplexity.md** — API pricing, rate limits
4. **research-openai.md** — ATS endpoint schemas
5. **CLAUDE.md** — Full build spec (except overrides)
6. **ui-prototype.jsx** — Component patterns (except mock data)

---

## 4. UI Component Structure from Prototype

### Design System (Source of Truth)
```css
:root {
  --bg-base:        #000000;
  --bg-surface:     #0a0a0a;
  --bg-elevated:    #111111;
  --border:         #333333;
  --text-primary:   #EDEDED;
  --text-secondary: #888888;
  --accent:         #0070F3;   /* Vercel blue */
  --accent-green:   #10B981;
  --accent-amber:   #F5A623;
  --accent-red:     #E00000;
  --accent-cyan:    #3291FF;
  --font-ui:        'Geist', -apple-system, sans-serif;
  --font-mono:      'Geist Mono', monospace;
}
```

### Source Badge Colors
```typescript
const SOURCE_COLORS = {
  greenhouse:  'text-emerald-400 border-emerald-400/30 bg-emerald-400/10',
  lever:       'text-violet-400  border-violet-400/30  bg-violet-400/10',
  ashby:       'text-orange-400  border-orange-400/30  bg-orange-400/10',
  serpapi:     'text-red-400     border-red-400/30     bg-red-400/10',
  jobspy:      'text-slate-400   border-slate-400/30   bg-slate-400/10',
  theirstack:  'text-yellow-400  border-yellow-400/30  bg-yellow-400/10',
};
```

### Status Colors
```typescript
const STATUS_COLORS = {
  new:          'text-[var(--accent-green)]',
  saved:        'text-[var(--accent-amber)]',
  applied:      'text-[var(--accent-cyan)]',
  interviewing: 'text-purple-400',
  offer:        'text-pink-400',
  rejected:     'text-[var(--accent-red)]',
  ghosted:      'text-slate-500',
};
```

### Key Components to Carry Forward
| Component | Description |
|-----------|-------------|
| `ScoreRing` | SVG donut chart for match scores (copy verbatim) |
| `JobDetailPanel` | 480px slide-in with status selector, AI tools, flags |
| `ScraperLogDrawer` | Floating bottom-right terminal (600px, collapsible) |
| `KanbanBoard` | 8 columns with dnd-kit drag-and-drop |
| Clearbit logos | With initials fallback on `onError` |
| `glass-panel` | Utility class for blur effects |

### Components to NOT Carry Forward
- `MOCK_JOBS` array — Replace with real API calls
- `callGeminiAPI()` — Replace with `POST /api/copilot` backend endpoint
- Settings page Ollama fields — Replace with OpenRouter fields

### Page Structure
1. **Dashboard** — 4 stat cards + Top Matches list + Source Activity chart + Skills chart
2. **Job Board** — Filter panel (280px) + Job list (virtualized) + Detail panel (480px)
3. **Pipeline** — Kanban with 8 columns (Saved → Ghosted)
4. **Analytics** — 4 chart rows (area, pie, bar, heatmap, funnel)
5. **Settings** — 4 tabs (API Keys, Scraper Config, Resume, Appearance)

---

## 5. Key Insights from Research Documents

### From research-claude.md (Primary Architecture Source)

**Recommended Polling Intervals:**
| Source | Interval | Strategy |
|--------|----------|----------|
| SerpApi (Google Jobs) | 3 hours | Paginate via `next_page_token` |
| Greenhouse API | 6 hours | Compare `updated_at` field |
| Lever API | 6 hours | Full fetch, diff `createdAt` |
| Ashby API | 6 hours | Full fetch, diff `publishedAt` |
| Workday API | 12 hours | Paginate with offset |
| JobSpy fallback | 12 hours | Use `hours_old=12` filter |

**Deduplication Strategy:**
1. URL normalization (strip UTM, trailing slashes, www)
2. Source hash: `SHA-256(source_platform + source_job_id)`
3. Cross-source key: `normalize(company)|normalize(title)|normalize(location)`

**Implementation Phases:**
1. Foundation (Week 1-2): uv + pnpm + Makefile, FastAPI skeleton, SQLite + FTS5, React shell
2. Core Scraping (Week 3-4): SerpApi + ATS scrapers, dedup engine, APScheduler
3. Frontend Dashboard (Week 5-6): TanStack Virtual, filters, kanban, job detail
4. AI Enrichment (Week 7-8): Ollama → OpenRouter, embeddings, resume matching
5. Advanced Sources (Week 9-10): Workday, JobSpy, analytics dashboard
6. Optimization (Week 11-12): Header rotation, circuit breakers, Docker

### From research-perplexity.md (API Pricing & Rate Limits)

**API Cost Comparison (per 1K jobs):**
| Provider | Cost | Notes |
|----------|------|-------|
| SerpApi | $10-25 | Best for Google Jobs aggregation |
| SearchAPI.io | $1-4 | Cheaper SerpApi alternative |
| TheirStack | $3-13 | Direct job data with enrichment |
| Apify actors | $1-5 + compute | Per-actor pricing |
| Bright Data | $0.75-1.50 | Enterprise-grade |
| JobSpy | FREE | No API key required |

**Rate Limits:**
- SerpApi: 20% of monthly quota per hour
- TheirStack: 2 req/sec (free), 4 req/sec (paid)
- Proxycurl: 2-300 req/min depending on plan
- ATS APIs (Greenhouse/Lever/Ashby): No documented limits, poll every 2-4 hours

### From research-openai.md (ATS Endpoint Schemas)

**Greenhouse Job Board API:**
```
GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
```
- No authentication required
- Fields: `id`, `title`, `location.name`, `absolute_url`, `content` (HTML), `updated_at`
- With `?pay_transparency=true`: includes `pay_input_ranges[]`

**Lever Postings API:**
```
GET https://api.lever.co/v0/postings/{company}?mode=json
```
- No authentication required
- Fields: `id`, `text` (title), `categories.location/team/commitment`, `description`, `createdAt`, `salaryRange`

**Ashby Job Postings API:**
```
GET https://api.ashbyhq.com/posting-api/job-board/{job_board_name}?includeCompensation=true
```
- No authentication required
- Fields: `title`, `location`, `department`, `team`, `descriptionHtml`, `publishedAt`, `employmentType`, `compensation`

**Workday (Complex):**
```
POST https://{company}.wd{N}.myworkdayjobs.com/wday/cxs/{company}/{site_path}/jobs
Content-Type: application/json
{ "appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "..." }
```
- URL patterns vary per company (wd1-wd5 datacenters)
- Recommend using Apify actor instead of DIY

---

## 6. Mandated Patterns, Libraries & Approaches

### Required Libraries (requirements.txt)
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.36
aiosqlite==0.20.0
pydantic==2.9.0
apscheduler==3.10.4
httpx==0.27.0
beautifulsoup4==4.12.3
html2text==2024.2.26
sentence-transformers==3.3.0
rapidfuzz==3.10.0
python-dotenv==1.0.1
aiofiles==24.1.0
openai==1.57.0
python-jobspy==1.1.82
sqlite-vec==0.1.6
python-multipart==0.0.17
pandas==2.2.0
```

**NOT included:** `ollama` (user chose OpenRouter)

### Required Frontend Dependencies (package.json)
```json
{
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@tanstack/react-query": "^5.0.0",
    "@tanstack/react-virtual": "^3.0.0",
    "@dnd-kit/core": "^6.0.0",
    "@dnd-kit/sortable": "^8.0.0",
    "zustand": "^5.0.0",
    "axios": "^1.7.0",
    "recharts": "^2.13.0",
    "react-hot-toast": "^2.4.0",
    "lucide-react": "^0.460.0",
    "date-fns": "^4.0.0"
  }
}
```

### Required .env Variables
```bash
# Scraping APIs
SERPAPI_KEY=                    # Required
THEIRSTACK_KEY=                 # Optional
APIFY_KEY=                      # Optional

# LLM Enrichment via OpenRouter
OPENROUTER_API_KEY=             # Required
OPENROUTER_PRIMARY_MODEL=anthropic/claude-3-5-haiku
OPENROUTER_FALLBACK_MODEL=openai/gpt-4o-mini

# App Config
DATABASE_URL=sqlite+aiosqlite:///./data/jobradar.db
BACKEND_PORT=8000
FRONTEND_PORT=5173
LOG_LEVEL=INFO
```

**NOT included:** `PROXYCURL_KEY`, `OLLAMA_*`

### Mandated Patterns

1. **Scraper Base Class:**
```python
class BaseScraper(ABC):
    source_name: str
    rate_limit_delay: float

    @abstractmethod
    async def fetch_jobs(self, query: str, location: str, limit: int) -> list[dict]: ...
    
    def compute_job_id(self, source: str, company: str, title: str) -> str:
        key = f"{source}:{company.lower().strip()}:{title.lower().strip()}"
        return hashlib.sha256(key.encode()).hexdigest()[:64]
```

2. **OpenRouter Client Setup:**
```python
client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "JobRadar"
    }
)
```

3. **Enrichment Prompt Pattern:**
```python
ENRICHMENT_PROMPT = """
Analyze this job posting and return ONLY valid JSON with these exact keys:
{
  "skills_required": [...],
  "skills_nice_to_have": [...],
  "tech_stack": [...],
  "experience_level": "entry|mid|senior|exec",
  "job_type": "full-time|part-time|contract|internship",
  "remote_type": "remote|hybrid|onsite",
  "seniority_score": 0-100,
  "remote_score": 0-100,
  "summary_ai": "2-3 sentence summary",
  "red_flags": ["max 3"],
  "green_flags": ["max 3"]
}
"""
```

4. **APScheduler Configuration:**
```python
scheduler = AsyncIOScheduler(
    jobstores={"default": SQLAlchemyJobStore(url="sqlite:///./data/jobradar.db")}
)

scheduler.add_job(run_scraper, 'interval', hours=6,   args=['serpapi'],     id='serpapi_scrape')
scheduler.add_job(run_scraper, 'interval', hours=3,   args=['greenhouse'],  id='greenhouse_scrape')
scheduler.add_job(run_scraper, 'interval', hours=3,   args=['lever'],       id='lever_scrape')
scheduler.add_job(run_scraper, 'interval', hours=3,   args=['ashby'],       id='ashby_scrape')
scheduler.add_job(run_scraper, 'interval', hours=12,  args=['jobspy'],      id='jobspy_scrape')
scheduler.add_job(run_enrichment_batch, 'interval', minutes=15,             id='enrichment_batch')
```

5. **AI Copilot Backend Pattern:**
```python
@router.post("/api/copilot")
async def copilot(request: CopilotRequest):
    # CopilotRequest: { tool: "coverLetter"|"interviewPrep"|"gapAnalysis", job_id: str }
    # Build prompt based on tool type, call OpenRouter, stream response back
```

---

## 7. Project Directory Structure

```
jobradar/
├── AGENT_OVERRIDES.md
├── CLAUDE.md
├── research-claude.md
├── research-perplexity.md
├── research-openai.md
├── ui-prototype.jsx
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── scheduler.py
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── serpapi_scraper.py
│   │   ├── greenhouse_scraper.py
│   │   ├── lever_scraper.py
│   │   ├── ashby_scraper.py
│   │   ├── jobspy_scraper.py
│   │   ├── theirstack_scraper.py
│   │   └── apify_scraper.py
│   ├── enrichment/
│   │   ├── __init__.py
│   │   ├── llm_enricher.py
│   │   ├── embedding.py
│   │   └── deduplicator.py
│   ├── routers/
│   │   ├── jobs.py
│   │   ├── scraper.py
│   │   ├── search.py
│   │   ├── stats.py
│   │   ├── copilot.py
│   │   └── settings.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/client.ts
│   │   ├── store/useJobStore.ts
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   ├── jobs/
│   │   │   ├── pipeline/
│   │   │   ├── scraper/
│   │   │   ├── stats/
│   │   │   └── settings/
│   │   ├── pages/
│   │   └── lib/
│   └── package.json
├── data/
│   └── jobradar.db
├── .env.example
├── .env
├── Makefile
└── README.md
```

---

## 8. Execution Directive

> "Do not build a demo. Do not build a prototype. Build the real tool — the one you would actually use every day to hunt for jobs. Every scraper must fetch real data. Every chart must render real numbers. Every filter must actually filter. Every AI enrichment must actually call OpenRouter and return structured results. Eradicate all placeholder text, lorem ipsum, and hardcoded fake data. This is a personal intelligence system. Build it like one."

---

*Document generated: March 1, 2026*
*For use as context in multi-agent build system research*
