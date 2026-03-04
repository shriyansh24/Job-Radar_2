# Scraper Module Context

## Purpose
Unified job scraping across 7 platforms with consistent normalization, rate limiting, and dedup-ready SHA256 job IDs.

## Current Status
- SerpApi (Google Jobs): Implemented, paginated (start=0,10,20...)
- Greenhouse ATS: Implemented, company watchlist slugs
- Lever ATS: Implemented, company watchlist slugs
- Ashby ATS: Implemented, with compensation extraction
- JobSpy (multi-board): Implemented, sync lib in thread executor
- TheirStack: Implemented, optional (requires THEIRSTACK_KEY)
- Apify: Implemented, optional (requires APIFY_KEY)

## Data Schema
```python
# Output of BaseScraper.normalize() — dict ready for Job model insert
{
    "job_id": str,           # SHA256(source:company:title)[:64]
    "source": str,           # "serpapi", "greenhouse", etc.
    "title": str,
    "company_name": str,
    "company_domain": str,   # Extracted from URL or inferred
    "company_logo_url": str, # Clearbit: logo.clearbit.com/domain
    "url": str,              # Apply/posting URL
    "location_city": str,
    "location_state": str,
    "location_country": str,
    "remote_type": str,      # "remote" | "hybrid" | "onsite" | None
    "job_type": str,         # "full-time" | "part-time" | "contract" | "internship"
    "salary_min": float,
    "salary_max": float,
    "salary_currency": str,  # Default "USD"
    "salary_period": str,    # "annual" | "hourly"
    "description_raw": str,  # Original HTML
    "description_clean": str,# BeautifulSoup text extraction
    "description_markdown": str, # html2text conversion
    "posted_at": datetime,
    "scraped_at": datetime,
}
```

## Key Functions
- `BaseScraper.fetch_jobs(query, location, limit)` -> `list[dict]` (abstract)
- `BaseScraper.normalize(raw_dict)` -> `dict` (builds full job record)
- `BaseScraper.compute_job_id(source, company, title)` -> `str` (SHA256 hash)
- `BaseScraper._clean_html(html)` -> `str` (BeautifulSoup text)
- `BaseScraper._html_to_markdown(html)` -> `str` (html2text)
- `BaseScraper._parse_location(location_str)` -> `dict` (city/state/country/remote_type)
- `BaseScraper._rate_limit()` -> `None` (asyncio.sleep)

## Dependencies
- httpx==0.27.0 (async HTTP for SerpApi, Greenhouse, Lever, Ashby, TheirStack, Apify)
- python-jobspy==1.1.82 (JobSpy multi-board scraping)
- beautifulsoup4==4.12.3 (HTML parsing/cleaning)
- html2text==2024.2.26 (HTML to markdown)

## Known Limitations
- SerpApi: 1s delay between pages, 20% hourly cap on free tier
- Greenhouse/Lever/Ashby: Require company slugs (no global search)
- JobSpy: Synchronous library, runs in thread executor
- Apify: 120-second max polling timeout for actor completion
- TheirStack: Free tier limited to 2 req/sec

## Adding a New Scraper
1. Create `backend/scrapers/newscraper.py`
2. Extend `BaseScraper`, set `source_name` and `rate_limit_delay`
3. Implement `async def fetch_jobs(self, query, location, limit) -> list[dict]`
4. Register in `SCRAPERS` dict in `backend/scheduler.py`
5. Add scheduler job in `create_scheduler()`
