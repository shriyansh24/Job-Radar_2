# RESEARCH.md

## Scraping API landscape analysis

This section compares the major “get me jobs” options in 2026 for a **local-only**, **single-user**, **real-data** job aggregation app. The market splits into three practical categories:

- **Job data APIs / datasets**: already-structured job records, often deduplicated across many sources (best for “always-on” ingestion at scale).
- **SERP-based job extraction**: structured output from **Google Jobs** results (best for discovery, saved searches, and breadth; can be noisier/duplicative).
- **Scraper infrastructure / actor marketplaces**: you scrape pages yourself (or via packaged “actors”), gaining flexibility at the cost of fragility and ToS risk.

### Comparison matrix

| Provider | Category | Best use in this app | What you get back |
|---|---|---|---|
| **entity["company","TheirStack","job postings api"]** | Job postings API + webhooks + datasets | Primary “backbone” job feed + incremental refresh + firmographics/technographics | Parsed job JSON + company enrichment; dedup + webhooks citeturn20search4turn25search16turn32search7turn32search1 |
| **entity["company","Proxycurl","linkedin data api"]** | LinkedIn-focused API | Targeted LinkedIn jobs when you explicitly need that source | Parsed job JSON + search filters; paid per call citeturn30view1turn30view0turn0search1 |
| **entity["company","ScrapingBee","web scraping api"]** | Scraper API (HTML + optional rendering) | Fallback for niche pages / company sites not covered elsewhere | HTML (and optional extraction features), rate-limited by concurrency/credits citeturn28search3turn34search0turn34search4 |
| **entity["company","Apify","web scraping platform"]** | Actor marketplace + scheduling | “Bring your own actor” ingestion for hard ATS pages / special cases | Structured datasets from actors; costs vary (compute units / pay-per-event) citeturn35search0turn35search1turn35search15 |
| **entity["company","SerpApi","serp scraping api"]** | SERP API (Google Jobs engine) | Google Jobs discovery, saved searches, broad coverage | Stable JSON `jobs_results[]`, apply links/options, filters like remote citeturn31view1turn31view0turn36search0turn36search3 |
| **entity["company","SearchAPI.io","serp api provider"]** | SERP API (Google Jobs engine) | Alternative to SerpApi; good schema + pagination token | JSON `jobs[]`, `apply_links`, `job_highlights`, `next_page_token` citeturn10view1turn10view2turn10view0 |
| **entity["company","Bright Data","web data company"]** | Datasets + scraper APIs | Enterprise-grade dataset backfills; “difficult” sites | Datasets (JSON/CSV/Parquet) + site-specific scrapers/APIs citeturn38search2turn38search3turn38search11turn38search5 |
| **entity["company","Coresignal","jobs and company data provider"]** | Job datasets + jobs API | Secondary structured jobs feed; Glassdoor/Indeed datasets | Multi-source Jobs API + datasets; explicit API rate limits citeturn33search0turn27view0turn26view2turn33search6 |
| **entity["company","Firecrawl","web data api for ai"]** | LLM-oriented scraping API | Converting pages → clean Markdown/JSON for enrichment pipelines | Multi-format outputs (Markdown/HTML/JSON/screenshot), Bearer auth citeturn19search8turn19search13turn24search9turn24search13 |
| **entity["company","ScraperAPI","proxy scraping api"]** | Proxy/render scraping API | Generic “get HTML reliably” fallback + occasional rendering | HTML via `api_key` + `url`; plans limit concurrent threads citeturn39search1turn39search0turn28search1 |
| **entity["company","JobsPikr","job data api provider"]** | Job data feed + API | Alternate job feed with dedup + enriched fields | Credit-based job download + API/feeds; feature-rich plans citeturn16view0turn17search2 |
| **entity["company","RapidAPI","api marketplace"]** | Marketplace for job/SERP APIs | Quick experimentation; variability across providers | Depends on provider; unified auth header + per-API plans citeturn17search21turn17search20 |

### Per-provider deep dives (R1)

**TheirStack — job data API (recommend as primary feed)**  
Pricing and limits: TheirStack exposes a free plan and paid plan that are explicitly documented, including **rate limits** (free: **2 req/sec**, paid: **4 req/sec**) and paging limits, plus monthly “company credits” and “API credits”. citeturn25search16 Authentication is **Bearer token via `Authorization` header**. citeturn28search0  
Coverage and data quality: TheirStack positions itself as a unified job postings API across **195 countries**, with large source coverage and job search + company enrichment. citeturn32search10turn20search12 It also documents tiered scraping frequency (e.g., **every 10 minutes** for high-volume sources; slower for smaller sites), and claims this strategy captures the bulk of new tech jobs within a day window. citeturn32search7 For incremental ingestion, TheirStack provides guidance on periodically fetching jobs (and also supports **webhooks** for “new jobs” events). citeturn32search3turn32search1  
ToS/legal posture: you still must evaluate target-site ToS for your specific usage, but the practical advantage is you’re consuming a vendor API rather than directly automating browsers against job boards.

**Proxycurl — LinkedIn jobs via API (use selectively, not as your only feed)**  
Pricing and limits: Proxycurl’s Jobs API page documents pay-as-you-go starting at **$0.009/credit**, and states **2 credits per successful API call** (for the jobs APIs shown). citeturn30view0 Community documentation also cites a **300 requests/minute limit**. citeturn0search1  
Coverage and data quality: Proxycurl demonstrates two key patterns: (1) listing jobs by company via a Jobs Listing endpoint, and (2) fetching “job details” by job URL. Example fields for listings include `company`, `job_title`, `job_url`, `list_date`, `location`, and job detail examples include fields like `employment_type`, `industry`, and `total_applicants`. citeturn30view1turn30view2  
Legal/ToS considerations: Proxycurl’s own materials emphasize they scrape **public** profiles and not private profiles (and note some fields may be missing when not publicly available). citeturn30view3 This matters because LinkedIn is historically aggressive about automated access.

**ScrapingBee — general scraping API (HTML + concurrency; good fallback)**  
Pricing and concurrency: ScrapingBee publishes plan tiers with monthly price points and included credits + concurrent requests (e.g., “Freelance” showing **$49/mo**, **250,000** API credits, **10** concurrent requests). citeturn34search0 ScrapingBee also documents plan-based concurrency explicitly, and provides credit multipliers depending on request type and proxy tier. citeturn34search1turn34search3turn34search4  
Auth and SDK support: requests authenticate via `api_key` (query parameter); docs show curl and a Python client example, indicating practical support for Python and common HTTP stacks. citeturn28search3  
ToS/legal: ScrapingBee publishes terms and an acceptable use policy; their blog guidance frames legality as generally hinging on not circumventing security measures and respecting ToS. citeturn34search2turn34search20turn34search6  
Fit: use ScrapingBee as a “break glass” tool for pages where structured APIs don’t exist, but keep it out of the hot path for major job boards.

**Apify — actor marketplace + scheduling (excellent “adapter layer”)**  
Pricing model: Apify publishes a free plan that includes **$5** to spend, and shows a compute-unit price (e.g., **$0.3 per compute unit**) alongside paid subscription tiers. citeturn35search0 For actors, pricing can also be **pay-per-event** (charged per “event” defined by the actor). citeturn35search1turn35search9  
Auth: Apify API access uses a secret API token; docs recommend Bearer auth. citeturn35search3turn35search15  
Legal/ToS risk: Apify’s own legal guidance stresses ToS constraints and warns about scraping behind logins / personal data, even if scraping public data can be lawful. citeturn35search2  
Fit: Apify is ideal when you want to outsource “scrape mechanics” per-site to actors (especially ATS pages), while your local app just calls Apify runs + ingests datasets.

**SerpApi — SERP parsing with a strong Google Jobs engine (best discovery layer)**  
Pricing and throughput limits: SerpApi publishes a free plan (example: **250 searches/month**, **50 throughput/hour**). citeturn36search0 SerpApi’s FAQ describes hourly throughput for most plans as **20% of monthly plan volume** and recommends distributing load across the hour. citeturn36search3turn36search4 They also provide an Account API to check monthly usage and hourly throughput limit. citeturn36search1  
Schema quality: SerpApi’s Google Jobs API returns structured `jobs_results[]` with fields like `title`, `company_name`, `location`, `via`, and often extensions and apply options; the docs show examples where “apply options” include an **Indeed** link, and “via” can be “LinkedIn”, “Workday”, “Lever”, etc. citeturn31view0turn31view1  
Legal/reliability signal: SerpApi is involved in active legal disputes in the scraping/SERP space; Reuters reported a Google lawsuit accusing SerpApi of illegally scraping search results at scale (SerpApi disputed the claims). citeturn36news40 SerpApi also publishes its legal documents page. citeturn36search2  
Fit: use SerpApi for “saved searches” and discovery, but architect for redundancy and failover.

**SearchAPI.io — SERP parsing alternative (strong schema + pagination token)**  
Pricing: SearchAPI advertises **100 requests free** and paid plans starting at **$40/month**. citeturn36search12  
Auth: docs allow `api_key` either in query string or as `Authorization: Bearer YOUR_API_KEY`. citeturn10view0  
Schema quality: SearchAPI’s Google Jobs response contains `jobs[]` entries (title/company/location/via/description), `job_highlights`, `detected_extensions`, `apply_link` + `apply_links[]`, and a `pagination.next_page_token`. citeturn10view1turn10view2  
Fit: implement it as a drop-in alternative to SerpApi for reliability and cost arbitrage.

**Bright Data — datasets + scraper APIs (best for backfills and “hard sites”)**  
Datasets pricing and formats: Bright Data’s Indeed job dataset pages show “Starts from **$250/100K records**” and list download formats including JSON/CSV/Parquet. citeturn38search2turn38search0 Bright Data also advertises free dataset samples (e.g., 1,000 records). citeturn38search6  
Scraper API pricing: Bright Data’s “Scraping Functions (IDE)” pricing shows **$1.5 / 1K page loads** for pay-as-you-go. citeturn38search4 Bright Data’s Web Scraper positioning also advertises “starting at $0.001/record” (important: “record” is not necessarily “page load”; architect to measure your real unit costs). citeturn38search8  
Compliance / ToS posture: Bright Data publishes a license agreement and a compliance/ethics trust center section, reflecting a stronger enterprise procurement posture. citeturn38search5turn38search9  
Fit: use as an optional “premium backfill provider” (e.g., download 6–12 months of history, then keep current via a cheaper API).

**Coresignal — multi-source jobs API + source-specific datasets**  
Throughput limits: Coresignal publishes explicit API rate limits; for Jobs APIs, the docs show (for example) **18 req/sec** for Search (POST), **54 req/sec** for Collect (GET), and **27 req/sec** for Bulk Collect. citeturn27view0  
Credit model: Coresignal explains credits are deducted for successful “200” responses; Jobs APIs consume credits per request, and bulk collects can be charged per record. citeturn26view2  
Source coverage: Coresignal publishes documentation sections for additional sources like Indeed and Glassdoor datasets, including data dictionaries. citeturn33search2turn33search6  
Fit: Coresignal is a strong **secondary structured source** when you want “multi-source + datasets” and are willing to integrate a credit/rate-limit model. Treat around-the-edges details like plan pricing as sales-dependent unless you’re using a public self-serve plan quote.

**Firecrawl — LLM-optimized scraping (best for clean text + targeted extractions)**  
Plans: Firecrawl billing documents a **Free plan** as a *one-time* allotment of **500 credits** (non-renewing), and the pricing page shows a “Scale” plan at **$599/month billed yearly** for **1,000,000 credits** and “150 concurrent requests”. citeturn24search9turn24search13  
Output formats: Firecrawl supports multiple output formats (Markdown/HTML/raw HTML/screenshot/links/JSON) and provides an advanced scraping guide that explicitly describes returning “clean markdown”. citeturn19search8turn19search7turn19search8  
Auth: Firecrawl requires a Bearer `Authorization` header containing the API key token. citeturn19search13  
Fit: use Firecrawl when you want high-quality `description_markdown` and/or schema-driven extraction for sites you can legally scrape, but keep it off the hot path for high-volume board crawling.

**ScraperAPI — proxy-based HTML retrieval (fallback + resilience tool)**  
Free tier and concurrency: ScraperAPI documents a free plan of **1,000 API credits per month** and **max 5 concurrent connections**, plus a 7-day trial with 5,000 credits. citeturn39search1 Paid plans list higher volumes and threads (e.g., “Hobby” shows 100,000 credits and 20 concurrent threads on the pricing page). citeturn39search0  
Auth: docs show the Sync API requires query parameters `api_key` and `url`. citeturn28search1  
ToS posture: terms are published; for a personal app, the key is still target-site ToS compliance. citeturn39search2

**JobsPikr — job feed API with dedup + enriched fields**  
Plan features: JobsPikr’s pricing page describes multiple plans with monthly credit caps (e.g., 1,000 / 5,000 / 25,000 credits), deduplication across sources, remote filters, and (for higher plan tiers) “ML Enriched Data Points”. citeturn16view0  
API mechanics: their Apiary documentation notes endpoints can consume fixed “volume credits” (e.g., aggregation consuming 100 credits per request). citeturn17search2  
Fit: use as an alternate/backup job feed—particularly if you value dedup and enriched features and are comfortable with a credits-per-job model.

**RapidAPI job-board APIs — convenient, variable, and provider-dependent**  
Rate limits: RapidAPI’s own documentation for marketplace plans notes free API plans are commonly limited to **1,000 requests/hour** and **500K requests/month** (actual enforcement depends on the provider’s configuration). citeturn17search21  
Auth: RapidAPI consumers typically use the `X-RapidAPI-Key` header. citeturn17search20  
Fit: great for quick experiments, but you should architect a provider abstraction because endpoints, quotas, and schema quality vary widely across listings.

## Target job board and ATS extraction mechanics

This section documents **practical extraction strategies** that avoid brittle DOM scraping where possible, and instead prioritize widely-used public endpoints, job APIs, and SERP-derived structured data.

### LinkedIn Jobs

**Recommended approach**: Prefer a vendor API that returns structured records (Proxycurl) rather than direct website scraping.

**Proxycurl endpoints and schema** (examples from Proxycurl docs):

- List jobs for a company (query-filterable):
```text
GET https://nubela.co/proxycurl/api/v2/professionalsocmed/company/job
Authorization: Bearer <API_KEY>
```
Example fields for each listing include `company`, `company_url`, `job_title`, `job_url`, `list_date`, `location`. citeturn30view1

- Fetch a job’s details:
```text
GET https://nubela.co/proxycurl/api/professionalsocmed/job?url=<JOB_URL>
Authorization: Bearer <API_KEY>
```
Example fields include company object, `employment_type`, `industry`, and `total_applicants` (where available). citeturn30view2

**Note on legal/ToS**: Proxycurl emphasizes they scrape only public profiles/data, and that some fields are inherently inaccessible when not public. citeturn30view3

**Alternative approach**: Use Google Jobs results and filter to entries where `via` is “LinkedIn” (this is not “LinkedIn’s own API”, but it can surface LinkedIn-sourced listings). SerpApi’s Google Jobs examples show `via: "LinkedIn"` for some results. citeturn31view1

### Indeed

**Recommended approach**: treat Indeed as either (a) a structured dataset provider problem, or (b) a discovery layer via Google Jobs—not a DIY HTML scraping target.

- **Dataset / scraper provider route**: Bright Data sells an Indeed Job Posting dataset that starts at **$250/100K records**, and also points to a dedicated Indeed Scraper API as an alternative to purchasing a dataset. citeturn38search2turn38search0  
- **Multi-source dataset route**: Coresignal’s documentation includes “Indeed Data” with an “Indeed Jobs” dataset dictionary, indicating availability as a structured source. citeturn33search2turn33search10  
- **Google Jobs route**: SerpApi’s Google Jobs schema includes `apply_options[]` which can contain an Indeed apply link. citeturn31view0

**Freshness strategy**: For vendor feeds, set refresh according to the provider’s published capture cadence; for example, TheirStack documents scraping frequencies by source tier (high volume as often as every 10 minutes). citeturn32search7

### Google Jobs via SERP APIs

**Recommended approach**: This should be a first-class ingestion lane in the app because it provides broad discovery and already-parsed schema.

**SerpApi (Google Jobs engine)**  
- A “work from home” filter is documented via `ltype=1`. citeturn31view0  
- The returned schema includes `jobs_results[]` (structured entries) and can include multiple apply options and “via” fields like “Lever”, “Workday”, “LinkedIn”, etc. citeturn31view1turn31view0  
- Pricing/limits: free tier and hourly throughput are published. citeturn36search0turn36search3

**SearchAPI.io (Google Jobs engine)**  
- Auth supports either query param or Bearer header in docs. citeturn10view0  
- Schema includes `jobs[]` entries, `job_highlights`, `apply_link`, `apply_links[]`, and `pagination.next_page_token`. citeturn10view2turn10view1

**Operational note**: SearchAPI includes a `request_time_taken` field in its sample metadata, which can be logged for monitoring latency. citeturn10view1

### Glassdoor

**Recommended approach**: Prefer structured datasets/APIs; treat DOM scraping as a last resort.

- Bright Data offers a Glassdoor dataset and states you can receive dataset updates on daily/weekly/monthly/custom schedules, and also points to using a Glassdoor scraper if you don’t want to buy a dataset. citeturn38search3  
- Coresignal documents Glassdoor datasets (including “Glassdoor Jobs”) and provides data dictionaries. citeturn33search6turn33search17

### Company ATS direct pages (highest leverage lane)

This is the most reliable “direct-to-source” method, because you avoid aggregators and often get canonical apply URLs.

**Greenhouse**  
Greenhouse’s Job Board API is explicitly documented as a public JSON representation of jobs; GET endpoints require **no authentication**. citeturn21view0  
- List jobs:
```text
GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs
```
Optional: `content=true` includes full description + departments/offices. citeturn21view1  
Example fields include `id`, `internal_job_id`, `title`, `updated_at`, `location.name`, `absolute_url`, and when `content=true`, `content`, `departments[]`, `offices[]`. citeturn21view0turn21view1

**Lever**  
Lever maintains a public repository documenting its postings REST API. It confirms a base URL of `https://api.lever.co/v0/postings/` and that published postings are publicly viewable; it also notes limitations (e.g., no full-text search across open jobs). citeturn22view0  
A common listing pattern is:
```text
GET https://api.lever.co/v0/postings/<COMPANY>?mode=json
```
Field-level examples for typical Lever JSON include title (`text`), `categories.location/team/commitment`, and application URL (`applyUrl`). citeturn22view1turn22view3

**Ashby**  
Ashby documents a public job postings API:
```text
GET https://api.ashbyhq.com/posting-api/job-board/{JOB_BOARD_NAME}?includeCompensation=true
```
Schema includes `jobs[]` with `descriptionHtml`, `descriptionPlain`, `publishedAt`, `employmentType`, `jobUrl`, `applyUrl`, and an optional compensation sub-object when `includeCompensation=true`. citeturn40view0

**Workday**  
Workday has official APIs for customers and partners (exposed as documented web services), but public career sites are a separate surface area and are often not “officially documented for scraping.” citeturn23search2  
Practical approach for a personal tool: treat Workday feeds as either (a) vendor job APIs/datasets, or (b) specialized scrapers/actors per company portal. Apify actors explicitly target “Workday-powered career sites” and show output fields like `url`, `descriptionHtml`, `description`, `scrapedAt`. citeturn23search6turn23search14  
Also, Google Jobs often labels postings “via Workday,” which can be harvested via SERP APIs for discovery. citeturn31view1

### Handshake

entity["company","Handshake","student career platform"] is not positioned as a public job-board scraping target; it provides an EDU API help-center documentation surface for institutional integrations, which implies access and permissions are controlled rather than “crawl freely.” citeturn5search0turn5search5  
For a local personal tool, treat Handshake as a **manual-import** source unless you have explicit authorized API access.

### Wellfound

entity["company","Wellfound","startup jobs platform"] (formerly AngelList Talent) is frequently discussed in the scraping community as being behind modern web-app patterns (e.g., API-driven frontends), making it prone to breakage if scraped directly. A safer posture for a personal tool is: (1) prefer SERP-based discovery and (2) store canonical apply links rather than attempting full site crawling.

## Data schema and normalization strategy

A personal “command center” needs two things simultaneously:

- **A stable normalized core** for dedup, status tracking, and UI queries.
- **A flexible “raw payload” layer** so you can ingest multiple sources without losing information.

### Canonical job record model

Use **Schema.org JobPosting** as a conceptual baseline for web-native fields like `datePosted` and `baseSalary`. citeturn20search0 For remote roles, Google’s job posting structured data guidance distinguishes `jobLocationType` and `applicantLocationRequirements`, which maps well to your `remote_type` and geo constraints. citeturn20search1 HR Open Standards has also referenced converging around schema.org JobPosting as part of broader job exchange schemas like JDX. citeturn20search11

### Recommended normalized tables

A practical SQLite-first schema:

- `jobs` (one row per deduplicated canonical job)
- `job_sources` (many→one: each source’s representation pointing at a canonical job)
- `companies` (normalized company identity, domain, logo, metadata)
- `locations` (structured geo + remote flags)
- `job_events` (status timeline: saved/applied/interview/etc.)
- `job_notes` (freeform notes)
- `tags` + `job_tags` (many-to-many)
- `job_ai` (summary, skills extraction, red/green flags, scores)
- `job_embeddings` (vector storage reference, model version, embedding)

Keep `raw_json` columns on `job_sources` (and optionally `jobs`) for traceability.

### Deduplication logic across sources

Dedup is fundamentally a **resolution problem**: different sources describe the “same opening” with small differences.

To anchor dedup:

- Prefer a canonical apply URL when it’s stable (ATS apply URLs are often best; SERP aggregator links are not).
- Maintain **per-source IDs** (e.g., Greenhouse job `id`, Lever posting `id`, SERP API `job_id`) on `job_sources`.
- Compute a **content fingerprint** (hash of normalized `title + company_domain + location + first-N chars of description_clean`) and treat that as a candidate key for clustering.

This architecture aligns with how multi-source providers describe their own value proposition (e.g., JobsPikr explicitly advertises “Deduplication Across Sources”). citeturn16view0

### Incremental refresh strategy

For sources that support it, incremental sync should be **cursor-based** (“fetch everything updated since T”).

Two pragmatic lanes:

- **Vendor job feeds**: follow the provider’s published capture cadence; for example, TheirStack documents a tiered scraping frequency and offers guidance on periodically fetching jobs while minimizing API cost. citeturn32search7turn32search3  
- **SERP-based searches**: treat saved searches as “streams” and page via provider pagination tokens (SearchAPI’s `next_page_token`) while storing the returned `search_metadata` and request time metrics for observability. citeturn10view0turn10view1turn10view2

### Schema versioning

Version your schema in two layers:

- `db_schema_version` (migrations)
- `ai_schema_version` (the JSON schema you expect from extraction/enrichment)

This matters because even mature tools evolve schema formats; for example, Chroma explicitly maintains migration tooling as schemas/data formats change. citeturn12search0 For your local tool, a lightweight migration system is enough (because you control the machine), but treat it as mandatory for long-lived usage.

## Local-first architecture and stack recommendation

The goal is a **localhost-only** “job command center” that is fast with 10k–100k jobs, supports background ingestion, full-text search, and local AI enrichment.

### Database recommendation

Use **SQLite** as your primary OLTP store, with:

- **WAL** mode for better read/write concurrency (many readers, single writer). citeturn11search0turn11search12  
- **FTS5** for full-text search over `description_clean` and `title`. citeturn11search1  

DuckDB is a strong optional add-on for analytical dashboards and aggregations, and multiple industry comparisons describe the split: SQLite for transactional workloads, DuckDB for analytics. citeturn11search3turn11search7

### Vector / semantic search recommendation

For local semantic matching:

- Generate embeddings with `all-MiniLM-L6-v2` (384-dimensional vectors) for speed/quality balance. citeturn12search1turn12search4  
- Store vectors either:
  - in SQLite via a vector extension like `sqlite-vec` (portable, “fast enough,” but explicitly **pre-v1** and may have breaking changes), citeturn12search9 or
  - in a local embedded vector DB like Chroma persistent client (good developer ergonomics and documented persistence use cases). citeturn12search3  

If you choose PostgreSQL later, `pgvector` supports exact search by default and optional ANN indexes like HNSW and IVFFlat. citeturn12search2

### Local LLM enrichment recommendation

Use entity["company","Ollama","local llm runner"] as the primary local inference runtime because it supports structured outputs via JSON schema grounding (critical for reliably extracting `skills_required[]`, `salary`, and standardized fields). citeturn13search3 Model selection for this workload:

- `llama3.2:3b` for lightweight summarization and extraction tasks. citeturn13search10  
- `qwen2.5:7b` for stronger extraction/categorization at moderate latency. citeturn13search2  

As a fallback, use entity["company","OpenAI","ai company"]’s API with `gpt-4o-mini` for “difficult” postings or when local throughput is insufficient. Pricing is published as **$0.15 / 1M input tokens** and **$0.60 / 1M output tokens** for `gpt-4o-mini`. citeturn13search4  
A rough cost estimate for enriching one job description of ~2,000 input tokens:
- Input: 2,000 × $0.15 / 1,000,000 ≈ **$0.0003**
- Output: if you budget ~500 output tokens for JSON + summary, 500 × $0.60 / 1,000,000 ≈ **$0.0003**
Total ≈ **$0.0006 per job** (plus any tool overhead). citeturn13search4

### Final stack decision

For a local-only app with Python-heavy scraping + ML, the most cohesive stack is:

- Backend: Python web API server + background scheduler + worker pool
- DB: SQLite (WAL + FTS5) as primary; optional DuckDB for analytics
- Semantic: sentence-transformers embeddings + sqlite-vec (or Chroma)
- LLM: Ollama local + OpenAI fallback
- Frontend: a SPA with virtualization + SSE/WebSocket for live scrape progress

### Architecture diagram

```mermaid
flowchart TB
  UI[Local Web UI\n(filters, kanban, search)] -->|HTTP| API[Local API Server]
  UI <-->|SSE/WebSocket| EVENTS[Live events\n(scrape progress, counters)]

  API --> DB[(SQLite\njobs + sources + FTS5)]
  API --> VEC[(Vector store\nsqlite-vec or Chroma)]
  API --> QUEUE[Job Queue\nscrape + enrich tasks]

  QUEUE --> INGEST[Ingestion workers\n(Serp APIs,\nJob data APIs,\nATS endpoints)]
  INGEST --> NORMALIZE[Normalization\n+ dedup]
  NORMALIZE --> DB

  QUEUE --> ENRICH[AI enrichment\nskills/summaries/scores]
  ENRICH -->|embeddings| VEC
  ENRICH --> DB

  INGEST --> EXT[Optional scraping providers\n(ScrapingBee/ScraperAPI/Firecrawl)]
  ENRICH --> LLMLOCAL[Local LLM runtime]
  ENRICH --> LLMFALLBACK[Optional cloud LLM fallback]
```

This diagram intentionally separates: **(1) ingestion adapters**, **(2) normalization+dedup**, and **(3) enrichment**, so you can swap data sources without rewriting the core.

## Responsible scraping, rate limiting, and legal risk

This project lives in a high-risk ToS environment because major job boards actively restrict automation. A “world-class” design for a personal tool prioritizes **compliance, stability, and observability**, not “stealth”.

### Practical guardrails

- Prefer **public job-board APIs and ATS endpoints** intentionally exposed for job listings (e.g., Greenhouse Job Board API with unauthenticated GET endpoints). citeturn21view0  
- Prefer **vendor job APIs / datasets** over direct DOM scraping of the job boards, especially for LinkedIn/Glassdoor/Indeed (Bright Data and Coresignal explicitly package these sources as datasets, which reduces your operational brittleness). citeturn38search2turn33search6turn33search2  
- Treat “anti-bot” as an engineering constraint and a legal risk. Scraping providers and legal guides repeatedly emphasize that legality and acceptability are shaped by ToS and by whether you circumvent access controls. citeturn35search2turn34search6  

### Rate limiting and backoff

When you use vendor APIs, follow their stated limits:

- TheirStack publishes explicit req/sec limits by plan and uses 429 responses when exceeded. citeturn25search16turn24search0  
- Coresignal publishes explicit per-endpoint req/sec limits. citeturn27view0  
- SerpApi publishes throughput-per-hour constraints and documents 429 behavior when throughput is exceeded. citeturn36search3turn36search7  

Also, the industry is converging on standardized rate limit headers (IETF RateLimit header draft); implement a generic rate-limit middleware that can consume `RateLimit-*`-style headers where present. citeturn25search17turn25search3

### Browser automation choice

When you truly must automate a browser (e.g., for a JS-heavy ATS):

- Playwright supports Chromium/WebKit/Firefox and multiple languages, which makes it a strong default for cross-browser automation. citeturn15search0turn15search6  
- Puppeteer is a high-level automation library for Chrome/Firefox and is explicitly headless-by-default. citeturn15search4turn15search1  
- Selenium remains a broad umbrella around WebDriver-based automation. citeturn15search11  

### Anti-bot landscape awareness

Modern bot protection is often provided by vendors such as entity["company","Cloudflare","web security company"], entity["company","Akamai","cdn and security company"], entity["company","PerimeterX","bot mitigation company"], entity["company","DataDome","bot protection company"], entity["company","Kasada","bot detection company"], and entity["company","Shape Security","fraud prevention company"]. citeturn15search2turn15search23  
For a personal tool, the correct posture is: **don’t try to beat these systems**. Route around the problem using public endpoints, SERP-derived results, and vendor APIs.

### Jurisdiction and personal/non-commercial framing

If you are operating from entity["country","United States","country"], you should assume ToS enforcement (account bans, IP blocks, legal threats) is a realistic risk even when the data is publicly visible. Practical “ethical scraping” guides emphasize ToS and restrictions around private/personal data. citeturn35search2turn34search6

## Competitive feature analysis and open-source landscape

This section maps what commercial tools emphasize so your local app can match the “feel” while staying local-first.

### What Simplify, Jobright, and Teal optimize for

entity["company","Simplify.jobs","job search tool"] centers on **application autofill**, tracking, and resume keywording. Their Copilot page claims autofill, resume tailoring, and automatic application tracking, and positions the extension as free. citeturn14search0turn14search4turn14search8  
entity["company","Jobright.ai","ai job search platform"] positions itself as an AI “copilot” that provides matched jobs, autofill, resume support, and suggested connections. citeturn14search1turn14search13  
entity["company","Teal","career platform"] emphasizes a job tracker and organization layer; Teal states you can bookmark and track unlimited jobs and contacts for free, and markets premium pricing separately. citeturn14search6turn14search2turn14search18

image_group{"layout":"carousel","aspect_ratio":"16:9","query":["job application tracker dashboard UI","kanban job application tracker interface","resume keyword match dashboard UI","Teal job tracker chrome extension screenshot"],"num_per_query":1}

### Feature set worth replicating locally

The commercial pattern is consistent:

- **Unified capture**: “Save job from anywhere” via a browser extension + canonical job URL storage (Teal explicitly markets saving from many job boards). citeturn14search18turn14search10  
- **Single source of truth**: A job tracker as the “system of record” (Teal’s tracker framing). citeturn14search6turn14search10  
- **Assistance layer**: Autofill and “match quality / keyword missing” overlays (Simplify and Jobright market this directly). citeturn14search4turn14search13  

For your local app, translate this into:

- A **saved job** primitive (`job_sources` row) from any URL.
- A **canonical job** primitive (`jobs` row) after normalization/dedup.
- A **status pipeline** (new → saved → applied → interviewing → offer) with timestamps and notes.
- **Local scoring** that is explainable: show which skills/keywords drove the match score (derived from embedding similarity + extracted skills lists).

### Open-source projects that already solve pieces

GitHub’s “job-scraper” topic highlights multiple scrapers and aggregators, demonstrating the ecosystem breadth but also how fragmented implementations are. citeturn14search3  
A few noteworthy patterns:

- “Local-first AI job scraper + dashboard” (privacy-focused) projects exist and combine scraping + local UI. citeturn14search11  
- There are self-hosted aggregators that layer LLM structuring and analysis on top of job listings. citeturn14search23  
- There are also standalone “job tracker” full-stack apps emphasizing local DB choices (often SQLite first). citeturn14search15  

The gap your project fills is not “can I scrape a site,” but “can I build a coherent, durable, locally-run system” that unifies: ingestion adapters + dedup + search + status workflow + AI enrichment, while minimizing direct job-board scraping risk via structured providers and ATS endpoints.