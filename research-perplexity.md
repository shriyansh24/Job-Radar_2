# Personal Job Scraper / Aggregator – RESEARCH.md

## 0. Overview & Goals

This document defines the research, architecture, and technology choices for a fully local, developer‑focused job aggregation and scraping app similar in capability to Simplify, Jobright, and Teal, but running entirely on localhost with no multi‑user concerns.
It covers the external data providers, direct scraping mechanics, unified job schema, local stack, anti‑bot strategies, and competitive feature set to replicate or exceed commercial tools.[^1][^2]

***

## R1 – Scraping API Landscape Analysis

### R1.1 High‑Level Comparison

_Key for columns: Src = primary sources it aggregates; PL = main programming language SDKs; Data = primary output format; LL = likely legal risk & ToS friction for personal use (low/med/high, not legal advice)._

| Provider | Pricing (entry tier, 2025–26) | Rate limits / concurrency | Src focus | Data quality / format | SDK support | Major boards / ATS | LL (personal use) |
|----------|-------------------------------|---------------------------|----------|------------------------|-------------|--------------------|-------------------|
| TheirStack | Free 200 API credits/mo; paid from ≈$59/mo for 1.5k jobs, $169/mo for 10k jobs, ~$600 for 100k, ~$1.5k for 1M jobs[^1] | Credit‑based, REST; no hard RPS publicly, but webhook + async model; per‑record credits (1/job)[^3] | Multi‑source job postings + tech stack | Parsed JSON jobs, enriched with salary fields and some normalisation[^4][^1] | REST; examples in Python/Node via HTTP | Multi‑board aggregation, focus on LinkedIn, Indeed and company career pages (indirect via their crawlers)[^1] | Low–med (API‑based, but commercial data resale in ToS) |
| Proxycurl (Enrich Layer Jobs API) | Credit system: Jobs API uses 2 credits/job; Starter $49/mo for 2.5k credits (~1.2k jobs), Pro $899/mo for 89.9k credits (~44k jobs)[^1] | Rate limit by subscription plan: 2 req/min (PAYG) up to 300 req/min on $1,899+ plans[^5] | LinkedIn jobs (and broader LinkedIn people/company data) | Structured JSON for LinkedIn job listing and job profile endpoints (title, description, company, seniority, applicants, etc.)[^6] | Official Python & JS SDKs; plain REST examples[^5][^7] | LinkedIn Jobs only; no Indeed/Glassdoor/ATS[^1][^7] | Low–med (API abstracts LinkedIn; still subject to LinkedIn data use policy) |
| ScrapingBee | Freelance: 250k credits/$49.99, Startup: 1M/$99.99, Business: 3M/$249.99, Enterprise up to 41M credits;$[^8] | Concurrency‑limited: basic plan 5–10 concurrent req; docs mention 5 concurrent on smallest plan[^9][^8] | Generic web; you point at any URL | Raw HTML or rendered HTML via JS browser, optional screenshot; you parse yourself[^10][^8] | REST; language‑agnostic; examples for Python/Node | Any site including LinkedIn/Indeed/Glassdoor/ATS, but you handle anti‑bot | Med–high (you are directly scraping target sites) |
| Apify Actors (job scrapers) | Actor‑based billing by compute units & per‑result; many job actors charge e.g. $14/1k jobs (Handshake), similar rates for LinkedIn/Indeed/Google Jobs actors[^11][^12] | Platform enforces per‑account concurrency; each actor has its own recommended max; runs orchestrated in Apify cloud[^13] | Actor‑specific: LinkedIn Jobs, Google Jobs, Indeed, Handshake, Workday, etc.[^12][^14] | Structured JSON output from each actor (jobs array with title, company, description, salary, etc.)[^12][^14] | REST API, JS & Python clients; you call actor run endpoints | LinkedIn Jobs, Indeed, Google Jobs, Handshake, Workday and others via marketplace actors[^12][^14] | Low–med (Apify assumes scraping risk; still subject to target ToS) |
| SerpApi (Google Jobs) | Free tier ≈100–250 searches/mo; paid plans like Developer 5k searches ≈$75/mo, 15k & 30k tiers higher[^15][^16][^17] | Hourly throughput limit 20% of monthly quota (e.g. 1k searches/hr on 5k plan); cached searches free[^18][^19] | Google Jobs SERPs | Structured JSON `jobs_results[]` arrays with title, company, location, snippets, and `apply_options` links; optional raw HTML[text][^20][^21] | REST; official clients for Python, Node and others | Indirectly covers LinkedIn/Indeed/ZipRecruiter/etc. via Google Jobs aggregation[^20][^21] | Med (Google ToS restrict automated search, but SerpApi assumes proxy/CAPTCHA risk) |
| SearchAPI.io (Google Jobs) | Developer: $40/mo for 10k searches ($4/1k); Production: $100/35k ($3/1k); BigData: $250/100k; Scale: $500/250k[^22] | Limit: can only use up to 20% of plan credits per hour (throughput throttle)[^22] | Google Jobs SERPs | JSON with `jobs` array including title, company, location, via, share link and related metadata[^23][^24] | REST; examples for Python and generic HTTP[^23] | Same coverage as Google Jobs (LinkedIn, Indeed etc. via Google aggregation)[^24] | Med (similar to SerpApi) |
| Bright Data (Scraper API + datasets) | Scraper APIs ~ $1.5/1k records PAYG, down to ~$0.75/1k on subscriptions; LinkedIn/Indeed/Glassdoor job APIs in this range[^15][^25]; Indeed dataset pricing example: $250/100k records, volume discounts[^26][^27] | High throughput; API plans specify RPS caps but are generous for enterprise workloads[^15][^27] | Dedicated scrapers + prebuilt datasets for LinkedIn, Indeed, Glassdoor and others[^15][^26][^28] | Clean JSON/CSV/Parquet datasets with enriched job attributes; Scraper API returns structured JSON job objects[^15][^26][^28] | REST; official SDKs & code examples; language‑agnostic | LinkedIn Jobs, Indeed Jobs, Glassdoor Jobs, plus many more[^15][^26][^28] | Low–med for API/datasets (they emphasise compliance); you must still respect local laws |
| Coresignal (Jobs API) | Credit‑based: Starter from $49/mo, but practical job volumes usually start at Pro ~$800/mo and Premium ~$1,500+/mo; datasets start ≈$1,000/mo[^29][^30] | REST with API key; rate limits negotiated by plan[^31] | Multi‑source jobs (LinkedIn, Indeed, Glassdoor, Wellfound)[^32][^33] | Structured multi‑source jobs JSON (title, desc, company, skills, seniority, etc.), with multi‑source dedup tagging[^31][^33] | REST; generic HTTP; integration guides; MCP server support for LLMs[^33] | LinkedIn, Indeed, Glassdoor, Wellfound; no direct ATS scraping[^32] | Low–med (aggregated dataset provider, but very commercial‑oriented) |
| Firecrawl | Free: 500 one‑time credits; Hobby: $16/mo for 3k credits; Standard: $83/mo for 100k; Growth: $333/mo for 500k[^34] | Per‑page credit system; timeouts and concurrency limits; designed for batch crawling rather than ultra‑high RPS[^35] | Any website, optimised for LLM‑ready content | Returns clean Markdown and/or HTML, plus optional JSON structured extraction via v2 JSON mode with `formats: [{ type: "json", schema: {...} }]`[^35][^36] | Official Python client and REST API; simple usage for structured extraction[^35] | Any job description page (company careers, ATS, boards) but not job‑specific product | Med–high (you scrape targets directly, Firecrawl just helps with structure) |
| ScraperAPI | Free: 1k credits/mo with 5 concurrent connections[^37][^38]; Hobby $49/mo for 100k credits; Startup $149/mo for 1M; Business $299/mo for 3M; higher tiers up to 5M+ credits[^39][^40] | Concurrency caps by plan: Hobby ~20 threads, Startup 50, Business 100, Scaling 200; complex sites may consume 5–25 credits/request[^40][^41] | Generic web (HTML) with proxy+CAPTCHA handling | Raw HTML with optional JS rendering; you parse the DOM/JSON yourself[^37][^41] | REST; examples for many languages; simple query‑string API | Any job/ATS site (LinkedIn, Indeed, Glassdoor, Greenhouse, Lever, etc.) if you handle selectors/flows | Med–high (you still scrape targets; provider just manages infra) |
| JobsPikr | Tiered job feed/data pricing (exact numbers depend on plan), with live XML/JSON feeds and API; marketed as “affordable” vs enterprise datasets; free trial available[^42][^43] | API supports real‑time job feeds; rate limits depend on contract; focuses on daily refreshed feeds rather than high‑RPS interactive use[^43] | Aggregated jobs from “leading job boards” globally[^44][^43] | Structured job JSON/CSV/XML with title, description, salary, location, jobboard name, contact data, etc.[^42][^43] | REST; multi‑language examples; XML feeds for ETL[^42][^43] | Major global job boards (Indeed‑style boards; exact list not fully disclosed) | Low–med (data feed provider) |
| RapidAPI Job APIs (JSearch, Jobs Search Realtime, etc.) | JSearch: free 200 req/mo basic tier; higher paid tiers through RapidAPI marketplace[^45]; Jobs Search Realtime API pricing via RapidAPI (plans vary) | Rate limits enforced per RapidAPI plan (basic hard monthly limit, per‑second/ minute caps defined per API)[^45] | Aggregated jobs from Indeed, ZipRecruiter, Glassdoor and others[^46] | JSON with job listings including title, company, location, salary, URL, etc.[^45][^46] | Any language via RapidAPI HTTP client; copy‑paste code snippets | Jobs from Indeed, ZipRecruiter, Glassdoor (Jobs Search Realtime Data API) and other boards via additional APIs[^46] | Med (RapidAPI handles infra; still must respect each site’s ToS) |

#### Takeaways for a local personal tool

- At small to mid volume (≤10k jobs/day), TheirStack, SerpApi/SearchAPI, and JobsPikr give the best cost vs. coverage vs. engineering‑effort trade‑off if you are comfortable paying a SaaS provider.[^15][^43][^1]
- Proxycurl is excellent if you want _only_ LinkedIn jobs with rich LinkedIn‑native fields, but cost scales steeply beyond ~50k jobs/month.[^5][^6][^1]
- ScrapingBee/ScraperAPI/Firecrawl are generic building blocks; you trade cost predictability and job‑specific features for maximal control and ability to scrape niches not covered by APIs.[^10][^37][^8][^35]
- Bright Data and Coresignal are priced and architected for enterprise pipelines, not an individual running everything locally, unless you want to occasionally buy a static dataset snapshot.[^29][^26][^32][^15]

### R1.2 Per‑API Deep Dives (Design‑Relevant Aspects)

#### TheirStack

- **Coverage & data model** – Aggregates job postings from top job boards and company careers, exposing a `job_posting` JSON with salary fields (`salary_string`, `min_annual_salary`, etc.) and normalised metadata.[^4][^1]
- **Pricing model** – Dual credit system; for your use case you care mainly about API credits (1 per job returned via Job Search endpoint); free 200 credits/month then tiers at 1.5k, 5k, 10k, 50k, 100k, 1M jobs as in the comparison table.[^3][^1]
- **Limits & auth** – API key in header, HTTPS REST; rate limiting not aggressively documented but primarily governed by credit consumption per job.[^3]
- **Pros** – Turnkey multi‑source job data with dedup and salaries; generous free tier; good for bootstrapping while you implement your own scrapers.[^1]
- **Cons** – Costs can reach hundreds of dollars/month if you push toward 100k+ jobs, and the schema is provider‑specific so you still need a local normalisation layer.[^1]

#### Proxycurl (Enrich Layer Jobs API)

- **Scope** – Purpose‑built for LinkedIn data: jobs, companies, and people.[^7][^5]
  - `company/job` listing endpoint returns jobs posted by a company with fields like company, `job_title`, `job_url`, `list_date`, and location.[^6]
  - Job profile endpoint takes a LinkedIn job URL and returns detailed job JSON: title, description, seniority, employment type, industry, `apply_url`, applicants count etc.[^47][^6]
- **Pricing & limits** – Jobs endpoints consume 2 credits per job; subscription tiers from $49/mo (2.5k credits) up to unlimited annual plans; credit‑based rate limits per minute from 2 req/min (PAYG) up to 300 req/min on high tiers.[^5][^1]
- **Auth & SDKs** – Bearer token in `Authorization` header; official Python and JS SDKs and good cURL examples.[^7][^5]
- **Pros** – Very clean LinkedIn‑native job JSON, precise company matching, and built‑in rate limiting; minimal anti‑bot burden for you.[^6][^5]
- **Cons** – Only LinkedIn; credit system gets expensive if you need hundreds of thousands of jobs; still subject to LinkedIn‑related compliance constraints.[^48][^1]

#### ScrapingBee

- **Scope** – Full‑page scraping API with optional JS rendering and proxy rotation; you send `url` + query params and get HTML back.[^8][^10]
- **Pricing & concurrency** – Plans from ~$49.99/mo for 250k credits up to multi‑million credits on enterprise; basic plans limit concurrent requests (5–10 concurrent connections).[^9][^8]
- **Data quality** – You receive raw or rendered HTML; they handle bots/proxies, but all DOM traversal and schema extraction is on you.[^10]
- **Pros** – Excellent when you need control (e.g. scraping unusual ATS, or pages with tricky JS) but don’t want to manage proxies, headless browsers, and CAPTCHAs yourself.[^9][^10]
- **Cons** – No job‑aware primitives (no implicit pagination or job JSON); credit consumption can spike on heavy JS pages, and you’re still scraping in the legal sense.[^41][^8]

#### Apify

- **Scope** – Marketplace of hosted scrapers (“actors”), many of which are dedicated job actors like LinkedIn Jobs, Indeed Jobs, Google Jobs, Handshake, Workday, etc.[^12][^14]
- **Pricing** – Each actor charges by compute units (CU) and sometimes additionally per result; Handshake Jobs Scraper is priced “from $14 / 1,000 jobs”, many LinkedIn/Indeed actors are in a similar per‑thousand band.[^11][^12]
- **Data** – Actors emit structured JSON arrays in datasets that you pull via REST, often with job‑specific fields (title, company, location, description, salary, apply URLs, recruiter info, etc.).[^14][^12]
- **Pros** – Very fast way to access multiple boards/ATS without building scrapers; actors are maintained by specialists (e.g. Fantastic.jobs for LinkedIn/Workday) and updated when targets change.[^12][^14]
- **Cons** – You are tied to Apify’s cloud; using this in a strictly offline/local‑only tool requires periodically exporting datasets and importing them locally, rather than live scraping from localhost.

#### SerpApi (Google Jobs)

- **Scope** – Google Jobs SERPs, either via the `google_jobs` engine or Google Jobs Results embedded in standard search.[^20][^21]
- **Pricing & rate limits** – Free tier gives on the order of 100–250 searches/month; paid plans at 5k, 15k, 30k, etc. with monthly caps; per‑hour throughput set at 20% of monthly search allowance.[^18][^16][^17]
- **Data structure** – JSON includes `jobs_results` array with fields such as `title`, `company_name`, `location`, `via` (source board), snippets, detected extensions (e.g. `posted_at`, salary), and `apply_options` for canonical apply URLs.[^21][^20]
- **Pros** – One of the easiest ways to get broad job coverage across many boards and ATS with structured JSON and minimal anti‑bot work.[^17][^20][^21]
- **Cons** – Indirect; you are limited to what Google chooses to index and expose, and you don’t see every field that a native ATS API would return (e.g. full HTML descriptions not always present).[^20]

#### SearchAPI.io (Google Jobs alternative)

- **Scope** – Google Jobs scraping similar to SerpApi but with different pricing and some extra parameters (pagination via `next_page_token`, location settings, etc.).[^23]
- **Pricing & rate limits** – Developer/Production/BigData/Scale plans between $40–$500/mo for 10k–250k searches; capped at 20% of plan volume per hour to avoid abuse.[^22]
- **Data** – JSON with `jobs` array containing position, title, `company_name`, `location`, `via`, and other fields; `search_information` provides metadata like detected location.[^24][^23]
- **Pros/Cons** – Similar trade‑offs to SerpApi; might be cheaper at higher volumes, but ecosystem and tooling around SerpApi is richer.

#### Bright Data

- **Scope** – Two relevant offerings: (1) job‑specific scraper APIs (LinkedIn Jobs, Indeed Jobs, Glassdoor Jobs, etc.), (2) static or subscription datasets (e.g. Indeed/LinkedIn job listings).[^26][^28][^15]
- **Pricing** – Scraper APIs are typically ~$1.5 per 1k records PAYG, falling to ~$0.75 per 1k at $499–$999/mo subscription levels; datasets like the Indeed dataset priced at $250/100k records with volume discounts.[^27][^15][^26]
- **Data** – Very structured JSON/CSV/Parquet with tens of fields per job: job ID, title, company, location, description, salary, posting/refresh dates, ratings, etc.[^28][^26]
- **Pros** – Almost no anti‑bot work, very high coverage and freshness (e.g. 50M+ Indeed records, refreshed monthly) with strong compliance posture.[^15][^26]
- **Cons** – Overkill and expensive for a single‑user local app unless you amortise cost by doing serious labour‑market analytics.

#### Coresignal

- **Scope** – Multi‑source jobs product plus separate LinkedIn‑only jobs; sources include LinkedIn, Indeed, Glassdoor, and Wellfound.[^33][^32]
- **Pricing** – Officially posts entry at $49/mo for Starter, but realistic team‑level access starts around $800/mo (Pro) and $1,500/mo (Premium), with datasets from $1,000/mo.[^30][^29]
- **Data** – Multi‑source jobs API exposes search and collect endpoints, with fields like title, description, company, skills, location, seniority, etc., and job IDs referencing multiple boards.[^31][^33]
- **Pros** – You get unified jobs from several major sources without writing any scraping code; strong for analytics.
- **Cons** – Pricing and enterprise focus make it a poor fit for a solo dev’s localhost tool; you also lose control over which boards/ATS are emphasised.

#### Firecrawl

- **Scope** – LLM‑aware scraping and content extraction; you can fetch Markdown and/or JSON structured according to a schema you provide.[^35][^36]
- **Pricing** – Free 500‑credit starter; Hobby $16/mo (3k credits), Standard $83/mo (100k credits), Growth $333/mo (500k credits).[^34]
- **Data** – `scrape` endpoint can produce Markdown, HTML, or JSON; JSON mode in v2 takes a JSON schema and returns `data.json` object plus metadata (title, description, robots, og tags, sourceURL, etc.).[^36][^35]
- **Pros** – Excellent for turning messy ATS or company job pages into clean Markdown/JSON ready for an LLM pipeline; integrates naturally with AI enrichment.
- **Cons** – Cost and credit consumption may be higher than raw HTML scrapers; still subject to anti‑bot; not job‑aware.

#### ScraperAPI

- **Scope** – HTTP proxy plus HTML unblocking service; supports automatic proxy rotation, CAPTCHAs, JS rendering.[^37][^41]
- **Pricing & limits** – Free 1k credits/month with 5 concurrent connections; paid plans from $49/mo for 100k credits (Hobby) up to millions of credits with 100–200 concurrent threads.[^40][^39][^37]
- **Data** – Raw HTML, with optional JS‑rendered HTML; no parsing or structure.
- **Pros** – Good building block if you want to own the scraping logic but outsource infra.
- **Cons** – Credit‑based pricing can be unpredictable (complex pages cost 5–25 credits), and you must handle parsing, pagination, and legal risk.[^41]

#### JobsPikr

- **Scope** – Job feeds and APIs aggregating job postings from “leading job boards worldwide,” with features for expired jobs and aggregation.[^44][^43]
- **Pricing** – Tiered; marketing emphasises affordability vs. enterprise providers; exact per‑1k pricing depends on plan (starter/growth/enterprise).[^42][^43]
- **Data** – Feeds include job URL, title, description (HTML and text), salary, contact data, jobboard name, post valid‑through date, etc., in JSON/CSV/XML.[^43][^42][^44]
- **Pros** – Solid mid‑market option if you want broad coverage via a single provider; feed model suits nightly ingestion rather than strongly real‑time use.
- **Cons** – Less control over which boards are scraped and how aggressively; not as cheap as building a narrowly focused bespoke scraper.

#### RapidAPI Job APIs (JSearch, Jobs Search Realtime, LinkedIn Job Scrapers, etc.)

- **Scope** – Multiple job APIs on RapidAPI, notably JSearch (Google Jobs‑like), “Jobs Search Realtime Data API” (Indeed, ZipRecruiter, Glassdoor), and third‑party LinkedIn Jobs Scraper APIs (e.g. ApiFirst’s).[^45][^46][^49]
- **Pricing** – JSearch basic free 200 req/mo; paid tiers scale up; each API defines its own per‑month/ per‑second caps under RapidAPI billing.[^45]
- **Data** – JSON with per‑job objects: title, company, location, salary, description snippet, posting date, and apply URL.[^46][^45]
- **Pros** – Very easy to prototype with copy‑paste snippets in many languages; good as a backup source if Google Jobs coverage is insufficient.
- **Cons** – Vendor fragmentation (each API is independent); many providers are small shops with less stability than SerpApi/TheirStack.

***

## R2 – Target Job Board Scraping Mechanics

### R2.1 LinkedIn Jobs

**API‑style options**

- Proxycurl Jobs API:
  - Job listing endpoint: `GET https://nubela.co/proxycurl/api/v2/linkedin/company/job?search_id={company_search_id}` returns jobs with `company`, `company_url`, `job_title`, `job_url`, `list_date`, `location` fields.[^6]
  - Job profile endpoint: `GET https://nubela.co/proxycurl/api/linkedin/job?url={linkedin_job_url}` returns rich job JSON including `apply_url`, `company { name, url, logo }`, `employment_type`, `industry`, full `job_description`, `job_functions`, `seniority_level`, `total_applicants`, `location`, `linkedin_internal_id`, `title`.[^47][^6]
  - Auth via `Authorization: Bearer {API_KEY}` header; rate limits depend on subscription tier (2–300 requests/min).[^5]
- Bright Data LinkedIn Jobs Scraper API: takes a list of LinkedIn job URLs, returns structured records with job ID, title, company name & ID, location, and more; handles proxies, CAPTCHAs, and IP rotation.[^28]

**Scraping‑style options**

- Direct DOM/HTML scraping faces increasingly sophisticated defences: LinkedIn uses heavy browser fingerprinting, behavioural analysis (mouse movements, scrolling), IP reputation scoring, and CAPTCHA challenges.[^50]
- Most modern LinkedIn scrapers use stealth automation stacks (Playwright/Puppeteer with stealth plugins or tools like Ulixee Hero/Nodriver) plus residential proxies to approximate human browsing.[^51][^50]

**Recommended approach**

- For a local tool, avoid building your own raw LinkedIn scraper; prefer:
  - Proxycurl Jobs API for targeted LinkedIn company or job‑URL enrichment when you really need LinkedIn‑specific fields.
  - Optionally Bright Data’s LinkedIn Jobs scraper if you want periodic bulk snapshots rather than live scraping.[^28]
- Treat LinkedIn coverage as a premium add‑on rather than the backbone of your aggregator, both for legal risk and engineering complexity.

### R2.2 Indeed

**Options**

- Google Jobs via SerpApi/SearchAPI – Many Indeed postings are mirrored in Google Jobs; using SerpApi `engine=google_jobs` with `q` parameters yields `jobs_results` where `via` may be Indeed or other boards, and `apply_options` often link back to Indeed.[^21][^20]
- Bright Data Indeed datasets – Dedicated Indeed job listing datasets with 50M+ records, refreshed monthly, priced from $250/100k records; includes title, description, salary, company ratings, publish dates, etc.[^26]
- Apify Indeed Jobs actors – Marketplace actors like `orgupdate/indeed-jobs-scraper` provide structured Indeed jobs via Apify, priced per 1k jobs.[^12]
- Direct scraping – Modern Indeed uses Cloudflare/DataDome and JS‑heavy result pages; best results use browser automation (e.g. Scrapy with Splash or Playwright) with randomized headers and delays.[^52]

**DOM & anti‑bot notes**

- Job cards often live under containers like `.job_seen_beacon`; fields such as title, company and location can be found via selectors like `h2 span`, `[data-testid="company-name"]` and `[data-testid="text-location"]`.[^52]
- Indeed aggressively fingerprints browsers, so traditional `requests`+`BeautifulSoup` often fails beyond a few pages without advanced headers and proxies.[^52]

**Recommendation**

- For freshness with minimal complexity, use Google Jobs (SerpApi/SearchAPI) to capture Indeed‑sourced jobs plus others.
- Only build a dedicated Indeed scraper (or use Apify/Bright Data) if you need Indeed‑exclusive metadata or coverage that Google Jobs misses.

### R2.3 Google Jobs via SerpApi / SearchAPI

**SerpApi – API mechanics**

- Endpoint: `GET https://serpapi.com/search?engine=google_jobs&q={query}&location={city}`.[^20]
- Response JSON:
  - `jobs_results[]` items contain `title`, `company_name`, `location`, `via`, `description`, `extensions[]` (e.g. posted time, job type), and `apply_options[]` (each with `title` – job board, `link` – apply URL).[^21][^20]
  - `chips[]` capture filter chips for job type, posting date, etc., which you can re‑use to refine queries.[^20]
- Key parameters:
  - `q` – search query, e.g. `"ai engineer"`, `"data scientist intern"`.
  - `location` or `uule` – geo; leaving `location` blank relies on IP‑based detection.[^20]
  - `hl` / `gl` – language and country, e.g. `hl=en&gl=us`.
  - Pagination via `start` or via Google Jobs Listing endpoint for per‑listing pages.[^53][^21]

**SearchAPI.io – API mechanics**

- Endpoint: `GET https://www.searchapi.io/api/v1/search?engine=google_jobs&q={query}` with `api_key` in query or `Authorization: Bearer` header.[^23]
- Response JSON:
  - Top‑level `jobs` array with fields like `position`, `title`, `company_name`, `location`, `via`, often plus salary text and apply link.[^24]
  - `search_information` block with `query_displayed` and `detected_location`.
- Parameters for pagination via `next_page_token`, plus usual `hl`, `gl`, `location` filters.[^23]

**Parameter strategy for maximum listings**

- Use broad `q` like `"software engineer"`, `"data scientist"`, or `"ai engineer"` plus `location` and optionally remote filters encoded in `q` (e.g. `"software engineer remote"`).[^17][^20]
- Use pagination (start / `next_page_token`) until no more `jobs_results`/`jobs` are returned or you hit your per‑query job cap.

### R2.4 Glassdoor

**Options**

- Aggregated: Many Glassdoor jobs appear through Google Jobs (SerpApi/SearchAPI) with `via` = Glassdoor and apply links pointing to Glassdoor.[^21][^20]
- Provider APIs:
  - Bright Data has Glassdoor‑specific job scrapers and datasets, accessible via Web Scraper API and datasets, priced on a per‑record basis.[^15][^26]
  - RapidAPI Jobs Search Realtime Data API also surfaces Glassdoor jobs alongside Indeed and ZipRecruiter.[^46]
- Direct scraping:
  - Glassdoor employs strong anti‑bot measures; best practice includes respecting robots.txt, throttling requests, rotating proxies, and using headless browsers if you need dynamic content.[^54]

**Recommendation**

- Lean on Google Jobs and RapidAPI/JobsPikr for basic Glassdoor coverage.
- For deep Glassdoor analytics, Bright Data’s dataset or Scraper API is the most realistic path.

### R2.5 Company ATS Direct Pages

These are particularly important for your use case because they provide canonical source jobs, often without the noise and duplication of aggregators.

#### Greenhouse

- Public Job Board API:
  - Core endpoint: `GET https://api.greenhouse.io/v1/boards/{board_token}/jobs?content=true` returns all published jobs with key fields (ID, title, location, departments, offices, and optionally description HTML).[^55][^56]
  - Additional endpoints for offices and departments: `.../offices`, `.../departments`, `.../offices/{id}`, etc., giving a hierarchical view of jobs.[^55]
- Schema example (simplified from docs): job objects include `id`, `title`, `location { name }`, `absolute_url`, `updated_at`, `content` (HTML description), and lists of offices/departments.[^55]
- Recommended tool: simple `requests`/FastAPI client or Firecrawl if you need LLM‑ready Markdown.

#### Lever

- Public postings API:
  - Base: `GET https://api.lever.co/v0/postings/{company}?mode=json` returns all published job postings for a company.[^57]
  - Job schema includes fields such as `id`, `text` (job title), `categories { location, commitment, team, department }`, `description`, `createdAt`, `updatedAt`, and URLs.[^57]
- Authentication: None required for published jobs; POST endpoints for applying require API keys but you won’t use them.
- Recommended tool: direct JSON ingestion via HTTP.

#### Ashby

- Public Job Postings API:
  - Endpoint: `GET https://api.ashbyhq.com/posting-api/job-board/{JOB_BOARD_NAME}?includeCompensation=true`.[^58]
  - Response schema: `jobs[]` with `title`, `location`, `secondaryLocations[]`, `department`, `team`, `isListed`, `isRemote`, `workplaceType`, `descriptionHtml`, `descriptionPlain`, `publishedAt`, `employmentType`, `address`, `jobUrl`, `applyUrl`; plus optional `compensation` block summarising salary and equity tiers.[^58]
- Recommended tool: direct JSON import; Ashby’s schema gives richer salary metadata than most.

#### Workday

- Workday itself doesn’t have a single open public jobs API, but its customer career sites are powered by Workday and typically expose JSON or XML feeds behind the scenes.
- Official integration connectors describe “Core Connector—Job Postings” that export all active job postings in an XML format to downstream job boards; this implies each tenant can expose XML/JSON feeds for partners.[^59]
- For scraping, common patterns are:
  - Job search endpoints like `/wday/cxs/{tenant}/{site}/jobs` returning JSON; or
  - Custom API endpoints surfaced via third‑party products (e.g. Apify’s Workday Jobs API actor).[^14]
- Workday is one of the trickiest ATS to reverse engineer; using a maintained actor (e.g. `fantastic-jobs/workday-jobs-api` on Apify) is strongly recommended instead of DIY scraping.[^14]

### R2.6 Handshake

- Handshake is a student/early‑career job platform with no official public jobs API for arbitrary scraping, but:
  - Apify marketplace offers a “Handshake Jobs Scraper” actor that extracts real‑time Handshake postings, priced roughly $14 per 1,000 jobs.[^60][^11]
- Recommended approach: use Apify’s Handshake actor for periodic fetches and ingest into your local DB; treat it similarly to a board integration.

### R2.7 Wellfound (AngelList Talent)

- Wellfound itself relies heavily on APIs (and GraphQL) under the hood, but there is no sanctioned public jobs API for general scraping.
- Many Wellfound jobs also flow from ATS/Greenhouse via integrations, meaning you can often capture them more reliably at the ATS layer (Greenhouse > Wellfound) rather than scraping Wellfound directly.[^61]
- For direct scraping, you would likely need a headless browser plus GraphQL interception to capture job JSON.
- Given legal and technical overhead, your architecture should prefer:
  - ATS endpoints (Greenhouse, Lever, Ashby, Workday) as primary sources.
  - Google Jobs and SerpApi/SearchAPI as secondary aggregators capturing Wellfound‑mirrored jobs.

***

## R3 – Data Schema & Normalization

### R3.1 Base Job Entity Schema

Design a single `jobs` table (relational) plus auxiliary tables for skills/tags. A normalised schema that aligns with schema.org `JobPosting` while accommodating ATS/aggregator fields is ideal.[^62][^58][^57]

**Core fields**

| Field | Type | Notes |
|-------|------|-------|
| `id` | INTEGER PK (DB) | Internal DB primary key |
| `job_uid` | TEXT (UUID) UNIQUE | Deterministic UUID (e.g. v5) based on canonical `source`, `source_job_id` & `company_domain` for cross‑source dedup |
| `source` | TEXT (enum) | `linkedin`, `indeed`, `google_jobs`, `greenhouse`, `lever`, `ashby`, `workday`, `jobsPikr`, `serpapi`, etc. |
| `source_job_id` | TEXT | Native job identifier (LinkedIn internal ID, ATS job ID, Google job hash, etc.)[^6][^58] |
| `title` | TEXT | Job title from source |
| `company_name` | TEXT | As‑displayed company name |
| `company_domain` | TEXT | Normalised domain if known (from ATS URL or enrichment) |
| `location_city` | TEXT | Parsed from location string and/or ATS address fields[^58][^57] |
| `location_state` | TEXT | US state/region |
| `location_country` | TEXT | ISO country code |
| `remote_type` | TEXT (enum) | `onsite`, `hybrid`, `remote`, `remote_usa`, etc., derived from description and ATS `workplaceType` fields[^58] |
| `url` | TEXT | Canonical apply URL prioritising ATS over aggregators (e.g. Ashby/Lever/Greenhouse URL first, then board link)[^58][^57] |
| `source_listing_url` | TEXT | Original listing page (e.g. LinkedIn job URL, Google Jobs share link)[^6][^20] |
| `posted_at` | DATETIME | From ATS `publishedAt`, `list_date`, or Google Jobs detected `posted_at` extension; stored in ISO 8601 UTC[^6][^58][^21] |
| `scraped_at` | DATETIME | When your system last fetched this record |
| `is_active` | BOOLEAN | False when expired/removed (from ATS feed status or 404) |

**Content fields**

| Field | Type | Notes |
|-------|------|-------|
| `description_raw_html` | TEXT | Raw HTML from ATS/job page (Greenhouse `content`, Ashby `descriptionHtml`, Lever `description`, LinkedIn `job_description`)[^55][^58][^6] |
| `description_text` | TEXT | Plaintext stripped from HTML (for fast keyword filters) |
| `description_markdown` | TEXT | Markdown version optimised for LLM prompts (e.g. via Firecrawl or local HTML→MD pipeline)[^35][^36] |
| `requirements` | JSON | Array of bullet strings extracted via heuristic/LLM chunking from description |
| `responsibilities` | JSON | Similar array for responsibilities |
| `salary_min` | REAL | Normalised numeric min salary if available (Ashby compensation components, Indeed/BrightData salary fields, Google Jobs salary ext).[^58][^26][^21] |
| `salary_max` | REAL | Max salary |
| `salary_currency` | TEXT | ISO currency code (USD, EUR, etc.) |
| `salary_period` | TEXT (enum) | `hourly`, `annual`, `monthly`, `contract`, derived from text/ATS metadata |

**Classification & metadata**

| Field | Type | Notes |
|-------|------|-------|
| `job_type` | TEXT (enum) | `full_time`, `part_time`, `contract`, `internship`, from ATS `employmentType` or Google `extensions`.[^58][^20] |
| `experience_level` | TEXT (enum) | `entry`, `mid`, `senior`, `exec`, derived from title and description (and ATS fields like `experienceRequirements` when present).[^62] |
| `department` | TEXT | From ATS `department`/`team` fields when available.[^58][^55] |
| `team_size_hint` | INTEGER | Optional estimate from company data / description |
| `industry` | TEXT | From ATS or LinkedIn `industry` field.[^6][^33] |

**AI‑enriched fields** (populated by local LLM/OpenAI pipeline)

| Field | Type | Notes |
|-------|------|-------|
| `skills_required` | JSON | Array of canonicalised skill names |
| `skills_nice_to_have` | JSON | Array |
| `tech_stack` | JSON | Language/framework/tool list (Python, FastAPI, React, AWS, etc.) |
| `seniority_score` | INTEGER | 0–100 numeric score derived from years of experience requirements, title keywords, and responsibilities |
| `remote_score` | INTEGER | 0–100 indicating how remote‑friendly the role is (fully remote vs. occasional onsite) |
| `match_score` | INTEGER | 0–100 match vs. user’s resume/profile embedding |
| `summary_ai` | TEXT | ~150‑word LLM summary of job |
| `red_flags` | JSON | Array of strings explaining potential issues (e.g. vague comp, overtime hints) |
| `green_flags` | JSON | Array of positives (e.g. clear salary, good tech stack, visa support)

**User state fields**

| Field | Type | Notes |
|-------|------|-------|
| `status` | TEXT (enum) | `new`, `saved`, `applied`, `rejected`, `ghosted`, `interviewing`, `offer` |
| `notes` | TEXT | Freeform user notes |
| `applied_at` | DATETIME | When user logged application |
| `last_updated` | DATETIME | Last user edit time |
| `is_starred` | BOOLEAN | For favourites |
| `tags` | JSON | Array of user tags (e.g. `"dream"`, `"onsite only"`, `"H1B"`)

**Auxiliary tables**

- `skills` – master list of skills with `id`, `name`, optional category.
- `job_skills` – many‑to‑many mapping from job to skills with `is_required` flag.
- `job_tech_stack` – mapping from job to tech stack items.
- `job_embeddings` – vector storage table if using SQLite vector extension or Chroma (job_id, embedding, model, created_at).[^63][^64]

### R3.2 Deduplication Logic Across Sources

Key dedup goal: treat a job advertised on LinkedIn, Google Jobs, and the company’s Greenhouse page as **one canonical record** in your DB.

Recommended strategy (inspired by Coresignal’s multi‑source jobs design and Fantastic.jobs’ ATS duplicate detection):[^32][^31][^14]

1. **Canonical source priority**
   - Prefer ATS (Greenhouse, Lever, Ashby, Workday) as canonical; treat board listings as secondary.[^58][^57][^55]
   - If no ATS but Google Jobs listing points directly to company careers site, treat careers page as canonical.
2. **Deterministic `job_uid`**
   - Generate a UUID v5 from `company_domain` + normalised title + `location_country` + `normalized_workplace_type`.
   - For ATS sources, use `source_job_id` instead (e.g. Ashby `jobUrl` hash, Greenhouse job ID).[^56][^58]
3. **Matching heuristics**
   - URL match: if a LinkedIn or Google Jobs listing’s `apply_options` includes the exact ATS/careers URL already in DB, link as duplicate.[^14][^21][^20]
   - Title+company+location match within a short posting window (e.g. ±3 days) and similar description length.
   - Fuzzy description similarity (cosine similarity of embeddings) above threshold (e.g. 0.9).
4. **Source precedence rules**
   - When merging duplicates, keep:
     - Description from ATS or careers page if present (richer and more stable).
     - Salary info from whichever source has the most structured comp (Ashby > Bright Data dataset > Google Jobs > board text).[^26][^58][^21]
   - Maintain a `job_sources` table listing all source records that collapsed into the canonical job, including their URLs and provider IDs.

### R3.3 Incremental Refresh Strategy

A local tool should prioritise stability and incremental updates while avoiding bans.

- **Polling intervals** (defaults; configurable per source):
  - ATS APIs (Greenhouse/Lever/Ashby): every 2–4 hours per company; they are designed for programmatic job board use and do not impose harsh anti‑bot rules.[^57][^55][^58]
  - SerpApi/SearchAPI (Google Jobs): run per‑query refreshes every 6–12 hours during active job search periods; rely on SerpApi’s caching to reduce costs.[^17][^20]
  - RapidAPI/JobsPikr: align with plan quotas; e.g. hourly for narrow filters, daily for broad scans.[^43][^45]
  - Direct scraped pages (using ScraperAPI/ScrapingBee/Firecrawl): stick to **at most** every 24 hours per job detail page or search URL, with conservative concurrency.
- **Change detection**:
  - For ATS, treat jobs as active until they disappear from API responses or an explicit `isListed`/status flag flips false (Ashby, Greenhouse, Lever).[^55][^58][^57]
  - For scraped pages, compute a stable hash of the description HTML; only trigger AI enrichment when the hash changes.
- **Backfills vs. live mode**:
  - On first run per source/query, backfill up to N pages/records (configurable), then switch to incremental mode that only fetches “new since last run” via time filters when possible (e.g. Apify LinkedIn jobs actor supports time ranges like last hour/day/week).[^14]

### R3.4 Schema Versioning

- Maintain a `schema_version` integer at the DB level and an optional `record_schema_version` per row.
- When adding or changing fields (e.g. new AI scores, new salary components):
  - Create a migration script that adds columns with default `NULL` and backfills when feasible.
  - Update LLM enrichment logic to write `record_schema_version = CURRENT_VERSION`.
  - When reading, handle both old and new versions gracefully (e.g. treat missing fields as defaults).

***

## R4 – Local Technology Stack Selection

### R4.1 Backend Runtime

**Options**

- Python (FastAPI + SQLAlchemy + APScheduler)
- Node.js (Fastify/Express + Drizzle ORM + node‑cron/BullMQ)
- Python FastAPI + Redis/BullMQ‑style queue

**Evaluation for a single‑developer local app**

- **Async scraping** – Python’s `httpx`/`aiohttp` plus Playwright are mature and integrate nicely with FastAPI’s async model; many job/ATS clients (e.g. Lever/Greenhouse/Ashby examples) are in Python.[^58][^57][^55]
- **Database access** – SQLAlchemy works well with SQLite and can later swap to Postgres if you outgrow local; Python ecosystem has FTS5, `sqlite-vss` and `sqlite-vec` bindings for vector semantics.[^64][^65]
- **Scheduling** – APScheduler supports cron‑like jobs, persistence via DB, per‑job intervals, and retry mechanisms.
- **Ecosystem fit** – Most AI/LLM tooling (sentence‑transformers, Ollama/LLM clients, OpenAI SDK) is Python‑first.[^66][^67][^68]

**Decision** – **Python FastAPI + SQLAlchemy + APScheduler** as the primary backend runtime and scheduler. Node.js only adds value if you strongly prefer JS everywhere; you already do heavy ML/AI in Python, so consolidating is more efficient.

### R4.2 Database: SQLite vs Postgres vs DuckDB

**SQLite**

- Extremely well‑suited to local desktop apps; single file, no server, robust journalling.
- FTS5 can handle tens of millions of rows: blog demos show substring search on 18.2M rows with FTS5 trigram indexes yielding queries in 10–30 ms, ~50–100x faster than naive LIKE queries.[^69]
- Real‑world reports indicate FTS5 queries are “blindingly fast” for result sets under ~100 rows returned, with slower performance only when matching huge portions of the corpus.[^70][^71]
- WAL mode significantly improves concurrent read/write performance and recovery vs rollback journals, which is helpful when a background scraper updates while the UI queries.[^72]

**PostgreSQL**

- Strong for multi‑user and networked deployments; with pgvector you can store embeddings and run ANN search in‑DB.[^73][^74]
- But local setup adds complexity (service management, config) for little gain in a single‑user context; 500k job rows is trivial for SQLite when indexed properly.

**DuckDB**

- In‑process OLAP engine; superb for analytical queries and columnar workloads (aggregations over millions of rows).[^75]
- Less convenient as the primary transactional store; better as an optional read‑only analytics mirror of SQLite if you later want heavy dashboards.

**Decision** – Use **SQLite** as the primary DB with:

- WAL mode enabled (`PRAGMA journal_mode=WAL`) and sensible cache size.
- FTS5 virtual table for full‑text search over `title`, `company_name`, and `description_text`.
- Optional vector extension (`sqlite-vss` or `sqlite-vec`) for semantic search embeddings.[^65][^64]
- Optional DuckDB export path for heavy analytics later.

### R4.3 Frontend Framework

Requirements: local‑only, but capable of real‑time updates (WebSocket/SSE), complex filters, and virtualised lists for 10k+ jobs.

**React + Vite + Tailwind**

- Lightweight dev server, fast HMR; you can bundle as a static SPA served by FastAPI.
- React ecosystem has mature table/grid and virtualised list components (e.g. React‑Virtualized, TanStack Table) that can handle 10k–50k job rows without performance issues.

**Next.js**

- Adds server‑side rendering and routing; helpful for SEO, which you don’t need on localhost.
- More moving parts; little advantage for a single‑user tool when compared with a SPA plus API.

**SvelteKit**

- Lighter runtime and simple reactivity model; also good for SPAs.
- Smaller ecosystem vs React; fewer drop‑in components for complex data tables.

**Decision** – **React 19 + Vite + TailwindCSS** as the frontend stack.

- Serve the React bundle statically from FastAPI.
- Use WebSockets (via FastAPI’s `websockets` support) or SSE to push job counts and progress updates into the UI.

### R4.4 Background Job Scheduler & Workers

For a local tool, you want minimal infrastructure with persistence and cron syntax.

- **APScheduler (Python)** supports cron expressions, interval triggers, persistent job stores (SQLAlchemy/SQLite), and per‑job retry logic.
- **Celery + Redis** is heavyweight and optimised for distributed systems; running Redis locally solely for your app is overkill.
- **BullMQ / node‑cron** make more sense in Node‑centric systems.

**Decision** – Use **APScheduler** integrated into the FastAPI app (or a sidecar process) for:

- Per‑source schedules (e.g. `greenhouse_every_3h`, `serpapi_google_jobs_every_6h`).
- Retry with exponential backoff on transient errors.
- Keeping last‑run timestamps per job/source in the DB.

### R4.5 Vector / Semantic Search

**Embedding model**

- `sentence-transformers/all-MiniLM-L6-v2` (384‑dim) is a widely used light model for semantic search; on commodity CPUs it can encode thousands of short texts per second, though performance drops on very constrained machines.[^66]
- For 50k job descriptions of moderate length (~256 tokens), a one‑time embedding pass is manageable on CPU (tens of minutes at worst), and incremental updates per new job are trivial.

**Vector store options**

- **ChromaDB** – Local vector DB; benchmarks show ~3 ms per query on 5k documents with HNSW index and relatively flat latency up to 10k+ docs.[^63]
  - Pros: dead‑simple Python API, good for low‑concurrency local search.
  - Cons: in‑memory index; concurrency under heavy multi‑user load is less strong than pgvector, but that’s irrelevant here.[^76]
- **SQLite vector extensions (`sqlite-vss`, `sqlite-vec`)** – Embeddings stored directly in SQLite using Faiss‑backed ANN; good fit for a single local DB file and avoids an extra service.[^64][^65]
- **pgvector** – Only worth it if you move to Postgres later.[^74][^73]

**Decision** – Two viable paths; for this app:

- Start with **SQLite + `sqlite-vss`** for co‑located vectors:
  - Table `job_embeddings(job_id INTEGER, embedding BLOB/array, model TEXT)` plus VSS index.[^64]
- Optionally support Chroma for experimentation (easier to iterate embeddings logic) but standardise around SQLite for deployment simplicity.[^63]

### R4.6 LLM for AI Enrichment

Tasks: extract skills/tech stack, summarise descriptions, compute seniority/remote/match scores.

**Local LLM via Ollama**

- Ollama lets you run models like `llama3.2:3b` and `qwen2.5:7b` locally on Apple/Intel hardware with GPU acceleration via Metal on M‑series chips.[^77][^68]
- Independent speed benchmarks show Llama 3.2 3B outputs around 48 tokens per second on typical infrastructure; on Apple Silicon with Metal you can reach ~15–30 tok/s depending on chip.[^78][^77]
- For 150‑word summaries (≈200–250 tokens) and short JSON extractions per job, throughput of a few jobs/second is realistic, particularly in batch mode.

**OpenAI GPT‑4o‑mini fallback**

- GPT‑4o‑mini is priced at roughly $0.60 per 1M input tokens and $2.40 per 1M output tokens.[^67]
- A typical job description of ~2,000 tokens plus 200‑token output costs roughly 2.2k tokens 6 0.0022 of 1M, i.e. ~$0.0018 per job; 10k jobs would cost ≈$18 in enrichment.

**Prompt pattern**

Use single‑prompt JSON schema extraction where possible, e.g. (pseudo‑example for local LLM or GPT‑4o‑mini):

```json
{
  "task": "Extract structured info about a job posting.",
  "instructions": [
    "Read the job description.",
    "Output strictly valid JSON matching the provided schema.",
    "Do not include extra keys or comments."
  ],
  "schema": {
    "title": "JobEnrichment",
    "type": "object",
    "properties": {
      "skills_required": {"type": "array", "items": {"type": "string"}},
      "skills_nice_to_have": {"type": "array", "items": {"type": "string"}},
      "tech_stack": {"type": "array", "items": {"type": "string"}},
      "seniority_score": {"type": "integer", "minimum": 0, "maximum": 100},
      "remote_score": {"type": "integer", "minimum": 0, "maximum": 100},
      "summary_ai": {"type": "string"},
      "red_flags": {"type": "array", "items": {"type": "string"}},
      "green_flags": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["skills_required", "tech_stack", "seniority_score", "remote_score", "summary_ai"]
  },
  "job_markdown": "...description_markdown_here..."
}
```

- For Ollama, wrap this in a system message emphasising **strict JSON only**; for GPT‑4o‑mini, use the JSON mode of the API if available.[^35][^67]

**Decision**

- **Primary enrichment** via **Ollama running `llama3.2:3b`** (or a similar 3–7B instruct model) for privacy and zero marginal cost once set up.[^68][^77]
- **Fallback** to GPT‑4o‑mini for:
  - Complex/ambiguous descriptions
  - Batch re‑processing where quality is critical
  - When local hardware is underpowered.

### R4.7 Final Stack & Architecture Diagram

**Chosen stack**

- Backend: FastAPI (Python), SQLAlchemy ORM, APScheduler.
- DB: SQLite with WAL, FTS5, and `sqlite-vss` for vector search.
- Frontend: React 19 + Vite + TailwindCSS SPA served by FastAPI.
- Background workers: APScheduler jobs + async tasks inside FastAPI (or a small worker process sharing DB).
- AI: Ollama local LLM for JSON extraction & summaries; optional GPT‑4o‑mini via OpenAI API.
- Integrations: SerpApi/SearchAPI for Google Jobs, ATS APIs (Greenhouse, Lever, Ashby), optional TheirStack/JobsPikr, optional Proxycurl/Bright Data for LinkedIn.

```mermaid
flowchart LR
  subgraph Frontend
    UI[React + Tailwind SPA]
  end

  subgraph Backend[FastAPI Backend]
    API[REST/WS API]
    SCHED[APScheduler]
    SCRAPE[Scraper Integrations\n(SerpApi, ATS, etc.)]
    ENRICH[AI Enrichment Service\n(Ollama / OpenAI)]
  end

  subgraph DB[SQLite]
    JOBS[(jobs table + FTS5)]
    EMBED[(job_embeddings + VSS)]
    META[(scheduler metadata, job_sources, user_state)]
  end

  UI <--> API
  API --> JOBS
  API --> EMBED
  API --> META

  SCHED --> SCRAPE
  SCRAPE --> JOBS
  SCRAPE --> META

  SCHED --> ENRICH
  ENRICH --> JOBS
  ENRICH --> EMBED
```

***

## R5 – Anti‑Bot Evasion & Rate Limiting Best Practices

### R5.1 Headers, Fingerprints, and Behaviour

Modern job sites and social platforms use a combination of HTTP header analysis, browser fingerprinting, behavioural modelling, and IP reputation to detect bots.[^50][^52]

**Header best practices**

- Always send coherent header sets:
  - User‑Agent matching a real browser version.
  - Matching `Accept`, `Accept-Language`, and client hints consistent with that UA and proxy geo.[^79]
  - Avoid rotating only the UA string; rotate **UA + headers + proxy** as a unit.[^79]
- For browser‑based scrapers (Playwright/Puppeteer):
  - Let the automation framework set realistic browser headers; avoid obvious `HeadlessChrome` UAs.
  - Use stealth plugins or undetected‑chromedriver‑style patches where necessary.[^51][^50]

**Behaviour**

- Randomise delays between actions; for search‑result pagination, wait 3–8 seconds between pages and 1–3 seconds between job detail clicks as recommended in anti‑bot guides.[^52]
- Avoid 24/7 scraping; schedule runs during typical user times (daytime in target timezone) with gaps.

### R5.2 Per‑Domain Request Cadence

Based on community benchmarks and anti‑bot guides:[^54][^50][^52]

- **LinkedIn** – Extremely sensitive; if scraping directly, keep to ≤1–2 page loads per minute per account/IP, with long randomised delays; but for this app you should **avoid direct scraping** and instead use Proxycurl or Bright Data.
- **Indeed** – Hard anti‑bot; avoid more than 1 request every 5–10 seconds per IP for search result pages; job detail pages can be slightly faster but still <0.5–1 Hz, especially without residential proxies.[^52]
- **Glassdoor** – Similar to Indeed; throttle strongly and obey rate limits (e.g. 1 request every few seconds) while monitoring for captchas.[^54]
- **ATS APIs** – Greenhouse/Lever/Ashby support programmatic use; you can safely poll every 15–60 minutes per company without issue as long as you don’t hammer them with hundreds of parallel requests.[^57][^55][^58]
- **Google Jobs via SerpApi/SearchAPI** – You are limited by SerpApi/SearchAPI’s own throughput caps (20% of plan per hour), which will be far below what would risk blocks from Google.[^22][^18]

### R5.3 Proxies and Headless Browsers

- **Residential vs datacenter proxies**:
  - Residential proxies are more expensive ($5–$15/GB) but much harder to block and appear as real home users; recommended for LinkedIn/Indeed‑class sites.[^50][^15]
  - Datacenter proxies are cheaper but often quickly blocked by heavily protected sites.
- **Scraping APIs as a proxy abstraction**:
  - Using ScraperAPI, ScrapingBee, or Bright Data Scraper APIs offloads proxy rotation and CAPTCHA solving; you just pay per successful request/record.[^37][^10][^15]
- **Headless browser choice**:
  - Comparative benchmarks show that plain Selenium has high detection rates (85–95%), while basic Playwright/Puppeteer are detected 60–80% of the time on protected sites.[^51]
  - With stealth plugins (or specialised tools like Ulixee Hero or Nodriver), detection can drop to single‑digit percentages; for jobs you probably don’t need extreme stealth, but Playwright with stealth plugin is a good middle ground.[^51]

### R5.4 Cookies and Sessions

- For sites requiring login (e.g. if you ever scrape your own LinkedIn feed), use manual login in a normal browser profile, export cookies to your scraper, and rotate sessions infrequently.
- Store cookies securely on disk, encrypted where possible, and refresh them when logins expire.
- Your architecture should not depend on authenticated scraping for core features; this avoids account lockout and ToS risk.

### R5.5 Legal & Ethical Considerations

- Laws such as GDPR and CCPA restrict collection of personal/sensitive data; do **not** scrape personal data like email addresses or candidate information.[^80]
- Many sites’ Terms of Service explicitly prohibit automated scraping; breaching ToS can constitute a contract violation and potential legal exposure even for personal projects.[^80]
- Mitigation strategies:
  - Prefer official/public APIs (Greenhouse, Lever, Ashby, SerpApi, Proxycurl) where possible.[^5][^55][^58][^57][^20]
  - Restrict scraping to publicly accessible job postings and avoid bypassing paywalls or authentication.
  - Provide configuration toggles in your app so the user consciously enables or disables scraping for specific sites.

***

## R6 – Competitive Feature Analysis

### R6.1 Simplify.jobs

**Core value props**

- Browser extension “Simplify Copilot” that autofills job applications in 1‑click across ATS and company career pages; it maps profile data to fields and uses AI to generate tailored responses for open‑ended questions.[^81]
- Automatically tracks all applications submitted via the extension into a dashboard, acting as a job tracker without manual logging.[^81]
- Provides resume scoring against job descriptions and AI‑assisted optimisation suggestions.[^2][^81]

**Feature implications for your local app**

- Implement autofill as a separate browser extension is out of scope for a pure localhost web app, but you can still:
  - Generate application snippets (e.g. “Why are you a good fit?”) based on the stored job + your resume.
  - Provide a manual “log application” flow and pre‑populate fields when the user clicks “Apply” from your dashboard.
- A local resume‑matching score (semantic similarity between job embedding and resume embedding) is essential to match this functionality.[^66][^63]

### R6.2 Jobright.ai

**Capabilities**

- Jobright positions itself as a near‑fully automated job search copilot that:
  - Recommends positions based on your uploaded resume and preferences, with match scoring so you can prioritise high‑fit roles.[^82][^83]
  - Auto‑generates tailored resumes and cover letters per role and can autofill applications in many cases via its Chrome extension.[^84][^85]
  - Includes a job tracker with board‑style views, application statuses, notes, reminders and integration with LinkedIn for networking.
  - Offers AI coaching for interview prep, salary negotiation, and career decisions.[^84][^82]

**Key UX patterns to emulate**

- **Match scores & filters** – Score each job vs. your profile and expose filters like “show only 70+ match” to cut noise.[^85][^82]
- **Board view** – Kanban board of job statuses (saved, applied, interviewing, offer) with drag‑and‑drop; free‑text notes per card.[^86][^87]
- **Automation** – Even without autofill, pre‑generate responses and cover letters to drastically reduce effort per application.

### R6.3 Teal HQ

**Features**

- Teal’s Job Tracker Chrome extension saves roles from 40+ boards (LinkedIn, Indeed, Glassdoor, etc.) and stores job descriptions, salary info, and resume keywords in one dashboard.[^88]
- Web app provides kanban‑style tracking, contacts management, outreach templates, and weekly goals for applications.[^89][^88]
- Pricing: core tracker and basic features are free; Teal+ subscription ($29/mo) adds advanced AI assistance and deeper resume analysis.[^89]

**Patterns to adopt**

- Browser capture of job listings into the local app (via bookmarklet/extension) is powerful; your app should at least support manual job import by pasting a URL + description.
- Clear separation of “job data” vs “process data” (status, contacts, outreach logs) is important; your schema already includes `status`, `notes`, and `tags` to support this.

### R6.4 Feature Checklist for Your Local Tool

Based on Simplify, Jobright, and Teal plus open‑source scrapers, a strong local feature set should include:

**Data ingestion**

- Integrations:
  - ATS: Greenhouse, Lever, Ashby via public JSON APIs.[^55][^58][^57]
  - Aggregators: Google Jobs via SerpApi/SearchAPI; optional JobsPikr/RapidAPI.[^45][^23][^20]
  - LinkedIn: optional enrichment via Proxycurl or Bright Data (paid add‑on).[^28][^5]
- Open‑source scrapers you can learn from or integrate:
  - Python LinkedIn Job Scraper storing into SQLite with Flask UI.[^90]
  - Go‑based “Jobs Scraper” app storing into SQLite with endpoints for retrieval.[^91]
  - Discord job bots using JobSpy to scrape LinkedIn/Indeed/Glassdoor/Google/ZipRecruiter into SQLite.[^92]

**Core UX**

- Job list view with powerful filters (title, company, location, remote, salary range, skills, match score) and sorting.
- Detail view showing:
  - Raw description and cleaned Markdown.
  - AI summary, tech stack chips, skills chips.
  - Red/green flag badges.
- Kanban board (similar to Teal/Jobright) with columns for each status; drag‑and‑drop to update `status` and auto‑set timestamps.[^88][^84]

**AI assistance**

- Local match score computation between resume embedding and job embedding.[^66][^63]
- AI‑generated snippets for:
  - “Why are you a good fit?”
  - Company‑specific notes (e.g. “What this team does”).
- “Opportunity quality” flags based on salary disclosure, role clarity, and stack alignment.

**Automation & quality‑of‑life**

- Background scheduler that:
  - Re‑runs ATS and Google Jobs queries on a configurable cadence.
  - Marks jobs inactive when no longer present or after a user‑configurable expiry window (e.g. 60 days since posting).
- Full‑text search over titles/descriptions with FTS5 and semantic search over embeddings.[^69][^63]
- Export/import as CSV/JSON so you can back up your applications or port them to other tools.

***

This research document should be treated as the architectural baseline. The next phase is to translate it into concrete module boundaries (scraper drivers, normalisation layer, enrichment worker, UI components) and then implement them in the chosen stack.

---

## References

1. [Best Job Posting Data APIs in 2026 (Compared) - TheirStack.com](https://theirstack.com/en/blog/best-job-posting-apis) - TheirStack offers a generous free tier (200 API credits/month) and flexible paid plans starting at $...

2. [Simplify Jobs Review (2026) - AutoApplier](https://www.autoapplier.com/blog/simplify-jobs) - Simplify Jobs primarily functions as a browser extension. Once installed, it detects application for...

3. [How credits work - TheirStack.com](https://theirstack.com/en/docs/pricing/credits) - API credits are consumed for each record (job or company) returned from our API endpoints or dispatc...

4. [Job Postings API - TheirStack.com](https://theirstack.com/en/job-posting-api) - Our job posting API integrates with the top job posting data sources to provide you with the most ac...

5. [Proxycurl Overview – API Docs](https://nubela.co/proxycurl/docs.html) - Complete API documentation for Proxycurl's B2B data enrichment APIs. Built by developers, for develo...

6. [Get a company's LinkedIn jobs listings by using Proxycurl's Jobs API](https://dev.to/veektor_v/get-a-linkedin-companys-jobs-listings-by-using-proxycurls-jobs-api-16m2) - The Job API makes it simple to fetch a list of jobs posted by a company on LinkedIn and also get str...

7. [Jobs API | Proxycurl - NinjaPear](https://nubela.co/proxycurl/jobs-api.html) - Monitor the growth of job postings of any target company with Proxycurl's Job Listing Count API. See...

8. [Available plans explained - ScrapingBee Knowledge Base](https://help.scrapingbee.com/en/article/available-plans-explained-kbinm/) - Currently, ScrapingBee has these plans available: Freelance: 250k API credits and 10 concurrent requ...

9. [Migrating from ScrapingBee to Zyte API](https://docs.zyte.com/zyte-api/migration/scrapingbee/index.html) - ScrapingBee limits the number of concurrent requests that you can send, starting at 5 with the most ...

10. [ScrapingBee Overview (2025) – Features, Pros, Cons & Pricing](https://www.salesforge.ai/directory/sales-tools/scrapingbee) - ScrapingBee is a web scraping API designed to simplify data extraction by managing headless browsers...

11. [Handshake Jobs Scraper API - Apify](https://apify.com/orgupdate/handshake-jobs-scraper/api) - Learn how to interact with Handshake Jobs Scraper via API. Includes an example code snippet for your...

12. [Handshake Jobs Scraper API in JavaScript - Apify](https://apify.com/orgupdate/handshake-jobs-scraper/api/javascript) - Learn how to interact with Handshake Jobs Scraper API in JavaScript. Includes an example JavaScript ...

13. [Actors in Store | Platform - Apify Documentation](https://docs.apify.com/platform/actors/running/actors-in-store) - You can set a limit on how many items an Actor should return and the amount you will be charged in O...

14. [Advanced LinkedIn Job Search API - Apify](https://apify.com/fantastic-jobs/advanced-linkedin-job-search-api) - Access our real-time LinkedIn Jobs database with over 10 million new jobs per month. With detailed c...

15. [Best Job APIs and Data Providers to Use in 2026](https://brightdata.com/blog/web-data/best-job-apis) - 5.

16. [Best SERP APIs for Scraping Google in 2026 - IPRoyal.com](https://iproyal.com/blog/best-google-serp-api/) - Conveniently, SerpApi includes a free plan with 100 searches per month. Other plans include 5,000, 1...

17. [Google Jobs Search Query Operators - SerpApi](https://serpapi.com/blog/google-jobs-search-query-operators/) - Create beautiful job board posts using SerpApi with this Ruby script that scrapes Google Jobs and ge...

18. [SerpApi: Google Search API](https://serpapi.com) - The hourly throughput limit for plans with under 1 million searches per month is 20% of your plan vo...

19. [Google Search Engine Results API - SerpApi](https://serpapi.com/search-api) - Cached searches are free, and are not counted towards your searches per month. It can be set to fals...

20. [Google Jobs API - SerpApi](https://serpapi.com/google-jobs-api) - Scrape Google Job results with SerpApi's Google Jobs Results API. Job titles, company names and loca...

21. [Google Jobs Results API - SerpApi](https://serpapi.com/google-jobs-results) - The Google Jobs Results API allows a user to scrape jobs results from a regular Google Search page. ...

22. [Affordable SERP API Pricing - SearchApi](https://www.searchapi.io/pricing) - To maintain fairness and server integrity, there's a rate limit in place. Please note that you can u...

23. [Google Jobs Scraper API - SearchApi](https://www.searchapi.io/docs/google-jobs) - Parameter defines an engine that will be used to retrieve real-time data. It must be set to google_j...

24. [Google Jobs API](https://www.searchapi.io/google-jobs) - Scrape job listings, company details, salary estimates, and more. Receive structured results in JSON...

25. [Best Rank Tracking APIs for Developers & Agencies - ScrapingBee](https://www.scrapingbee.com/blog/best-rank-tracker-apis/) - Bright Data's API uses a record-based model: pay-as-you-go costs $1.5 per 1K records with no commitm...

26. [Indeed Datasets - Buy Indeed Data - $250/100K Records - Bright Data](https://brightdata.com/products/datasets/indeed) - Our Indeed dataset contains more than 40M records. Collect Indeed data for job hiring strategies and...

27. [Bright Data vs Coresignal: Which Is Right for You?](https://brightdata.com/blog/comparison/bright-data-vs-coresignal) - Dataset pricing starts at $250 per 1,000 records, with the price per 1,000 records decreasing as vol...

28. [LinkedIn Jobs Scraper - Free Trial - Bright Data](https://brightdata.com/products/web-scraper/linkedin/jobs) - Scrape LinkedIn jobs and collect public LinkedIn jobs data such as job ID, description, location, hi...

29. [Jobs API Pricing Comparison 2026: Pylot vs Coresignal vs TheirStack](https://pylothq.com/blog/jobs-api-pricing-comparison-coresignal-theirstack-alternative) - Compare job data API pricing: Pylot offers 30000 requests/month for $25 vs Coresignal's $800/month a...

30. [Is Coresignal Good? Honest Review, Pricing, Features [2025]](https://crustdata.com/blog/coresignal-review-b2b-data-provider) - API plans officially start at $49/month (Starter), but meaningful access for teams typically begins ...

31. [Collect: Multi-source Jobs API | Coresignal Docs](https://docs.coresignal.com/jobs-api/multi-source-jobs-api/collect) - Find instructions for collection endpoint usage and data collection. General information about colle...

32. [The best job posting data providers I recommend in 2025 - Bloomberry](https://bloomberry.com/blog/the-best-job-posting-data-providers-i-recommend-in-2025/) - As mentioned, Coresignal scrapes professional social networks and business-related sites including G...

33. [Jobs API - LinkedIn](https://www.linkedin.com/products/coresignal-company-data-api/) - With Coresignal's Jobs API, you can retrieve details such as job titles, descriptions, locations, co...

34. [Firecrawl Review: Best AI Web Scraper for LLMs in 2025](https://www.fahimai.com/firecrawl) - Firecrawl pricing starts at free with 500 credits. The Hobby plan is $16/month with 3,000 credits. T...

35. [JSON mode - Firecrawl Docs](https://docs.firecrawl.dev/features/llm-extract) - Firecrawl uses AI to get structured data from web pages in 3 steps. This makes getting web data in t...

36. [Firecrawl - Introduction](https://docs.sim.ai/tools/firecrawl) - Firecrawl is a powerful web scraping and content extraction API that integrates seamlessly into Sim,...

37. [Plans & Billing - ScraperAPI Documentation](https://docs.scraperapi.com/resources/faq/plans-and-billing) - ScraperAPI offers a free plan of 1,000 free API credits per month (with a maximum of 5 concurrent co...

38. [Top Scraper APIs That Actually Work in 2025 - Google Sites](https://sites.google.com/view/davescorner/top-scraper-apis-that-actually-work-in-2025) - For $49/month you get 150,000 API credits and 5 concurrent requests. The free trial includes 1,000 c...

39. [ScraperAPI → Features, Pricing & Alternatives (2025) - ColdIQ](https://coldiq.com/tools/scraperapi) - Pricing ; Hobby. $49.00. Per User, Per Month · 100,000 API credits ; Startup. $149.00. Per User, Per...

40. [Compare Plans and Get Started for Free - ScraperAPI Pricing](https://www.scraperapi.com/pricing/) - ... Concurrent Threads; US & EU regions only. Start Trial. Startup. Great for small teams and advanc...

41. [ScraperAPI Review: Best Web Scraping Tools October 2025 - Skyvern](https://www.skyvern.com/blog/scraperapi-alternatives-web-scraping-tools/) - ScraperAPI starts at $49 per month with a credit based system where complex sites consume 5-25 credi...

42. [Job Data Pricing | Affordable Plans for Job Data Extraction - JobsPikr](https://www.jobspikr.com/jobspikr-data-pricing/) - Explore our competitive job data pricing plans for job data extraction. Choose the right plan for yo...

43. [Empowering Businesses with Quality Job Data - JobsPikr API](https://www.jobspikr.com/jobspikr-api/) - The JobsPikr API delivers real-time job data from leading job boards, providing businesses, employer...

44. [Navigating the World of Job Search API: A Spotlight on Indeed API](https://www.jobspikr.com/blog/navigating-job-search-api-spotlight-indeed-api/) - Easy Integration: JobsPikr's user-friendly API make integration straightforward, enabling developers...

45. [JSearch - Rapid API](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch/pricing) - RapidAPI partners directly with API providers to give you no-fuss, transparent pricing. Basic. $0.00...

46. [Scrape jobs from Indeed, LinkedIn & more with RapidAPI to Google ...](https://n8n.io/workflows/8250-scrape-jobs-from-indeed-linkedin-and-more-with-rapidapi-to-google-sheets/) - Active Job Scraper Workflow Using RapidAPI Jobs Search Realtime Data API This powerful Active Job Sc...

47. [Scraping LinkedIn Data With Proxycurl Jobs API - DEV Community](https://dev.to/heymich/scraping-linkedin-data-with-proxycurl-jobs-api-2jgb) - Proxycurl gives free 10 credits for trial and each successful request to the API costs 1 credit. You...

48. [PeopleDataLabs vs Proxycurl: Comprehensive Comparison for ...](https://fullenrich.com/tools/PeopleDataLabs-vs-Proxycurl) - Official Documentation for Proxycurl API - Learn more about Proxycurl's API, data coverage, and inte...

49. [Access LinkedIn job data with ApiFirst's Jobs Scraper API](https://www.linkedin.com/posts/api-first-1_linkedin-jobs-scraper-api-activity-7367314017272352769-E6rI) - Looking for real-time job data from LinkedIn? Check out the LinkedIn Jobs Scraper API by ApiFirst: ✓...

50. [LinkedIn Data Scraping - The Ultimate Guide - Autoposting.ai](https://autoposting.ai/linkedin-data-scraping/) - ... linkedin data scraping landscape in 2025 is more treacherous than ever. LinkedIn has invested mi...

51. [Selenium vs Playwright vs Puppeteer vs Ulixee Hero vs Nodriver](https://bytetunnels.com/posts/browser-automation-showdown-selenium-playwright-puppeteer-ulixee-hero-nodriver/) - The Stealth Factor​​ Detection rates vary significantly: Selenium: 85-95% detection rate on protecte...

52. [How to Scrape Indeed: 2025 Guide for Job Market Data - Automatio AI](https://automatio.ai/how-to-scrape/indeed) - Aggressive Anti-Bot Layers ... Indeed uses a combination of Cloudflare and DataDome to detect and bl...

53. [Google Jobs Listing Results API - SerpApi](https://serpapi.com/google-jobs-listing-api) - Our Google Jobs Listing API allows you to scrape SERP results from a Google Jobs Listing search. The...

54. [How to build a Glassdoor review scraper with Python for HR analytics](https://www.hr-analytics-trends.com/blog/how-to-build-a-glassdoor-review-scraper-with-python-for-hr-analytics) - Glassdoor employs various anti-bot mechanisms to protect its job listings, company reviews, and user...

55. [Introduction – Job Board API - Developer Resources | Greenhouse](https://developers.greenhouse.io/job-board.html) - With our Job Board API, you will have easy access to a simple JSON representation of your company's ...

56. [Greenhouse Jobs API - Job Data Feeds - Fantastic.jobs](https://fantastic.jobs/ats/greenhouse) - Greenhouse Official Jobs API​​ The API will return a JSON containing most relevant job posting field...

57. [lever/postings-api: API documentation and examples for the ... - GitHub](https://github.com/lever/postings-api) - This repository contains documentation and example apps for the Lever Postings REST API. This API is...

58. [Ashby Job Postings API](https://developers.ashbyhq.com/docs/public-job-posting-api) - This API allows you to get data for all currently published Job Postings for your organization. If y...

59. [[PDF] Workday Integration Cloud Connectors for HCM](https://www.workday.com/content/dam/web/sg/documents/datasheets/workday-integration-cloud-connectors-hcml-datasheet.pdf) - As you post, update, or delete jobs, the integration generates a Workday XML output file that contai...

60. [orgupdate/Apify-Handshake-Jobs-Scraper - GitHub](https://github.com/orgupdate/Apify-Handshake-Jobs-Scraper) - The Handshake Jobs Scraper is a powerful data extraction tool designed to aggregate job listings fro...

61. [Wellfound (formerly AngelList) integration - Greenhouse Support](https://support.greenhouse.io/hc/en-us/articles/206535045-Wellfound-formerly-AngelList-integration) - Greenhouse Recruiting's integration with Wellfound matches applicants created in Wellfound to your c...

62. [JobPosting - Schema.org Type](https://schema.org/JobPosting) - A listing that describes a job opening in a certain organization. Examples Copy to clipboard Example...

63. [Introduction to Vector Databases using ChromaDB - Dataquest](https://www.dataquest.io/blog/introduction-to-vector-databases-using-chromadb/) - Learn when brute-force breaks, how vector databases speed up semantic search, and how to build fast ...

64. [asg017/sqlite-vss: A SQLite extension for efficient vector ... - GitHub](https://github.com/asg017/sqlite-vss) - sqlite-vss (SQLite Vector Similarity Search) is a SQLite extension that brings vector search capabil...

65. [[FEATURE] Add support for SQLite with sqlite-vec as a vector store](https://github.com/Hawksight-AI/semantica/issues/240) - SQLite is already widely used in these contexts, and the sqlite-vec extension enables efficient vect...

66. [sentence-transformers/all-MiniLM-L6-v2 - Hugging Face](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/discussions/22) - Hi, Can someone please advise me upon the hardware requirements of using this model for a semantic s...

67. [LLM API Pricing Comparison (2025): OpenAI, Gemini, Claude](https://intuitionlabs.ai/articles/llm-api-pricing-comparison-2025) - GPT-4o: $5.00 per 1M input tokens ($2.50 cached) and $20.00 per 1M output. GPT-4o Mini: $0.60 per 1M...

68. [llama3.2:3b](https://ollama.com/library/llama3.2:3b) - It's use cases include: Personal information management; Multilingual knowledge retrieval; Rewriting...

69. [Faster SQLite LIKE Queries Using FTS5 Trigram Indexes](https://andrewmara.com/blog/faster-sqlite-like-queries-using-fts5-trigram-indexes) - So it takes about 1.75 seconds to run a simple substring query on 18.2 million rows no matter how ma...

70. [We are running FTS5 with a bunch of sqlite databases for an internal ...](https://news.ycombinator.com/item?id=41207085) - Speed is very fast -- the biggest dbs are hundreds of ms response time, but others are sub 10 or ten...

71. [JOINs with FTS5 virtual tables are very slow - SQLite User Forum](https://sqlite.org/forum/info/509bdbe534f58f20) - I don't have a cut-off number, but a query finding fewer than 100 rows is blindingly fast but a quer...

72. [What are the advantages of WAL mode during concurrent SQLite ...](https://www.tencentcloud.com/techpedia/138381) - The Write-Ahead Logging (WAL) mode in SQLite offers several advantages during concurrent writes, pri...

73. [Pgvector Extension – CedarDB Documentation](https://cedardb.com/docs/references/advanced/pgvector/) - CedarDB supports working with vectors using the syntax from the pgvector Postgres extension. All vec...

74. [Enable and use pgvector in Azure Database for PostgreSQL](https://learn.microsoft.com/en-us/azure/postgresql/extensions/how-to-use-pgvector) - The pgvector extension adds an open-source vector similarity search to PostgreSQL. This article intr...

75. [DuckDB: The In-Process OLAP Engine Redefining Analytics | Uplatz](https://www.youtube.com/watch?v=ywkhVosFPC0) - DuckDB is one of the fastest-growing tools in the data world — an in-process analytical database des...

76. [The Good and Bad of ChromaDB for RAG: Based on Our Experience](https://www.altexsoft.com/blog/chroma-pros-and-cons/) - Learn how Chroma DB for RAG works, its strengths, weaknesses, and whether it's the right vector stor...

77. [Run Llama 3 on Mac: Step-by-Step Ollama Setup (M1/M2/M3/M4)](https://localaimaster.com/blog/run-llama3-on-mac) - How to run Llama 3 on Mac with Ollama: 1) brew install ollama 2) ollama run llama3.1. Works on M1/M2...

78. [Llama 3.2 Instruct 3B Intelligence, Performance & Price Analysis](https://artificialanalysis.ai/models/llama-3-2-instruct-3b) - ... 3B on the Intelligence Index. At 48 tokens per second, Llama 3.2 Instruct 3B is slower than aver...

79. [How to Set User Agents for Web Scraping (Python & No-Code)](https://www.octoparse.com/blog/user-agents-for-web-scraping) - Each user agent should always ship with: Matching Accept headers; Matching Accept Language; A matchi...

80. [Is Web Scraping Legal? Legality Guide and Best Practices](https://scrapegraphai.com/blog/is-web-scraping-legal) - Scraping personal or sensitive data without explicit consent can lead to serious legal consequences ...

81. [Simplify Copilot | Autofill Job Applications and Track Jobs](https://simplify.jobs/copilot) - Autofill job applications anywhere on the web, get notified when new jobs open & seamlessly track yo...

82. [Jobright Review: Features, Pros and Cons, and Alternatives ... - Sprout](https://www.usesprout.com/blog/jobright-ai-review) - The tool uses AI to match you with relevant opportunities and customize your applications for each r...

83. [Your personal AI job search copilot - Jobright](https://jobright.ai/ai-agent) - Job Search Agent That's Always On ; 90% Job Search Automation · Unlock Auto-Apply ; Your Own AI Care...

84. [What Can The Jobright Chrome Extension Do To Free Up Time For ...](https://www.vervecopilot.com/hot-blogs/jobright-chrome-extension-interview-time) - Prioritize roles by match score and prepare 2–3 role-specific STAR stories before applying. Use AI-t...

85. [Supercharge Your Job Search with Jobright Autofill](https://jobright.ai/blog/supercharge-your-job-search-with-jobright-autofill/) - AI-Tailored Resumes: Create recruiter-optimized resumes for each role in under a minute and autofill...

86. [Efficient Online Job Tracker | Organize Your Search - Jobright](https://jobright.ai/tools/job-tracker) - Jobright's Job Tracker lets users upload external jobs. The system parses the details and creates a ...

87. [The Best LinkedIn Chrome Extensions for Different Users](https://jobright.ai/blog/chrome-extensions-for-linkedin/) - Some Chrome extensions can assist you in optimizing your profile, saving contact information, genera...

88. [Free Job Search Chrome Extension - Teal](https://www.tealhq.com/tool/job-search-chrome-extension) - The Job Tracker Chrome Extension helps you move faster, stay organized, and instantly see if a role ...

89. [Teal vs. Simplify: Job Tracker Comparison - Scale.jobs](https://scale.jobs/blog/teal-vs-simplify-job-tracker-comparison) - Cost-effective pricing: A one-time fee of $199 covers 250 applications, compared to Simplify's recur...

90. [cwwmbm/linkedinscraper: Scrape job postings from LinkedIn - GitHub](https://github.com/cwwmbm/linkedinscraper) - This is a Python application that scrapes job postings from LinkedIn and stores them in a SQLite dat...

91. [Pavel401/JobsScraper: Jobs Scraper - GitHub](https://github.com/Pavel401/JobsScraper) - The Jobs Scraper is a powerful Go application designed for scraping job postings from a variety of w...

92. [haydenthai/Linkedin-Discord-Job-Scraper-Bot - GitHub](https://github.com/haydenthai/Linkedin-Discord-Job-Scraper-Bot) - This library is a Discord bot that automates job postings in Discord channels by scraping job listin...
