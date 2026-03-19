# Chunk 3: New Scraper Adapters (Cloudscraper, Scrapling, Nodriver, Workday)
> **Depends on:** Chunk 2 (execution ports: FetcherPort, BrowserPort, ExtractorPort)
> **Produces:** All Tier 0-2 adapters installed and working: Cloudscraper fetcher, Scrapling dual-mode fetcher, Nodriver browser, Workday ATS scraper
> **Spec sections:** 4.1-4.5, 6.1-6.3

---

### Task 15: Install New Python Dependencies

- [ ] **Step 1: Install all new packages**

```bash
cd D:/jobradar-v2/backend
pip install cloudscraper nodriver camoufox seleniumbase crawl4ai browserforge fake-useragent protego "scrapling[all]"
```

- [ ] **Step 2: Verify imports work**

```bash
python -c "import cloudscraper; print('cloudscraper OK')"
python -c "import nodriver; print('nodriver OK')"
python -c "from camoufox.sync_api import Camoufox; print('camoufox OK')"
python -c "import seleniumbase; print('seleniumbase OK')"
python -c "import crawl4ai; print('crawl4ai OK')"
python -c "import browserforge; print('browserforge OK')"
python -c "from fake_useragent import UserAgent; print('fake-useragent OK')"
python -c "from protego import Protego; print('protego OK')"
```

- [ ] **Step 3: Add to pyproject.toml dependencies**

> **IMPORTANT:** Use the quoted-string-with-version format that matches the existing `pyproject.toml` style (array of strings in `[project.dependencies]`). Do NOT use the `package = ">=version"` TOML table syntax.

Add these lines to the `dependencies` array in `[project]`:

```toml
"cloudscraper>=1.2.0",
"nodriver>=0.38.0",
"camoufox>=0.4.0",
"seleniumbase>=4.30.0",
"crawl4ai>=0.4.0",
"browserforge>=1.1.0",
"fake-useragent>=1.5.0",
"protego>=0.3.0",
"scrapling[all]>=0.4.0",
"typer>=0.12.0",
"rich>=13.7.0",
"openpyxl>=3.1.0",
```

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add scraper ecosystem dependencies"
```

---

### Task 16: Build Cloudscraper Fetcher Adapter

**Files:**
- Create: `backend/app/scraping/execution/cloudscraper_fetcher.py`
- Test: `backend/tests/unit/scraping/test_cloudscraper_fetcher.py`

> **IMPORTANT — Thread Safety:** Cloudscraper uses `requests.Session` internally, which is NOT thread-safe. Create a **new scraper session per call** instead of sharing one across async tasks. This prevents cookie/header cross-contamination between concurrent fetches.

> **Note:** Conditional requests (ETag/If-Modified-Since) are deferred to Phase 3. Adapters compute `content_hash` for change detection but do not send conditional headers yet.

- [ ] **Step 1: Write test**

```python
# tests/unit/scraping/test_cloudscraper_fetcher.py
from app.scraping.execution.cloudscraper_fetcher import CloudscraperFetcher
from app.scraping.execution.fetcher_port import FetcherPort

def test_implements_fetcher_port():
    assert issubclass(CloudscraperFetcher, FetcherPort)

def test_fetcher_name():
    f = CloudscraperFetcher()
    assert f.fetcher_name == "cloudscraper"
```

- [ ] **Step 2: Create cloudscraper_fetcher.py**

```python
# app/scraping/execution/cloudscraper_fetcher.py
from __future__ import annotations
import hashlib
import time
import cloudscraper as cs
from app.scraping.execution.fetcher_port import FetcherPort, FetchResult

class CloudscraperFetcher(FetcherPort):
    @property
    def fetcher_name(self) -> str:
        return "cloudscraper"

    async def fetch(self, url: str, timeout_s: int = 30,
                    user_agent: str | None = None) -> FetchResult:
        import asyncio
        # Create a NEW session per call for thread safety.
        # cloudscraper uses requests.Session internally which is NOT safe
        # to share across concurrent asyncio.to_thread calls.
        scraper = cs.create_scraper(browser={"browser": "chrome", "platform": "windows"})
        if user_agent:
            scraper.headers["User-Agent"] = user_agent
        start = time.monotonic()
        try:
            resp = await asyncio.to_thread(scraper.get, url, timeout=timeout_s)
            duration = int((time.monotonic() - start) * 1000)
            content_hash = hashlib.sha256(resp.text.encode()).hexdigest()[:64]
            return FetchResult(
                html=resp.text, status_code=resp.status_code,
                headers=dict(resp.headers), url_final=str(resp.url),
                duration_ms=duration, content_hash=content_hash,
            )
        finally:
            scraper.close()

    async def health_check(self) -> bool:
        return True

    async def close(self) -> None:
        pass  # no persistent state to clean up (session-per-call)
```

- [ ] **Step 3: Run tests, commit**

```bash
python -m pytest tests/unit/scraping/test_cloudscraper_fetcher.py -v
git add app/scraping/execution/cloudscraper_fetcher.py tests/unit/scraping/test_cloudscraper_fetcher.py
git commit -m "feat: add Cloudscraper fetcher adapter (session-per-call for thread safety)"
```

---

### Task 17: Port Scrapling Fetcher from V1

**Files:**
- Create: `backend/app/scraping/execution/scrapling_fetcher.py`
- Test: `backend/tests/unit/scraping/test_scrapling_fetcher.py`

> **Adapter Registry Note:** Scrapling implements BOTH `FetcherPort` and `BrowserPort` in a single class. When the AdapterRegistry (built in Chunk 5, Task 24b) registers adapters, the same `ScraplingFetcher` instance is registered under two names:
> - `"scrapling_fast"` -> registered as a fetcher (calls `fetch()`) — Tier 1
> - `"scrapling_stealth"` -> registered as a browser (calls `render()`) — Tier 2
>
> The TierRouter's `scraper_name` field in `Step` determines which registration is used. When the execution loop calls `registry.resolve("scrapling_fast")`, it gets `(scrapling_instance, scrapling_instance.fetch)`. When it calls `registry.resolve("scrapling_stealth")`, it gets `(scrapling_instance, scrapling_instance.render)`.

- [ ] **Step 1: Write test**

```python
# tests/unit/scraping/test_scrapling_fetcher.py
from app.scraping.execution.scrapling_fetcher import ScraplingFetcher
from app.scraping.execution.fetcher_port import FetcherPort
from app.scraping.execution.browser_port import BrowserPort

def test_implements_both_ports():
    """Scrapling has dual mode: fast (FetcherPort) + stealth (BrowserPort)."""
    f = ScraplingFetcher()
    assert isinstance(f, FetcherPort)
    assert isinstance(f, BrowserPort)

def test_fetcher_name():
    f = ScraplingFetcher()
    assert f.fetcher_name == "scrapling_fast"
    assert f.browser_name == "scrapling_stealth"
```

- [ ] **Step 2: Create scrapling_fetcher.py**

Port from v1's `ScraplingScraper` (D:/jobradar-v1/merged_project/backend/scrapers/scrapling_scraper.py), adapting to the new `FetcherPort` and `BrowserPort` interfaces. The dual-mode pattern:
- `fetch()` uses `Fetcher.get(url, impersonate="chrome")` — Tier 1
- `render()` uses `StealthyFetcher.fetch(url, headless=True)` — Tier 2

Include graceful degradation: if `scrapling` package is not installed, `health_check()` returns False.

- [ ] **Step 3: Run tests, commit**

```bash
python -m pytest tests/unit/scraping/test_scrapling_fetcher.py -v
git add app/scraping/execution/scrapling_fetcher.py tests/unit/scraping/test_scrapling_fetcher.py
git commit -m "feat: port Scrapling dual-mode fetcher from v1"
```

---

### Task 18: Build Nodriver Browser Adapter

**Files:**
- Create: `backend/app/scraping/execution/nodriver_browser.py`
- Test: `backend/tests/unit/scraping/test_nodriver_browser.py`

- [ ] **Step 1: Write test**

```python
# tests/unit/scraping/test_nodriver_browser.py
from app.scraping.execution.nodriver_browser import NodriverBrowser
from app.scraping.execution.browser_port import BrowserPort

def test_implements_browser_port():
    assert issubclass(NodriverBrowser, BrowserPort)

def test_browser_name():
    b = NodriverBrowser()
    assert b.browser_name == "nodriver"
```

- [ ] **Step 2: Create nodriver_browser.py**

> **Note:** This is the initial skeleton. The reusable browser instance pattern (maintaining a persistent browser across calls instead of start/stop per render) is applied in Chunk 4 alongside the browser pool integration.

```python
# app/scraping/execution/nodriver_browser.py
from __future__ import annotations
import hashlib
import time
from app.scraping.execution.browser_port import BrowserPort, BrowserResult

try:
    import nodriver as uc
    NODRIVER_AVAILABLE = True
except ImportError:
    NODRIVER_AVAILABLE = False

class NodriverBrowser(BrowserPort):
    @property
    def browser_name(self) -> str:
        return "nodriver"

    async def render(self, url: str, timeout_s: int = 60,
                     fingerprint: dict | None = None,
                     wait_for_selector: str | None = None) -> BrowserResult:
        if not NODRIVER_AVAILABLE:
            raise RuntimeError("nodriver not installed")

        start = time.monotonic()
        browser = await uc.start()
        try:
            page = await browser.get(url)
            if wait_for_selector:
                await page.find(wait_for_selector, timeout=timeout_s)
            else:
                await page.sleep(2)  # wait for JS rendering
            html = await page.get_content()
            duration = int((time.monotonic() - start) * 1000)
            content_hash = hashlib.sha256(html.encode()).hexdigest()[:64]
            return BrowserResult(
                html=html, status_code=200, url_final=str(page.url),
                duration_ms=duration, content_hash=content_hash,
            )
        finally:
            browser.stop()

    async def health_check(self) -> bool:
        return NODRIVER_AVAILABLE

    async def close(self) -> None:
        pass
```

- [ ] **Step 3: Run tests, commit**

```bash
python -m pytest tests/unit/scraping/test_nodriver_browser.py -v
git add app/scraping/execution/nodriver_browser.py tests/unit/scraping/test_nodriver_browser.py
git commit -m "feat: add Nodriver browser adapter"
```

---

### Task 19: Build Workday Scraper

**Files:**
- Create: `backend/app/scraping/scrapers/workday.py`
- Test: `backend/tests/unit/scraping/test_workday_scraper.py`

- [ ] **Step 1: Write test with fixture**

```python
# tests/unit/scraping/test_workday_scraper.py
import pytest
from app.scraping.scrapers.workday import WorkdayScraper

MOCK_RESPONSE = {
    "total": 2,
    "jobPostings": [
        {"title": "ML Engineer", "locationsText": "Seattle, WA",
         "postedOn": "2026-03-15", "bulletFields": ["Full-time"],
         "externalPath": "/job/ML-Engineer/12345"},
        {"title": "Data Scientist", "locationsText": "Remote",
         "postedOn": "2026-03-14", "bulletFields": ["Full-time"],
         "externalPath": "/job/Data-Scientist/12346"},
    ]
}

def test_parse_workday_response():
    scraper = WorkdayScraper()
    jobs = scraper._parse_response(MOCK_RESPONSE, "https://microsoft.wd5.myworkdayjobs.com")
    assert len(jobs) == 2
    assert jobs[0].title == "ML Engineer"
    assert jobs[0].location == "Seattle, WA"
    assert jobs[0].source == "workday"

def test_extract_tenant_from_url():
    scraper = WorkdayScraper()
    assert scraper._extract_tenant("https://microsoft.wd5.myworkdayjobs.com/en-US/Global") == ("microsoft", "wd5", "Global")
```

- [ ] **Step 2: Create workday.py**

Build a Workday ATS scraper that:
- Extracts tenant, subdomain, and career section from URL
- POSTs to `/wday/cxs/{tenant}/{section}/jobs` with pagination
- Parses the JSON response into `ScrapedJob` objects
- Implements `ScraperPort` interface

- [ ] **Step 3: Run tests, commit**

```bash
python -m pytest tests/unit/scraping/test_workday_scraper.py -v
git add app/scraping/scrapers/workday.py tests/unit/scraping/test_workday_scraper.py
git commit -m "feat: add Workday ATS scraper"
```

---

## Chunk Status
- [ ] All tasks completed
- [ ] All tests passing
- [ ] All dependencies installed and importable
- [ ] pyproject.toml updated with correct syntax
- [ ] Cloudscraper adapter thread-safe (session-per-call)
- [ ] Scrapling dual-mode fetcher working
- [ ] Nodriver browser adapter working
- [ ] Workday ATS scraper parsing correctly

### Notes / Issues Encountered
_Record any deviations from the plan, issues hit, or decisions made during implementation._

| Date | Note |
|------|------|
| | |
