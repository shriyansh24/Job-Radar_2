# Scraper Audit - JobRadar V2

## SC-01 - CRITICAL: Pagination Metadata Not Persisted on `ScrapeAttempt`
- **Files:** `backend/app/scraping/models.py`, `backend/app/scraping/schemas.py`, `backend/app/migrations/versions/20260321_db_audit_fixes.py`
- **Detail:** Fixed. `pages_crawled` and `pagination_stopped_reason` are now mapped on the model, included in the response schema, and added to the database schema.
- **Evidence:** `backend/tests/unit/scraping/test_attempt_model.py`
- **Status:** FIXED

## SC-02 - CRITICAL: Workday URL Case Sensitivity
- **File:** `backend/app/scraping/scrapers/workday.py`
- **Detail:** Fixed. The Workday URL regex now uses `re.IGNORECASE`, so uppercase hostnames parse correctly.
- **Evidence:** `backend/tests/unit/scraping/test_workday_scraper.py`
- **Status:** FIXED

## SC-03 - CRITICAL: Circuit Breaker Stuck in Half-Open
- **File:** `backend/app/scraping/rate_limiter.py`
- **Detail:** Stale as written. The current breaker preserves failure counts and re-opens correctly when a half-open probe fails.
- **Status:** STALE

## SC-04 - HIGH: No JSON Validation in ATS Scrapers
- **Files:** `backend/app/scraping/scrapers/ashby.py`, `backend/app/scraping/scrapers/greenhouse.py`, `backend/app/scraping/scrapers/lever.py`, `backend/app/scraping/scrapers/workday.py`
- **Detail:** Fixed. The ATS scrapers now validate root payload shapes and gracefully return an empty result for malformed upstream responses.
- **Evidence:** `backend/tests/unit/scraping/test_ats_validation.py`
- **Status:** FIXED

## SC-05 - HIGH: EventBus Single Subscriber Blocks All
- **File:** `backend/app/shared/events.py`
- **Detail:** Stale as written. Subscriber queues are unbounded `asyncio.Queue()` instances, so the audited "full queue blocks all" mode does not match the live implementation.
- **Status:** STALE

## SC-06 - HIGH: Missing Workday Rate Policy
- **File:** `backend/app/scraping/rate_limiter.py`
- **Detail:** Fixed. `DEFAULT_POLICIES` now includes a dedicated Workday policy.
- **Evidence:** `backend/tests/unit/test_rate_limiter.py`
- **Status:** FIXED

## SC-07 - HIGH: Simhash False Positives
- **File:** `backend/app/scraping/deduplication.py`
- **Detail:** Stale as written. The threshold remains `< 3`, but the audited false-positive example does not reproduce against the current implementation.
- **Status:** STALE

## SC-08 - MEDIUM: Browser Pool Domain Semaphore Growth
- **File:** `backend/app/scraping/execution/browser_pool.py`
- **Detail:** Fixed. Domain semaphores now track live references and are automatically removed after the last acquisition releases them.
- **Evidence:** `backend/tests/unit/scraping/test_browser_pool.py`
- **Status:** FIXED

## SC-09 - MEDIUM: PageCrawler Loop Detection
- **File:** `backend/app/scraping/execution/page_crawler.py`
- **Detail:** Fixed. URL loop detection now normalizes fragments, trailing slashes, and query parameter order before revisit checks.
- **Evidence:** `backend/tests/unit/scraping/test_page_crawler.py`
- **Status:** FIXED

## SC-10 - MEDIUM: Ashby GraphQL Errors Silent
- **File:** `backend/app/scraping/scrapers/ashby.py`
- **Detail:** Fixed. Ashby GraphQL `errors` payloads are now detected and treated as failures instead of being interpreted as a valid empty board.
- **Evidence:** `backend/tests/unit/scraping/test_ats_validation.py`
- **Status:** FIXED

## SC-11 - MEDIUM: No Pagination Timeout
- **File:** `backend/app/scraping/service.py`
- **Detail:** Fixed. Pagination is now bounded by a service timeout so a stalled crawler cannot hang the target run forever.
- **Evidence:** `backend/tests/unit/scraping/test_run_target_batch.py`
- **Status:** FIXED

## SC-12 - MEDIUM: Scheduler No Interval Validation
- **File:** `backend/app/scraping/control/scheduler.py`
- **Detail:** Fixed. `compute_next_run()` now clamps `schedule_interval_m` to a positive minimum instead of trusting zero or negative intervals.
- **Evidence:** `backend/tests/unit/scraping/test_scheduler.py`
- **Status:** FIXED

## SC-13 - LOW: Dead Code - ScrapingBee
- **Files:** `backend/app/scraping/scrapers/scrapingbee.py`, `backend/app/config.py`
- **Detail:** Fixed. The dead scraper was removed and the unused ScrapingBee config surface was dropped with it.
- **Status:** FIXED

## SC-14 - LOW: Dead Code - Apify
- **File:** `backend/app/scraping/scrapers/apify.py`
- **Detail:** Stale. `ApifyScraper` is still registered in the live scraping service and remains a real runtime integration.
- **Status:** STALE
