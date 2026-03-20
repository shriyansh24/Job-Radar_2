# Chunk 1: Foundation (Database + Registry + Classification)
> **Depends on:** Nothing (first chunk)
> **Produces:** scrape_targets table, scrape_attempts table, job lifecycle columns, ATS registry, classifier, CLI import tool, 1,473 URLs imported
> **Spec sections:** 2.1-2.6, 3.2-3.3, 7.1-7.2, 8.1-8.3

---

### Task 1: Verify Existing Alembic Setup

**Files:**
- Modify: `backend/app/migrations/env.py` (add new model imports as models are created)

> **Note:** Alembic is already initialized at `backend/app/migrations/` with async support. The existing `alembic.ini` points to `script_location = app/migrations`. Do NOT run `alembic init` — it would create a competing directory.

- [ ] **Step 1: Verify alembic works**

```bash
cd D:/jobradar-v2/backend
alembic current
alembic history
```
Expected: shows existing migration history

- [ ] **Step 2: Verify env.py imports**

Read `backend/app/migrations/env.py` line ~23. Confirm it imports `from app.scraping.models import CareerPage, ScraperRun`. These imports will be extended in Task 2 when new models are added.

---

### Task 2: Create scrape_targets Table

**Files:**
- Modify: `backend/app/scraping/models.py`
- Modify: `backend/app/migrations/env.py` (add ScrapeTarget import)
- Create: `backend/tests/unit/scraping/__init__.py`
- Test: `backend/tests/unit/scraping/test_target_model.py`

- [ ] **Step 1: Write test for ScrapeTarget model**

```python
# tests/unit/scraping/test_target_model.py
import pytest
from app.scraping.models import ScrapeTarget

def test_scrape_target_has_required_columns():
    """ScrapeTarget should have all columns defined in spec."""
    columns = {c.name for c in ScrapeTarget.__table__.columns}
    required = {"id", "user_id", "url", "company_name", "ats_vendor",
                "ats_board_token", "start_tier", "max_tier", "priority_class",
                "schedule_interval_m", "enabled", "quarantined", "content_hash",
                "consecutive_failures", "next_scheduled_at", "lca_filings"}
    assert required.issubset(columns)

def test_scrape_target_column_defaults():
    """Check default values are set via mapped_column(default=...)."""
    col = ScrapeTarget.__table__.columns
    assert col["start_tier"].default.arg == 1
    assert col["max_tier"].default.arg == 3
    assert col["priority_class"].default.arg == "cool"
    assert col["schedule_interval_m"].default.arg == 720
    assert col["enabled"].default.arg is True
    assert col["quarantined"].default.arg is False

def test_scrape_target_with_ats():
    target = ScrapeTarget(
        url="https://boards.greenhouse.io/huggingface",
        company_name="Hugging Face",
        ats_vendor="greenhouse",
        ats_board_token="huggingface",
        start_tier=0,
        priority_class="watchlist",
        schedule_interval_m=120,
    )
    assert target.ats_vendor == "greenhouse"
    assert target.ats_board_token == "huggingface"
    assert target.start_tier == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd D:/jobradar-v2/backend
python -m pytest tests/unit/scraping/test_target_model.py -v
```
Expected: FAIL — `ScrapeTarget` not defined in models.py

- [ ] **Step 3: Add ScrapeTarget model to models.py**

Add to `backend/app/scraping/models.py`. First, update the import line to add `DateTime, SmallInteger, Index, text`:

```python
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, SmallInteger, String, Text, func, text
```

Then add the model:

```python
class ScrapeTarget(Base):
    __tablename__ = "scrape_targets"
    __table_args__ = (
        Index("idx_targets_schedule", "priority_class", "next_scheduled_at",
              postgresql_where=text("enabled = TRUE AND quarantined = FALSE")),
        Index("idx_targets_ats", "ats_vendor"),
        Index("idx_targets_active", "enabled", "quarantined"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    url: Mapped[str] = mapped_column(Text, nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(300))
    company_domain: Mapped[str | None] = mapped_column(String(255))
    source_kind: Mapped[str] = mapped_column(String(50), default="career_page")
    ats_vendor: Mapped[str | None] = mapped_column(String(50))
    ats_board_token: Mapped[str | None] = mapped_column(String(255))
    start_tier: Mapped[int] = mapped_column(SmallInteger, default=1)
    max_tier: Mapped[int] = mapped_column(SmallInteger, default=3)
    priority_class: Mapped[str] = mapped_column(String(10), default="cool")
    schedule_interval_m: Mapped[int] = mapped_column(Integer, default=720)
    enabled: Mapped[bool] = mapped_column(default=True)
    quarantined: Mapped[bool] = mapped_column(default=False)
    quarantine_reason: Mapped[str | None] = mapped_column(Text)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_tier: Mapped[int | None] = mapped_column(SmallInteger)
    last_http_status: Mapped[int | None] = mapped_column(SmallInteger)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    etag: Mapped[str | None] = mapped_column(String(255))
    last_modified: Mapped[str | None] = mapped_column(String(255))
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    next_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lca_filings: Mapped[int | None] = mapped_column(Integer)
    industry: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/unit/scraping/test_target_model.py -v
```
Expected: PASS

- [ ] **Step 5: Generate and run migration**

```bash
cd D:/jobradar-v2/backend
alembic revision --autogenerate -m "create scrape_targets table"
alembic upgrade head
```

- [ ] **Step 6: Commit**

```bash
git add app/scraping/models.py app/migrations/versions/ tests/unit/scraping/
git commit -m "feat: add scrape_targets table and model"
```

---

### Task 3: Create scrape_attempts Table

**Files:**
- Modify: `backend/app/scraping/models.py`
- Test: `backend/tests/unit/scraping/test_attempt_model.py`

- [ ] **Step 1: Write test for ScrapeAttempt model**

```python
# tests/unit/scraping/test_attempt_model.py
import uuid
from app.scraping.models import ScrapeAttempt

def test_scrape_attempt_defaults():
    attempt = ScrapeAttempt(
        target_id=uuid.uuid4(),
        selected_tier=1,
        actual_tier_used=2,
        scraper_name="nodriver",
    )
    assert attempt.status == "pending"
    assert attempt.retries == 0
    assert attempt.escalations == 0
    assert attempt.jobs_extracted == 0
    assert attempt.browser_used is False

def test_scrape_attempt_status_values():
    """Valid status values per spec."""
    valid = {"pending", "success", "partial", "failed", "skipped", "escalated", "not_modified"}
    attempt = ScrapeAttempt(
        target_id=uuid.uuid4(), selected_tier=1, actual_tier_used=1, scraper_name="test"
    )
    for status in valid:
        attempt.status = status  # should not raise
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/scraping/test_attempt_model.py -v
```
Expected: FAIL — `ScrapeAttempt` not defined

- [ ] **Step 3: Add ScrapeAttempt model**

Add to `backend/app/scraping/models.py`:

```python
class ScrapeAttempt(Base):
    __tablename__ = "scrape_attempts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("scraper_runs.id"))
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scrape_targets.id"))
    selected_tier: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    actual_tier_used: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    scraper_name: Mapped[str] = mapped_column(String(50), nullable=False)
    parser_name: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    http_status: Mapped[int | None] = mapped_column(SmallInteger)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    retries: Mapped[int] = mapped_column(SmallInteger, default=0)
    escalations: Mapped[int] = mapped_column(SmallInteger, default=0)
    jobs_extracted: Mapped[int] = mapped_column(Integer, default=0)
    content_hash_before: Mapped[str | None] = mapped_column(String(64))
    content_hash_after: Mapped[str | None] = mapped_column(String(64))
    content_changed: Mapped[bool | None] = mapped_column()
    error_class: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    browser_used: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 4: Run test, generate migration, apply**

```bash
python -m pytest tests/unit/scraping/test_attempt_model.py -v
alembic revision --autogenerate -m "create scrape_attempts table"
alembic upgrade head
```
Expected: tests PASS, migration applied

- [ ] **Step 5: Commit**

```bash
git add app/scraping/models.py app/migrations/versions/ tests/unit/scraping/
git commit -m "feat: add scrape_attempts table and model"
```

---

### Task 4: Add Job Lifecycle Columns

**Files:**
- Modify: `backend/app/jobs/models.py`
- Test: `backend/tests/unit/test_job_lifecycle.py`

- [ ] **Step 1: Write test**

```python
# tests/unit/test_job_lifecycle.py
from app.jobs.models import Job

def test_job_has_lifecycle_columns():
    """Job model should have lifecycle tracking columns."""
    job = Job(id="test123", title="ML Engineer", source="test")
    assert hasattr(job, "first_seen_at")
    assert hasattr(job, "last_seen_at")
    assert hasattr(job, "disappeared_at")
    assert hasattr(job, "content_hash")
    assert hasattr(job, "previous_hash")
    assert hasattr(job, "seen_count")
    assert hasattr(job, "source_target_id")
    assert job.seen_count == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/unit/test_job_lifecycle.py -v
```

- [ ] **Step 3: Add columns to Job model**

Add to `backend/app/jobs/models.py` in the Job class:

```python
    # Lifecycle tracking
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    disappeared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    content_hash: Mapped[str | None] = mapped_column(String(64))
    previous_hash: Mapped[str | None] = mapped_column(String(64))
    seen_count: Mapped[int] = mapped_column(Integer, default=1)
    source_target_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("scrape_targets.id"))
```

- [ ] **Step 4: Run test, generate migration, apply**

```bash
python -m pytest tests/unit/test_job_lifecycle.py -v
alembic revision --autogenerate -m "add job lifecycle columns"
alembic upgrade head
```

- [ ] **Step 5: Commit**

```bash
git add app/jobs/models.py app/migrations/versions/ tests/unit/test_job_lifecycle.py
git commit -m "feat: add job lifecycle tracking columns"
```

---

### Task 5: Add scraper_runs Tier Counters

**Files:**
- Modify: `backend/app/scraping/models.py`
- Test: `backend/tests/unit/scraping/test_scraper_run_model.py`

- [ ] **Step 1: Write test for new columns**

```python
# tests/unit/scraping/test_scraper_run_model.py
from app.scraping.models import ScraperRun

def test_scraper_run_has_tier_counters():
    run = ScraperRun(source="test")
    assert hasattr(run, "targets_attempted")
    assert hasattr(run, "tier_0_count")
    assert hasattr(run, "tier_api_count")
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Add columns to ScraperRun model**

```python
    # Tier execution counters
    targets_attempted: Mapped[int] = mapped_column(Integer, default=0)
    targets_succeeded: Mapped[int] = mapped_column(Integer, default=0)
    targets_failed: Mapped[int] = mapped_column(Integer, default=0)
    tier_0_count: Mapped[int] = mapped_column(Integer, default=0)
    tier_1_count: Mapped[int] = mapped_column(Integer, default=0)
    tier_2_count: Mapped[int] = mapped_column(Integer, default=0)
    tier_3_count: Mapped[int] = mapped_column(Integer, default=0)
    tier_api_count: Mapped[int] = mapped_column(Integer, default=0)
```

- [ ] **Step 2: Generate migration, apply**

```bash
alembic revision --autogenerate -m "add tier counters to scraper_runs"
alembic upgrade head
```

- [ ] **Step 3: Commit**

```bash
git add app/scraping/models.py app/migrations/versions/
git commit -m "feat: add tier counters to scraper_runs"
```

---

### Task 5b: Migrate career_pages Data and Drop Table

**Files:**
- Modify: `backend/app/migrations/env.py` (remove CareerPage import after drop)

- [ ] **Step 1: Create data migration**

```bash
cd D:/jobradar-v2/backend
alembic revision -m "migrate career_pages to scrape_targets and drop"
```

In the generated migration, write:
- `upgrade()`: INSERT INTO scrape_targets (user_id, url, company_name, enabled, ...) SELECT user_id, url, company_name, enabled, ... FROM career_pages. Then DROP TABLE career_pages.
- `downgrade()`: Recreate career_pages and copy data back.

- [ ] **Step 2: Apply migration**

```bash
alembic upgrade head
```

- [ ] **Step 3: Remove CareerPage model from models.py**

Remove the `CareerPage` class from `app/scraping/models.py` and update the import in `app/migrations/env.py` to remove `CareerPage`.

- [ ] **Step 4: Update router.py references**

The existing career page endpoints in `app/scraping/router.py` reference `CareerPage`. Update them to use `ScrapeTarget` with `source_kind='career_page'` filter.

- [ ] **Step 5: Commit**

```bash
git add app/scraping/models.py app/scraping/router.py app/migrations/
git commit -m "feat: migrate career_pages to scrape_targets, drop old table"
```

---

### Task 6: Create Constants Module

**Files:**
- Create: `backend/app/scraping/constants.py`
- Test: `backend/tests/unit/scraping/test_constants.py`

- [ ] **Step 1: Write test**

```python
# tests/unit/scraping/test_constants.py
from app.scraping.constants import PRIORITY_INTERVALS, TIER_CONCURRENCY

def test_priority_intervals_complete():
    assert set(PRIORITY_INTERVALS.keys()) == {"watchlist", "hot", "warm", "cool"}
    assert PRIORITY_INTERVALS["watchlist"] == 120
    assert PRIORITY_INTERVALS["hot"] == 240
    assert PRIORITY_INTERVALS["warm"] == 360
    assert PRIORITY_INTERVALS["cool"] == 720

def test_tier_concurrency_defined():
    assert TIER_CONCURRENCY[0] == 50
    assert TIER_CONCURRENCY[1] == 30
    assert TIER_CONCURRENCY[2] == 8
    assert TIER_CONCURRENCY[3] == 3
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Create constants.py**

```python
# app/scraping/constants.py
"""Single source of truth for scraper platform configuration."""

PRIORITY_INTERVALS: dict[str, int] = {
    "watchlist": 120,  # 2 hours
    "hot": 240,        # 4 hours
    "warm": 360,       # 6 hours
    "cool": 720,       # 12 hours
}

TIER_CONCURRENCY: dict[int, int] = {
    0: 50,   # API calls
    1: 30,   # HTTP fetch
    2: 8,    # Nodriver browser
    3: 3,    # Camoufox browser
}

MAX_GLOBAL_CONCURRENCY = 100
MAX_PER_DOMAIN_CONCURRENCY = 2
BROWSER_MEMORY_BUDGET_MB = 8192  # 8GB

QUARANTINE_THRESHOLD = 10  # consecutive failures
TIER_BUMP_THRESHOLD = 5    # consecutive failures at current tier

VALID_PRIORITY_CLASSES = frozenset({"watchlist", "hot", "warm", "cool"})
VALID_ATTEMPT_STATUSES = frozenset({
    "pending", "success", "partial", "failed", "skipped", "escalated", "not_modified"
})
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add app/scraping/constants.py tests/unit/scraping/test_constants.py
git commit -m "feat: add scraper platform constants"
```

---

### Task 7: Build ATS Registry

**Files:**
- Create: `backend/app/scraping/control/__init__.py`
- Create: `backend/app/scraping/control/ats_registry.py`
- Test: `backend/tests/unit/scraping/test_ats_registry.py`

- [ ] **Step 1: Write tests**

```python
# tests/unit/scraping/test_ats_registry.py
import pytest
from app.scraping.control.ats_registry import classify_url, ATS_RULES

def test_greenhouse_url():
    result = classify_url("https://boards.greenhouse.io/huggingface")
    assert result.vendor == "greenhouse"
    assert result.board_token == "huggingface"
    assert result.start_tier == 0

def test_lever_url():
    result = classify_url("https://jobs.lever.co/stripe")
    assert result.vendor == "lever"
    assert result.board_token == "stripe"
    assert result.start_tier == 0

def test_ashby_url():
    result = classify_url("https://jobs.ashbyhq.com/ramp")
    assert result.vendor == "ashby"
    assert result.board_token == "ramp"
    assert result.start_tier == 0

def test_workday_url():
    result = classify_url("https://microsoft.wd5.myworkdayjobs.com/en-US/Global/")
    assert result.vendor == "workday"
    assert result.start_tier == 0

def test_unknown_url():
    result = classify_url("https://careers.google.com/jobs")
    assert result.vendor is None
    assert result.start_tier == 1

def test_icims_url():
    result = classify_url("https://careers-acme.icims.com/jobs")
    assert result.vendor == "icims"
    assert result.start_tier == 1

def test_registry_is_extensible():
    """Adding a new rule should not require code changes to classify_url.

    Note: spec uses 'board_token_extractor' key name. Plan uses 'token_pattern'
    (regex) instead — more self-contained, no separate extractor functions needed.
    """
    assert isinstance(ATS_RULES, list)
    required_keys = {"vendor", "url_patterns", "start_tier"}
    assert all(required_keys.issubset(rule.keys()) for rule in ATS_RULES)
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Create ats_registry.py**

```python
# app/scraping/control/ats_registry.py
"""Data-driven ATS classification registry.

Adding a new ATS vendor = adding one dict to ATS_RULES. Zero code changes.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class ATSClassification:
    vendor: str | None
    board_token: str | None
    start_tier: int


ATS_RULES: list[dict] = [
    {
        "vendor": "greenhouse",
        "url_patterns": ["boards.greenhouse.io/", ".greenhouse.io/"],
        "header_signatures": ["X-Greenhouse"],
        "html_signatures": ['content="Greenhouse"'],
        "start_tier": 0,
        "token_pattern": r"greenhouse\.io/([^/?#]+)",
    },
    {
        "vendor": "lever",
        "url_patterns": ["jobs.lever.co/"],
        "header_signatures": ["X-Powered-By: Lever"],
        "html_signatures": ["lever-jobs-container"],
        "start_tier": 0,
        "token_pattern": r"lever\.co/([^/?#]+)",
    },
    {
        "vendor": "ashby",
        "url_patterns": ["jobs.ashbyhq.com/"],
        "header_signatures": [],
        "html_signatures": ["ashby-job-posting"],
        "start_tier": 0,
        "token_pattern": r"ashbyhq\.com/([^/?#]+)",
    },
    {
        "vendor": "workday",
        "url_patterns": [".myworkdayjobs.com"],
        "header_signatures": [],
        "html_signatures": ["wday/cxs"],
        "start_tier": 0,
        "token_pattern": r"([\w-]+)\.(?:wd\d\.)?myworkdayjobs\.com",
    },
    {
        "vendor": "icims",
        "url_patterns": [".icims.com"],
        "header_signatures": [],
        "html_signatures": [],
        "start_tier": 1,
        "token_pattern": None,
    },
    {
        "vendor": "smartrecruiters",
        "url_patterns": [".smartrecruiters.com"],
        "header_signatures": [],
        "html_signatures": [],
        "start_tier": 1,
        "token_pattern": None,
    },
    {
        "vendor": "jobvite",
        "url_patterns": [".jobvite.com"],
        "header_signatures": [],
        "html_signatures": [],
        "start_tier": 1,
        "token_pattern": None,
    },
    {
        "vendor": "breezy",
        "url_patterns": [".breezy.hr"],
        "header_signatures": [],
        "html_signatures": [],
        "start_tier": 1,
        "token_pattern": None,
    },
]


def classify_url(url: str) -> ATSClassification:
    """Classify a URL by walking the ATS registry. No vendor-specific logic."""
    url_lower = url.lower()
    for rule in ATS_RULES:
        for pattern in rule["url_patterns"]:
            if pattern.lower() in url_lower:
                token = _extract_token(url, rule.get("token_pattern"))
                return ATSClassification(
                    vendor=rule["vendor"],
                    board_token=token,
                    start_tier=rule["start_tier"],
                )
    return ATSClassification(vendor=None, board_token=None, start_tier=1)


def classify_headers(headers: dict[str, str]) -> ATSClassification | None:
    """Classify from HTTP response headers."""
    header_str = str(headers).lower()
    for rule in ATS_RULES:
        for sig in rule.get("header_signatures", []):
            if sig.lower() in header_str:
                return ATSClassification(
                    vendor=rule["vendor"], board_token=None, start_tier=rule["start_tier"]
                )
    return None


def classify_html(html: str) -> ATSClassification | None:
    """Classify from HTML content (first 5KB)."""
    snippet = html[:5120].lower()
    for rule in ATS_RULES:
        for sig in rule.get("html_signatures", []):
            if sig.lower() in snippet:
                return ATSClassification(
                    vendor=rule["vendor"], board_token=None, start_tier=rule["start_tier"]
                )
    return None


def _extract_token(url: str, pattern: str | None) -> str | None:
    if not pattern:
        return None
    match = re.search(pattern, url, re.IGNORECASE)
    return match.group(1) if match else None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/unit/scraping/test_ats_registry.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/scraping/control/ tests/unit/scraping/test_ats_registry.py
git commit -m "feat: add data-driven ATS classification registry"
```

---

### Task 8: Build Classifier (URL Pattern + Priority)

**Files:**
- Create: `backend/app/scraping/control/classifier.py`
- Test: `backend/tests/unit/scraping/test_classifier.py`

- [ ] **Step 1: Write tests**

```python
# tests/unit/scraping/test_classifier.py
from app.scraping.control.classifier import classify_target, assign_priority

def test_classify_greenhouse_target():
    result = classify_target(
        url="https://boards.greenhouse.io/huggingface",
        company_name="Hugging Face",
    )
    assert result["ats_vendor"] == "greenhouse"
    assert result["ats_board_token"] == "huggingface"
    assert result["start_tier"] == 0
    assert result["source_kind"] == "ats_board"

def test_classify_unknown_target():
    result = classify_target(
        url="https://careers.google.com/jobs",
        company_name="Google",
    )
    assert result["ats_vendor"] is None
    assert result["start_tier"] == 1
    assert result["source_kind"] == "career_page"

def test_assign_priority_watchlist():
    p = assign_priority(lca_filings=5000, company_name="Google",
                        watchlist=["Google", "Meta", "OpenAI"])
    assert p["priority_class"] == "watchlist"
    assert p["schedule_interval_m"] == 120

def test_assign_priority_hot():
    p = assign_priority(lca_filings=2000, company_name="Acme Corp", watchlist=[])
    assert p["priority_class"] == "hot"
    assert p["schedule_interval_m"] == 240

def test_assign_priority_warm():
    p = assign_priority(lca_filings=500, company_name="MidCorp", watchlist=[])
    assert p["priority_class"] == "warm"

def test_assign_priority_cool():
    p = assign_priority(lca_filings=50, company_name="SmallCo", watchlist=[])
    assert p["priority_class"] == "cool"

def test_watchlist_override_low_filings():
    """Watchlist companies get watchlist priority regardless of LCA count.

    Note: spec originally said watchlist requires >= 1000 AND in watchlist,
    but the plan intentionally overrides this — a user's dream company should
    ALWAYS be watchlist priority. Spec updated to match this behavior.
    """
    p = assign_priority(lca_filings=10, company_name="OpenAI",
                        watchlist=["OpenAI"])
    assert p["priority_class"] == "watchlist"
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Create classifier.py**

```python
# app/scraping/control/classifier.py
"""Target classification: ATS type + priority assignment."""
from __future__ import annotations

from difflib import SequenceMatcher

from app.scraping.constants import PRIORITY_INTERVALS
from app.scraping.control.ats_registry import classify_url


def classify_target(url: str, company_name: str | None = None) -> dict:
    """Classify a target URL into ATS type and source kind.

    Phase 1: URL-only classification. Header and HTML probing added in a later chunk.
    """
    ats = classify_url(url)
    return {
        "ats_vendor": ats.vendor,
        "ats_board_token": ats.board_token,
        "start_tier": ats.start_tier,
        "source_kind": "ats_board" if ats.vendor is not None else "career_page",
    }


def assign_priority(
    lca_filings: int | None,
    company_name: str | None,
    watchlist: list[str],
) -> dict:
    """Assign priority class and schedule interval."""
    filings = lca_filings or 0

    # Watchlist override: fuzzy match against dream companies
    if company_name and watchlist:
        for w in watchlist:
            if _fuzzy_match(company_name, w):
                return {
                    "priority_class": "watchlist",
                    "schedule_interval_m": PRIORITY_INTERVALS["watchlist"],
                }

    if filings >= 1000:
        cls = "hot"
    elif filings >= 100:
        cls = "warm"
    else:
        cls = "cool"

    return {
        "priority_class": cls,
        "schedule_interval_m": PRIORITY_INTERVALS[cls],
    }


def _fuzzy_match(a: str, b: str, threshold: float = 0.8) -> bool:
    """Case-insensitive fuzzy match."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() >= threshold
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/unit/scraping/test_classifier.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/scraping/control/classifier.py tests/unit/scraping/test_classifier.py
git commit -m "feat: add target classification and priority assignment"
```

---

### Task 9: Fix Simhash Determinism

**Files:**
- Modify: `backend/app/scraping/deduplication.py`
- Test: `backend/tests/unit/scraping/test_simhash_deterministic.py`

- [ ] **Step 1: Write test for deterministic simhash**

```python
# tests/unit/scraping/test_simhash_deterministic.py
from app.scraping.deduplication import DeduplicationService
from app.scraping.port import ScrapedJob

def _make_job(title: str, company: str, desc: str = "") -> ScrapedJob:
    return ScrapedJob(title=title, company_name=company, source="test",
                      description_raw=desc)

def test_simhash_deterministic_across_calls():
    """Simhash must produce the same value for the same input."""
    svc = DeduplicationService()
    job = _make_job("Senior ML Engineer", "Google", "Mountain View role")
    h1 = svc._compute_simhash(job)
    h2 = svc._compute_simhash(job)
    assert h1 == h2

def test_simhash_different_for_different_input():
    svc = DeduplicationService()
    h1 = svc._compute_simhash(_make_job("ML Engineer", "Google"))
    h2 = svc._compute_simhash(_make_job("Data Scientist", "Meta"))
    assert h1 != h2

def test_simhash_similar_for_similar_input():
    svc = DeduplicationService()
    h1 = svc._compute_simhash(_make_job("Senior ML Engineer", "Google",
                                         "Mountain View CA office"))
    h2 = svc._compute_simhash(_make_job("Senior ML Engineer", "Google",
                                         "Mountain View California office"))
    distance = bin(h1 ^ h2).count("1")
    assert distance < 5
```

- [ ] **Step 2: Run test — may pass or fail depending on current implementation**

- [ ] **Step 3: Fix _compute_simhash to use hashlib.md5**

In `backend/app/scraping/deduplication.py`, keep the existing `ScrapedJob` parameter signature but replace the internal hash computation. Find the line `h = hash(token) & ((1 << 64) - 1)` and replace with deterministic hashlib:

```python
import hashlib

# Inside _compute_simhash(self, job: ScrapedJob), replace the hash line:
# OLD: h = hash(token) & ((1 << 64) - 1)
# NEW:
h = int(hashlib.md5(token.encode()).hexdigest(), 16) & ((1 << 64) - 1)
```

The method signature `_compute_simhash(self, job: ScrapedJob) -> int` stays unchanged. Only the internal hash function changes. The caller `deduplicate()` does not need modification.

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/unit/scraping/test_simhash_deterministic.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/scraping/deduplication.py tests/unit/scraping/test_simhash_deterministic.py
git commit -m "fix: make simhash deterministic using hashlib.md5"
```

---

### Task 10: Build Target Import CLI (H1B Excel)

**Files:**
- Create: `backend/app/scraping/ops.py`
- Create: `backend/app/scraping/control/target_registry.py`
- Test: manual — `python -m app.scraping.ops targets import --dry-run`

- [ ] **Step 1: Install CLI dependencies**

```bash
pip install typer rich openpyxl
```

- [ ] **Step 2: Create target_registry.py (CRUD for scrape_targets)**

```python
# app/scraping/control/target_registry.py
"""ScrapeTarget CRUD operations and bulk import."""
from __future__ import annotations

import uuid
from datetime import datetime, UTC
from pathlib import Path

import openpyxl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.scraping.models import ScrapeTarget
from app.scraping.control.classifier import classify_target, assign_priority


async def import_from_excel(
    db: AsyncSession,
    file_path: str | Path,
    user_id: uuid.UUID,
    watchlist: list[str],
    dry_run: bool = False,
) -> dict:
    """Import H1B career page URLs from Excel file."""
    wb = openpyxl.load_workbook(file_path, read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=5, values_only=True))  # skip header rows 1-4
    wb.close()

    stats = {"total": 0, "imported": 0, "skipped_duplicate": 0, "skipped_no_url": 0}

    for row in rows:
        if not row or len(row) < 4:
            continue
        stats["total"] += 1

        rank, company_name, industry, url, *rest = row
        if not url or not str(url).startswith("http"):
            stats["skipped_no_url"] += 1
            continue

        url = str(url).strip()
        company_name = str(company_name).strip() if company_name else None
        industry = str(industry).strip() if industry else None
        lca_filings = int(rest[0]) if rest and rest[0] else None

        # Check for duplicate URL
        existing = await db.scalar(
            select(ScrapeTarget).where(ScrapeTarget.url == url, ScrapeTarget.user_id == user_id)
        )
        if existing:
            stats["skipped_duplicate"] += 1
            continue

        # Classify
        classification = classify_target(url, company_name)
        priority = assign_priority(lca_filings, company_name, watchlist)

        if not dry_run:
            target = ScrapeTarget(
                user_id=user_id,
                url=url,
                company_name=company_name,
                industry=industry,
                lca_filings=lca_filings,
                next_scheduled_at=datetime.now(UTC),
                **classification,
                **priority,
            )
            db.add(target)
        stats["imported"] += 1

    if not dry_run:
        await db.commit()

    return stats


async def list_targets(
    db: AsyncSession,
    user_id: uuid.UUID,
    priority: str | None = None,
    ats: str | None = None,
    quarantined: bool | None = None,
    failing: bool = False,
    limit: int = 50,
) -> list[ScrapeTarget]:
    """List targets with optional filters."""
    query = select(ScrapeTarget).where(ScrapeTarget.user_id == user_id)
    if priority:
        query = query.where(ScrapeTarget.priority_class == priority)
    if ats:
        query = query.where(ScrapeTarget.ats_vendor == ats)
    if quarantined is not None:
        query = query.where(ScrapeTarget.quarantined == quarantined)
    if failing:
        query = query.where(ScrapeTarget.consecutive_failures > 0)
    query = query.order_by(ScrapeTarget.created_at.desc()).limit(limit)
    result = await db.scalars(query)
    return list(result.all())
```

- [ ] **Step 3: Create ops.py CLI entry point**

```python
# app/scraping/ops.py
"""CLI operations tool for scraper platform management."""
from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Scraper platform operations")
targets_app = typer.Typer(help="Target management")
quarantine_app = typer.Typer(help="Quarantine management")
app.add_typer(targets_app, name="targets")
app.add_typer(quarantine_app, name="quarantine")

console = Console()


@targets_app.command("import")
def import_targets(
    file: Path = typer.Argument(..., help="Path to Excel/CSV file"),
    classify: bool = typer.Option(True, help="Run URL classification"),
    dry_run: bool = typer.Option(False, help="Preview without importing"),
):
    """Bulk import career page URLs from Excel/CSV."""
    from app.config import settings
    from app.database import async_session_factory
    from app.scraping.control.target_registry import import_from_excel

    async def _run():
        async with async_session_factory() as db:
            # Get first user (single-user system)
            from sqlalchemy import select, text
            row = await db.execute(text("SELECT id FROM users LIMIT 1"))
            user_id = row.scalar_one()

            # User's watchlist from profile
            from app.profile.models import UserProfile
            profile = await db.scalar(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            watchlist = profile.watchlist_companies if profile and profile.watchlist_companies else []

            stats = await import_from_excel(
                db, file, user_id, watchlist, dry_run=dry_run,
            )

        table = Table(title="Import Results" + (" (DRY RUN)" if dry_run else ""))
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        table.add_row("Total rows", str(stats["total"]))
        table.add_row("Imported", str(stats["imported"]))
        table.add_row("Skipped (duplicate)", str(stats["skipped_duplicate"]))
        table.add_row("Skipped (no URL)", str(stats["skipped_no_url"]))
        console.print(table)

    asyncio.run(_run())


@targets_app.command("list")
def list_targets_cmd(
    priority: str = typer.Option(None, help="Filter by priority class"),
    ats: str = typer.Option(None, help="Filter by ATS vendor"),
    quarantined: bool = typer.Option(False, help="Show quarantined only"),
    failing: bool = typer.Option(False, help="Show failing only"),
    limit: int = typer.Option(50, help="Max results"),
):
    """List scrape targets."""
    from app.database import async_session_factory
    from app.scraping.control.target_registry import list_targets

    async def _run():
        async with async_session_factory() as db:
            from sqlalchemy import text
            row = await db.execute(text("SELECT id FROM users LIMIT 1"))
            user_id = row.scalar_one()

            targets = await list_targets(
                db, user_id, priority=priority, ats=ats,
                quarantined=quarantined if quarantined else None,
                failing=failing, limit=limit,
            )

        table = Table(title=f"Scrape Targets ({len(targets)} results)")
        table.add_column("Company", style="cyan", max_width=25)
        table.add_column("ATS", style="yellow")
        table.add_column("Tier", style="green")
        table.add_column("Priority", style="magenta")
        table.add_column("Failures", style="red")
        table.add_column("Last Success")
        for t in targets:
            table.add_row(
                t.company_name or "—",
                t.ats_vendor or "unknown",
                str(t.start_tier),
                t.priority_class,
                str(t.consecutive_failures),
                str(t.last_success_at.date()) if t.last_success_at else "never",
            )
        console.print(table)

    asyncio.run(_run())


if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Test the import with dry-run**

```bash
cd D:/jobradar-v2/backend
python -m app.scraping.ops targets import "C:/Users/shriy/Downloads/H1B_Sponsors_Career_Pages.xlsx" --dry-run
```
Expected: table showing ~1,473 total rows, ~1,473 imported, 0 duplicates

- [ ] **Step 5: Run the actual import**

```bash
python -m app.scraping.ops targets import "C:/Users/shriy/Downloads/H1B_Sponsors_Career_Pages.xlsx"
```

- [ ] **Step 6: Verify with list command**

```bash
python -m app.scraping.ops targets list --limit 10
python -m app.scraping.ops targets list --ats greenhouse --limit 10
python -m app.scraping.ops targets list --priority watchlist
```

- [ ] **Step 7: Commit**

```bash
git add app/scraping/ops.py app/scraping/control/target_registry.py
git commit -m "feat: add CLI ops tool with H1B career page import"
```

---

## Chunk Status
- [x] All tasks completed
- [x] All tests passing (153/153 unit tests pass)
- [x] Migration applied successfully (4 migrations: scrape_targets+attempts, indexes, lifecycle+tier, career_pages migration)
- [ ] 1,473 URLs imported and classified (CLI ready, import not yet run against real data)

### Notes / Issues Encountered

| Date | Note |
|------|------|
| 2026-03-19 | Tasks 2+3 combined into single commit (models tightly coupled via FK) |
| 2026-03-19 | Tasks 4+5 combined into single commit (both add columns to existing models) |
| 2026-03-19 | Code review found missing indexes on scrape_attempts — fixed in separate commit |
| 2026-03-19 | script.py.mako was missing from Alembic setup — created standard template |
| 2026-03-19 | Alembic autogenerate detects many spurious type diffs (JSONB/JSON, TIMESTAMP) — manually trimmed all migrations |
| 2026-03-19 | SQLAlchemy 2.0 mapped_column(default=X) sets SQL INSERT default, not Python __init__ default — tests adjusted accordingly |
| 2026-03-19 | CareerPage schemas kept in schemas.py for API compatibility (renamed internally to use ScrapeTarget) |
