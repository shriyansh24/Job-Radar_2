# Scraper Platform Design Specification

> **Status:** Approved design, pending implementation plan
> **Author:** Shriyansh Singh + Claude
> **Date:** 2026-03-19
> **Scope:** Transform the scraping subsystem from a collection of scraper components into a policy-driven ingestion platform

---

## Vision Statement

The scraper subsystem will evolve into a source-driven ingestion platform for public job opportunities, optimized for early discovery from primary employer-controlled endpoints. It will route each target through a policy-based, tiered execution engine that prefers structured ATS APIs and lightweight HTML extraction before escalating to stealth browsers or supplementary aggregator feeds. The system will normalize, deduplicate, version, and enrich job data into a durable canonical model suitable for ranking, alerting, and downstream personalization.

The platform will remain local-first and Python-led in its control plane, with optional sidecars introduced only where throughput or isolation justifies them. It will prioritize correctness, observability, and testability over premature service sprawl. Backend and database rigor will come first: source registry, execution traces, versioned job records, retry and escalation policy, scheduler intelligence, and fixture-based parser testing. Frontend controls and dashboards will be layered on after the ingestion plane is reliable.

---

## 1. Platform Architecture

### 1.1 Six Backend Concerns

The scraper platform is organized into six logical planes. These are module boundaries inside a modular monolith, not network services.

**Control Plane** — the system brain
- Source registration and configuration
- Run scheduling with business-priority scoring
- Routing to the correct scraper tier
- Rate limits, circuit breaking, concurrency governance
- Lifecycle management (enable, disable, quarantine, release)
- Event emission for live UI
- Retry and escalation policy enforcement

**Execution Plane** — page and API fetching
- HTTP requests (httpx, cloudscraper)
- Browser orchestration (Nodriver, Camoufox, SeleniumBase)
- Stealth tactics (BrowserForge fingerprints, fake-useragent rotation)
- Anti-bot escalation (Scrapling dual-mode)
- ATS API calls (Greenhouse, Lever, Ashby, Workday)

**Extraction Plane** — turning raw responses into structured data
- ATS-specific JSON parsers (Greenhouse, Lever, Ashby, Workday)
- Adaptive CSS selector engine (20+ selector patterns)
- JSON-LD JobPosting extraction
- Detail page extraction (salary, requirements, benefits)
- Crawl4AI markdown conversion for LLM pipeline
- AIScraper LLM fallback when parsers return 0 jobs
- Salary, location, remote-type, seniority normalization

**Data Quality Plane** — making data trustworthy
- Page-level content hashing (SHA-256 of noise-stripped HTML — for change detection on targets)
- Job-level dedup hashing (MD5 of normalized title|company — for fast duplicate detection)
- Stable job identity (SHA-256 of source|title|company|location, truncated to 64 hex chars — this is the `jobs.id` primary key, a String(64), not UUID)
- 3-layer deduplication (exact MD5 hash, URL canonical, simhash near-duplicate)
- Job lifecycle tracking (first_seen, last_seen, disappeared_at)
- Content change detection between runs
- Freshness and staleness policy

**Enrichment Plane** — making data useful (downstream, decoupled from scraping)
- HTML-to-markdown conversion
- LLM extraction (summary, skills, tech stack, red/green flags)
- Salary inference when missing
- Embedding generation for semantic search
- TF-IDF scoring against user resume
- Per-user relevance scoring

**Observability Plane** — making the system debuggable
- Scraper run records with aggregate metrics
- Per-target attempt logging with tier, duration, outcome
- Source health scoring (success rate, latency, circuit state)
- Scheduler decision traces
- SSE event stream for live frontend
- CLI operations tool for triage

### 1.2 Service Decomposition (Modular Monolith)

All services run in-process inside the FastAPI backend. Clean module boundaries allow future extraction if needed.

**Service 1: Scraper Control Service** — orchestration and policy
- Owns: scrape_targets registry, tier router, scheduler, run coordinator
- Module: `app/scraping/control/`

**Service 2: Scraper Workers** — stateless execution
- Owns: fetcher adapters, parser invocation, result bundling
- Module: `app/scraping/workers/`

**Service 3: Browser Execution Service** — browser lifecycle
- Owns: Nodriver pool, Camoufox pool, session management, memory governance
- Module: `app/scraping/browsers/`

**Service 4: Enrichment Service** — post-scrape transformation
- Owns: LLM enrichment, embedding, scoring
- Module: `app/enrichment/` (existing, keep separate)

**Service 5: Notification / Match Service** — user-facing output
- Owns: TF-IDF matching, alerts, digest generation
- Module: `app/notifications/` (existing)

---

## 2. Database Schema

### 2.1 New Table: `scrape_targets`

Replaces the current `career_pages` table. Canonical registry of all scraping targets.

```sql
CREATE TABLE scrape_targets (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID REFERENCES users(id),
    url                     TEXT NOT NULL,
    company_name            VARCHAR(300),
    company_domain          VARCHAR(255),
    source_kind             VARCHAR(50) NOT NULL DEFAULT 'career_page',
    ats_vendor              VARCHAR(50),
    ats_board_token         VARCHAR(255),
    start_tier              SMALLINT NOT NULL DEFAULT 1,
    max_tier                SMALLINT NOT NULL DEFAULT 3,
    priority_class          VARCHAR(10) NOT NULL DEFAULT 'cool',
    schedule_interval_m     INTEGER NOT NULL DEFAULT 720,
    enabled                 BOOLEAN NOT NULL DEFAULT TRUE,
    quarantined             BOOLEAN NOT NULL DEFAULT FALSE,
    quarantine_reason       TEXT,
    last_success_at         TIMESTAMPTZ,
    last_failure_at         TIMESTAMPTZ,
    last_success_tier       SMALLINT,
    last_http_status        SMALLINT,
    content_hash            VARCHAR(64),
    etag                    VARCHAR(255),
    last_modified           VARCHAR(255),
    consecutive_failures    INTEGER NOT NULL DEFAULT 0,
    failure_count           INTEGER NOT NULL DEFAULT 0,
    next_scheduled_at       TIMESTAMPTZ,
    lca_filings             INTEGER,
    industry                VARCHAR(255),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_targets_schedule ON scrape_targets (priority_class, next_scheduled_at)
    WHERE enabled = TRUE AND quarantined = FALSE;
CREATE INDEX idx_targets_ats ON scrape_targets (ats_vendor);
CREATE INDEX idx_targets_active ON scrape_targets (enabled, quarantined);
```

**Column notes:**
- `source_kind`: 'career_page', 'ats_board', 'aggregator'
- `ats_vendor`: 'greenhouse', 'lever', 'ashby', 'workday', 'icims', 'smartrecruiters', etc. NULL for unknown/custom
- `ats_board_token`: extracted slug for ATS APIs (e.g., 'huggingface' from lever.co/huggingface)
- `priority_class`: 'watchlist', 'hot', 'warm', 'cool'
- `schedule_interval_m`: minutes between scrapes (120 for watchlist, 240 for hot, 360 for warm, 720 for cool)

### 2.2 New Table: `scrape_attempts`

Per-target execution log. **One row per physical fetch attempt.** If a target escalates from Tier 1 → Tier 2, that produces TWO rows: one with `status='escalated'` for the Tier 1 attempt, and one with `status='success'` (or `'failed'`) for the Tier 2 attempt. Both share the same `run_id` and `target_id`.

```sql
CREATE TABLE scrape_attempts (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id                  UUID REFERENCES scraper_runs(id),
    target_id               UUID REFERENCES scrape_targets(id),
    selected_tier           SMALLINT NOT NULL,
    actual_tier_used        SMALLINT NOT NULL,
    scraper_name            VARCHAR(50) NOT NULL,
    parser_name             VARCHAR(50),
    status                  VARCHAR(20) NOT NULL DEFAULT 'pending',
    http_status             SMALLINT,
    duration_ms             INTEGER,
    retries                 SMALLINT NOT NULL DEFAULT 0,
    escalations             SMALLINT NOT NULL DEFAULT 0,
    jobs_extracted          INTEGER NOT NULL DEFAULT 0,
    content_hash_before     VARCHAR(64),
    content_hash_after      VARCHAR(64),
    content_changed         BOOLEAN,
    error_class             VARCHAR(100),
    error_message           TEXT,
    browser_used            BOOLEAN NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_attempts_run ON scrape_attempts (run_id);
CREATE INDEX idx_attempts_target ON scrape_attempts (target_id, created_at DESC);
```

**Status values:** 'pending', 'success', 'partial', 'failed', 'skipped', 'escalated', 'not_modified'

- `skipped`: scheduler decided not to attempt this target (e.g., circuit open)
- `escalated`: this attempt failed and triggered escalation to a higher tier
- `not_modified`: HTTP 304 response — server confirmed no content change since last fetch

### 2.3 Additions to Existing `jobs` Table

```sql
ALTER TABLE jobs ADD COLUMN first_seen_at    TIMESTAMPTZ;
ALTER TABLE jobs ADD COLUMN last_seen_at     TIMESTAMPTZ;
ALTER TABLE jobs ADD COLUMN disappeared_at   TIMESTAMPTZ;
ALTER TABLE jobs ADD COLUMN content_hash     VARCHAR(64);
ALTER TABLE jobs ADD COLUMN previous_hash    VARCHAR(64);
ALTER TABLE jobs ADD COLUMN seen_count       INTEGER NOT NULL DEFAULT 1;
ALTER TABLE jobs ADD COLUMN source_target_id UUID REFERENCES scrape_targets(id);

CREATE INDEX idx_jobs_active ON jobs (disappeared_at) WHERE disappeared_at IS NULL;
CREATE INDEX idx_jobs_target ON jobs (source_target_id);
```

Job versioning is deferred to Phase 3. For now, `content_hash` + `previous_hash` detects changes, and `first_seen_at` / `last_seen_at` / `disappeared_at` tracks lifecycle.

**Note on `jobs.id`:** The existing `jobs.id` column is `String(64)` (truncated SHA-256 hex), NOT UUID. This differs from all other tables' PK convention. The `source_target_id` FK references `scrape_targets.id` (UUID). This asymmetry is intentional — job IDs are content-addressable for deduplication.

### 2.4 Additions to Existing `scraper_runs` Table

```sql
ALTER TABLE scraper_runs ADD COLUMN targets_attempted INTEGER NOT NULL DEFAULT 0;
ALTER TABLE scraper_runs ADD COLUMN targets_succeeded INTEGER NOT NULL DEFAULT 0;
ALTER TABLE scraper_runs ADD COLUMN targets_failed    INTEGER NOT NULL DEFAULT 0;
ALTER TABLE scraper_runs ADD COLUMN tier_0_count      INTEGER NOT NULL DEFAULT 0;
ALTER TABLE scraper_runs ADD COLUMN tier_1_count      INTEGER NOT NULL DEFAULT 0;
ALTER TABLE scraper_runs ADD COLUMN tier_2_count      INTEGER NOT NULL DEFAULT 0;
ALTER TABLE scraper_runs ADD COLUMN tier_3_count      INTEGER NOT NULL DEFAULT 0;
ALTER TABLE scraper_runs ADD COLUMN tier_api_count    INTEGER NOT NULL DEFAULT 0;
```

### 2.5 Hashing Strategy (Clarification)

Two different hashes serve two different purposes:

| Hash | Algorithm | Column | Purpose |
|---|---|---|---|
| Page content hash | SHA-256 (noise-stripped HTML) | `scrape_targets.content_hash`, `scrape_attempts.content_hash_*` | Detect if a career page's HTML changed between runs |
| Job dedup hash | MD5(normalize(title) \| normalize(company)) | Used in-memory by DeduplicationService Layer 1 | Fast duplicate detection across scraped jobs |
| Job identity | SHA-256(source\|title\|company\|location)[:64] | `jobs.id` (String(64) PK) | Stable primary key for cross-run identity |
| Job content hash | SHA-256(description text) | `jobs.content_hash` | Detect if a job's description text changed |

The simhash used for near-duplicate detection (Layer 3) must use a deterministic hash function, not Python's built-in `hash()`. Implementation should use `hashlib.md5` on each token for deterministic simhash computation across processes. Set `PYTHONHASHSEED=0` in the `.env` as a defense-in-depth measure.

### 2.6 Migration of `career_pages` Data

Existing career_pages rows migrate to scrape_targets with `source_kind = 'career_page'`, `ats_vendor = NULL`, `start_tier = 1`. The career_pages table is then dropped.

---

## 3. Tier Router & Execution Policy

### 3.1 Tier Definitions

**Tier 0 — Structured ATS APIs** (fastest, cheapest, most reliable)
- Greenhouse: `GET boards-api.greenhouse.io/v1/boards/{token}/jobs`
- Lever: `GET api.lever.co/v0/postings/{token}?mode=json`
- Ashby: `POST jobs.ashbyhq.com/api/non-user-graphql`
- Workday: `POST *.myworkdayjobs.com/wday/cxs/{tenant}/jobs` (new)
- Characteristics: <1s per page, no browser, structured JSON, preferred by policy

**Tier 1 — Lightweight HTTP Fetch + Parse** (fast, low resource)
- Cloudscraper: Cloudflare v2 bypass without browser
- Scrapling fast mode: `Fetcher.get(url, impersonate="chrome")`
- httpx + adaptive parser: direct HTTP with CSS selector extraction
- JSON-LD extraction from `<script type="application/ld+json">`
- Characteristics: 1-3s per page, no browser, handles most generic career pages

**Tier 2 — Stealth Browser** (moderate resource, higher success)
- Nodriver: async undetected Chrome, no Selenium dependency
- Scrapling stealth mode: `StealthyFetcher.fetch(url, headless=True)`
- Crawl4AI: post-fetch markdown extraction (not a fetcher itself)
- Characteristics: 2-5s per page, browser session required, handles JS-heavy pages

**Tier 3 — Heavy Hardened Browser** (expensive, last resort)
- Camoufox: anti-fingerprint Firefox with C++-level spoofing
- SeleniumBase UC Mode: undetected ChromeDriver with CAPTCHA bypass
- Characteristics: 5-15s per page, high memory, reserved for high-value targets that fail all lower tiers

**Tier API — Supplementary Sources** (keyword-based, not target-based)
- JobSpy: Indeed, LinkedIn, Glassdoor, ZipRecruiter
- SerpAPI: Google Jobs (free 100/mo)
- TheirStack: tech job feeds (free 200/mo)
- Characteristics: query-driven not URL-driven, supplementary coverage

### 3.2 ATS Registry (Data-Driven, Not If/Elif)

Classification uses a registry of rules, evaluated in order. Adding a new ATS vendor requires adding one dict entry, zero code changes.

```python
ATS_RULES: list[dict] = [
    {
        "vendor": "greenhouse",
        "url_patterns": ["boards.greenhouse.io/", ".greenhouse.io/"],
        "header_signatures": ["X-Greenhouse"],
        "html_signatures": ['content="Greenhouse"'],
        "start_tier": 0,
        "board_token_extractor": "greenhouse",
    },
    {
        "vendor": "lever",
        "url_patterns": ["jobs.lever.co/"],
        "header_signatures": ["X-Powered-By: Lever"],
        "html_signatures": ["lever-jobs-container"],
        "start_tier": 0,
        "board_token_extractor": "lever",
    },
    {
        "vendor": "ashby",
        "url_patterns": ["jobs.ashbyhq.com/"],
        "header_signatures": [],
        "html_signatures": ["ashby-job-posting"],
        "start_tier": 0,
        "board_token_extractor": "ashby",
    },
    {
        "vendor": "workday",
        "url_patterns": [".myworkdayjobs.com"],
        "header_signatures": [],
        "html_signatures": ["wday/cxs"],
        "start_tier": 0,
        "board_token_extractor": "workday",
    },
    {
        "vendor": "icims",
        "url_patterns": [".icims.com"],
        "header_signatures": [],
        "html_signatures": [],
        "start_tier": 1,
        "board_token_extractor": None,
    },
    {
        "vendor": "smartrecruiters",
        "url_patterns": [".smartrecruiters.com"],
        "header_signatures": [],
        "html_signatures": [],
        "start_tier": 1,
        "board_token_extractor": None,
    },
]
```

The classifier function walks the registry. It never contains vendor-specific logic. Future: this registry can migrate to a database table for runtime updates.

### 3.3 Classification Pipeline

**Step 1: URL pattern matching** (instant, no network)
- Walk ATS_RULES, match URL against url_patterns
- Extract board token if extractor is defined
- ~30-40% of targets classifiable from URL alone

**Step 2: Priority classification** (instant, from H1B data)
- LCA filings >= 1000 AND in watchlist → 'watchlist' (every 2h)
- LCA filings >= 1000 → 'hot' (every 4h)
- LCA filings >= 100 → 'warm' (every 6h)
- LCA filings < 100 → 'cool' (every 12h)
- Watchlist override: fuzzy match company_name against user's dream companies

**Step 3: Deferred HTTP probing** (background worker, one-time for unknowns)
- HEAD request to check response headers for ATS fingerprints
- If still unknown, fetch first 5KB of HTML body and check meta tags, DOM patterns, script contents
- If still unknown → stays `ats_vendor = NULL`, `start_tier = 1`

### 3.4 Routing Logic

> Note: this is simplified pseudocode. See Appendix A.5 for canonical `ExecutionPlan` and `Step` dataclass definitions.

```python
def route(target: ScrapeTarget) -> ExecutionPlan:
    effective_start = target.last_success_tier or target.start_tier

    if target.ats_vendor in TIER_0_VENDORS:
        return ExecutionPlan(
            primary_tier=0,
            max_tier=0,
            primary_step=Step(tier=0, scraper_name=ATS_SCRAPER_MAP[target.ats_vendor],
                              parser_name=ATS_PARSER_MAP[target.ats_vendor]),
            fallback_chain=[],
            rate_policy=target.ats_vendor,
        )

    # Build full chain, then prune to steps >= effective_start
    full_chain = [
        Step(tier=1, scraper_name='cloudscraper', parser_name='adaptive'),
        Step(tier=1, scraper_name='scrapling_fast', parser_name='adaptive'),
        Step(tier=2, scraper_name='nodriver', parser_name='adaptive', browser_required=True),
        Step(tier=2, scraper_name='scrapling_stealth', parser_name='adaptive', browser_required=True),
        Step(tier=3, scraper_name='camoufox', parser_name='adaptive', browser_required=True),
        Step(tier=3, scraper_name='seleniumbase', parser_name='adaptive', browser_required=True),
    ]
    pruned = [s for s in full_chain if s.tier >= effective_start and s.tier <= target.max_tier]

    return ExecutionPlan(
        primary_tier=effective_start,
        max_tier=target.max_tier,
        primary_step=pruned[0],
        fallback_chain=pruned[1:],
        rate_policy='generic',
    )
```

### 3.5 Escalation Triggers

| Condition | Action |
|---|---|
| HTTP 403 | Escalate to next tier |
| HTTP 429 | Back off (exponential), retry same tier, then escalate |
| HTTP 5xx | Retry same tier once, then escalate |
| Timeout | Escalate with 2x timeout |
| Empty response body | Escalate (page may need JS rendering) |
| Cloudflare challenge detected | Skip to Tier 2 minimum |
| 0 jobs from non-empty HTML | Try AIScraper LLM fallback, then escalate |
| Tier 3 fails 3 consecutive times | Quarantine target |

### 3.6 History-Based Learning

- If `target.last_success_tier = 2`, start at Tier 2 next run (skip 0, 1)
- If target succeeds at Tier 1 after previously needing Tier 2, update `last_success_tier = 1` (sites can improve)
- If `target.consecutive_failures >= 5` at current tier, auto-bump `start_tier` to next tier
- If `target.consecutive_failures >= 10`, quarantine with reason

### 3.7 Concurrency Governance

Machine specs: 64GB RAM, 24 cores (Intel Core Ultra 9 275HX)

```
Tier 0 (API calls):     max 50 concurrent
Tier 1 (HTTP fetch):    max 30 concurrent
Tier 2 (Nodriver):      max 8 concurrent browser sessions
Tier 3 (Camoufox):      max 3 concurrent browser sessions
Global:                  max 100 concurrent operations
Per-domain:              max 2 concurrent requests to same domain
Browser memory budget:   max 8GB total for all browser sessions
```

Admission control: if browser memory budget is near limit, queue Tier 2/3 requests instead of launching new sessions.

---

## 4. Scraper Integration Map

### 4.1 Active Scrapers (Phase 1-2)

**Tier 0 — ATS API Adapters:**
| Scraper | Status | Interface |
|---|---|---|
| Greenhouse | Existing in v2 | `ScraperPort.fetch_jobs(board_token)` |
| Lever | Existing in v2 | `ScraperPort.fetch_jobs(slug)` |
| Ashby | Existing in v2 | `ScraperPort.fetch_jobs(org_slug)` |
| Workday | New — build | `ScraperPort.fetch_jobs(tenant_url)` |

**Tier 1 — Lightweight HTTP:**
| Scraper | Status | Interface |
|---|---|---|
| Cloudscraper | New — install | `FetcherPort.fetch(url) -> HTML` |
| Scrapling (fast mode) | Port from v1 | `FetcherPort.fetch(url) -> HTML` |
| httpx + adaptive parser | Existing (refactor) | `FetcherPort.fetch(url) -> HTML` |

**Tier 2 — Stealth Browser:**
| Scraper | Status | Interface |
|---|---|---|
| Nodriver | New — install | `BrowserPort.render(url) -> HTML` |
| Scrapling (stealth mode) | Port from v1 | `BrowserPort.render(url) -> HTML` |

**Post-Fetch Extraction:**
| Tool | Status | Interface |
|---|---|---|
| Crawl4AI | New — install | `ExtractorPort.to_markdown(html) -> str` |
| AIScraper | Existing (refactor to fallback) | `ExtractorPort.extract_jobs(html) -> list[ScrapedJob]` |

**Tier 3 — Heavy Browser:**
| Scraper | Status | Interface |
|---|---|---|
| Camoufox | New — install | `BrowserPort.render(url) -> HTML` |
| SeleniumBase UC Mode | New — install | `BrowserPort.render(url) -> HTML` |

**Tier API — Supplementary:**
| Scraper | Status | Interface |
|---|---|---|
| JobSpy | Existing in v2 | `ScraperPort.fetch_jobs(query, location)` |
| SerpAPI | Existing in v2 | `ScraperPort.fetch_jobs(query, location)` |
| TheirStack | Existing in v2 | `ScraperPort.fetch_jobs(query, location)` |

### 4.2 Utility Libraries

| Tool | Stars | Purpose | Used By |
|---|---|---|---|
| BrowserForge | 1,014 | Realistic fingerprint + header generation | Nodriver, Scrapling, Camoufox sessions |
| fake-useragent | 4,048 | User-Agent string rotation | Tier 1-3 HTTP requests (NOT Tier 0 ATS APIs — use consistent UA for API calls to avoid anomaly detection) |
| Protego | 86 | robots.txt parsing + crawl-delay | Policy layer — checked before fetch |
| typer | — | CLI framework | ops tool |
| rich | — | Terminal tables, progress bars | ops tool, CLI output |
| httpx | 15,151 | Async HTTP client | Tier 0, Tier 1, all API calls |

### 4.3 Deferred Tools

| Tool | Trigger to Evaluate |
|---|---|
| Crawlee-Python | When homegrown queue/retry logic becomes painful |
| ScrapeGraphAI | When LLM extraction needs multi-page graph traversal |
| Katana (Go) | When target count exceeds 5,000 pages |
| Colly (Go) | Same trigger as Katana |
| Spider-rs (Rust) | When target count exceeds 100,000 pages |
| aiohttp | When httpx becomes a measurable bottleneck |
| Scrapoxy | When IP bans become a recurring problem |

### 4.4 Dropped Tools

| Tool | Reason |
|---|---|
| Apify | Replaced by JobSpy + Nodriver |
| ScrapingBee | Replaced by Cloudscraper + Scrapling + Nodriver |
| Scrapy | Competing framework, not needed |
| Botasaurus | Fails on remote/Docker servers |
| undetected-chromedriver | Deprecated, succeeded by Nodriver |
| puppeteer-stealth | Deprecated Feb 2025 |

### 4.5 Execution Flow (Single Target)

```
Target: https://careers.microsoft.com
Classification: custom_html, priority: hot, start_tier: 1

TierRouter.route(target) → ExecutionPlan(primary=1, max=3, chain=[...])

Attempt 1 (Tier 1):
  cloudscraper.get(url)
  → 200 OK, 45KB HTML
  → Protego: check robots.txt crawl-delay → OK
  → AdaptiveParser.extract(html) → 0 jobs (page needs JS)
  → Status: 'escalated', reason: '0 jobs from non-empty HTML'

Attempt 2 (Tier 2):
  Nodriver.render(url, fingerprint=BrowserForge.generate())
  → Rendered DOM, 180KB
  → AdaptiveParser.extract(html) → 23 jobs ✓
  → Crawl4AI.to_markdown(html) → clean markdown stored
  → Status: 'success'
  → Update: target.last_success_tier = 2

Records (one per physical attempt):
  scrape_attempt #1: { target_id=X, selected_tier=1, actual_tier_used=1,
    scraper_name='cloudscraper', status='escalated', jobs_extracted=0,
    error_class='zero_extraction', duration_ms=1200 }
  scrape_attempt #2: { target_id=X, selected_tier=1, actual_tier_used=2,
    scraper_name='nodriver', status='success', jobs_extracted=23,
    content_changed=true, duration_ms=3000, browser_used=true }

Output: 23 ScrapedJob → dedup → persist → queue for enrichment
```

---

## 5. Scheduler Design

### 5.1 Scoring-Based Target Selection

The scheduler does not use fixed cron intervals per priority class. Instead, it runs a selection loop every 30 minutes and picks due targets by priority score.

`priority_score` is computed at query time, NOT stored as a column. The scheduler computes it in Python after fetching due targets:

```sql
-- Step 1: fetch due targets
SELECT * FROM scrape_targets
WHERE enabled = TRUE
  AND quarantined = FALSE
  AND next_scheduled_at <= NOW()
ORDER BY next_scheduled_at ASC
LIMIT 500;

-- Step 2: in Python, compute priority_score for each target
-- Step 3: sort by score descending, take top 200
```

This avoids a stored column that would need constant recalculation. The formula is applied in-memory after the DB query returns due targets.

### 5.2 Priority Score Formula

```
score = base_priority
      + recency_bonus
      + success_rate_bonus
      - failure_penalty
      - cost_penalty

WHERE:
  base_priority:
    watchlist = 100
    hot       = 70
    warm      = 40
    cool      = 10

  recency_bonus:
    never scraped     = +20
    overdue by 2x     = +10
    overdue by 1x     = +5

  success_rate_bonus:
    last 5 all success = +10
    last 5 mostly good = +5

  failure_penalty:
    per consecutive failure = -15

  cost_penalty:
    last_success_tier >= 2  = -5
    last_success_tier >= 3  = -10
```

### 5.3 After Completion

**On success:**
```
target.next_scheduled_at = NOW() + schedule_interval_m minutes
target.last_success_at = NOW()
target.last_success_tier = actual_tier_used
target.consecutive_failures = 0
target.content_hash = new_hash
```

**On failure:**
```
backoff = schedule_interval_m * (1.5 ^ min(consecutive_failures, 5))
target.next_scheduled_at = NOW() + backoff minutes
target.last_failure_at = NOW()
target.consecutive_failures += 1
target.failure_count += 1

IF consecutive_failures >= 10:
    target.quarantined = TRUE
    target.quarantine_reason = 'auto: 10 consecutive failures'
```

### 5.4 Run Modes

**Mode 1: Career Page Scraping (target-based)**
- Scheduler tick every 30 minutes
- Selects due targets, groups by tier, runs in parallel pools
- Primary ingestion strategy

**Mode 2: Keyword Search (query-based)**
- Runs every 6 hours
- Reads search_queries from user profile
- Sends to SerpAPI, JobSpy, TheirStack
- Supplementary discovery

**Mode 3: Watchlist Priority Run**
- Runs every 2 hours
- Force-selects all targets where `priority_class = 'watchlist'`
- Runs regardless of `next_scheduled_at`
- Maximum frequency for dream companies
- **After completion, updates `next_scheduled_at`** so Mode 1 does not re-select the same targets in the next 30-min tick. This prevents duplicate runs.

### 5.5 Batch Execution

```
Scheduler tick:
  Select due targets (up to 200)
  Group by start_tier:
    Tier 0 targets → asyncio pool (concurrency: 50)
    Tier 1 targets → asyncio pool (concurrency: 30)
    Tier 2 targets → browser pool (concurrency: 8)
    Tier 3 targets → browser pool (concurrency: 3)
  All pools run simultaneously
  Create ScraperRun record with aggregate metrics
  Emit SSE events for live UI
  Queue successful new jobs for enrichment
```

---

## 6. Data Quality

### 6.1 Deduplication (Existing, Enhanced)

Three-layer dedup preserved from current system (see Section 2.5 for hash algorithm details):
1. **Exact job hash:** MD5(normalize(title) | normalize(company)) — fast O(1) lookup
2. **URL canonicalization:** strip tracking params (utm_*, ref, trk), normalize host — catches same job from different referral links
3. **Simhash near-duplicate:** 64-bit simhash using deterministic hashlib.md5 per token, hamming distance < 3 — catches slight rewording

Note: this is job-level dedup (are two scraped jobs the same listing?), distinct from page-level content hashing (did a career page change since last scrape?).

Enhancement: cross-mode dedup. Same job found via career page AND Indeed → keep career page version (richer data, faster discovery), link back to Indeed URL.

### 6.2 Job Lifecycle

```
New job scraped        → first_seen_at = NOW(), last_seen_at = NOW(), seen_count = 1
Same job found again   → last_seen_at = NOW(), seen_count += 1
                         if content_hash changed: previous_hash = old, content_hash = new
Job not found in run   → (no immediate action — may be pagination)
Job missing for 72h    → disappeared_at = NOW()
Job reappears          → disappeared_at = NULL, last_seen_at = NOW()
```

### 6.3 Content Change Detection

Each target stores `content_hash` (SHA-256 of noise-stripped HTML). On re-scrape:
- If hash unchanged → skip full parsing (ETag/Last-Modified optimization)
- If hash changed → full parse, compare job sets, detect new/removed/modified jobs

### 6.4 robots.txt Compliance

Before first fetch of any target:
- Fetch and parse robots.txt using Protego
- Cache result for 24 hours
- Respect Crawl-delay directive (override rate limiter if robots.txt specifies longer delay)
- Extract Sitemap URLs (may contain direct job page links)
- Log compliance decision in attempt record

---

## 7. CLI Operations Tool

### 7.1 Technology

- Framework: **typer** (type-hint-driven CLI, auto-generates help)
- Output: **rich** (tables, progress bars, colored status)
- Entry point: `python -m app.scraping.ops`

### 7.2 Commands

```
app.scraping.ops targets list [--priority] [--ats] [--quarantined] [--failing] [--limit]
app.scraping.ops targets import <file> [--format xlsx|csv] [--classify] [--dry-run]
app.scraping.ops targets classify [--probe] [--dry-run]
app.scraping.ops targets reclassify <target_id>
app.scraping.ops targets set-priority <target_id> <class>
app.scraping.ops targets enable <target_id>
app.scraping.ops targets disable <target_id>

app.scraping.ops quarantine list
app.scraping.ops quarantine review <target_id>
app.scraping.ops quarantine release <target_id> [--force-tier]
app.scraping.ops quarantine purge [--older-than-days 30]

app.scraping.ops runs list [--limit]
app.scraping.ops runs detail <run_id>
app.scraping.ops runs stats

app.scraping.ops test fetch <url> [--tier] [--dry-run]
app.scraping.ops test classify <url>

app.scraping.ops health sources
app.scraping.ops health targets
app.scraping.ops health browsers
```

---

## 8. H1B Career Pages Import

### 8.1 Source File

- Path: `C:/Users/shriy/Downloads/H1B_Sponsors_Career_Pages.xlsx`
- Sheet: "H1B Sponsors - Full List"
- Rows: 1,473 career page URLs
- Columns: Rank, Company Name, Industry, Career Page URL, Total LCA Filings (FY2024-25), H1B Grader Profile, Filing Entity Names

### 8.2 Import Process

1. Read Excel with openpyxl (skip header rows 1-4)
2. For each row, create scrape_target:
   - `url` = Career Page URL
   - `company_name` = Company Name
   - `industry` = Industry
   - `lca_filings` = Total LCA Filings
   - `source_kind` = 'career_page'
3. Run URL pattern classification (Step 1)
4. Run priority classification based on LCA filings + watchlist (Step 2)
5. Set `next_scheduled_at` based on priority class
6. Insert into `scrape_targets` table
7. Queue unknown targets for deferred HTTP probing (Step 3)

### 8.3 Extensibility

The import pipeline accepts multiple formats (Excel, CSV, JSON) and multiple data sources. Future sources:
- YC company directories
- AngelList startup listings
- Additional H1B data sources
- Manual additions via CLI or future UI

---

## 9. Legal & Safety Rails

### 9.1 Principles

- Personal use only — no resale, no redistribution
- Career pages are public by design — companies want applicants to find them
- ATS public APIs are intentionally exposed endpoints
- Job board scraping (Indeed, LinkedIn) uses conservative rate limits

### 9.2 Technical Safeguards

| Safeguard | Implementation |
|---|---|
| robots.txt compliance | Protego parser, cached 24h, respect Crawl-delay |
| Rate limiting | Per-source token bucket: 1 req/3s Indeed, 1 req/5s LinkedIn, 1-2 req/s career pages |
| 429 response handling | Immediate exponential backoff, respect Retry-After header |
| Per-domain concurrency | Max 2 concurrent requests to same domain |
| Circuit breaker | 5 failures → open circuit → 5 min cooldown |
| Content storage policy | Full content for career pages; metadata + links only for job boards |
| No authentication bypass | Never scrape behind login walls |
| No personal data | Never scrape recruiter profiles, emails, or salary data behind auth |
| User-Agent honesty | Rotate realistic UAs via fake-useragent, but never impersonate Googlebot |

---

## 10. Cost Analysis

### 10.1 Monthly Operating Cost

| Component | Approach | Cost |
|---|---|---|
| 1,473 career pages | Scrapling + Crawl4AI + Nodriver + Cloudscraper | $0 |
| Indeed/LinkedIn/Glassdoor | JobSpy (open source, local) | $0 |
| Google Jobs discovery | SerpAPI free tier (100/mo). Mode 2 runs 4x/day = ~120/mo, may slightly exceed free tier. Budget $0-10/mo if needed | $0-10 |
| TheirStack gap-fill | Free tier (200 credits/mo) | $0 |
| LLM enrichment | OpenRouter GPT-4o-mini | ~$3-5/mo |
| **Total** | | **~$3-15/mo** |

### 10.2 Dropped Services (Savings)

| Service | Was | Now |
|---|---|---|
| ScrapingBee | $49/mo | $0 — replaced by Cloudscraper + Scrapling |
| Apify | $49/mo | $0 — replaced by JobSpy + Nodriver |

---

## 11. Testing Strategy

### 11.1 Test Pyramid

**Layer 1: Unit Tests** (no network, no DB)
- URL canonicalization, salary parsing, remote-type normalization
- Content hashing, ATS registry classification, tier routing
- Priority scoring, circuit breaker state transitions
- Deduplication logic, escalation trigger detection

**Layer 2: Fixture-Based Parser Tests** (no network, saved HTML/JSON)
- Per-ATS: Greenhouse, Lever, Ashby, Workday fixtures → expected jobs
- Career pages: Amazon, Meta, Hugging Face saved HTML → expected extraction
- Edge cases: empty pages, malformed JSON-LD, CF challenge pages, JS-blank pages

**Layer 3: Service Integration Tests** (real test DB, mock fetchers)
- run_scrape lifecycle, persistence of runs and attempts
- Escalation logic end-to-end, scheduler target selection
- Content change detection, job lifecycle (first_seen → disappeared)
- Import from Excel, classification pipeline

**Layer 4: Contract Tests** (per scraper adapter)
- Known input fixture → assert required output fields present
- No invalid enums, no malformed URLs, source_name correct

**Layer 5: Failure Path Tests**
- HTTP 403/429/5xx → correct escalation
- Browser timeout/crash → graceful recovery
- Malformed HTML, empty pages, partial extraction
- 10 consecutive failures → auto-quarantine

**Layer 6: Performance Tests** (no network, simulated workload)
- 5,000 target scheduling selection: < 500ms
- 10,000 job deduplication: < 2 seconds
- 1,000 job bulk insert: < 5 seconds
- Concurrent pool simulation: 50 Tier 0 + 8 Tier 2

### 11.2 Test Infrastructure

- Separate database: `jobradar_v2_test`
- Migrations applied before test suite
- Each test uses transaction rollback for isolation
- Fixtures directory: `tests/fixtures/` with saved HTML/JSON responses
- No network calls in CI — all fetchers mocked
- pytest + pytest-asyncio for async test support

---

## 12. Implementation Phases

### Phase 1: Ingestion Control Plane (Iterative, test with real URLs)

**1a: Foundation** — build registry, test with 50 URLs
- Create scrape_targets table + migration
- Create scrape_attempts table + migration
- Add job lifecycle columns to jobs table
- Fix existing `deduplication.py` simhash to use `hashlib.md5` instead of Python `hash()` (required for deterministic cross-process behavior)
- Build ATS registry (data-driven)
- Build target import CLI (`ops targets import`)
- Import 50 H1B URLs, classify, verify

**1b: Routing** — build tier router, test with 200 URLs
- Build TierRouter with ExecutionPlan
- Build escalation engine
- Integrate with existing scrapers (Greenhouse, Lever, Ashby)
- Import 200 more URLs, run through router, verify classification
- Build scrape_attempt logging

**1c: Scheduler** — build scoring scheduler, test with all 1,473 URLs
- Build priority scoring function
- Build scheduler loop (30-min tick, batch selection)
- Build concurrency pools per tier
- Import all 1,473 URLs
- Run one full cycle, verify attempt logs and job persistence
- Build deferred HTTP probing worker

### Phase 2: Execution Engine Expansion (one scraper at a time)

**2a:** Install + integrate Cloudscraper (Tier 1 fallback)
**2b:** Port Scrapling from v1 (Tier 1-2, dual mode)
**2c:** Install + integrate Nodriver (Tier 2 default browser)
**2d:** Build Workday scraper (Tier 0)
**2e:** Install + integrate Camoufox (Tier 3)
**2f:** Install + integrate SeleniumBase UC Mode (Tier 3 backup)
**2g:** Install + integrate Crawl4AI (post-fetch extraction)
**2h:** Install + integrate BrowserForge, fake-useragent, Protego (utilities)

Each sub-step: install, write adapter, write fixture tests, verify with real URLs, commit.

### Phase 3: Data Quality & Job Lifecycle

- Content change detection with hash comparison
- Job first_seen / last_seen / disappeared_at lifecycle
- Cross-mode deduplication (career page vs aggregator)
- Parser quality reporting (extraction rates per target)
- Target health scoring

### Phase 4: Enrichment & Ranking Hardening

- Deterministic enrichment pipeline with caching
- Idempotent re-enrichment on content change
- Better feature extraction for ranking
- Per-user scoring with resume matching
- Notification thresholds for new jobs at watchlist companies

### Phase 5: Operator & Frontend Surfaces

- Wire ScraperControlPanel + ScraperLog into Settings page
- Add triggerScraper() to frontend API
- Career page management UI (list, bulk import, enable/disable)
- Live run logs with SSE
- Per-target status dashboard
- Force-reclassify / force-tier controls
- Crawl budget visualization

---

## 13. Non-Goals (Explicitly Deferred)

- Full polyglot sidecar architecture (Go/Rust) — only if scale demands it
- Distributed message queues (Redis Streams, RabbitMQ) — in-process asyncio is sufficient
- Grafana/SigNoz observability — CLI + SSE logs are sufficient for personal tool
- Crawlee-Python migration — evaluate after own policies are formalized
- Full job versioning table — content_hash + lifecycle columns are sufficient for now
- Frontend before backend correctness — operator surfaces come last
- Scraping behind login walls — explicitly out of scope (legal risk)
- Commercial data resale — personal use only

---

## 14. Tool Inventory Summary

### Active (Phase 1-2): 20 tools

**Scraping Execution (15):**
- Tier 0 (4): Greenhouse, Lever, Ashby, Workday
- Tier 1 (3): Cloudscraper, Scrapling (fast), httpx + adaptive parser
- Tier 2 (3): Nodriver, Scrapling (stealth), Crawl4AI (extraction)
- Tier 3 (2): Camoufox, SeleniumBase UC Mode
- Tier API (3): JobSpy, SerpAPI, TheirStack

**Utility / Infrastructure (5):**
- BrowserForge — fingerprint generation
- fake-useragent — User-Agent rotation
- Protego — robots.txt compliance
- typer — CLI framework
- rich — terminal output formatting

### Deferred

Crawlee-Python, ScrapeGraphAI, Katana (Go), Colly (Go), Spider-rs (Rust), aiohttp, Scrapoxy

### Dropped

Apify, ScrapingBee, Scrapy, Botasaurus, undetected-chromedriver, puppeteer-stealth

---

## Appendix A: Port Interface Definitions

Three abstract interfaces exist for the execution plane. `ScraperPort` (existing) handles end-to-end scraping (fetch + parse). `FetcherPort` and `BrowserPort` (new) handle raw page retrieval only — parsing is done separately by the extraction plane.

### A.1 ScraperPort (Existing — for ATS APIs and aggregators)

```python
class ScraperPort(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    async def fetch_jobs(
        self, query: str, location: str | None = None, limit: int = 50
    ) -> list[ScrapedJob]: ...

    @abstractmethod
    async def health_check(self) -> bool: ...

    async def close(self) -> None: ...
```

Used by: Greenhouse, Lever, Ashby, Workday (Tier 0), JobSpy, SerpAPI, TheirStack (Tier API).
Note: For Tier 0 ATS scrapers, `query` is overloaded to mean `board_token`. This is an existing convention. No change needed.

### A.2 FetcherPort (New — for Tier 1 HTTP fetchers)

```python
@dataclass
class FetchResult:
    html: str
    status_code: int
    headers: dict[str, str]
    url_final: str          # after redirects
    duration_ms: int
    content_hash: str       # SHA-256 of noise-stripped HTML

class FetcherPort(ABC):
    @property
    @abstractmethod
    def fetcher_name(self) -> str: ...

    @abstractmethod
    async def fetch(
        self, url: str, timeout_s: int = 30,
        user_agent: str | None = None,
    ) -> FetchResult: ...

    @abstractmethod
    async def health_check(self) -> bool: ...

    async def close(self) -> None: ...
```

Used by: Cloudscraper, Scrapling fast mode, httpx direct.

### A.3 BrowserPort (New — for Tier 2-3 browser fetchers)

```python
@dataclass
class BrowserResult:
    html: str               # fully rendered DOM
    status_code: int
    url_final: str
    duration_ms: int
    content_hash: str
    screenshot: bytes | None = None  # optional for debugging

class BrowserPort(ABC):
    @property
    @abstractmethod
    def browser_name(self) -> str: ...

    @abstractmethod
    async def render(
        self, url: str, timeout_s: int = 60,
        fingerprint: dict | None = None,
        wait_for_selector: str | None = None,
    ) -> BrowserResult: ...

    @abstractmethod
    async def health_check(self) -> bool: ...

    async def close(self) -> None: ...
```

Used by: Nodriver, Scrapling stealth, Camoufox, SeleniumBase UC Mode.

### A.4 ExtractorPort (New — for post-fetch extraction)

```python
class ExtractorPort(ABC):
    @abstractmethod
    async def extract_jobs(self, html: str, url: str) -> list[ScrapedJob]: ...

    @abstractmethod
    async def to_markdown(self, html: str) -> str: ...
```

Used by: AdaptiveParser, AIScraper (LLM fallback), Crawl4AI.

### A.5 ExecutionPlan and Step (New data structures)

```python
@dataclass
class Step:
    tier: int
    scraper_name: str       # key into fetcher/browser registry
    parser_name: str        # key into parser registry
    timeout_s: int = 30
    browser_required: bool = False

@dataclass
class ExecutionPlan:
    primary_tier: int
    max_tier: int
    primary_step: Step              # first attempt
    fallback_chain: list[Step]      # ordered escalation (filtered to tiers >= primary_tier)
    rate_policy: str                # key into RatePolicy registry
```

When `effective_start > 1` (from history-based learning), the `fallback_chain` is pruned at construction time to skip steps below `effective_start`. Example: if `effective_start = 2`, the chain starts at the first Step where `tier >= 2`.

---

## Appendix B: Migration Plan for Existing ScrapingService

The current `ScrapingService` in `app/scraping/service.py` is refactored incrementally, not replaced in one shot.

### B.1 What Changes

| Current | After |
|---|---|
| `ScrapingService._init_scrapers()` hardcodes 8 scraper classes | Replaced by target registry + tier router. Scrapers instantiated on-demand per target type |
| `ScrapingService.run_scrape(query, location, sources)` | Split into two paths: `run_keyword_search(query, location)` for Mode 2, and `run_target_batch(targets)` for Mode 1/3 |
| All scrapers get the same (query, location) args | Tier 0: gets board_token. Tier 1-3: gets URL. Tier API: gets (query, location) |
| `ScraperRunRequest.sources` filter | Replaced by tier routing. User does not choose sources; the system routes based on target classification |
| Career page scraping is separate in `run_career_page_scrape()` | Merged into the unified `run_target_batch()` pipeline |

### B.2 What Stays

- `ScrapedJob` dataclass (unchanged)
- `ScraperPort` interface (unchanged, ATS scrapers keep using it)
- `DeduplicationService` (unchanged, called after all extraction)
- `ScraperRun` model (extended with new columns)
- Rate limiter and circuit breaker (unchanged, extended to new scrapers)
- Event bus SSE integration (unchanged)
- Job persistence logic (extended with lifecycle columns)

### B.3 Migration Order

1. Add new tables and columns (non-breaking, additive)
2. Build new modules (`control/`, `browsers/`) alongside existing code
3. Build `run_target_batch()` as a new method on ScrapingService
4. Route career page targets through new pipeline while keyword search uses old path
5. Once validated, deprecate `_init_scrapers()` and old `run_scrape()` path
6. Remove deprecated code

---

## Appendix C: Tier API Tracking

Tier API sources (JobSpy, SerpAPI, TheirStack) are query-driven, not target-driven. They do NOT have entries in `scrape_targets` and do NOT produce `scrape_attempts` rows tied to a target.

Instead, they are tracked via the existing mechanism:
- `scraper_runs` records include their results in `jobs_found`, `jobs_new`, `jobs_updated`
- The `source` column in `scraper_runs` lists which Tier API sources were used (e.g., "serpapi,jobspy,theirstack")
- The new `tier_api_count` column on `scraper_runs` tracks how many jobs came from Tier API sources
- Individual jobs have `source = 'jobspy_indeed'`, `source = 'serpapi'`, etc. but `source_target_id = NULL` (no target)

This is a deliberate design choice: Tier API sources are supplementary gap-fillers, not the primary ingestion path. They do not need the same per-target observability.

---

## Appendix D: User Scoping

`scrape_targets.user_id` is nullable to support both shared and per-user targets. Current behavior:

- **H1B career pages** are imported with the current user's `user_id` (single-user system today)
- **Scheduler** filters by user_id: `WHERE user_id = current_user_id` (added to the scheduler query)
- **If multi-user is needed later:** targets with `user_id = NULL` are treated as global/shared; targets with a specific `user_id` are private to that user

For now, this is a single-user application. All targets belong to your user account.

---

## Appendix E: ETag / If-Modified-Since Optimization

The `etag` and `last_modified` columns on `scrape_targets` enable conditional HTTP requests:

1. On first fetch: store `ETag` and `Last-Modified` response headers
2. On subsequent fetches: send `If-None-Match: {etag}` and `If-Modified-Since: {last_modified}` headers
3. If server responds 304 Not Modified: skip parsing entirely, update `last_seen_at` on existing jobs, record attempt as `status='skipped'` with `content_changed=false`
4. If server responds 200: full parse cycle, update content_hash

This optimization is most effective for Tier 0 ATS APIs (Greenhouse, Lever) which properly support conditional requests. Generic career pages rarely implement ETag/Last-Modified.

---

## Appendix F: Priority Interval Constants (Single Source of Truth)

```python
PRIORITY_INTERVALS: dict[str, int] = {
    "watchlist": 120,   # 2 hours
    "hot": 240,         # 4 hours
    "warm": 360,        # 6 hours
    "cool": 720,        # 12 hours
}
```

This dict is the ONLY place intervals are defined. The classification pipeline, scheduler, and CLI all read from this constant. No duplication.
