# Firecrawl for Job Site Mapping: Extensive Research Document

**JobRadar V2 -- Scraping Infrastructure Research**
**Date: 2026-03-28**
**Research Basis:** Training knowledge through August 2025, cross-referenced with repo dependency tree.

---

## 1. What Is Firecrawl?

Firecrawl is a managed web scraping and crawling API built by Mendable AI (YC S23), open-sourced at `github.com/mendableai/firecrawl`. First released publicly in early 2024, it reached roughly 15,000-18,000 GitHub stars by mid-2025.

Its core design philosophy is to abstract away the hardest parts of modern web scraping: JavaScript rendering, bot detection evasion, proxy rotation, and LLM-native output (Markdown, structured JSON). Rather than building around raw HTML, Firecrawl makes content immediately usable by AI pipelines by returning clean Markdown or structured objects.

### Architecture

The cloud offering runs on a distributed scraping cluster with:
- Rotating residential proxies
- Stealth browser pools (Playwright-based headless Chrome)
- Cloudflare bypass via undetected browser fingerprinting
- Redis-backed job queues
- Per-request LLM extraction (OpenAI-compatible)

The self-hosted version (available in the same GitHub repo) is a Docker Compose stack containing the Node.js API server, a Playwright worker pool, Redis, and optional Supabase for auth.

### Four Core Endpoints

**1. `/scrape` -- Single-page scraping**

Fetches one URL, renders JavaScript, returns the page as clean Markdown, structured HTML, raw HTML, links, and/or a screenshot. Supports specifying which formats to return, which actions to perform before scraping (click, scroll, wait, fill form), and a JSON extraction schema. The `actions` array lets you interact with the page before capturing -- directly comparable to Playwright's scripted interaction model.

The `extract` parameter within `/scrape` accepts a JSON Schema (Pydantic-compatible) and a prompt string. Firecrawl passes the rendered page content through an LLM (GPT-4o or their own models depending on tier) and returns a typed JSON object matching the schema. This is the LLM extraction mode.

**2. `/crawl` -- Recursive site crawling**

Starts from a seed URL and follows links matching configurable rules (include/exclude path patterns, max depth, max pages, subdomain inclusion). Each discovered page is scraped and returned. Returns a job ID immediately; results are polled or received via webhook. Supports the same extraction options per-page as `/scrape`.

Limits: free tier caps crawl at 10 pages; paid tiers allow thousands. Rate limits apply per-minute.

**3. `/map` -- URL discovery without scraping content**

This is the most relevant endpoint for the "map once" strategy. Given a seed URL, it discovers all URLs on the site without fetching and rendering every page's full content. Internally it uses a combination of:
- Fetching and parsing `sitemap.xml` (and nested sitemaps)
- Following robots.txt discovery hints
- Shallow link extraction from the seed page and 1-2 levels of navigation

It returns a flat list of URLs -- potentially thousands per domain -- in seconds to minutes, without the cost of rendering each page. This is dramatically cheaper than `/crawl`.

Key parameters: `limit` (max URLs to return), `includeSubdomains`, `search` (filter returned URLs by keyword -- crucial for filtering to `/jobs/`, `/careers/` paths), `ignoreSitemap` (force link-following instead of sitemap parsing).

**4. `/extract` -- LLM-powered structured extraction across multiple URLs**

Introduced in late 2024 as a higher-level endpoint. You pass a list of URLs (or a seed + crawl config) and a JSON schema with a natural language prompt. Firecrawl internally orchestrates scraping + LLM extraction per URL and returns structured data matching the schema. This is the "batch extract" capability -- usable for site-profiling without writing any parsing logic.

### Pricing (as of mid-2025)

Firecrawl pricing is credit-based. Credits are consumed per operation:

| Operation | Credit cost |
|-----------|-------------|
| `/scrape` (HTML/Markdown only) | 1 credit |
| `/scrape` with LLM extraction | ~5 credits (varies by model/tokens) |
| `/crawl` per page crawled | 1 credit |
| `/map` (full URL discovery) | 1 credit per URL discovered, minimum ~2 |
| `/extract` (LLM structured) | ~5-10 credits per URL |

Pricing tiers (approximate, mid-2025):
- **Free**: 500 credits/month, rate-limited, no SLA
- **Hobby** (~$16/month): ~3,000 credits/month
- **Standard** (~$83/month): ~100,000 credits/month
- **Growth** (~$333/month): ~500,000 credits/month
- **Enterprise**: custom

**NOTE**: Firecrawl has adjusted pricing several times. Verify at `firecrawl.dev/pricing` before budgeting.

### Calculating Cost for 1,500-Site Mapping

For the "map once" strategy:

- **Phase 1: URL discovery** via `/map` on 1,500 career sites
  - Assume average 50 URLs discovered per site (career pages often have a focused URL space)
  - 1,500 sites x 50 URLs = 75,000 URL discoveries
  - At 1 credit/URL: ~75,000 credits
  - On Standard tier (~$83/month for 100k): fits within one month's allocation

- **Phase 2: Schema extraction** on 1-3 representative job listing pages per site
  - 1,500 sites x 2 sample pages x ~5 credits = 15,000 credits
  - Fits comfortably in Standard tier alongside Phase 1

- **Total one-time mapping cost estimate**: 75,000-100,000 credits = roughly one Standard month (~$83-$100)

---

## 2. The `/map` Endpoint -- Deep Dive

### How It Works Internally

When called on `https://company.com/careers`:
1. Firecrawl fetches `https://company.com/robots.txt` and checks for `Sitemap:` directives
2. If sitemaps exist, it fetches and parses them (including sitemap indexes)
3. It also fetches the seed URL and extracts `<a href>` links from the rendered page
4. Results are deduplicated and returned as a flat URL array

### Sitemap Reality for ATS Platforms

- **Greenhouse**: `https://boards.greenhouse.io/sitemap.xml` -- boards domain
- **Lever**: Lever job boards generally don't expose sitemaps; relies on link extraction
- **Workday**: Varies per instance; some expose sitemaps, many do not
- **Ashby**: `https://jobs.ashbyhq.com/company` -- typically parseable HTML
- **iCIMS**: Portal-specific; usually parseable via direct API

**Key insight**: For major ATS platforms you already scrape natively, `/map` adds limited value. Highest value is for **unknown custom career sites**.

---

## 3. LLM-Powered Site Profiling via `/extract`

### The "Site Profile" Concept

For JobRadar V2, the one-time extraction run would produce a **site profile** per domain:

```
{
  "domain": "careers.acmecorp.com",
  "ats_detected": "custom",
  "listing_url_pattern": "/jobs/{id}",
  "index_url": "https://careers.acmecorp.com/jobs",
  "pagination_type": "api_json",  // or "page_param", "infinite_scroll", "static"
  "job_container_selector": ".job-listing-card",
  "title_selector": "h2.job-title",
  "location_selector": ".job-location",
  "apply_url_pattern": "/jobs/{id}/apply",
  "requires_js": true,
  "cloudflare_protected": false,
  "last_profiled": "2025-06-01T00:00:00Z"
}
```

This profile then drives a **cheap, fast scraper** using tools already in the dependency tree. The key insight: LLM extraction is expensive per-call ($0.01-0.05 per page at GPT-4o rates), but you only pay it once per site, then run the derived selector/pattern cheaply forever.

---

## 4. Self-Hosting Firecrawl

### Components

Docker Compose stack:
- `api` -- Node.js Express server
- `worker` -- Playwright-based scraping workers (horizontally scalable)
- `playwright-service` -- Dedicated browser service container
- `redis` -- Job queue and caching

### Resource Requirements

- Worker container with Playwright: ~1-1.5 GB RAM per worker instance
- API service: ~256-512 MB
- Redis: ~128-256 MB
- Running 2 workers: ~3-4 GB total RAM overhead

On 16 GB RAM, this is feasible alongside Postgres, Redis, and backend. Concern: each concurrent browser context uses 200-400 MB.

### Self-Hosted vs Cloud Decision Matrix

| Concern | Self-Hosted | Cloud |
|---------|-------------|-------|
| Cost at scale | Near-zero marginal cost | Per-credit; expensive at volume |
| Proxy coverage | Your IP only; bot-detection risk | Rotating residential proxies |
| Cloudflare bypass | Weak without separate proxy service | Built-in |
| Setup effort | ~2-4 hours initially | Zero |
| Resource overhead | ~3-5 GB RAM | None local |
| Data privacy | All on-prem | Content sent to Firecrawl servers |

**Verdict**: Self-hosted is viable for non-Cloudflare sites. For Cloudflare-protected (~15-30% of sites), you need cloud tier or a residential proxy service.

---

## 5. Firecrawl vs Alternatives -- Detailed Comparison

### Already in the JobRadar V2 Dependency Tree

From `pyproject.toml`: `crawl4ai>=0.4.0`, `scrapling[all]>=0.4.0`, `playwright>=1.44.0`, `httpx>=0.27.0`, `beautifulsoup4>=4.12.0`, `cloudscraper>=1.2.0`, `nodriver>=0.38.0`, `camoufox>=0.4.0`, `browserforge>=1.1.0`.

This is an extremely capable scraping stack already. The question is not "should we add scraping capabilities" but "does Firecrawl add enough value over what we already have?"

### Crawl4AI v0.4.x (already in tree)
- **License**: Apache 2.0
- **GitHub stars**: ~20,000-25,000 (mid-2025)
- Closest free alternative to Firecrawl's core scraping+extraction pipeline
- Runs Playwright locally (same browsers already installed)
- Supports LLM-based extraction via `LLMExtractionStrategy`
- **LLM extraction cost**: You supply and pay for the LLM API key. At GPT-4o pricing (~$0.005/page), 1,500 sites x 2 pages = 3,000 calls = ~$15. Dramatically cheaper than Firecrawl credits.

### Scrapling v0.4.x (already in tree)
- **License**: BSD-3-Clause
- Strength is CSS selector stability across page redesigns via "adaptive selectors"
- Valuable for ongoing 30-minute scraping runs, not the one-time mapping pass
- No LLM extraction built in

### spider-rs / Spider Cloud
- Rust-based; benchmarks show 200+ pages/second
- Python bindings are thin wrapper around cloud API, not the Rust core
- Relevant for raw throughput but not the binding constraint for 1,500-site mapping

---

## 6. The Integration Pattern for JobRadar V2

### Recommended Architecture: Tier Classification

| Tier | Description | Estimated Count | Recommended Tool |
|------|-------------|-----------------|-----------------|
| A | Known ATS (Greenhouse, Lever, Workday, Ashby, iCIMS) | 800-1,000 | Existing native scrapers -- no Firecrawl needed |
| B | Custom careers page, static/simple HTML | 200-300 | Playwright + BS4 + LLM extraction via Crawl4AI |
| C | Custom careers page, JS-heavy, no Cloudflare | 150-200 | nodriver/camoufox + LLM extraction |
| D | Custom careers page + Cloudflare protection | 100-150 | Firecrawl cloud OR residential proxy + your stack |

**Only Tier D genuinely needs Firecrawl cloud.** For Tier D at 100-150 sites, the one-time mapping cost is well within Free or Hobby tier.

### Site Profile Data Model

```
site_profiles table:
  domain: str (PK)
  ats_type: enum (greenhouse, lever, workday, ashby, icims, custom_static, custom_js, unknown)
  index_url: str
  listing_url_pattern: str | null
  pagination_type: enum (none, page_param, cursor, api_json, infinite_scroll)
  api_endpoint: str | null
  job_container_selector: str | null
  title_selector: str | null
  location_selector: str | null
  salary_selector: str | null
  description_selector: str | null
  apply_url_pattern: str | null
  requires_browser: bool
  cloudflare_protected: bool
  profiled_at: DateTime(timezone=True)
  profiled_by: enum (firecrawl, crawl4ai, manual, ats_native)
  profile_confidence: float
  last_successful_scrape: DateTime(timezone=True)
  consecutive_failures: int
```

### Two-Phase Workflow

**Phase 1: One-time profiling**

- Tier A (known ATS): profiling done by ATS type detection alone -- no crawling needed
- Tiers B and C: Use Crawl4AI's `AsyncWebCrawler` with `LLMExtractionStrategy`
- Tier D (Cloudflare): Call Firecrawl `/map` then `/scrape` with extract schema

**Phase 2: Ongoing 30-minute scraping**

Scheduler reads `site_profile` and dispatches to appropriate scraper worker:
- `ats_type=greenhouse` -> existing Greenhouse API scraper
- `ats_type=custom_static` + selectors -> httpx + BS4 with stored selectors
- `ats_type=custom_js` + selectors -> nodriver/camoufox + stored selectors
- `cloudflare_protected=true` -> camoufox with browserforge fingerprinting

Ongoing scraping does **not** touch Firecrawl unless re-profiling is triggered by `consecutive_failures > 5`.

### ATS Detection Without LLM

Before spending credits, run fingerprinting:
- Greenhouse: `boards.greenhouse.io` in iframe src, or `boards-api.greenhouse.io` response
- Lever: `jobs.lever.co/{company}` in page source
- Workday: `myworkdayjobs.com` or `workday.com` in URL/iframe
- Ashby: `jobs.ashbyhq.com` or Ashby API headers
- iCIMS: `icims.com` in URL or `window.icims` in page JS
- Taleo: `taleo.net` in URL
- SmartRecruiters: `smartrecruiters.com` in page source
- BambooHR: `bamboohr.com` in URL

---

## 7. Real-World Community Experiences

### Community Observations (Reddit r/webscraping, HN, X, mid-2025)

**Pricing volatility**: Most-cited complaint. Firecrawl restructured credit pricing at least twice between late 2023 and mid-2025.

**Reliability at scale**: Managed API reports 99.5%+ uptime, but crawl jobs on complex JS SPAs sometimes return empty results without errors. Retry logic is essential.

**Cloudflare bypass**: Generally positive for most sites. Sites using Cloudflare Bot Management (enterprise tier) with behavioral scoring can still block.

**LLM extraction quality**: High satisfaction for well-structured job pages. Main failure mode: multi-step pages requiring "see more" clicks.

**Self-hosted**: Works well for non-Cloudflare sites but without proxy rotation, ~30-50% of sites get blocked within weeks.

**Community consensus (mid-2025)**: Crawl4AI preferred for teams that control their own LLM keys. Firecrawl preferred when you need Cloudflare bypass without managing proxies. Common pattern: Firecrawl for initial discovery, then Crawl4AI/Playwright for ongoing scraping.

---

## 8. Full Comparison Table

| Criterion | Firecrawl Cloud | Firecrawl Self-Hosted | Crawl4AI (in tree) | Raw Stack (Playwright+BS4+LLM) |
|-----------|-----------------|----------------------|-------------------|-------------------------------|
| Maturity | 18 months production | 12 months, lags cloud | ~18 months, active | All components mature |
| Cost (1,500 mapping) | ~$83-100 one-time | Server cost only | LLM API only (~$15) | LLM API only (~$15) |
| Cost (ongoing scraping) | Untenable at scale | Server cost only | Free (no LLM needed) | Free |
| Cloudflare bypass | Excellent | Poor (your IP) | Poor (your IP) | Good (camoufox in tree) |
| LLM extraction quality | High (managed) | Same as cloud | High (bring your model) | High (bring your model) |
| Data privacy | Content leaves network | On-prem | On-prem | On-prem |
| New dependency? | Yes (firecrawl-py) | Yes + Docker reconfig | Already in tree | Already in tree |

---

## 9. Final Recommendations

### Do Not Make Firecrawl a Core Dependency

Use it narrowly for Cloudflare-protected Tier D sites during the one-time profiling pass.

### Primary Recommendation for Site Profiling (Tiers B and C)

Use **Crawl4AI**, which is already in the optional dependency tree. Identical LLM extraction with your own API key, costs ~$15 for 3,000 page extractions, keeps all data on-prem.

### Primary Recommendation for Tier D (Cloudflare-Protected)

Use **Firecrawl cloud on Hobby tier** (~$16/month) during a one-time profiling sprint. Extract site profiles. Store them. Cancel or downgrade.

### Triage Order

1. Run ATS fingerprinting on all 1,500 sites -- 60-70% resolve to known ATS types immediately
2. For remaining ~400-500 unknown sites, run Crawl4AI LLM extraction (~$5-15 API cost)
3. For the ~100-150 that fail due to Cloudflare, escalate to Firecrawl cloud
4. Store all profiles in `site_profiles` table with staleness checks
5. Ongoing scraping uses stored profiles -- no Firecrawl, no LLM cost per scrape

### What NOT to Do

- Do not route all 1,500 sites through Firecrawl every 30 minutes (720,000 credits/month = $333+/month)
- Do not use Firecrawl self-hosted without residential proxies
- Do not skip ATS fingerprinting for known ATS sites

---

## 10. Reference URLs (verify current)

- Firecrawl docs: `https://docs.firecrawl.dev/`
- Firecrawl GitHub: `https://github.com/mendableai/firecrawl`
- Firecrawl pricing: `https://firecrawl.dev/pricing`
- Crawl4AI docs: `https://docs.crawl4ai.com/`
- Crawl4AI GitHub: `https://github.com/unclecode/crawl4ai`
- Scrapling GitHub: `https://github.com/D4Vinci/Scrapling`
- camoufox GitHub: `https://github.com/daijro/camoufox`
- nodriver GitHub: `https://github.com/ultrafunkamsterdam/nodriver`
- Spider Cloud: `https://spider.cloud/`
