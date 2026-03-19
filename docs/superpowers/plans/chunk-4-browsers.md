# Chunk 4: Heavy Browser Adapters + Browser Pool
> **Depends on:** Chunk 3 (Nodriver adapter skeleton, all dependencies installed)
> **Produces:** Camoufox adapter, SeleniumBase adapter, browser pool with tier-separated semaphores, Nodriver upgraded to reusable browser pattern, scrape_attempts indexes
> **Spec sections:** 4.4-4.6, 5.2-5.3

---

### Task 20: Build Camoufox Browser Adapter

**Files:**
- Create: `backend/app/scraping/execution/camoufox_browser.py`
- Test: `backend/tests/unit/scraping/test_camoufox_browser.py`

- [ ] **Step 1: Write test**

```python
# tests/unit/scraping/test_camoufox_browser.py
from app.scraping.execution.camoufox_browser import CamoufoxBrowser
from app.scraping.execution.browser_port import BrowserPort

def test_implements_browser_port():
    assert issubclass(CamoufoxBrowser, BrowserPort)

def test_browser_name():
    b = CamoufoxBrowser()
    assert b.browser_name == "camoufox"
```

- [ ] **Step 2: Create camoufox_browser.py**

Implement BrowserPort using Camoufox's async Playwright-compatible API with BrowserForge fingerprint generation. Include memory-aware session management.

```python
# app/scraping/execution/camoufox_browser.py
from __future__ import annotations
import hashlib
import time
from app.scraping.execution.browser_port import BrowserPort, BrowserResult

class CamoufoxBrowser(BrowserPort):
    @property
    def browser_name(self) -> str:
        return "camoufox"

    async def render(self, url: str, timeout_s: int = 60,
                     fingerprint: dict | None = None,
                     wait_for_selector: str | None = None) -> BrowserResult:
        from camoufox.async_api import AsyncCamoufox
        config = fingerprint or {}
        start = time.monotonic()
        async with AsyncCamoufox(config=config, headless=True) as browser:
            page = await browser.new_page()
            await page.goto(url, timeout=timeout_s * 1000)
            if wait_for_selector:
                await page.wait_for_selector(wait_for_selector, timeout=timeout_s * 1000)
            html = await page.content()
            url_final = page.url
        duration = int((time.monotonic() - start) * 1000)
        content_hash = hashlib.sha256(html.encode()).hexdigest()[:64]
        return BrowserResult(html=html, status_code=200, url_final=url_final,
                             duration_ms=duration, content_hash=content_hash)

    async def health_check(self) -> bool:
        try:
            from camoufox.async_api import AsyncCamoufox  # noqa: F401
            return True
        except ImportError:
            return False

    async def close(self) -> None:
        pass  # Camoufox uses context manager per-render, no persistent state
```

- [ ] **Step 3: Run tests, commit**

```bash
python -m pytest tests/unit/scraping/test_camoufox_browser.py -v
git add app/scraping/execution/camoufox_browser.py tests/unit/scraping/test_camoufox_browser.py
git commit -m "feat: add Camoufox browser adapter (Tier 3)"
```

---

### Task 21: Build SeleniumBase UC Mode Adapter

**Files:**
- Create: `backend/app/scraping/execution/seleniumbase_browser.py`
- Test: `backend/tests/unit/scraping/test_seleniumbase_browser.py`

- [ ] **Step 1: Write test**

```python
# tests/unit/scraping/test_seleniumbase_browser.py
from app.scraping.execution.seleniumbase_browser import SeleniumBaseBrowser
from app.scraping.execution.browser_port import BrowserPort

def test_implements_browser_port():
    assert issubclass(SeleniumBaseBrowser, BrowserPort)

def test_browser_name():
    b = SeleniumBaseBrowser()
    assert b.browser_name == "seleniumbase"
```

- [ ] **Step 2: Create seleniumbase_browser.py**

SeleniumBase is synchronous, so wrap in `asyncio.to_thread`. Use UC (Undetected Chromedriver) mode for anti-bot bypass.

```python
# app/scraping/execution/seleniumbase_browser.py
from __future__ import annotations
import hashlib
import time
from app.scraping.execution.browser_port import BrowserPort, BrowserResult

class SeleniumBaseBrowser(BrowserPort):
    @property
    def browser_name(self) -> str:
        return "seleniumbase"

    async def render(self, url: str, timeout_s: int = 60,
                     fingerprint: dict | None = None,
                     wait_for_selector: str | None = None) -> BrowserResult:
        import asyncio
        start = time.monotonic()

        def _sync_render():
            from seleniumbase import Driver
            driver = Driver(uc=True, headless=True)
            try:
                driver.get(url)
                if wait_for_selector:
                    driver.wait_for_element(wait_for_selector, timeout=timeout_s)
                return driver.page_source
            finally:
                driver.quit()

        html = await asyncio.to_thread(_sync_render)
        duration = int((time.monotonic() - start) * 1000)
        content_hash = hashlib.sha256(html.encode()).hexdigest()[:64]
        return BrowserResult(html=html, status_code=200, url_final=url,
                             duration_ms=duration, content_hash=content_hash)

    async def health_check(self) -> bool:
        try:
            import seleniumbase  # noqa: F401
            return True
        except ImportError:
            return False

    async def close(self) -> None:
        pass  # SeleniumBase creates/destroys driver per-render
```

- [ ] **Step 3: Run tests, commit**

```bash
python -m pytest tests/unit/scraping/test_seleniumbase_browser.py -v
git add app/scraping/execution/seleniumbase_browser.py tests/unit/scraping/test_seleniumbase_browser.py
git commit -m "feat: add SeleniumBase UC Mode adapter (Tier 3 backup)"
```

---

### Task 21b: Upgrade Nodriver to Reusable Browser Instance

**Files:**
- Modify: `backend/app/scraping/execution/nodriver_browser.py`

> **Why:** The Chunk 3 version of NodriverBrowser starts and stops a fresh Chromium process per `render()` call. This is wasteful — Nodriver supports reusing a browser instance across multiple page loads. This task upgrades to a **persistent browser** pattern with lazy init and a lock to prevent concurrent `_get_browser()` races.

- [ ] **Step 1: Update nodriver_browser.py with reusable pattern**

```python
# app/scraping/execution/nodriver_browser.py
from __future__ import annotations
import asyncio
import hashlib
import time
from app.scraping.execution.browser_port import BrowserPort, BrowserResult

try:
    import nodriver as uc
    NODRIVER_AVAILABLE = True
except ImportError:
    NODRIVER_AVAILABLE = False

class NodriverBrowser(BrowserPort):
    def __init__(self):
        self._browser = None
        self._lock = asyncio.Lock()

    async def _get_browser(self):
        """Lazy-init a reusable browser instance, protected by lock."""
        async with self._lock:
            if self._browser is None:
                self._browser = await uc.start()
            return self._browser

    @property
    def browser_name(self) -> str:
        return "nodriver"

    async def render(self, url: str, timeout_s: int = 60,
                     fingerprint: dict | None = None,
                     wait_for_selector: str | None = None) -> BrowserResult:
        if not NODRIVER_AVAILABLE:
            raise RuntimeError("nodriver not installed")

        start = time.monotonic()
        browser = await self._get_browser()
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
        # Do NOT stop browser — reuse across calls

    async def health_check(self) -> bool:
        return NODRIVER_AVAILABLE

    async def close(self) -> None:
        """Shut down the persistent browser instance."""
        if self._browser:
            self._browser.stop()
            self._browser = None
```

- [ ] **Step 2: Run existing Nodriver tests to verify no regression**

```bash
python -m pytest tests/unit/scraping/test_nodriver_browser.py -v
```

- [ ] **Step 3: Commit**

```bash
git add app/scraping/execution/nodriver_browser.py
git commit -m "feat: upgrade Nodriver to reusable browser instance pattern"
```

---

### Task 21c: Add scrape_attempts Indexes

**Files:**
- Modify: `backend/app/scraping/models.py`

> **Why:** The `scrape_attempts` table will be queried frequently by `run_id` (to list all attempts in a run) and by `target_id` + `created_at` desc (to show recent attempts for a target). Without indexes, these queries will full-scan.

- [ ] **Step 1: Add `__table_args__` to ScrapeAttempt model**

In `backend/app/scraping/models.py`, update the `ScrapeAttempt` class to include:

```python
class ScrapeAttempt(Base):
    __tablename__ = "scrape_attempts"
    __table_args__ = (
        Index("idx_attempts_run", "run_id"),
        Index("idx_attempts_target", "target_id", created_at.desc()),
    )
    # ... rest of columns unchanged
```

- [ ] **Step 2: Generate migration, apply**

```bash
cd D:/jobradar-v2/backend
alembic revision --autogenerate -m "add indexes to scrape_attempts"
alembic upgrade head
```

- [ ] **Step 3: Commit**

```bash
git add app/scraping/models.py app/migrations/versions/
git commit -m "feat: add performance indexes to scrape_attempts"
```

---

### Task 22: Build Browser Pool with Tier-Separated Concurrency Governance

**Files:**
- Create: `backend/app/scraping/execution/browser_pool.py`
- Test: `backend/tests/unit/scraping/test_browser_pool.py`

> **Design:** The browser pool does NOT own browser instances — adapters manage their own browser lifecycle. The pool controls **admission**: how many browser sessions can run concurrently, separated by tier. Key design decisions:
> - **Separate semaphores for Tier 2 and Tier 3** (not one combined pool) — Tier 3 browsers (Camoufox) are much heavier than Tier 2 (Nodriver)
> - **Domain semaphores created on-demand** with a lock (not `defaultdict`) to avoid race conditions
> - **`cleanup_idle_domains()`** prevents unbounded growth of domain semaphore dict

- [ ] **Step 1: Write tests**

```python
# tests/unit/scraping/test_browser_pool.py
import pytest
import asyncio
from app.scraping.execution.browser_pool import BrowserPool

@pytest.mark.asyncio
async def test_pool_respects_concurrency():
    pool = BrowserPool(max_tier2=2, max_tier3=1)
    acquired = 0
    async def acquire_and_hold():
        nonlocal acquired
        async with pool.acquire(tier=2):
            acquired += 1
            await asyncio.sleep(0.1)
    # Launch 3, only 2 should run concurrently (tier2 limit)
    tasks = [asyncio.create_task(acquire_and_hold()) for _ in range(3)]
    await asyncio.sleep(0.05)
    assert acquired <= 2
    await asyncio.gather(*tasks)
    assert acquired == 3

@pytest.mark.asyncio
async def test_pool_per_domain_limit():
    pool = BrowserPool(max_tier2=10, max_tier3=10, max_per_domain=2)
    count = 0
    async def fetch(domain):
        nonlocal count
        async with pool.acquire(tier=2, domain=domain):
            count += 1
            await asyncio.sleep(0.1)
    tasks = [asyncio.create_task(fetch("example.com")) for _ in range(5)]
    await asyncio.sleep(0.05)
    assert count <= 2  # per-domain limit
    await asyncio.gather(*tasks)

@pytest.mark.asyncio
async def test_tier3_separate_from_tier2():
    pool = BrowserPool(max_tier2=5, max_tier3=1)
    tier3_count = 0
    async def tier3_task():
        nonlocal tier3_count
        async with pool.acquire(tier=3):
            tier3_count += 1
            await asyncio.sleep(0.1)
    tasks = [asyncio.create_task(tier3_task()) for _ in range(3)]
    await asyncio.sleep(0.05)
    assert tier3_count <= 1  # tier3 has limit of 1
    await asyncio.gather(*tasks)

@pytest.mark.asyncio
async def test_cleanup_idle_domains():
    pool = BrowserPool(max_tier2=10, max_tier3=3)
    async with pool.acquire(tier=2, domain="active.com"):
        pass
    async with pool.acquire(tier=2, domain="stale.com"):
        pass
    # Both domains should have semaphores
    await pool.cleanup_idle_domains(active_domains={"active.com"})
    # stale.com should be cleaned up
    assert "stale.com" not in pool._domain_sems
    assert "active.com" in pool._domain_sems
```

- [ ] **Step 2: Create browser_pool.py**

```python
# app/scraping/execution/browser_pool.py
from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from app.scraping.constants import MAX_PER_DOMAIN_CONCURRENCY

class BrowserPool:
    """Manages browser session concurrency and per-domain limits.

    Does NOT own browser instances (adapters manage their own).
    Controls admission: how many browser sessions can run concurrently.
    """
    def __init__(self, max_tier2: int = 8, max_tier3: int = 3,
                 max_per_domain: int = MAX_PER_DOMAIN_CONCURRENCY):
        self._tier2_sem = asyncio.Semaphore(max_tier2)
        self._tier3_sem = asyncio.Semaphore(max_tier3)
        self._domain_sems: dict[str, asyncio.Semaphore] = {}
        self._domain_lock = asyncio.Lock()
        self._active = 0

    async def _get_domain_sem(self, domain: str) -> asyncio.Semaphore:
        async with self._domain_lock:
            if domain not in self._domain_sems:
                self._domain_sems[domain] = asyncio.Semaphore(MAX_PER_DOMAIN_CONCURRENCY)
            return self._domain_sems[domain]

    @asynccontextmanager
    async def acquire(self, tier: int, domain: str | None = None):
        """Acquire a browser session slot. Blocks until available."""
        sem = self._tier3_sem if tier >= 3 else self._tier2_sem
        domain_sem = await self._get_domain_sem(domain) if domain else None

        if domain_sem:
            await domain_sem.acquire()
        await sem.acquire()
        self._active += 1
        try:
            yield
        finally:
            self._active -= 1
            sem.release()
            if domain_sem:
                domain_sem.release()

    @property
    def active_sessions(self) -> int:
        return self._active

    async def cleanup_idle_domains(self, active_domains: set[str]):
        """Remove semaphores for domains no longer being scraped."""
        async with self._domain_lock:
            stale = set(self._domain_sems) - active_domains
            for d in stale:
                del self._domain_sems[d]
```

- [ ] **Step 3: Run tests, commit**

```bash
python -m pytest tests/unit/scraping/test_browser_pool.py -v
git add app/scraping/execution/browser_pool.py tests/unit/scraping/test_browser_pool.py
git commit -m "feat: add browser pool with tier-separated concurrency governance"
```

---

## Chunk Status
- [ ] All tasks completed
- [ ] All tests passing
- [ ] Camoufox adapter implements BrowserPort
- [ ] SeleniumBase adapter implements BrowserPort
- [ ] Nodriver upgraded to reusable browser pattern
- [ ] Browser pool uses separate Tier 2 / Tier 3 semaphores
- [ ] scrape_attempts indexes applied
- [ ] Domain semaphore cleanup working

### Notes / Issues Encountered
_Record any deviations from the plan, issues hit, or decisions made during implementation._

| Date | Note |
|------|------|
| | |
