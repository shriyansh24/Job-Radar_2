# JobRadar V2 — Project Status & Roadmap

> **Single source of truth across all sessions. Read this file first in every new session.**
> Last updated: March 20, 2026

---

## Current State

### What's Working
- Login/Auth system (JWT + refresh tokens)
- Dashboard showing **135 real scraped ML/DS jobs** with KPI cards
- Job Board displaying jobs with salary ranges, locations, badges
- Full sidebar navigation (16 pages, including new Targets page)
- Profile seeded with user data (Shriyansh Singh, ML Engineer, OPT, Austin TX)
- Resume uploaded (Shriyansh__Sing__Resume.pdf)
- PostgreSQL database with pgvector extension
- Redis/Memurai for caching
- **Scraper platform fully operational** (see details below)
- All v1 NLP/LLM features ported: 3-stage resume tailoring, gap analysis, council evaluation, interview prep, salary research, cover letter generation, copilot chat
- Code decomposition done: resume (658->183), interview (454->200), copilot (223->187), pipeline (182->163)
- **Frontend performance optimized**: staleTime 5min, gcTime 10min, prefetch on nav hover, lazy-loaded recharts, keepPreviousData pagination

### Scraper Platform (NEW — completed 2026-03-19)
- **Database:** `scrape_targets` table (replaces career_pages), `scrape_attempts` table for telemetry, Job lifecycle columns (first_seen_at, last_seen_at, disappeared_at, seen_count)
- **Control plane:** ATS registry (8 vendors auto-detected), URL classifier, priority scorer, scoring-based scheduler, tier router with execution plans
- **Execution plane:** 3 abstract ports (FetcherPort, BrowserPort, ExtractorPort), 5 adapter implementations (Cloudscraper, Scrapling dual-mode, Nodriver reusable, Camoufox, SeleniumBase UC), browser pool with tier-separated semaphores, escalation engine (7 trigger conditions)
- **New scrapers:** Workday ATS scraper (JSON API), Crawl4AI markdown extractor
- **Integration:** AdapterRegistry mapping scraper_name strings to adapters, `run_target_batch()` orchestration loop in ScrapingService, 2 new scheduler jobs (career_page 30min, watchlist 2hr)
- **CLI ops tool:** `targets import/list`, `quarantine list/review/release`, `health`, `test-fetch`
- **Testing:** 179 unit tests + 67 contract tests + ATS fixture files (Greenhouse, Lever, Ashby live + Workday synthetic)
- **Dependencies added:** cloudscraper, nodriver, camoufox, seleniumbase, crawl4ai, browserforge, fake-useragent, protego, scrapling, typer, rich, openpyxl

### How Scraping Works Now (Updated March 20, 2026)

**Three modes running:**

1. **KEYWORD SEARCH** — `POST /scraper/run` blasts SerpAPI, JobSpy, TheirStack
2. **TARGET BATCH** — `run_target_batch_job()` every 30min (career pages) + 2hr (watchlist)
   - 1,381 H1B career pages imported and classified
   - Smart tier routing: Tier 0 (ATS API) → Tier 1 (HTTP) → Tier 2 (browser) → Tier 3 (hardened)
   - Adapters registered: cloudscraper, scrapling (dual-mode), nodriver, camoufox, seleniumbase
   - ATS auto-detection: 141 Workday, 15 Greenhouse, 12 SmartRecruiters, 8 iCIMS, 5 Lever, 5 Ashby
   - Watchlist companies (11): Amazon, Microsoft, Meta, Google, Uber, SAP, Snap, Airbnb, Lyft, OpenAI, Macrosoft
3. **PAGINATED CRAWLING** — PageCrawler follows "Next" links across multi-page career listings

**End-to-end validated:** Triggered DoorDash (Greenhouse) → Tier 0 → 50 jobs extracted ✅

### Frontend Scraper UI (Updated March 20, 2026)
- **Targets page** (`/targets`): list 1,381 targets with filters, bulk import modal, trigger batch, per-target detail with attempt history
- **ScraperControlPanel**: wired into Settings page with "Run All Scrapers" + per-source "Run Now" buttons
- **ScraperLog**: draggable floating toggle on every page, SSE live stream
- **API client**: 15 functions for targets, attempts, triggers, imports

### What's Still Missing / Next Up
- ~~Frontend performance fixes~~ ✅ DONE (staleTime 5min, gcTime 10min, prefetch, lazy recharts)
- ~~Classification probing~~ ✅ DONE (probed 1,191 targets, reclassified 9: 7 iCIMS + 1 Workday + 1 SmartRecruiters)
- ~~Tier testing~~ ✅ DONE (Greenhouse, Lever, Ashby, keyword search all working. 135 jobs in DB.)
- **Workday scraper URL parsing fix** — NVIDIA URL format not parsed correctly (tenant extraction)
- **Parser tuning** for complex JS-heavy career pages (Microsoft, Amazon, Meta need Tier 2+ rendering)
- **Refero UI design research** — MCP server added, available next session for UI polish
- **Vendoring scraper libraries** locally (currently pip-installed, long-term should be source-vendored)
- **Docker deployment** preparation
- **E2E Playwright tests** before production deploy

---

## What's Broken / Not Yet Working

### ~~1. Scrapling Scraper NOT Ported~~ (RESOLVED)
- ~~V1: full ScraplingScraper (308 lines) + JobSpider (150 lines) + scheduler + career page management~~
- **FIXED:** ScraplingFetcher dual-mode adapter (fast + stealth) ported and registered. Tier 1 (fetch) + Tier 2 (render). All tests pass.

### 2. Scraper Control Panel NOT Wired Up
- V2 has ScraperControlPanel.tsx + ScraperLog.tsx but ORPHANED (not imported anywhere)
- V2 scraper.ts API: read-only (no trigger function)
- Need: wire into Settings page, add triggerScraper() API, start/stop controls

### 3. Slow Page Switching (CRITICAL UX)
- staleTime: 30s -> forces refetch on every page switch (should be 5 min)
- No gcTime -> cache evicted at 5 min default (should be 10 min)
- No prefetching -> pages load data only when mounted
- Dashboard: 3 API calls, Analytics: 5, JobBoard: 2 — all blocking
- Pessimistic loading (blank -> skeleton -> content)
- Duplicate fetches: jobsApi.list() called from 4+ pages
- recharts (330KB) loaded eagerly on Analytics

### 4. Missing V1 Features
- Resume: PDF generation, templates, preview, update with is_default
- Vault: PATCH endpoints (update version_label, update cover letter)
- Scheduler: dedup backfill, salary cache cleanup, interview cleanup, per-source intervals
- Saved search alert checks
- Stats/Analytics endpoint compatibility
- ATS detector API template generation

### 5. Known Bugs
**CRITICAL:** LLMClient chat_stream broken (unconfigured state), Pipeline missing terminal state transitions
**HIGH:** Hardcoded secret key, auto-apply missing type validation, scheduler conflicting imports
**MEDIUM:** Unsafe JSON extraction, unsafe sort column, login error handling, pipeline API path

### 6. Remaining Decomposition
Backend: scraping/service.py (264), auto_apply/service.py (183), auto_apply/orchestrator.py (179), enrichment/service.py (167), jobs/service.py (159), workers/scheduler.py (137), nlp/core.py (185)
Frontend: Dashboard.tsx (300+), JobBoard.tsx (200+)

---

## Scraper Ecosystem Plan

### The Goal
Beat Jobright.ai, Simplify, LinkedIn by scraping company career pages DIRECTLY. See listings within 2-6 hours of posting vs 24-72h lag on aggregators.

### The Dataset: H1B Sponsors Career Pages
- **File:** C:/Users/shriy/Downloads/H1B_Sponsors_Career_Pages.xlsx
- **Count:** 1,473 career page URLs from top H1B sponsoring companies
- **Columns:** Rank, Company Name, Industry, Career Page URL, Total LCA Filings (FY2024-25), H1B Grader Profile, Filing Entity Names
- **Top 5:** Amazon (7,171), Cognizant (5,255), Microsoft (4,727), EY (2,944), Infosys (2,907)
- **Source:** US Department of Labor LCA Disclosure Data

### Three-Mode Architecture

**MODE 1: KEYWORD SEARCH (breadth, catch everything)**
- Input: "ML Engineer" + "Austin, TX" (from profile search_queries)
- Runs every 6 hours
- SerpAPI (free 100/mo) + JobSpy (free, local) + TheirStack (free 200/mo)

**MODE 2: CAREER PAGES (targeted, fastest to source)**
- Input: 1,473 H1B sponsor URLs from Excel
- Runs every 4-12h (priority tiers)
- Auto-detect ATS type per URL:
  - Greenhouse -> API parser, Lever -> API parser, Ashby -> GraphQL, Workday -> JSON
  - Custom HTML -> Scrapling + Crawl4AI with escalation
- Escalation chain: HTTP -> Cloudscraper -> Scrapling -> Nodriver -> Camoufox

**MODE 3: WATCHLIST (dream companies, highest priority)**
- Input: Hugging Face, Google, Meta, OpenAI, Perplexity, Uber, etc.
- Runs every 2-4 hours
- Direct career page + keyword search filtered to company
- Push notification on new listing

### Scraper Tiers
- **TIER 1 FAST (<1s):** Greenhouse/Lever/Ashby APIs, Cloudscraper (~400 pages)
- **TIER 2 MEDIUM (2-5s):** Scrapling, Crawl4AI, Nodriver (~800 pages)
- **TIER 3 HEAVY (5-15s):** Camoufox, SeleniumBase UC Mode (~200 pages)
- **TIER API:** JobSpy, SerpAPI, TheirStack (supplementary/gap-fill)

### Smart Scheduling
- **HOT (every 4h):** Top 100 companies (1000+ LCA filings)
- **WARM (every 6h):** Next 400 companies (100-999 filings)
- **COOL (every 12h):** Remaining 973 companies (<100 filings)
- Result: ~2,400 fetches/day instead of 8,800

### Tools to Install Locally
| Tool | Stars | Size | Purpose |
|------|-------|------|---------|
| Scrapling | 31K | ~6 MB | Career page crawling + stealth + adaptive parsing |
| Crawl4AI | 62K | ~145 MB | LLM-ready markdown extraction |
| Nodriver | 3.8K | ~61 MB | Async undetected Chrome (no Selenium) |
| Cloudscraper | 6.2K | ~30 MB | Lightweight Cloudflare v2 bypass |
| Camoufox | 6.3K | ~618 MB | Nuclear anti-fingerprint Firefox fork |
| Crawlee-Py | 8.6K | ~34 MB | Production orchestration + retry + queue |
| Katana (Go) | 16K | ~15 MB | OPTIONAL future bulk CLI crawler |

### Cross-Language Research
- Python: best anti-bot ecosystem, richest libraries — right choice for 1,473 pages
- Go (Colly 25K, Katana 16K): 3-5x faster — add as sidecar if scaling to 5K+ pages
- Rust (Spider-rs 2.3K): 200-1000x faster — overkill unless 100K+ pages
- JS (Playwright 84K, Crawlee 22K): best for JS-heavy rendering
- Network latency is the bottleneck, not language speed. Python async handles 1,473 pages in 30-60 min.

### Cost Analysis
| Component | Approach | Monthly Cost |
|-----------|----------|-------------|
| 1,473 career pages | Scrapling + Crawl4AI + Nodriver + Cloudscraper | $0 |
| Indeed/LinkedIn/Glassdoor | JobSpy (open source, local) | $0 |
| Google Jobs discovery | SerpAPI free tier (100/mo) | $0 |
| TheirStack gap-fill | Free tier (200 credits/mo) | $0 |
| LLM enrichment | OpenRouter GPT-4o-mini | ~$3-5/mo |
| ScrapingBee | DROP — replaced by Cloudscraper + Scrapling | $0 |
| Apify | DROP — replaced by self-hosted Crawlee-Py | $0 |
| **TOTAL** | | **~$3-5/mo** |

---

## Legal Stance on Scraping

- **Personal use only** — no resale, no redistribution, no commercial use
- **Career pages = ZERO risk** — companies want these found, pay to have them indexed
- **Greenhouse/Lever/Ashby public APIs = ZERO risk** — intentionally exposed public endpoints
- **Indeed/LinkedIn/Glassdoor via JobSpy = LOW risk** — public listings, conservative rate limits
- **hiQ v. LinkedIn (2022):** public data scraping does NOT violate CFAA
- **No individual job seeker has ever been sued** for scraping job listings
- Jobright.ai, Simplify, Indeed — all do the same thing at commercial scale with zero legal consequences

**Safety Rails Baked Into Architecture:**
- Rate limits: 1 req/3s Indeed, 1 req/5s LinkedIn, 1-2 req/s career pages
- Store full content for career pages, metadata + links only for job boards
- Respect robots.txt where practical, honor 429 responses immediately
- Cache aggressively — don't re-scrape unchanged pages
- NEVER scrape behind login walls, personal profiles, or salary data behind auth
- NEVER link scrapers to personal LinkedIn account

---

## User Profile & Configuration

### Personal Details
- Name: Shriyansh Singh
- Email: shriyansh.singh24@gmail.com
- Phone: 930 333 5141
- Location: Austin, TX, USA
- LinkedIn: https://www.linkedin.com/in/shriyansh-bir-singh/
- GitHub: https://github.com/shriyansh24
- Portfolio: https://personalwebsite-9n7xiqgwk-shriyansh24s-projects.vercel.app/

### Professional Details
- Current Title: Machine Learning Engineer
- Current Company: Apexon
- Years of Experience: 1
- Highest Degree: MS Data Science
- University: Indiana University Bloomington
- Graduation Year: 2025
- Work Authorization: OPT
- Requires Visa Sponsorship: Yes
- Salary Target: $120,000 - $200,000

### Job Search Preferences
- Preferred Locations: Anywhere in USA, Remote, Austin, New York, San Francisco, Texas
- Dream Companies: Hugging Face, Perplexity, OpenAI, Google, Meta, Uber, Snap Inc, Lyft, Airbnb, Microsoft, BNSF, Amazon
- Resume: C:\Users\shriy\Downloads\Shriyansh__Sing__Resume.pdf (uploaded to DB)

### API Keys Configured
- PostgreSQL password: configured in .env
- OpenRouter API key: configured
- SerpAPI key: configured
- TheirStack key: configured
- ScrapingBee key: configured (to be dropped — replaced by local tools)
- Apify: skipped (to be dropped — replaced by Crawlee-Py)

---

## Infrastructure

### Dev Servers
- Backend: FastAPI + uvicorn on port 8000 (via D:/jobradar-v2/backend/start-dev.cjs wrapper)
- Frontend: Vite dev server on port 5173 (via D:/jobradar-v2/frontend/start-dev.cjs wrapper)
- Launch config: D:/.claude/launch.json (for preview_start)
- Database: PostgreSQL (localhost:5432, db=jobradar_v2)
- Cache: Memurai/Redis (localhost:6379)
- Frontend proxy: Vite proxies /api -> localhost:8000

### Key Config Files
- Backend .env: D:/jobradar-v2/backend/.env
- API base URL: /api/v1 (relative, uses Vite proxy — changed from hardcoded localhost:8000)
- Frontend constants: D:/jobradar-v2/frontend/src/lib/constants.ts

### Bugs Fixed During Testing
- Decimal('NaN') in salary fields -> added field_validator to clean NaN/Infinity
- Job model relationship -> added string annotation for lazy Application resolution
- DateTime timezone mismatch -> added DateTime(timezone=True) to model columns
- API base URL -> changed to relative /api/v1 for Vite proxy compatibility
- UTC import -> added from datetime import UTC for timezone-aware datetimes

---

## Priority Action List

### ~~Phase A: Scraper Ecosystem~~ (COMPLETE — 2026-03-19)
1. ~~Install Python scraper packages~~ — DONE (9 packages in pyproject.toml)
2. ~~Load H1B career pages Excel~~ — DONE (CLI import tool ready, 1,473 URLs classified)
3. ~~Build ATS auto-detector~~ — DONE (8 vendors: greenhouse, lever, ashby, workday, icims, smartrecruiters, jobvite, breezy)
4. ~~Port full Scrapling scraper~~ — DONE (dual-mode: fast fetch + stealth render)
5. ~~Wire new scrapers into ScrapingService~~ — DONE (run_target_batch + AdapterRegistry + EscalationEngine)
6. ~~Set up smart scheduler~~ — DONE (watchlist/hot/warm/cool priority classes, scoring-based batch selection)

### Phase B: Frontend Scraper UI
7. Wire ScraperControlPanel + ScraperLog into Settings page
8. Add triggerScraper(source) to frontend API + start/stop/run-all buttons
9. Add career page management UI (list, add, enable/disable, bulk import)

### Phase C: Performance Fixes
10. Fix slow page switching (staleTime 5min, gcTime 10min, prefetching, progressive loading)
11. Lazy-load recharts, consolidate duplicate API calls
12. Add route-level data prefetching on nav hover

### Phase D: Remaining V1 Ports
13. Resume: PDF generation, templates, preview, is_default update
14. Vault: PATCH endpoints
15. Scheduler: dedup backfill, salary/interview cleanup, saved search alerts

### Phase E: Bug Fixes
16. Fix all CRITICAL and HIGH bugs from audit
17. Fix pipeline terminal state transitions
18. Fix LLMClient chat_stream for unconfigured state

### Phase F: Polish
19. Decompose remaining monolithic files
20. End-to-end testing of all features
21. Docker containerization for deployment

---

## Files Modified This Session (Scraper Platform Build — 2026-03-19)

### New Modules (33 source files)
- `app/scraping/control/` — ats_registry, classifier, priority_scorer, scheduler, target_registry, tier_router
- `app/scraping/execution/` — fetcher_port, browser_port, extractor_port, cloudscraper_fetcher, scrapling_fetcher, nodriver_browser, camoufox_browser, seleniumbase_browser, crawl4ai_extractor, adapter_registry, browser_pool, escalation_engine
- `app/scraping/scrapers/workday.py`, `app/scraping/constants.py`, `app/scraping/ops.py`

### Modified Files
- `app/scraping/models.py` — added ScrapeTarget + ScrapeAttempt, removed CareerPage, added ScraperRun tier counters
- `app/jobs/models.py` — added lifecycle tracking columns
- `app/scraping/service.py` — added run_target_batch() orchestration
- `app/scraping/router.py` — migrated from CareerPage to ScrapeTarget
- `app/workers/scraping_worker.py` — added run_target_batch_job()
- `app/workers/scheduler.py` — added 2 new scheduled jobs
- `app/migrations/env.py` — removed CareerPage import
- `pyproject.toml` — added 12 new dependencies

### Test Files (27 files, 246 tests)
- `tests/unit/scraping/` — 25 files, 179 tests (all pass)
- `tests/contracts/` — 3 files, 67 tests (all pass)
- `tests/fixtures/` — 12 fixture files (4 ATS JSON + 4 expected + 4 HTML)
