# JobRadar — Personal Job Intelligence System
# CLAUDE.md — Coding Agent Build Prompt

---

## CRITICAL: READ THIS FIRST

The research phase is **already complete**. Do NOT conduct your own research.
Do NOT write a new RESEARCH.md. Read the provided files in this order before
writing any code:

1. `AGENT_OVERRIDES.md` — ground truths, takes precedence over everything
2. `research-claude.md` — primary architecture source
3. `research-perplexity.md` — API pricing and rate limits
4. `research-openai.md` — ATS endpoint schemas
5. `ui-prototype.jsx` — component patterns and design reference

**Start at Step 1 of the Agent Flow below. Skip research entirely.**

---

## Application: "JobRadar" — Personal Job Intelligence System

### Core Purpose

A locally-run, full-stack web application that:
1. Scrapes jobs from multiple sources on a configurable schedule
2. Deduplicates, normalizes, and stores them in a local SQLite database
3. Enriches each job with AI-generated metadata via OpenRouter API
4. Presents them in a polished dark dashboard UI
5. Tracks application status in a drag-and-drop kanban pipeline

Runs exclusively on localhost. No deployment. No authentication. No public users.
Do not prototype. Do not scaffold placeholders. Build the real tool.

---

## Agent Flow — STRICT ORDER

1. Read all 5 files listed above before writing any code
2. Create full project directory structure
3. Write `requirements.txt` and `package.json`
4. Build `database.py`, `models.py`, `schemas.py`
5. Build all scraper classes: base → serpapi → greenhouse → lever → ashby → jobspy → theirstack → apify
6. Build enrichment pipeline: llm_enricher → embedding → deduplicator
7. Build scheduler
8. Build all FastAPI routers + SSE endpoint
9. Build FastAPI `main.py`
10. Build frontend: design system → layout shell → Zustand + React Query + API client
11. Build Dashboard page
12. Build Job Board page
13. Build Pipeline page
14. Build Analytics page
15. Build Settings page
16. Build Scraper Log drawer
17. Wire all backend ↔ frontend integrations
18. Write `README.md`

---

## Project Structure

```
jobradar/
├── AGENT_OVERRIDES.md
├── CLAUDE.md
├── research-claude.md
├── research-perplexity.md
├── research-openai.md
├── ui-prototype.jsx
├── backend/
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # All env vars loaded from .env
│   ├── database.py               # SQLAlchemy async engine, session, Base
│   ├── models.py                 # ORM models: Job, SavedSearch, ScraperRun, UserProfile
│   ├── schemas.py                # Pydantic v2 schemas
│   ├── scheduler.py              # APScheduler setup + job registration
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py               # Abstract BaseScraper
│   │   ├── serpapi_scraper.py    # Google Jobs via SerpApi (PRIMARY)
│   │   ├── greenhouse_scraper.py # Free public ATS JSON API
│   │   ├── lever_scraper.py      # Free public ATS JSON API
│   │   ├── ashby_scraper.py      # Free public ATS JSON API
│   │   ├── jobspy_scraper.py     # Free multi-board fallback (replaces ProxyCurl)
│   │   ├── theirstack_scraper.py # Optional paid job feed
│   │   └── apify_scraper.py      # Optional Apify actor wrapper
│   ├── enrichment/
│   │   ├── __init__.py
│   │   ├── llm_enricher.py       # OpenRouter claude-3-5-haiku / gpt-4o-mini
│   │   ├── embedding.py          # sentence-transformers resume similarity
│   │   └── deduplicator.py       # Hash-based + rapidfuzz cross-source dedup
│   ├── routers/
│   │   ├── jobs.py               # GET/PATCH /api/jobs
│   │   ├── scraper.py            # POST /api/scraper/run, GET /api/scraper/status
│   │   ├── search.py             # GET /api/search/semantic
│   │   ├── stats.py              # GET /api/stats
│   │   ├── copilot.py            # POST /api/copilot (OpenRouter proxy for frontend)
│   │   └── settings.py           # GET/POST /api/settings, POST /api/resume/upload
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   └── client.ts
│   │   ├── store/
│   │   │   └── useJobStore.ts
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── TopBar.tsx
│   │   │   │   └── Layout.tsx
│   │   │   ├── jobs/
│   │   │   │   ├── JobCard.tsx
│   │   │   │   ├── JobList.tsx           # Virtualized — @tanstack/react-virtual
│   │   │   │   ├── JobDetailPanel.tsx    # 480px slide-in
│   │   │   │   ├── JobFilters.tsx        # 280px collapsible sidebar
│   │   │   │   ├── JobStatusBadge.tsx
│   │   │   │   └── ScoreRing.tsx         # SVG donut — copy from ui-prototype.jsx
│   │   │   ├── pipeline/
│   │   │   │   ├── KanbanBoard.tsx
│   │   │   │   └── KanbanCard.tsx
│   │   │   ├── scraper/
│   │   │   │   ├── ScraperControlPanel.tsx
│   │   │   │   └── ScraperLog.tsx        # SSE terminal drawer
│   │   │   ├── stats/
│   │   │   │   ├── StatsOverview.tsx
│   │   │   │   └── SourceBreakdownChart.tsx
│   │   │   └── settings/
│   │   │       ├── SettingsPage.tsx
│   │   │       └── ResumeUpload.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── JobBoard.tsx
│   │   │   ├── Pipeline.tsx
│   │   │   ├── Analytics.tsx
│   │   │   └── Settings.tsx
│   │   └── lib/
│   │       ├── utils.ts
│   │       └── constants.ts
│   └── package.json
├── data/
│   └── jobradar.db
├── .env.example
├── .env
├── Makefile
└── README.md
```

---

## Design System (FROM AGENT_OVERRIDES.md — THIS OVERRIDES ANYTHING BELOW)

```css
/* index.css — copy StyleSystem from ui-prototype.jsx verbatim */
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap');

:root {
  --bg-base:        #000000;
  --bg-surface:     #0a0a0a;
  --bg-elevated:    #111111;
  --border:         #333333;
  --text-primary:   #EDEDED;
  --text-secondary: #888888;
  --accent:         #0070F3;
  --accent-green:   #10B981;
  --accent-amber:   #F5A623;
  --accent-red:     #E00000;
  --accent-cyan:    #3291FF;
  --font-ui:        'Geist', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono:      'Geist Mono', monospace;
}

body {
  background: var(--bg-base);
  color: var(--text-primary);
  font-family: var(--font-ui);
  margin: 0;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
}

/* Noise overlay — eliminates flat void feel */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image: url("data:image/svg+xml,..."); /* feTurbulence at 0.03 opacity */
  pointer-events: none;
  z-index: 9999;
  opacity: 0.03;
}

/* Thin custom scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-secondary); }

.font-mono { font-family: var(--font-mono); }
.glass-panel { background: rgba(10,10,10,0.7); backdrop-filter: blur(12px); border-top: 1px solid var(--border); }
```

**Spacing:** 8px base grid. Radii: `rounded-lg` (8px) cards, `rounded-xl` (12px) panels,
`rounded-full` badges.

**Source badge colors (Tailwind classes):**
```ts
const SOURCE_COLORS = {
  greenhouse:  'text-emerald-400 border-emerald-400/30 bg-emerald-400/10',
  lever:       'text-violet-400  border-violet-400/30  bg-violet-400/10',
  ashby:       'text-orange-400  border-orange-400/30  bg-orange-400/10',
  serpapi:     'text-red-400     border-red-400/30     bg-red-400/10',
  jobspy:      'text-slate-400   border-slate-400/30   bg-slate-400/10',
  theirstack:  'text-yellow-400  border-yellow-400/30  bg-yellow-400/10',
}
```

**Status colors:**
```ts
const STATUS_COLORS = {
  new:          'text-[var(--accent-green)]',
  saved:        'text-[var(--accent-amber)]',
  applied:      'text-[var(--accent-cyan)]',
  interviewing: 'text-purple-400',
  offer:        'text-pink-400',
  rejected:     'text-[var(--accent-red)]',
  ghosted:      'text-slate-500',
}
```

---

## Backend Specification

### Database Models (SQLAlchemy 2.0 async)

**Job model:**
```python
class Job(Base):
    __tablename__ = "jobs"

    # Identity
    job_id: Mapped[str]           = mapped_column(String(64), primary_key=True)
    source: Mapped[str]           = mapped_column(String(32))
    url: Mapped[str]              = mapped_column(Text)
    posted_at: Mapped[datetime | None]
    scraped_at: Mapped[datetime]  = mapped_column(default=func.now())
    is_active: Mapped[bool]       = mapped_column(default=True)
    duplicate_of: Mapped[str | None] = mapped_column(ForeignKey("jobs.job_id"))

    # Company
    company_name: Mapped[str]
    company_domain: Mapped[str | None]
    company_logo_url: Mapped[str | None]

    # Role
    title: Mapped[str]
    location_city: Mapped[str | None]
    location_state: Mapped[str | None]
    location_country: Mapped[str | None]
    remote_type: Mapped[str | None]      # remote/hybrid/onsite/unknown
    job_type: Mapped[str | None]         # full-time/part-time/contract/internship
    experience_level: Mapped[str | None] # entry/mid/senior/exec
    department: Mapped[str | None]
    industry: Mapped[str | None]

    # Compensation
    salary_min: Mapped[float | None]
    salary_max: Mapped[float | None]
    salary_currency: Mapped[str | None]  = mapped_column(default="USD")
    salary_period: Mapped[str | None]    # hourly/annual

    # Content
    description_raw: Mapped[str | None]      = mapped_column(Text)
    description_clean: Mapped[str | None]    = mapped_column(Text)
    description_markdown: Mapped[str | None] = mapped_column(Text)

    # AI Enrichment (populated async after insert)
    skills_required: Mapped[list | None]     = mapped_column(JSON)
    skills_nice_to_have: Mapped[list | None] = mapped_column(JSON)
    tech_stack: Mapped[list | None]          = mapped_column(JSON)
    seniority_score: Mapped[float | None]
    remote_score: Mapped[float | None]
    match_score: Mapped[float | None]
    summary_ai: Mapped[str | None]           = mapped_column(Text)
    red_flags: Mapped[list | None]           = mapped_column(JSON)
    green_flags: Mapped[list | None]         = mapped_column(JSON)
    is_enriched: Mapped[bool]                = mapped_column(default=False)
    enriched_at: Mapped[datetime | None]

    # User State
    status: Mapped[str]   = mapped_column(default="new")
    notes: Mapped[str | None] = mapped_column(Text)
    applied_at: Mapped[datetime | None]
    last_updated: Mapped[datetime] = mapped_column(onupdate=func.now())
    is_starred: Mapped[bool] = mapped_column(default=False)
    tags: Mapped[list | None] = mapped_column(JSON)
```

**FTS5 shadow table** (run on DB init):
```sql
CREATE VIRTUAL TABLE IF NOT EXISTS jobs_fts USING fts5(
    job_id UNINDEXED,
    title,
    company_name,
    description_clean,
    skills_required,
    tech_stack,
    content='jobs',
    content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS jobs_fts_insert AFTER INSERT ON jobs BEGIN
    INSERT INTO jobs_fts(job_id, title, company_name, description_clean, skills_required, tech_stack)
    VALUES (new.job_id, new.title, new.company_name, new.description_clean,
            new.skills_required, new.tech_stack);
END;

CREATE TRIGGER IF NOT EXISTS jobs_fts_update AFTER UPDATE ON jobs BEGIN
    DELETE FROM jobs_fts WHERE job_id = old.job_id;
    INSERT INTO jobs_fts(job_id, title, company_name, description_clean, skills_required, tech_stack)
    VALUES (new.job_id, new.title, new.company_name, new.description_clean,
            new.skills_required, new.tech_stack);
END;

CREATE TRIGGER IF NOT EXISTS jobs_fts_delete AFTER DELETE ON jobs BEGIN
    DELETE FROM jobs_fts WHERE job_id = old.job_id;
END;
```

**SavedSearch model:**
`id, name, query_params (JSON), alert_enabled (bool), created_at`

**ScraperRun model:**
`id, source, started_at, completed_at, jobs_found, jobs_new, jobs_updated,
error_message, status (running/completed/failed)`

**UserProfile model (singleton, id=1):**
`resume_filename, resume_text, resume_uploaded_at,
default_queries (JSON), default_locations (JSON), company_watchlist (JSON)`

---

### Scraper Implementation

```python
class BaseScraper(ABC):
    source_name: str
    rate_limit_delay: float

    @abstractmethod
    async def fetch_jobs(self, query: str, location: str, limit: int) -> list[dict]: ...
    def normalize(self, raw: dict) -> dict: ...
    def compute_job_id(self, source: str, company: str, title: str) -> str:
        import hashlib
        key = f"{source}:{company.lower().strip()}:{title.lower().strip()}"
        return hashlib.sha256(key.encode()).hexdigest()[:64]
```

**SerpApiScraper:**
`GET https://serpapi.com/search.json`
Params: `engine=google_jobs`, `q`, `location`, `hl=en`, `gl=us`
Paginate: `start=0,10,20,...` until empty or limit hit.
Parse `jobs_results[]` → map `title`, `company_name`, `location`, `via` (source hint),
`detected_extensions` (salary, schedule), `apply_options[0].link` (url).
Rate: 1s delay between pages, respect 20% hourly SerpApi cap.

**GreenhouseScraper:**
`GET https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true`
No auth. Parse `jobs[]`.
Fields: `id`, `title`, `location.name`, `absolute_url`, `content` (HTML), `updated_at`.
Poll: every 3h per slug from `company_watchlist`.

**LeverScraper:**
`GET https://api.lever.co/v0/postings/{slug}?mode=json`
Parse root array.
Fields: `id`, `text` (title), `hostedUrl`, `categories.location`, `categories.team`,
`descriptionPlain`, `description` (HTML), `createdAt` (epoch ms).

**AshbyScraper:**
`GET https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true`
Parse `jobPostings[]`.
Fields: `id`, `title`, `teamName`, `locationName`, `employmentType`,
`descriptionHtml`, `applicationLink`, `compensation.summaryComponents`.

**JobSpyScraper (free, no auth — replaces ProxyCurl):**
```python
from jobspy import scrape_jobs

async def fetch_jobs(self, query: str, location: str, limit: int) -> list[dict]:
    import asyncio
    loop = asyncio.get_event_loop()
    df = await loop.run_in_executor(None, lambda: scrape_jobs(
        site_name=["linkedin", "indeed", "glassdoor", "google", "zip_recruiter"],
        search_term=query,
        location=location,
        results_wanted=limit,
        hours_old=72,
        country_indeed="USA"
    ))
    return df.to_dict('records')
```

**TheirStackScraper:**
`GET https://api.theirstack.com/v1/jobs/search`
Bearer auth. Params: `q, location, date_posted_after, limit`. Paginate.
Rate: 2 req/sec free, 4 req/sec paid.

---

### Enrichment Pipeline

**LLM Enricher (`llm_enricher.py`):**

OpenRouter via OpenAI SDK — see AGENT_OVERRIDES.md for client setup.
Runs as APScheduler job every 15 minutes, processes unenriched jobs in batches of 10.

```python
PRIMARY_MODEL  = "anthropic/claude-3-5-haiku"
FALLBACK_MODEL = "openai/gpt-4o-mini"

ENRICHMENT_PROMPT = """
Analyze this job posting and return ONLY valid JSON with these exact keys:
{
  "skills_required":     ["skill1", ...],
  "skills_nice_to_have": ["skill1", ...],
  "tech_stack":          ["Python", "AWS", ...],
  "experience_level":    "entry|mid|senior|exec",
  "job_type":            "full-time|part-time|contract|internship",
  "remote_type":         "remote|hybrid|onsite",
  "seniority_score":     0-100,
  "remote_score":        0-100,
  "summary_ai":          "2-3 sentence plain English summary",
  "red_flags":           ["max 3 strings"],
  "green_flags":         ["max 3 strings"]
}

Job Title: {title}
Company: {company_name}
Description: {description_clean[:3000]}
"""
```

Call pattern:
```python
response = await client.chat.completions.create(
    model=PRIMARY_MODEL,
    response_format={"type": "json_object"},
    messages=[
        {"role": "system", "content": "Return ONLY valid JSON. No commentary."},
        {"role": "user",   "content": ENRICHMENT_PROMPT.format(**job)}
    ],
    temperature=0.1,
    max_tokens=1000
)
```

On failure, retry once with FALLBACK_MODEL before marking job as `enrichment_failed`.

**AI Copilot Endpoint (`routers/copilot.py`):**

The frontend's AI Copilot Tools (cover letter, interview prep, gap analysis) call
`POST /api/copilot` — never directly to OpenRouter. This keeps the API key server-side.

```python
@router.post("/api/copilot")
async def copilot(request: CopilotRequest):
    # CopilotRequest: { tool: "coverLetter"|"interviewPrep"|"gapAnalysis", job_id: str }
    # Build prompt based on tool type, call OpenRouter, stream response back
    ...
```

**Embedding Matcher (`embedding.py`):**
- Model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, CPU-fast)
- On startup: if resume exists, embed and cache
- Per job: embed `f"{title}. {' '.join(skills_required or [])}. {description_clean[:500]}"`
- Cosine similarity vs resume → × 100 → `match_score`
- Batch in groups of 50. Store in sqlite-vec.

**Deduplicator (`deduplicator.py`):**
- Primary: exact `job_id` hash match
- Cross-source: same `company_domain` + `rapidfuzz.ratio(title_a, title_b) > 0.92`
  + posted within 7 days → mark newer as `duplicate_of = older_job_id`
- Run before insert, not as a separate pass
- UI shows "Also on X other boards" badge on primary record

---

### Scheduler

```python
scheduler = AsyncIOScheduler(
    jobstores={"default": SQLAlchemyJobStore(url="sqlite:///./data/jobradar.db")}
)

scheduler.add_job(run_scraper, 'interval', hours=6,   args=['serpapi'],     id='serpapi_scrape',     replace_existing=True)
scheduler.add_job(run_scraper, 'interval', hours=3,   args=['greenhouse'],  id='greenhouse_scrape',  replace_existing=True)
scheduler.add_job(run_scraper, 'interval', hours=3,   args=['lever'],       id='lever_scrape',       replace_existing=True)
scheduler.add_job(run_scraper, 'interval', hours=3,   args=['ashby'],       id='ashby_scrape',       replace_existing=True)
scheduler.add_job(run_scraper, 'interval', hours=12,  args=['jobspy'],      id='jobspy_scrape',      replace_existing=True)
scheduler.add_job(run_enrichment_batch, 'interval', minutes=15,             id='enrichment_batch',   replace_existing=True)
```

All intervals user-configurable via `/api/settings`.

---

### API Routes

```
GET   /api/jobs
      ?page=1&limit=50&q=&location=&source=&status=&experience_level=
      &remote_type=&posted_within_days=&min_match_score=&min_salary=
      &tech_stack=&company=&sort_by=match_score|posted_at|scraped_at&sort_dir=desc

GET   /api/jobs/{job_id}

PATCH /api/jobs/{job_id}
      Body: { status?, notes?, tags?, is_starred? }

GET   /api/search/semantic?q=&limit=20

POST  /api/scraper/run
      Body: { source: "all"|"serpapi"|"greenhouse"|"lever"|"ashby"|"jobspy" }

GET   /api/scraper/status
GET   /api/scraper/stream          # SSE: data: {"event":"job_found","source":"serpapi","count":5,"new":3}

GET   /api/stats
      # total_jobs, new_today, by_source{}, by_status{}, by_experience_level{},
      # top_companies[], top_skills[], jobs_over_time[] (30d), avg_match_score

POST  /api/copilot
      Body: { tool: "coverLetter"|"interviewPrep"|"gapAnalysis", job_id: str }
      # Calls OpenRouter server-side, streams response

GET   /api/settings
POST  /api/settings

POST  /api/resume/upload           # Multipart PDF/TXT → parse → embed → re-score all

GET   /api/saved-searches
POST  /api/saved-searches
DELETE /api/saved-searches/{id}
```

CORS: `http://localhost:5173`. All errors: `{"error": "message", "detail": "..."}`.

---

## Frontend Specification

### Layout Shell

Fixed sidebar (240px) + scrollable main. Top bar (56px):

- Left: "JobRadar" wordmark + pulsing `--accent` dot (animates while any scraper running)
  + live job count in `Geist Mono` (updates via SSE)
- Right: scraper status pill (green "Live" / amber "Scheduled" / gray "Idle")
  + resume indicator ("Resume: Active" with green dot)

Sidebar nav: Dashboard · Job Board · Pipeline · Analytics · Settings
Sidebar bottom: `v0.1.0` + "Local Only 🔒" badge

---

### Page 1: Dashboard

**4 stat cards (Geist Mono numbers):**
- Total Jobs (with 7-day sparkline)
- New Today (--accent-green, Δ vs yesterday)
- Applied (--accent-cyan, success rate %)
- Avg Match Score (--accent, small histogram)

**Two-column below (60/40):**

Left — "Top Matches": top 10 by `match_score DESC, posted_at DESC`.
Each row: Clearbit logo (fallback: initials div), title, company, location,
source badge, ScoreRing, time-ago (Geist Mono).

Right — stacked:
1. "Source Activity (7d)" — Recharts `BarChart`, jobs per source per day
2. "Top Skills in Market" — Recharts `BarChart` horizontal, top 15 skills
3. "Last Scraper Runs" — table: `source | found | new | duration | status`

---

### Page 2: Job Board

**Filter Panel (280px collapsible left):**
All filters sync to URL query params.
- Full-text search (debounced 300ms → `/api/jobs?q=`)
- Source checkboxes (Greenhouse / Lever / Ashby / Google Jobs / JobSpy)
- Experience level pills (Entry / Mid / Senior / Exec)
- Remote type pills (Remote / Hybrid / On-site)
- Posted within (Today / 3d / 7d / 14d / 30d)
- Match score range slider (only if resume active)
- Salary range slider (only for jobs with salary data)
- Company typeahead
- Tech stack multi-select typeahead
- "Save this Search" → POST `/api/saved-searches`

**Job List:**
Toggle list ↔ grid (2-col on large screens).
`@tanstack/react-virtual` — handles 50K+ items.

Each card:
- Clearbit logo + company + time-ago (Geist Mono)
- Title (bold)
- Location pill + Remote badge
- Source badge (color-coded per SOURCE_COLORS)
- ScoreRing (only if resume active)
- Top 3 tech_stack pills (--accent colored)
- Status dot + label
- Star toggle
- Hover: quick actions "Save" / "Mark Applied" / "Open ↗"

**Job Detail Panel (480px, slides in from right, no page navigation):**
Copy structure from `ui-prototype.jsx` JobDetailPanel verbatim, then:
- Replace mock data with real job from API
- Status selector → PATCH `/api/jobs/{id}`
- Notes textarea → auto-save on blur
- Tags input
- AI Copilot Tools (cover letter / interview prep / gap analysis)
  → call `POST /api/copilot` (NOT callGeminiAPI — that was prototype only)
- ScoreRing (size=64) + match explanation
- AI Summary card with green/red flags
- Full description rendered from `description_markdown`
- Apply button → opens url + sets status to applied
- Source metadata footer (Geist Mono)

---

### Page 3: Pipeline (Kanban)

`@dnd-kit/core` + `@dnd-kit/sortable`.

Columns: Saved → Applied → Phone Screen → Interview → Final Round → Offer → Rejected → Ghosted

Each column: header + count badge, scrollable card list, dashed empty state.
Each card: Clearbit logo, title, company, applied_at (Geist Mono), ScoreRing small,
"Add Note" inline textarea.

Drag → optimistic update → PATCH `/api/jobs/{id}` with new status → revert on error.

---

### Page 4: Analytics

**Row 1:** Recharts `AreaChart` — jobs per day last 30 days, stacked by source.

**Row 2 (2-col):**
- Left: Recharts `PieChart` — by experience level
- Right: Recharts `BarChart` horizontal — top 20 companies

**Row 3:** Skills Heatmap — grid: rows = top 30 skills, cols = last 4 weeks.
Cell color = `rgba(0, 112, 243, opacity)` where opacity scales with job count.

**Row 4:** Application Funnel — Recharts showing Saved → Applied → Phone Screen
→ Interview → Offer with conversion rates between each stage.

---

### Page 5: Settings

Tabs: API Keys | Scraper Config | Resume | Appearance

**API Keys tab:**
Password inputs with show/hide toggle, masked display, per-key "Test" button.

Fields:
```
SerpApi Key              (required — Google Jobs)
TheirStack Key           (optional)
Apify Key                (optional)
OpenRouter API Key       (required — LLM enrichment)
OpenRouter Primary Model (default: anthropic/claude-3-5-haiku)
OpenRouter Fallback Model(default: openai/gpt-4o-mini)
```

Note: JobSpy requires no key. Do NOT show Ollama fields.

**Scraper Config tab:**
- Per-source enable/disable + interval selector (1/3/6/12/24h)
- Default search queries (multi-input, pre-fill: "AI Engineer", "ML Engineer", "Data Scientist")
- Target locations (multi-input, pre-fill: "Remote", "New York, NY")
- Company watchlist textarea (one Greenhouse/Lever/Ashby slug per line)
- Max jobs per run slider (50–500)
- "Run All Scrapers Now" button

**Resume tab:** (copy from `ui-prototype.jsx` ResumeUpload structure)
- Drag-and-drop zone (PDF/TXT, max 5MB)
- Status: filename, upload date, embedding status
- "Re-Embed Resume" button
- Parsed text preview (collapsible)

---

### Scraper Log Drawer

Floating bottom-right, 600px wide, collapsible (200px expanded / 40px collapsed).
Copy expand/collapse behavior from `ui-prototype.jsx` `ScraperLogDrawer` verbatim.

Terminal format:
```
[14:23:01] serpapi      → Found 47 jobs for "AI Engineer" in "Remote"
[14:23:04] serpapi      → 12 new · 35 existing · 0 errors
[14:23:04] greenhouse   → Scanning 28 company boards...
[14:23:09] greenhouse   → openai: 3 new · anthropic: 1 new · stripe: 0 new
```

Colors: `--text-secondary` for existing, `--accent-green` for new, `--accent-red` for errors.
Auto-scrolls to bottom unless user has manually scrolled up. Pause button to freeze.
Connects to `GET /api/scraper/stream` SSE endpoint.

---

## Technical Requirements (LOCKED)

### `requirements.txt`

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

No `ollama`. The `openai` package handles OpenRouter via `base_url`.

### `package.json` dependencies

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
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "vite": "^6.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0"
  }
}
```

### `.env.example`

```bash
# Scraping APIs
SERPAPI_KEY=                         # Required — get at serpapi.com
THEIRSTACK_KEY=                      # Optional
APIFY_KEY=                           # Optional
SCRAPINGBEE_KEY=                     # Optional fallback

# LLM Enrichment via OpenRouter (openrouter.ai/keys)
OPENROUTER_API_KEY=                  # Required
OPENROUTER_PRIMARY_MODEL=anthropic/claude-3-5-haiku
OPENROUTER_FALLBACK_MODEL=openai/gpt-4o-mini

# App Config
DATABASE_URL=sqlite+aiosqlite:///./data/jobradar.db
BACKEND_PORT=8000
FRONTEND_PORT=5173
LOG_LEVEL=INFO
```

No `PROXYCURL_KEY`. No `OLLAMA_*`.

### `Makefile`

```makefile
install:
	uv sync
	cd frontend && pnpm install

dev:
	uvicorn backend.main:app --reload --port 8000 &
	cd frontend && pnpm dev

reset:
	rm -f data/jobradar.db
	make dev
```

---

## Implementation Phases

**Phase 1 — Foundation**
uv + pnpm + Makefile. FastAPI skeleton. SQLAlchemy async models. SQLite WAL + FTS5.
React + Vite + Tailwind shell with design system. Settings page. SSE wired.
✓ Empty dashboard connects to backend.

**Phase 2 — Core Scraping**
SerpApi + Greenhouse + Lever + Ashby + JobSpy scrapers. Dedup engine. APScheduler.
Scraper status dashboard.
✓ Automated scraping on schedule, deduped storage.

**Phase 3 — Frontend**
Job list (TanStack Virtual). Filter panel. Job detail panel (from prototype).
Kanban (dnd-kit). FTS search. Sort controls. Scraper log drawer.
✓ Full browsing, filtering, application tracking.

**Phase 4 — AI Enrichment**
OpenRouter enrichment pipeline. APScheduler batch job. Embeddings + sqlite-vec.
Resume upload + re-embedding. Match scoring. AI Copilot backend endpoint.
✓ Every job enriched within 15min. Copilot tools live in detail panel.

**Phase 5 — Analytics + Polish**
All 4 Analytics chart rows (Recharts). Skills heatmap. Application funnel.
Clearbit logos. Saved searches. CSV/JSON export. Noise texture overlay.
✓ Full analytics + polished UI.

**Phase 6 — Extended Sources (Optional)**
TheirStack integration. Apify actor wrapper. Docker Compose.
✓ Extended coverage + portability.

---

## Execution Directive

"Do not build a demo. Do not build a prototype. Build the real tool — the one you
would actually use every day to hunt for jobs. Every scraper must fetch real data.
Every chart must render real numbers. Every filter must actually filter. Every AI
enrichment must actually call OpenRouter and return structured results. Eradicate
all placeholder text, lorem ipsum, and hardcoded fake data. This is a personal
intelligence system. Build it like one."