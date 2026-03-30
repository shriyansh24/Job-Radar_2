# Stealth Job Scraping at Scale: 1,500 Sites / 30 Minutes / 16GB RAM

**Date: 2026-03-28 | Research basis: Web search + training knowledge**

---

## 1. The Anti-Bot Landscape (2025-2026)

### Major Anti-Bot Systems

| System | Deployment | Detection Methods |
|--------|-----------|-------------------|
| Cloudflare Bot Management | ~20% of the web | TLS fingerprint (JA3/JA4), behavioral ML, challenge pages, Turnstile |
| DataDome | Enterprise career sites | Intent-based detection (2025), behavioral ML, device fingerprint |
| Akamai Bot Manager | Large enterprises | JA4 fingerprinting (2026), behavioral scoring, sensor data |
| PerimeterX/HUMAN | E-commerce, some career sites | Client-side JS challenges, behavioral biometrics |
| Kasada | Financial, some tech | Proof-of-work challenges, dynamic obfuscation |

### Key Evolution: Intent-Based Detection (2025+)

DataDome introduced intent-based detection in 2025 -- analyzing **what the visitor is trying to accomplish** rather than just "is this a bot?" Even a scraper with a perfect browser fingerprint can be flagged if the navigation pattern suggests automated data collection. Anti-bot deployments grew **78% year-over-year** in 2025.

### TLS Fingerprinting: JA3 -> JA4

- **JA3**: Hashes TLS ClientHello parameters. Chrome now randomizes extension order, generating billions of different JA3 hashes per version.
- **JA4** (Akamai, 2026): Sorts extensions alphabetically before hashing, resistant to randomization. Adds ALPN values, SNI info, TCP/QUIC distinction.
- **Implication**: Simple JA3 spoofing no longer works. Need actual browser TLS stacks or curl-impersonate.

Sources:
- [Castle.io: Anti-detect frameworks evolution](https://blog.castle.io/from-puppeteer-stealth-to-nodriver-how-anti-detect-frameworks-evolved-to-evade-bot-detection/)
- [Scrapfly: DataDome bypass 2026](https://scrapfly.io/blog/posts/how-to-bypass-datadome-anti-scraping)
- [Scrapfly: Cloudflare bypass 2026](https://scrapfly.io/blog/posts/how-to-bypass-cloudflare-anti-scraping)
- [Cloudflare JA3/JA4 docs](https://developers.cloudflare.com/bots/additional-configurations/ja3-ja4-fingerprint/)

---

## 2. Anti-Detection Tool Stack

### Tier 1: camoufox (Already in repo -- BEST stealth)

- **How it works**: Modifies Firefox at the **C++ level** (not JS patches), avoiding detection vectors that trip other tools
- **Stealth score**: 0% detection across major test suites (CreepJS, BotD, etc.)
- **Memory**: ~300-400MB per context
- **Key advantage**: Only tool that consistently achieves perfect stealth scores
- **Limitation**: Firefox-based, so some sites that specifically target Chrome fingerprints may behave differently

### Tier 2: nodriver (Already in repo)

- **How it works**: CDP-minimal framework, communicates with Chrome directly, avoids traditional automation protocol detection vectors
- **Stealth**: Emulates real user behavior through native OS-level inputs
- **Key advantage**: Chrome-based (matches majority user fingerprint), lightweight
- **Memory**: ~200-300MB per context

### Tier 3: Playwright + stealth plugins

- **playwright-stealth**: JS patches to hide automation signals
- **Limitation**: Detectable by advanced systems (DataDome, Akamai) since patches are applied at JS level, not browser binary level
- **Use case**: Sites with basic bot detection only

### Tier 4: Pure HTTP (httpx + curl-impersonate)

- **curl-impersonate**: Extends libcurl to mimic real browser TLS behavior
- **Memory**: <10MB per connection
- **Key advantage**: 100x more memory-efficient than browser contexts
- **Limitation**: No JS rendering -- only works for API-backed ATS (Greenhouse, Lever) and static HTML sites

### Recommended Stack for JobRadar

```
Site Type              -> Tool                  -> Memory per connection
API-backed ATS         -> httpx (pure HTTP)     -> ~5MB
Static HTML career     -> httpx + BS4           -> ~5MB
JS-heavy, no anti-bot  -> nodriver              -> ~200MB
JS-heavy + Cloudflare  -> camoufox              -> ~350MB
Hardened (DataDome)    -> camoufox + proxy      -> ~400MB
```

Sources:
- [camoufox GitHub](https://github.com/daijro/camoufox)
- [ScrapingBee: How to scrape with camoufox](https://www.scrapingbee.com/blog/how-to-scrape-with-camoufox-to-bypass-antibot-technology/)
- [Patchright alternatives 2026](https://roundproxies.com/blog/best-patchright-alternatives/)
- [ScrapingAnt: Playwright undetectable](https://scrapingant.com/blog/playwright-scraping-undetectable)

---

## 3. Memory Budget for 16GB RAM

### Baseline Services (always running)

| Service | RSS |
|---------|-----|
| PostgreSQL | ~500MB |
| Redis | ~100MB |
| Python backend (FastAPI) | ~300MB |
| Python scheduler | ~150MB |
| Python worker (scraping) | ~200MB |
| Python worker (analysis) | ~150MB |
| Python worker (ops) | ~100MB |
| OS + system | ~2GB |
| **Total baseline** | **~3.5GB** |

### Available for scraping: ~12.5GB (leaves 16GB - 3.5GB)

### Concurrent Browser Contexts

| Tool | Memory per context | Max concurrent (in 12.5GB) |
|------|-------------------|---------------------------|
| camoufox | ~350MB | 35 |
| nodriver | ~200MB | 62 |
| httpx (no browser) | ~5MB | 2,500 |

### Optimal Concurrency Mix

For 1,500 sites where ~60-70% are API-backed ATS:
- **~1,000 API-backed sites**: httpx, 100 concurrent connections = ~500MB
- **~300 static HTML sites**: httpx + BS4, 50 concurrent = ~250MB
- **~200 JS-heavy sites**: nodriver, 5 concurrent contexts = ~1GB (reused across sites)
- **~100 Cloudflare sites**: camoufox, 3 concurrent contexts = ~1.05GB

**Total scraping memory**: ~2.8GB -- fits comfortably in the 12.5GB budget

---

## 4. Scheduling Strategy for 30-Minute Cycles

### The Math

- 1,500 sites / 30 minutes = 50 sites per minute
- At 2 requests per site (index + detail) = 100 requests per minute
- Per-domain rate limit: 1 request per second per domain (politeness standard)
- Since each domain is unique: no rate-limit bottleneck between domains

### Staggered Batch Architecture

```
Batch 1 (t=0s):    50 API-backed sites via httpx (completes in ~10s)
Batch 2 (t=10s):   50 API-backed sites via httpx (completes in ~10s)
...repeating for ~20 batches of API sites (~200s total)...
Batch 21 (t=200s): 50 static HTML sites via httpx+BS4 (~15s each)
...6 batches (~90s total)...
Batch 27 (t=290s): 40 JS-heavy sites via nodriver (5 concurrent, ~30s each)
...5 rotations of 40 sites (~150s total)...
Batch 32 (t=440s): 25 Cloudflare sites via camoufox (3 concurrent, ~45s each)
...4 rotations (~180s total)...

Total wall-clock: ~620s = ~10.3 minutes for 1,500 sites
Buffer: ~20 minutes for retries, slow sites, errors
```

### Adaptive Scheduling

- **Content hash**: Store SHA-256 of extracted job listings. Skip expensive processing if hash unchanged.
- **Variable frequency**: High-value targets (top companies) every 30 min. Low-change sites every 2-4 hours.
- **Priority queue**: Sites with recent job changes get higher priority in the next cycle.
- **Failure backoff**: After 3 consecutive failures, reduce frequency. After 5, mark inactive.

---

## 5. Rate Limiting and Politeness

### Per-Domain Rules

| Domain Type | Rate Limit | Rationale |
|-------------|-----------|-----------|
| Public API (Greenhouse boards-api) | 2 req/s | API is designed for consumption |
| Public API (Lever) | 1 req/s | Implicit rate limit in API |
| Career page (standard) | 1 req/s | robots.txt standard |
| Career page (Workday) | 0.5 req/s | Workday is aggressive about blocking |
| Cloudflare-protected | 0.3 req/s | Minimize detection risk |

### Global Concurrency Limits

- **Total HTTP connections**: 200 (fits in memory budget)
- **Total browser contexts**: 8 (3 camoufox + 5 nodriver)
- **Redis queue depth limit**: 500 pending jobs max

### robots.txt Compliance

- Parse robots.txt on first visit, cache per domain (TTL: 24 hours)
- Honor `Crawl-delay` directive
- Respect `Disallow` for non-job paths (no need to crawl /about, /blog, etc.)
- **Career pages are almost never disallowed** -- companies want their jobs found

---

## 6. Reliability and Error Handling

### Soft Block Detection

Not all blocks return HTTP 403/429. Common soft blocks:
- **200 OK with CAPTCHA page**: Check for CAPTCHA indicators in response body
- **200 OK with empty results**: Compare result count against historical baseline
- **200 OK with redirect to login**: Detect auth redirect patterns
- **Slow response (>10s)**: Tarpit detection

### Circuit Breaker Pattern

```
State Machine:
  CLOSED (normal) --[3 failures]--> OPEN (skip site)
  OPEN --[60s cooldown]--> HALF_OPEN (try 1 request)
  HALF_OPEN --[success]--> CLOSED
  HALF_OPEN --[failure]--> OPEN (reset cooldown to 120s)
```

Already implemented in the repo (`CircuitBreaker` with monotonic clock).

### Retry Strategy

- **Immediate retry**: Never (makes detection worse)
- **Next cycle retry**: Default (30 min later)
- **Backoff retry**: After 3 consecutive failures, try every 2 hours instead of 30 min
- **Inactive threshold**: After 5 consecutive failures, mark target inactive, alert

---

## 7. Proxy Strategy (Optional but Recommended for Hardened Sites)

### When Proxies Are Needed

- Cloudflare Bot Management (enterprise tier)
- DataDome intent-based detection
- Sites that IP-ban after N requests from same IP

### Proxy Options

| Provider | Type | Cost | Use Case |
|----------|------|------|----------|
| BrightData | Residential rotating | ~$5-10/GB | Hardened sites |
| Oxylabs | Residential | ~$8/GB | Cloudflare bypass |
| SmartProxy | Residential | ~$4-7/GB | Budget option |
| Free (no proxy) | Your IP | $0 | API-backed ATS, unprotected sites |

### Cost Estimate for JobRadar

- ~100-150 Cloudflare-protected sites, scraped every 30 min
- Each scrape: ~500KB page data = ~0.5MB
- 48 scrapes/day x 150 sites x 0.5MB = ~3.6GB/day
- At $5/GB: **~$18/day = ~$540/month**

**This is expensive.** Mitigation:
- Only use proxies for the subset that actually blocks your IP
- Use adaptive scheduling: reduce frequency for proxy-required sites to every 2 hours
- Revised estimate with 2-hour frequency: ~$135/month

### Alternative: Self-Hosted Proxy Rotation

If you have access to multiple IPs (VPS instances, cloud functions):
- Rotate requests across 5-10 IPs
- Much cheaper ($5/month per small VPS)
- Less effective against behavioral detection

---

## 8. Legal and Ethical Considerations

### Key Legal Precedents

- **hiQ Labs v. LinkedIn (2022)**: 9th Circuit ruled that scraping publicly accessible data does not violate CFAA. Career pages are public.
- **Van Buren v. United States (2021)**: Supreme Court narrowed CFAA to "gates-up-or-down" test. Public career pages are "gates up."
- **GDPR (EU)**: Job postings are not personal data. Scraping company career pages is generally permitted.
- **CCPA (CA)**: Similar -- public business information is not covered.

### Best Practices

- Respect robots.txt (advisory, not legally binding, but shows good faith)
- Don't scrape behind login walls (creates CFAA risk)
- Don't scrape personal data (recruiter profiles, employee info)
- Don't overwhelm servers (rate limiting = good faith)
- Store only job listing data, not full HTML dumps

### Career Pages Specifically

Career pages are designed to be publicly consumed. Companies **want** their job listings found by candidates. Scraping career pages is materially different from scraping social media profiles or proprietary databases.

---

## 9. Optimal Architecture Recommendation

### Three-Tier Scraper

```
Tier 1: API Scraper (httpx, async, 100 concurrent)
  - Greenhouse boards-api, Lever JSON, Ashby posting-api
  - ~1,000 sites, completes in ~3-4 minutes
  - Memory: ~500MB total
  - Zero detection risk (using public APIs as intended)

Tier 2: HTTP Scraper (httpx + BS4, async, 50 concurrent)
  - Static HTML career pages, known CSS selectors from site_profile
  - ~300 sites, completes in ~2-3 minutes
  - Memory: ~250MB total
  - Low detection risk (no browser fingerprint to detect)

Tier 3: Browser Scraper (nodriver/camoufox, 5-8 concurrent contexts)
  - JS-heavy pages, Cloudflare-protected sites
  - ~200 sites, completes in ~5-10 minutes
  - Memory: ~2GB total
  - Moderate detection risk (mitigated by stealth tools)
```

### Total Cycle Time: ~10-15 minutes (well within 30-min window)
### Total Memory: ~3GB during peak scraping
### Total with baseline services: ~6.5GB of 16GB (plenty of headroom)

Sources:
- [PromptCloud Scalable Architecture](https://www.promptcloud.com/blog/scalable-web-scraping-architecture/)
- [DataPrixa Memory Optimization](https://dataprixa.com/how-to-reduce-memory-usage-when-scraping/)
- [BrightData Distributed Crawling](https://brightdata.com/blog/web-data/distributed-web-crawling)
- [Latenode Headless Browsers 2025](https://latenode.com/blog/web-automation-scraping/web-scraping-techniques/headless-browsers-for-web-scraping)
- [ScrapeOps Playwright Undetectable](https://scrapeops.io/playwright-web-scraping-playbook/nodejs-playwright-make-playwright-undetectable/)
