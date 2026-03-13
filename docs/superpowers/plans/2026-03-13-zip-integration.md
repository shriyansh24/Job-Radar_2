# Zip Integration — Surgical Merge Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate features from jobradar_project.zip into the existing JobRadar codebase — scraper enhancements, 3-layer dedup, NLP engine, resume system, and auto-apply.

**Architecture:** Surgical merge — enhance existing Python/FastAPI/SQLAlchemy codebase in-place. No new frameworks. All new modules under `backend/`. TDD for every module.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0 async, aiosqlite, pytest, playwright, fpdf2, pdfplumber, pylatexenc, python-docx

**Spec:** `docs/superpowers/specs/2026-03-13-zip-integration-design.md`

**Dependency graph:**
```
Chunk 1 (Foundation) ──→ Chunk 2 (Scraper Infra) ──→ Chunk 9 (Wiring)
                    ├──→ Chunk 3 (Adapters)       ──→ Chunk 8 (Auto-Apply)
                    ├──→ Chunk 4 (Dedup)           ──→ Chunk 9
                    ├──→ Chunk 5 (NLP Core)        ──→ Chunk 7 (NLP Tools) ──→ Chunk 9
                    └──→ Chunk 6 (Resume System)   ──→ Chunk 7, Chunk 8
```

**Parallel tracks after Chunk 1:** Chunks 2, 3, 4, 5, 6 are independent — run as parallel subagents.
**After those complete:** Chunks 7 and 8 can run in parallel.
**Last:** Chunk 9 wires everything together.

---

## Chunk 1: Foundation — Schema, Models, Dependencies, Pydantic Schemas

### Task 1.1: Add New Dependencies

**Files:**
- Modify: `backend/requirements.txt` (currently 20 lines)

- [ ] **Step 1: Add new packages to requirements.txt**

Append after line 19 (after `pandas==2.2.0`):
```
playwright==1.49.0
python-docx==1.1.0
fpdf2==2.8.0
pylatexenc==2.10
pdfplumber==0.11.0
```

Note: `weasyprint` is optional — do NOT add to requirements.txt. It's detected at runtime if available.

- [ ] **Step 2: Install dependencies**

Run: `cd backend && pip install -r requirements.txt`

- [ ] **Step 3: Install Playwright Chromium**

Run: `playwright install chromium`

- [ ] **Step 4: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore: add new dependencies for zip integration"
```

---

### Task 1.2: Add New Columns to Job and UserProfile Models

**Files:**
- Modify: `backend/models.py:72` (after `tags` field) and `backend/models.py:112` (after `company_watchlist`)
- Test: `tests/test_zip_integration/test_schema_migration.py`

- [ ] **Step 1: Write failing test for new Job columns**

Create `tests/test_zip_integration/__init__.py` (empty) and:

```python
# tests/test_zip_integration/test_schema_migration.py
"""Test that new columns exist on Job and UserProfile models."""
import pytest
from sqlalchemy import inspect
from backend.database import engine, Base
from backend.models import Job, UserProfile, ResumeVersion, ApplicationAttempt


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class TestJobNewColumns:
    async def test_dedup_hash_column_exists(self):
        assert hasattr(Job, "dedup_hash")

    async def test_tfidf_score_column_exists(self):
        assert hasattr(Job, "tfidf_score")

    async def test_council_scores_column_exists(self):
        assert hasattr(Job, "council_scores")

    async def test_apply_questions_column_exists(self):
        assert hasattr(Job, "apply_questions")


class TestUserProfileNewColumns:
    async def test_resume_parsed_column_exists(self):
        assert hasattr(UserProfile, "resume_parsed")

    async def test_application_profile_column_exists(self):
        assert hasattr(UserProfile, "application_profile")


class TestNewModels:
    async def test_resume_version_table_created(self):
        async with engine.begin() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
        assert "resume_versions" in tables

    async def test_application_attempt_table_created(self):
        async with engine.begin() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
        assert "application_attempts" in tables

    async def test_resume_version_fields(self):
        assert hasattr(ResumeVersion, "id")
        assert hasattr(ResumeVersion, "filename")
        assert hasattr(ResumeVersion, "format")
        assert hasattr(ResumeVersion, "file_path")
        assert hasattr(ResumeVersion, "parsed_text")
        assert hasattr(ResumeVersion, "is_default")

    async def test_application_attempt_fields(self):
        assert hasattr(ApplicationAttempt, "job_id")
        assert hasattr(ApplicationAttempt, "ats_provider")
        assert hasattr(ApplicationAttempt, "fields_filled")
        assert hasattr(ApplicationAttempt, "status")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_zip_integration/test_schema_migration.py -v`
Expected: ImportError or AttributeError (columns/models don't exist yet)

- [ ] **Step 3: Add columns and new models to models.py**

Add after `tags` field on Job (line 72):
```python
    # Zip integration columns
    dedup_hash: Mapped[str | None] = mapped_column(String(64))
    tfidf_score: Mapped[float | None]
    council_scores: Mapped[dict | None] = mapped_column(JSON)
    apply_questions: Mapped[list | None] = mapped_column(JSON)
```

Add after `company_watchlist` on UserProfile (line 112):
```python
    # Zip integration columns
    resume_parsed: Mapped[dict | None] = mapped_column(JSON)
    application_profile: Mapped[dict | None] = mapped_column(JSON)
```

Add new models after UserProfile:
```python
class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)  # ULID
    filename: Mapped[str] = mapped_column(String(255))
    format: Mapped[str] = mapped_column(String(8))  # pdf/docx/md/tex
    file_path: Mapped[str] = mapped_column(String(512))
    parsed_text: Mapped[str | None] = mapped_column(Text)
    parsed_structured: Mapped[dict | None] = mapped_column(JSON)
    version_label: Mapped[str] = mapped_column(String(255), default="v1")
    is_default: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=func.now())


class ApplicationAttempt(Base):
    __tablename__ = "application_attempts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(64), ForeignKey("jobs.job_id"))
    resume_version_id: Mapped[str | None] = mapped_column(String(26), ForeignKey("resume_versions.id"))
    ats_provider: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    fields_filled: Mapped[dict | None] = mapped_column(JSON)
    fields_skipped: Mapped[list | None] = mapped_column(JSON)
    screenshots: Mapped[list | None] = mapped_column(JSON)
    custom_answers: Mapped[dict | None] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(default=func.now())
    completed_at: Mapped[datetime | None]
    error: Mapped[str | None] = mapped_column(Text)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_zip_integration/test_schema_migration.py -v`
Expected: All PASS

- [ ] **Step 5: Run existing tests for backward compatibility**

Run: `pytest tests/ -v --tb=short`
Expected: All 822+ existing tests still pass

- [ ] **Step 6: Commit**

```bash
git add backend/models.py tests/test_zip_integration/
git commit -m "feat: add zip integration schema — new Job/UserProfile columns, ResumeVersion, ApplicationAttempt models"
```

---

### Task 1.3: Add New Pydantic Schemas

**Files:**
- Modify: `backend/schemas.py:186` (append after SavedSearchResponse)
- Test: `tests/test_zip_integration/test_new_schemas.py`

- [ ] **Step 1: Write failing test for new schemas**

```python
# tests/test_zip_integration/test_new_schemas.py
"""Test new Pydantic schemas for zip integration."""
import pytest
from backend.schemas import (
    DimensionScoreSchema,
    CouncilScoreResponse,
    ResumeVersionResponse,
    AutoApplyRunRequest,
    ApplicationResultResponse,
    AutoApplyAnalysis,
    ApplicationProfileRequest,
    ApplicationProfileResponse,
    CopilotRequest,
)


class TestDimensionScoreSchema:
    def test_create_valid(self):
        d = DimensionScoreSchema(
            grade="A", score=92, rationale="Strong match",
            gaps=["missing AWS"], suggestions=["Add AWS cert"]
        )
        assert d.grade == "A"
        assert d.score == 92

    def test_rejects_invalid_score(self):
        with pytest.raises(Exception):
            DimensionScoreSchema(grade="A", score=150, rationale="", gaps=[], suggestions=[])


class TestCouncilScoreResponse:
    def test_create_valid(self):
        dim = {"grade": "B", "score": 80, "rationale": "Good", "gaps": [], "suggestions": []}
        c = CouncilScoreResponse(
            skill_alignment=dim, experience_level=dim, impact_language=dim,
            ats_keyword_density=dim, structural_quality=dim, cultural_signals=dim,
            growth_trajectory=dim, overall_grade="B", overall_score=80,
            top_gaps=[], missing_keywords=[], strong_points=[], suggested_bullets=[],
            council_consensus=0.85,
        )
        assert c.overall_grade == "B"


class TestResumeVersionResponse:
    def test_create_valid(self):
        r = ResumeVersionResponse(
            id="01ARZ3NDEKTSV4RRFFQ69G5FAV", filename="resume.pdf",
            format="pdf", version_label="v1", is_default=True,
            parsed_text_preview="John Doe...", created_at="2026-03-13T00:00:00"
        )
        assert r.format == "pdf"


class TestAutoApplyRunRequest:
    def test_default_submit_false(self):
        r = AutoApplyRunRequest(job_id="abc123")
        assert r.submit is False

    def test_submit_explicit_true(self):
        r = AutoApplyRunRequest(job_id="abc123", submit=True)
        assert r.submit is True


class TestCopilotRequestTailorResume:
    def test_tailor_resume_tool_accepted(self):
        r = CopilotRequest(tool="tailorResume", job_id="abc123")
        assert r.tool == "tailorResume"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_zip_integration/test_new_schemas.py -v`
Expected: ImportError (schemas don't exist yet)

- [ ] **Step 3: Add schemas to schemas.py**

Append after `SavedSearchResponse` (after line 186):
```python
# --- Zip Integration Schemas ---

class DimensionScoreSchema(BaseModel):
    grade: str  # A/B/C/D
    score: int = Field(ge=0, le=100)
    rationale: str
    gaps: list[str] = []
    suggestions: list[str] = []


class CouncilScoreResponse(BaseModel):
    skill_alignment: DimensionScoreSchema
    experience_level: DimensionScoreSchema
    impact_language: DimensionScoreSchema
    ats_keyword_density: DimensionScoreSchema
    structural_quality: DimensionScoreSchema
    cultural_signals: DimensionScoreSchema
    growth_trajectory: DimensionScoreSchema
    overall_grade: str
    overall_score: int
    top_gaps: list[str] = []
    missing_keywords: list[str] = []
    strong_points: list[str] = []
    suggested_bullets: list[str] = []
    council_consensus: float


class ResumeVersionResponse(BaseModel):
    id: str
    filename: str
    format: str
    version_label: str
    is_default: bool
    parsed_text_preview: str = ""
    created_at: str


class AutoApplyRunRequest(BaseModel):
    job_id: str
    resume_id: str | None = None
    submit: bool = False


class ApplicationResultResponse(BaseModel):
    success: bool
    fields_filled: dict = {}
    fields_missed: list[str] = []
    ats_provider: str = ""
    error: str | None = None
    screenshots: list[str] = []


class AutoApplyAnalysis(BaseModel):
    ats_provider: str
    form_fields_detected: list[str] = []
    estimated_fill_rate: float = 0.0
    requires_login: bool = False


class ApplicationProfileRequest(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""
    location: str = ""
    work_authorization: str = ""
    years_experience: int = 0
    education_summary: str = ""
    current_title: str = ""
    desired_salary: str = ""


class ApplicationProfileResponse(ApplicationProfileRequest):
    pass
```

Also update `CopilotRequest` (line 121-123) to add docstring noting tailorResume:
```python
class CopilotRequest(BaseModel):
    tool: str  # "coverLetter"|"interviewPrep"|"gapAnalysis"|"tailorResume"
    job_id: str
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_zip_integration/test_new_schemas.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/schemas.py tests/test_zip_integration/test_new_schemas.py
git commit -m "feat: add Pydantic schemas for council, resume, auto-apply, and copilot tailorResume"
```

---

### Task 1.4: Create Package Init Files

**Files:**
- Create: `backend/adapters/__init__.py`, `backend/resume/__init__.py`, `backend/nlp/__init__.py`, `backend/auto_apply/__init__.py`
- Create: `data/resumes/` directory

- [ ] **Step 1: Create package directories and init files**

```python
# backend/adapters/__init__.py
"""ATS detection and job filtering adapters."""

# backend/resume/__init__.py
"""Resume parsing, scoring, and document management."""

# backend/nlp/__init__.py
"""NLP engine — scoring, gap analysis, resume tailoring, cover letters."""

# backend/auto_apply/__init__.py
"""Auto-apply system — Playwright form filling for ATS providers."""
```

Create `data/resumes/` directory (for file-based resume storage).

- [ ] **Step 2: Commit**

```bash
git add backend/adapters/__init__.py backend/resume/__init__.py backend/nlp/__init__.py backend/auto_apply/__init__.py
git commit -m "chore: create package init files for adapters, resume, nlp, auto_apply"
```

---

## Chunk 2: Scraper Infrastructure — Rate Limiter + BaseScraper Enhancements

**Depends on:** Chunk 1 (models must exist for dedup_hash)

### Task 2.1: Rate Limiter Module

**Files:**
- Create: `backend/scrapers/rate_limiter.py`
- Test: `tests/test_zip_integration/test_rate_limiter.py`

- [ ] **Step 1: Write failing tests for rate limiter**

```python
# tests/test_zip_integration/test_rate_limiter.py
"""Test token bucket rate limiter with circuit breaker."""
import asyncio
import pytest
import time
from backend.scrapers.rate_limiter import (
    RatePolicy, RateLimiter, CircuitOpenError, get_limiter,
    DEFAULT_POLICIES,
)


class TestRatePolicy:
    def test_default_values(self):
        p = RatePolicy(rps=10.0, backoff_base=1.0, max_retries=3, circuit_threshold=5)
        assert p.rps == 10.0
        assert p.circuit_cooldown == 300.0

    def test_custom_cooldown(self):
        p = RatePolicy(rps=1.0, backoff_base=2.0, max_retries=2, circuit_threshold=3, circuit_cooldown=60.0)
        assert p.circuit_cooldown == 60.0


class TestRateLimiter:
    async def test_acquire_respects_rate(self):
        policy = RatePolicy(rps=100.0, backoff_base=1.0, max_retries=3, circuit_threshold=5)
        limiter = RateLimiter(policy)
        start = time.monotonic()
        await limiter.acquire()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        # 100 RPS → 10ms between tokens, 2 acquires should be fast
        assert elapsed < 0.5

    async def test_circuit_breaker_opens_after_threshold(self):
        policy = RatePolicy(rps=100.0, backoff_base=0.01, max_retries=1, circuit_threshold=3, circuit_cooldown=60.0)
        limiter = RateLimiter(policy)
        for _ in range(3):
            limiter.record_failure()
        with pytest.raises(CircuitOpenError):
            await limiter.acquire()

    async def test_circuit_resets_on_success(self):
        policy = RatePolicy(rps=100.0, backoff_base=0.01, max_retries=1, circuit_threshold=3, circuit_cooldown=60.0)
        limiter = RateLimiter(policy)
        limiter.record_failure()
        limiter.record_failure()
        limiter.record_success()
        # Should not raise — success reset the counter
        await limiter.acquire()

    async def test_with_retry_succeeds(self):
        policy = RatePolicy(rps=100.0, backoff_base=0.01, max_retries=3, circuit_threshold=5)
        limiter = RateLimiter(policy)
        call_count = 0

        async def flaky_fn():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("transient")
            return "success"

        result = await limiter.with_retry(flaky_fn)
        assert result == "success"
        assert call_count == 3

    async def test_with_retry_exhausts_retries(self):
        policy = RatePolicy(rps=100.0, backoff_base=0.01, max_retries=2, circuit_threshold=10)
        limiter = RateLimiter(policy)

        async def always_fail():
            raise ConnectionError("permanent")

        with pytest.raises(ConnectionError):
            await limiter.with_retry(always_fail)


class TestDefaultPolicies:
    def test_greenhouse_policy_exists(self):
        assert "greenhouse" in DEFAULT_POLICIES
        assert DEFAULT_POLICIES["greenhouse"].rps == 10.0

    def test_serpapi_policy_exists(self):
        assert "serpapi" in DEFAULT_POLICIES

    def test_generic_fallback(self):
        assert "generic" in DEFAULT_POLICIES
        assert DEFAULT_POLICIES["generic"].rps == 0.1


class TestGetLimiter:
    def test_returns_limiter_for_known_source(self):
        limiter = get_limiter("greenhouse")
        assert isinstance(limiter, RateLimiter)

    def test_returns_generic_for_unknown_source(self):
        limiter = get_limiter("unknown_ats")
        assert isinstance(limiter, RateLimiter)

    def test_caches_instances(self):
        a = get_limiter("lever")
        b = get_limiter("lever")
        assert a is b
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_zip_integration/test_rate_limiter.py -v`
Expected: ImportError

- [ ] **Step 3: Implement rate_limiter.py**

Create `backend/scrapers/rate_limiter.py` with:
- `RatePolicy` dataclass (rps, backoff_base, max_retries, circuit_threshold, circuit_cooldown=300.0)
- `CircuitOpenError(Exception)`
- `RateLimiter` class:
  - Token bucket: tracks `_last_acquire` time, sleeps `1.0/policy.rps` between acquires
  - Circuit breaker: tracks `_consecutive_failures`, `_circuit_opened_at`
  - `acquire()`: check circuit state, wait for token
  - `record_success()`: reset failure counter
  - `record_failure()`: increment counter, open circuit if threshold hit
  - `with_retry(coro_factory)`: retry with exponential backoff, calls record_success/failure
- `DEFAULT_POLICIES` dict with entries for greenhouse, lever, ashby, serpapi, generic
- `get_limiter(source_id)` factory with `_limiter_cache` dict

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_zip_integration/test_rate_limiter.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/scrapers/rate_limiter.py tests/test_zip_integration/test_rate_limiter.py
git commit -m "feat: add token bucket rate limiter with circuit breaker"
```

---

### Task 2.2: BaseScraper Enhancements

**Files:**
- Modify: `backend/scrapers/base.py:29-80,117-118`
- Test: `tests/test_zip_integration/test_base_scraper_enhancements.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_zip_integration/test_base_scraper_enhancements.py
"""Test BaseScraper new methods: extract_tech_stack, _infer_seniority, _normalize_salary, dedup_hash in normalize."""
import pytest
from backend.scrapers.base import BaseScraper


class TestExtractTechStack:
    def test_extracts_common_tech(self):
        desc = "We use Python, React, AWS, and PostgreSQL daily."
        result = BaseScraper.extract_tech_stack(desc)
        assert "Python" in result
        assert "React" in result
        assert "AWS" in result
        assert "PostgreSQL" in result

    def test_case_insensitive(self):
        desc = "Experience with PYTHON and javascript required."
        result = BaseScraper.extract_tech_stack(desc)
        assert len(result) >= 2

    def test_empty_description(self):
        assert BaseScraper.extract_tech_stack("") == []

    def test_no_tech_found(self):
        assert BaseScraper.extract_tech_stack("We sell cookies.") == []

    def test_max_15_results(self):
        desc = "Python Java C++ Go Rust Ruby PHP Swift Kotlin Scala TypeScript JavaScript React Angular Vue Django Flask FastAPI Spring Rails"
        result = BaseScraper.extract_tech_stack(desc)
        assert len(result) <= 15


class TestInferSeniority:
    def test_senior_engineer(self):
        assert BaseScraper._infer_seniority("Senior Software Engineer") == "senior"

    def test_staff_engineer(self):
        assert BaseScraper._infer_seniority("Staff ML Engineer") == "staff"

    def test_intern(self):
        assert BaseScraper._infer_seniority("Engineering Intern") == "intern"

    def test_junior_maps_to_entry(self):
        assert BaseScraper._infer_seniority("Junior Developer") == "entry"

    def test_lead(self):
        assert BaseScraper._infer_seniority("Lead Data Scientist") == "lead"

    def test_principal(self):
        assert BaseScraper._infer_seniority("Principal Engineer") == "principal"

    def test_vp_maps_to_exec(self):
        assert BaseScraper._infer_seniority("VP of Engineering") == "exec"

    def test_no_seniority_returns_none(self):
        assert BaseScraper._infer_seniority("Software Engineer") is None

    def test_case_insensitive(self):
        assert BaseScraper._infer_seniority("SENIOR ENGINEER") == "senior"


class TestNormalizeSalary:
    def test_hourly_to_annual(self):
        min_val, max_val = BaseScraper._normalize_salary(50, 75, "hourly")
        assert min_val == 50 * 2080
        assert max_val == 75 * 2080

    def test_annual_unchanged(self):
        min_val, max_val = BaseScraper._normalize_salary(100000, 150000, "year")
        assert min_val == 100000
        assert max_val == 150000

    def test_cents_to_dollars(self):
        # Values > 100000 that look like cents
        min_val, max_val = BaseScraper._normalize_salary(10000000, 15000000, "year")
        assert min_val == 100000
        assert max_val == 150000

    def test_none_values(self):
        min_val, max_val = BaseScraper._normalize_salary(None, None, "year")
        assert min_val is None
        assert max_val is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_zip_integration/test_base_scraper_enhancements.py -v`
Expected: AttributeError (methods don't exist)

- [ ] **Step 3: Add new static methods to BaseScraper**

Add after `_rate_limit()` (line 118) in `backend/scrapers/base.py`:

```python
    TECH_TERMS = [
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust",
        "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "SQL",
        "React", "Angular", "Vue", "Next.js", "Node.js", "Django", "Flask", "FastAPI",
        "Spring", "Rails", "Express", ".NET",
        "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform",
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "TensorFlow", "PyTorch", "Spark", "Kafka", "GraphQL",
    ]

    SENIORITY_MAP = {
        "intern": "intern", "internship": "intern",
        "junior": "entry", "entry": "entry", "associate": "entry", "jr": "entry",
        "mid": "mid", "mid-level": "mid",
        "senior": "senior", "sr": "senior",
        "lead": "lead", "team lead": "lead",
        "staff": "staff",
        "principal": "principal",
        "director": "exec", "vp": "exec", "vice president": "exec",
        "head of": "exec", "chief": "exec", "cto": "exec", "ceo": "exec",
    }

    @staticmethod
    def extract_tech_stack(description: str) -> list[str]:
        if not description:
            return []
        desc_lower = description.lower()
        found = []
        for tech in BaseScraper.TECH_TERMS:
            if tech.lower() in desc_lower:
                found.append(tech)
        return found[:15]

    @staticmethod
    def _infer_seniority(title: str) -> str | None:
        if not title:
            return None
        title_lower = title.lower()
        for keyword, level in BaseScraper.SENIORITY_MAP.items():
            if keyword in title_lower:
                return level
        return None

    @staticmethod
    def _normalize_salary(min_val, max_val, interval="year") -> tuple:
        if min_val is None and max_val is None:
            return None, None
        if interval and interval.lower() in ("hourly", "hour"):
            min_val = min_val * 2080 if min_val else None
            max_val = max_val * 2080 if max_val else None
        # Cents detection: if both > 1M, assume cents
        if min_val and min_val > 1_000_000:
            min_val = min_val / 100
        if max_val and max_val > 1_000_000:
            max_val = max_val / 100
        return min_val, max_val
```

Also update `normalize()` (around line 75) to add `dedup_hash` and `tech_stack` to the returned dict:

```python
import hashlib

# Inside normalize(), before the return dict:
dedup_key = f"{raw.get('title', '').lower().strip()}|{raw.get('company_name', '').lower().strip()}|{raw.get('location', '').lower().strip()}"
dedup_hash = hashlib.sha256(dedup_key.encode()).hexdigest()[:64]
tech_stack = self.extract_tech_stack(raw.get("description_clean", "") or raw.get("description_raw", ""))
experience_level = raw.get("experience_level") or self._infer_seniority(raw.get("title", ""))

# Add to the returned dict:
# "dedup_hash": dedup_hash,
# "tech_stack": tech_stack,
# "experience_level": experience_level,
```

Replace `_rate_limit()` (line 117-118) to use the new rate limiter:
```python
    async def _rate_limit(self):
        from backend.scrapers.rate_limiter import get_limiter
        limiter = get_limiter(self.source_name)
        await limiter.acquire()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_zip_integration/test_base_scraper_enhancements.py -v`
Expected: All PASS

- [ ] **Step 5: Run existing scraper tests for backward compatibility**

Run: `pytest tests/ -k "scraper or base" -v --tb=short`
Expected: All existing tests still pass

- [ ] **Step 6: Commit**

```bash
git add backend/scrapers/base.py tests/test_zip_integration/test_base_scraper_enhancements.py
git commit -m "feat: add extract_tech_stack, _infer_seniority, _normalize_salary, dedup_hash to BaseScraper"
```

---

## Chunk 3: Adapters — ATS Detector + Job Filter + Scraper Enhancements

**Depends on:** Chunk 1 (schema), Chunk 2 (base scraper)

### Task 3.1: ATS Detector

**Files:**
- Create: `backend/adapters/ats_detector.py`
- Test: `tests/test_zip_integration/test_ats_detector.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_zip_integration/test_ats_detector.py
"""Test ATS URL pattern detection."""
import pytest
from backend.adapters.ats_detector import (
    detect_ats_provider, get_company_slug_from_url, build_api_url,
)


class TestDetectATSProvider:
    def test_greenhouse(self):
        assert detect_ats_provider("https://boards.greenhouse.io/airbnb/jobs/123") == "greenhouse"

    def test_lever(self):
        assert detect_ats_provider("https://jobs.lever.co/stripe/abc-123") == "lever"

    def test_ashby(self):
        assert detect_ats_provider("https://jobs.ashbyhq.com/figma") == "ashby"

    def test_workday(self):
        assert detect_ats_provider("https://company.myworkdayjobs.com/en-US/external") == "workday"

    def test_linkedin(self):
        assert detect_ats_provider("https://www.linkedin.com/jobs/view/123456") == "linkedin"

    def test_indeed(self):
        assert detect_ats_provider("https://www.indeed.com/viewjob?jk=abc") == "indeed"

    def test_unknown_returns_none(self):
        assert detect_ats_provider("https://example.com/careers") is None

    def test_empty_url(self):
        assert detect_ats_provider("") is None

    def test_none_url(self):
        assert detect_ats_provider(None) is None

    def test_case_insensitive(self):
        assert detect_ats_provider("https://BOARDS.GREENHOUSE.IO/company") == "greenhouse"


class TestGetCompanySlug:
    def test_greenhouse_slug(self):
        assert get_company_slug_from_url("https://boards.greenhouse.io/airbnb/jobs/123", "greenhouse") == "airbnb"

    def test_lever_slug(self):
        assert get_company_slug_from_url("https://jobs.lever.co/stripe", "lever") == "stripe"

    def test_ashby_slug(self):
        assert get_company_slug_from_url("https://jobs.ashbyhq.com/figma", "ashby") == "figma"

    def test_empty_returns_none(self):
        assert get_company_slug_from_url("", "greenhouse") is None


class TestBuildApiUrl:
    def test_greenhouse_api(self):
        url = build_api_url("greenhouse", "airbnb")
        assert "boards-api.greenhouse.io" in url
        assert "airbnb" in url

    def test_lever_api(self):
        url = build_api_url("lever", "stripe")
        assert "api.lever.co" in url

    def test_ashby_api(self):
        url = build_api_url("ashby", "figma")
        assert "api.ashbyhq.com" in url

    def test_unknown_returns_none(self):
        assert build_api_url("workday", "company") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_zip_integration/test_ats_detector.py -v`

- [ ] **Step 3: Implement ats_detector.py**

Translate from zip's `server/adapters/ats_detector.py` (TypeScript) to Python. Use `re.search()` for URL pattern matching. Include all 15 ATS patterns from the spec. Implement `detect_ats_provider()`, `get_company_slug_from_url()`, `build_api_url()`.

- [ ] **Step 4: Run tests, verify pass**

Run: `pytest tests/test_zip_integration/test_ats_detector.py -v`

- [ ] **Step 5: Commit**

```bash
git add backend/adapters/ats_detector.py tests/test_zip_integration/test_ats_detector.py
git commit -m "feat: add ATS URL pattern detector for 15 providers"
```

---

### Task 3.2: Job Filter DSL

**Files:**
- Create: `backend/adapters/job_filter.py`
- Test: `tests/test_zip_integration/test_job_filter.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_zip_integration/test_job_filter.py
"""Test declarative job filter DSL."""
import pytest
from dataclasses import dataclass
from datetime import datetime, timedelta
from backend.adapters.job_filter import JobFilter


@dataclass
class MockJob:
    """Minimal job-like object for filter testing."""
    title: str = "Software Engineer"
    title_normalized: str = "software engineer"
    description_plain: str = "Build web apps with Python and React"
    location: str = "San Francisco, CA"
    location_normalized: str = "san francisco, ca"
    remote_type: str = "hybrid"
    employment_type: str = "full_time"
    seniority_level: str = "mid"
    salary_min: float = 100000
    salary_max: float = 150000
    posted_at: datetime = None
    company: str = "Acme Corp"
    company_normalized: str = "acme corp"
    tech_stack: list = None
    match_score: float = 85

    def __post_init__(self):
        if self.tech_stack is None:
            self.tech_stack = ["Python", "React"]
        if self.posted_at is None:
            self.posted_at = datetime.utcnow()


class TestJobFilterKeywords:
    def test_include_keyword_passes(self):
        f = JobFilter(keywords_include=["python"])
        passes, reasons = f.evaluate(MockJob())
        assert passes

    def test_include_keyword_fails(self):
        f = JobFilter(keywords_include=["golang"])
        passes, reasons = f.evaluate(MockJob())
        assert not passes
        assert any("missing_keyword" in r for r in reasons)

    def test_exclude_keyword_blocks(self):
        f = JobFilter(keywords_exclude=["python"])
        passes, reasons = f.evaluate(MockJob())
        assert not passes

    def test_include_any_passes_with_one(self):
        f = JobFilter(keywords_include_any=["golang", "react"])
        passes, _ = f.evaluate(MockJob())
        assert passes


class TestJobFilterSalary:
    def test_salary_min_passes(self):
        f = JobFilter(salary_min=90000)
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_salary_min_fails(self):
        f = JobFilter(salary_min=200000)
        passes, reasons = f.evaluate(MockJob())
        assert not passes


class TestJobFilterTechStack:
    def test_tech_all_passes(self):
        f = JobFilter(tech_stack_all=["Python"])
        passes, _ = f.evaluate(MockJob())
        assert passes

    def test_tech_all_fails(self):
        f = JobFilter(tech_stack_all=["Python", "Rust"])
        passes, _ = f.evaluate(MockJob())
        assert not passes


class TestJobFilterFromDict:
    def test_from_dict_creates_filter(self):
        f = JobFilter.from_dict({"keywords_include": ["python"], "salary_min": 100000})
        assert f.keywords_include == ["python"]
        assert f.salary_min == 100000

    def test_from_dict_empty(self):
        f = JobFilter.from_dict({})
        assert f.keywords_include == []


class TestFilterJobs:
    def test_filters_list(self):
        f = JobFilter(keywords_include=["python"])
        jobs = [MockJob(), MockJob(title="Go Developer", title_normalized="go developer", description_plain="Write Go code")]
        result = f.filter_jobs(jobs)
        assert len(result) == 1
```

- [ ] **Step 2: Run test, verify fails**
- [ ] **Step 3: Implement job_filter.py** — translate from zip's `server/adapters/job_filter.py`
- [ ] **Step 4: Run tests, verify pass**
- [ ] **Step 5: Commit**

```bash
git add backend/adapters/job_filter.py tests/test_zip_integration/test_job_filter.py
git commit -m "feat: add declarative job filter DSL"
```

---

### Task 3.3: Greenhouse Scraper Enhancements

**Files:**
- Modify: `backend/scrapers/greenhouse_scraper.py`
- Test: `tests/test_zip_integration/test_greenhouse_enhanced.py`

- [ ] **Step 1: Write failing tests** for pay_transparency parsing and questions extraction
- [ ] **Step 2: Run test, verify fails**
- [ ] **Step 3: Add `pay_transparency=true` to URL, parse `pay_input_ranges`, parse `questions[]`**
- [ ] **Step 4: Run tests, verify pass**
- [ ] **Step 5: Run existing greenhouse tests for backward compat**
- [ ] **Step 6: Commit**

### Task 3.4: Lever Scraper Enhancements

**Files:**
- Modify: `backend/scrapers/lever_scraper.py`
- Test: `tests/test_zip_integration/test_lever_enhanced.py`

- [ ] **Step 1-5:** Same pattern. Add `workplaceType` parsing → remote_type mapping.
- [ ] **Step 6: Commit**

### Task 3.5: Ashby Scraper Enhancements

**Files:**
- Modify: `backend/scrapers/ashby_scraper.py`
- Test: `tests/test_zip_integration/test_ashby_enhanced.py`

- [ ] **Step 1-5:** Same pattern. Parse `compensationTiers[].components[]` for Salary/Equity/Bonus. Use `isRemote` boolean. Multi-part location.
- [ ] **Step 6: Commit**

---

## Chunk 4: 3-Layer Deduplication Upgrade

**Depends on:** Chunk 1 (dedup_hash column), Chunk 2 (dedup_hash in normalize)

### Task 4.1: SimHash + Fuzzy Blocking + DedupResult

**Files:**
- Modify: `backend/enrichment/deduplicator.py`
- Test: `tests/test_zip_integration/test_dedup_upgrade.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_zip_integration/test_dedup_upgrade.py
"""Test 3-layer deduplication: exact hash, SimHash, fuzzy blocking."""
import pytest
from backend.enrichment.deduplicator import (
    compute_simhash, hamming_distance, deduplicate_batch, DedupResult,
)


class TestSimHash:
    def test_identical_texts_same_hash(self):
        h1 = compute_simhash("Senior Software Engineer at Google in San Francisco")
        h2 = compute_simhash("Senior Software Engineer at Google in San Francisco")
        assert h1 == h2

    def test_similar_texts_close_hash(self):
        h1 = compute_simhash("Senior Software Engineer at Google in San Francisco")
        h2 = compute_simhash("Senior Software Engineer at Google in Mountain View")
        assert hamming_distance(h1, h2) <= 10  # similar but not identical

    def test_different_texts_far_hash(self):
        h1 = compute_simhash("Senior Software Engineer at Google")
        h2 = compute_simhash("Junior Marketing Manager at Nike")
        assert hamming_distance(h1, h2) > 3

    def test_empty_text(self):
        h = compute_simhash("")
        assert isinstance(h, int)


class TestHammingDistance:
    def test_same_value(self):
        assert hamming_distance(0b1010, 0b1010) == 0

    def test_one_bit_different(self):
        assert hamming_distance(0b1010, 0b1011) == 1

    def test_all_bits_different(self):
        assert hamming_distance(0, 0xFF) == 8


class TestDedupResult:
    def test_has_expected_fields(self):
        r = DedupResult(kept=[], duplicates=[], stats={})
        assert hasattr(r, "kept")
        assert hasattr(r, "duplicates")
        assert hasattr(r, "stats")


class TestDeduplicateBatch:
    def test_exact_hash_dedup(self):
        jobs = [
            {"dedup_hash": "abc123", "title": "SWE", "company_name": "Google", "location": "SF", "description_clean": "Build stuff"},
            {"dedup_hash": "abc123", "title": "SWE", "company_name": "Google", "location": "SF", "description_clean": "Build stuff"},
        ]
        result = deduplicate_batch(jobs, existing_hashes=set())
        assert len(result.kept) == 1
        assert len(result.duplicates) == 1
        assert result.stats["l1_deduped"] == 1

    def test_no_duplicates(self):
        jobs = [
            {"dedup_hash": "abc", "title": "SWE", "company_name": "Google", "location": "SF", "description_clean": "Python"},
            {"dedup_hash": "def", "title": "PM", "company_name": "Meta", "location": "NY", "description_clean": "Product"},
        ]
        result = deduplicate_batch(jobs, existing_hashes=set())
        assert len(result.kept) == 2
        assert len(result.duplicates) == 0

    def test_existing_hash_filtered(self):
        jobs = [
            {"dedup_hash": "existing_one", "title": "SWE", "company_name": "Google", "location": "SF", "description_clean": "Stuff"},
        ]
        result = deduplicate_batch(jobs, existing_hashes={"existing_one"})
        assert len(result.kept) == 0
        assert result.stats["l1_deduped"] == 1

    def test_fuzzy_dedup_similar_titles(self):
        jobs = [
            {"dedup_hash": "aaa", "title": "Senior Software Engineer", "company_name": "Google", "location": "San Francisco", "description_clean": "A"},
            {"dedup_hash": "bbb", "title": "Sr. Software Engineer", "company_name": "Google", "location": "San Francisco", "description_clean": "B"},
        ]
        result = deduplicate_batch(jobs, existing_hashes=set())
        # Should detect as near-duplicate via fuzzy blocking
        assert len(result.duplicates) >= 1 or len(result.kept) <= 1

    def test_empty_batch(self):
        result = deduplicate_batch([], existing_hashes=set())
        assert len(result.kept) == 0
```

- [ ] **Step 2: Run test, verify fails**
- [ ] **Step 3: Implement** — add `DedupResult` dataclass, `compute_simhash()`, `hamming_distance()`, `deduplicate_batch()`. Modify existing `deduplicate_and_insert()` to call `deduplicate_batch()` internally.
- [ ] **Step 4: Run tests, verify pass**
- [ ] **Step 5: Run existing dedup tests for backward compat**

Run: `pytest tests/ -k "dedup" -v`

- [ ] **Step 6: Commit**

```bash
git add backend/enrichment/deduplicator.py tests/test_zip_integration/test_dedup_upgrade.py
git commit -m "feat: upgrade deduplicator to 3-layer pipeline — exact hash, SimHash, fuzzy blocking"
```

---

## Chunk 5: NLP Core + TF-IDF Scorer

**Depends on:** Chunk 1 only

### Task 5.1: NLP Core Utilities

**Files:**
- Create: `backend/nlp/core.py`
- Test: `tests/test_zip_integration/test_nlp_core.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_zip_integration/test_nlp_core.py
"""Test NLP core utilities: tokenize, freq_map, cosine_similarity, tfidf, keyphrases."""
import pytest
from backend.nlp.core import (
    tokenize, build_freq_map, cosine_similarity, tfidf_vectors,
    extract_keyphrases,
)


class TestTokenize:
    def test_basic(self):
        tokens = tokenize("Hello world, this is a test!")
        assert "hello" in tokens
        assert "world" in tokens
        assert "," not in tokens

    def test_empty(self):
        assert tokenize("") == []

    def test_removes_stopwords(self):
        tokens = tokenize("the quick brown fox jumps over the lazy dog")
        assert "the" not in tokens
        assert "quick" in tokens


class TestBuildFreqMap:
    def test_basic(self):
        fm = build_freq_map(["a", "b", "a", "c"])
        assert fm["a"] == 2
        assert fm["b"] == 1

    def test_empty(self):
        assert build_freq_map([]) == {}


class TestCosineSimilarity:
    def test_identical(self):
        d = {"python": 3, "react": 2}
        assert cosine_similarity(d, d) == pytest.approx(1.0, abs=0.01)

    def test_orthogonal(self):
        a = {"python": 1}
        b = {"java": 1}
        assert cosine_similarity(a, b) == pytest.approx(0.0)

    def test_partial_overlap(self):
        a = {"python": 3, "react": 2}
        b = {"python": 1, "java": 4}
        score = cosine_similarity(a, b)
        assert 0.0 < score < 1.0

    def test_empty_doc(self):
        assert cosine_similarity({}, {"python": 1}) == 0.0


class TestTFIDFVectors:
    def test_produces_vectors(self):
        corpus = [
            "python machine learning tensorflow",
            "java spring boot microservices",
            "python django web development",
        ]
        vectors = tfidf_vectors(corpus)
        assert len(vectors) == 3
        # "python" appears in 2/3 docs → lower IDF than "java" (1/3)
        assert isinstance(vectors[0], dict)


class TestExtractKeyphrases:
    def test_extracts_from_text(self):
        text = "We need a senior Python engineer with experience in machine learning and distributed systems."
        phrases = extract_keyphrases(text, top_n=5)
        assert len(phrases) <= 5
        assert len(phrases) > 0

    def test_empty_text(self):
        assert extract_keyphrases("") == []
```

- [ ] **Step 2: Run test, verify fails**
- [ ] **Step 3: Implement core.py** — pure Python NLP utilities. `tokenize()` with basic stopword removal, `build_freq_map()`, `cosine_similarity()` using dot product / magnitude, `tfidf_vectors()` with IDF calculation across corpus, `extract_keyphrases()` using TF-IDF top-N.
- [ ] **Step 4: Run tests, verify pass**
- [ ] **Step 5: Commit**

```bash
git add backend/nlp/core.py tests/test_zip_integration/test_nlp_core.py
git commit -m "feat: add NLP core utilities — tokenize, cosine_similarity, tfidf_vectors"
```

---

### Task 5.2: TF-IDF Scorer

**Files:**
- Create: `backend/nlp/tfidf_scorer.py`
- Test: `tests/test_zip_integration/test_tfidf_scorer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_zip_integration/test_tfidf_scorer.py
"""Test TF-IDF job-resume matching scorer."""
import pytest
from backend.nlp.tfidf_scorer import compute_tfidf_score, ScoringResult


class TestComputeTfidfScore:
    def test_high_match_resume(self):
        job = {
            "title": "Senior Python Engineer",
            "description_clean": "We need a senior Python engineer with experience in FastAPI, PostgreSQL, and AWS.",
            "skills_required": ["Python", "FastAPI", "PostgreSQL", "AWS"],
            "tech_stack": ["Python", "FastAPI"],
        }
        resume = {
            "text": "Senior Python developer with 5 years experience. Built REST APIs with FastAPI and PostgreSQL. Deployed on AWS.",
            "skills": ["Python", "FastAPI", "PostgreSQL", "AWS", "Docker"],
        }
        result = compute_tfidf_score(job, resume)
        assert isinstance(result, ScoringResult)
        assert result.score >= 60
        assert len(result.skill_matches) >= 3

    def test_low_match_resume(self):
        job = {
            "title": "Senior Java Engineer",
            "description_clean": "We need a Java developer with Spring Boot and Kubernetes.",
            "skills_required": ["Java", "Spring Boot", "Kubernetes"],
            "tech_stack": ["Java", "Spring Boot"],
        }
        resume = {
            "text": "Marketing manager with experience in social media campaigns.",
            "skills": ["Marketing", "Social Media"],
        }
        result = compute_tfidf_score(job, resume)
        assert result.score < 50
        assert len(result.skill_gaps) > 0

    def test_score_clamped_10_99(self):
        result = compute_tfidf_score(
            {"title": "", "description_clean": "", "skills_required": [], "tech_stack": []},
            {"text": "", "skills": []},
        )
        assert 10 <= result.score <= 99

    def test_scoring_result_has_breakdown(self):
        result = compute_tfidf_score(
            {"title": "SWE", "description_clean": "Python", "skills_required": ["Python"], "tech_stack": ["Python"]},
            {"text": "Python developer", "skills": ["Python"]},
        )
        assert "base_cosine" in result.weight_breakdown
        assert "skill_bonus" in result.weight_breakdown

    def test_ai_ml_boost(self):
        """AI/ML keywords should boost the score."""
        job = {
            "title": "ML Engineer",
            "description_clean": "Machine learning engineer working with TensorFlow and PyTorch",
            "skills_required": ["Python", "TensorFlow", "PyTorch"],
            "tech_stack": ["TensorFlow", "PyTorch"],
        }
        resume = {
            "text": "ML engineer with TensorFlow and PyTorch experience. Built ML pipelines.",
            "skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning"],
        }
        result = compute_tfidf_score(job, resume)
        assert result.score >= 65  # AI/ML multiplier should boost
```

- [ ] **Step 2: Run test, verify fails**
- [ ] **Step 3: Implement tfidf_scorer.py** — `ScoringResult` dataclass, `compute_tfidf_score()` with 4-component assembly formula from spec Section 4.2. Uses `nlp.core` for tokenize/cosine_similarity.
- [ ] **Step 4: Run tests, verify pass**
- [ ] **Step 5: Commit**

```bash
git add backend/nlp/tfidf_scorer.py tests/test_zip_integration/test_tfidf_scorer.py
git commit -m "feat: add TF-IDF job-resume scorer with 4-component algorithm"
```

---

## Chunk 6: Resume System — Parser, Document Manager, Council Scorer, Router

**Depends on:** Chunk 1 (models), Chunk 5 is nice-to-have but not required

### Task 6.1: Resume Parser

**Files:**
- Create: `backend/resume/parser.py`
- Test: `tests/test_zip_integration/test_resume_parser.py`

- [ ] **Step 1: Write failing tests** for `extract_resume_text()` (TXT, MD paths) and `parse_resume_layout_aware()` (mocked LLM).
- [ ] **Step 2: Run test, verify fails**
- [ ] **Step 3: Implement parser.py** — translate from zip's `server/resume/parser.py`. Support PDF (pdfplumber), DOCX (python-docx), MD/TXT (direct read), LaTeX (pylatexenc). `parse_resume_layout_aware()` with 5 parallel LLM sub-tasks via httpx to OpenRouter.
- [ ] **Step 4: Run tests, verify pass**
- [ ] **Step 5: Commit**

### Task 6.2: Resume Document Manager

**Files:**
- Create: `backend/resume/document_manager.py`
- Test: `tests/test_zip_integration/test_document_manager.py`

- [ ] **Step 1: Write failing tests** for `ingest_resume()` (stores file on disk, creates ResumeDocument) and `render_resume()` (MD→HTML, PDF→fpdf2).
- [ ] **Step 2: Run test, verify fails**
- [ ] **Step 3: Implement document_manager.py** — file storage at `data/resumes/`, ULID generation, multi-format ingestion and rendering.
- [ ] **Step 4: Run tests, verify pass**
- [ ] **Step 5: Commit**

### Task 6.3: Council Scorer

**Files:**
- Create: `backend/resume/council.py`
- Test: `tests/test_zip_integration/test_council_scorer.py`

- [ ] **Step 1: Write failing tests** with mocked LLM responses for 3-stage council evaluation.
- [ ] **Step 2: Run test, verify fails**
- [ ] **Step 3: Implement council.py** — `DimensionScore` and `CouncilScore` dataclasses, `evaluate_resume_council()` with 3 parallel model calls via httpx/OpenRouter, scoring aggregation.
- [ ] **Step 4: Run tests, verify pass**
- [ ] **Step 5: Commit**

### Task 6.4: Resume Router

**Files:**
- Create: `backend/routers/resume.py`
- Modify: `backend/routers/settings.py:89-135` (remove old upload route)
- Test: `tests/test_zip_integration/test_resume_router.py`

- [ ] **Step 1: Write failing tests** for all 7 resume endpoints (upload, list, preview, tailored preview, download, update, delete).
- [ ] **Step 2: Run test, verify fails**
- [ ] **Step 3: Implement resume router** — FastAPI router with `/api/resume/` prefix. Upload handles multi-format (PDF/DOCX/MD/TEX), creates ResumeVersion, stores file on disk. Other endpoints query/modify ResumeVersion records.
- [ ] **Step 4: Remove old upload route** from `backend/routers/settings.py` (delete lines 89-135).
- [ ] **Step 5: Run tests, verify pass**
- [ ] **Step 6: Run existing settings tests for backward compat**
- [ ] **Step 7: Commit**

```bash
git add backend/resume/ backend/routers/resume.py backend/routers/settings.py tests/test_zip_integration/test_resume_*.py tests/test_zip_integration/test_document_manager.py tests/test_zip_integration/test_council_scorer.py
git commit -m "feat: add resume system — parser, document manager, council scorer, REST API"
```

---

## Chunk 7: NLP Tools — Gap Analyzer, Resume Tailor, Cover Letter, Interview Prep

**Depends on:** Chunk 5 (NLP core), Chunk 6 (resume parser for parsed resume data)

### Task 7.1: Gap Analyzer

**Files:**
- Create: `backend/nlp/gap_analyzer.py`
- Test: `tests/test_zip_integration/test_gap_analyzer.py`

- [ ] **Step 1: Write failing tests** — test `analyze_gaps()` with mock resume_parsed and job_data, verify matched_skills, missing_skills, transferable_skills.
- [ ] **Step 2: Run test, verify fails**
- [ ] **Step 3: Implement gap_analyzer.py** — `GapAnalysis` dataclass, `analyze_gaps()` using NLP core cosine similarity on each resume bullet vs JD requirements.
- [ ] **Step 4: Run tests, verify pass**
- [ ] **Step 5: Commit**

### Task 7.2: Resume Tailor

**Files:**
- Create: `backend/nlp/resume_tailor.py`
- Test: `tests/test_zip_integration/test_resume_tailor.py`

- [ ] **Step 1: Write failing tests** with mocked LLM responses.
- [ ] **Step 2-5: Implement, test, commit.** `TailoredResume` dataclass, `tailor_resume()` calling OpenRouter to enhance bullets based on gap_analysis.

### Task 7.3: Cover Letter Generator

**Files:**
- Create: `backend/nlp/cover_letter.py`
- Test: `tests/test_zip_integration/test_cover_letter.py`

- [ ] **Step 1-5: Same TDD pattern.** `CoverLetter` dataclass, `generate_cover_letter()` with 4 style options, uses gap_analysis data.

### Task 7.4: Interview Prep

**Files:**
- Create: `backend/nlp/interview_prep.py`
- Test: `tests/test_zip_integration/test_interview_prep.py`

- [ ] **Step 1-5: Same TDD pattern.** `InterviewPrep` dataclass, `generate_interview_prep()` producing STAR stories and likely questions.

---

## Chunk 8: Auto-Apply System

**Depends on:** Chunk 3 (ATS detector), Chunk 6 (resume document manager)

### Task 8.1: Application Profile

**Files:**
- Create: `backend/auto_apply/profile.py`
- Test: `tests/test_zip_integration/test_auto_apply_profile.py`

- [ ] **Step 1-5: TDD.** `ApplicationProfile` dataclass with all fields from spec Section 5.5. `load_profile()` and `save_profile()` using UserProfile.application_profile JSON column.

### Task 8.2: Generic ATS Filler

**Files:**
- Create: `backend/auto_apply/ats_filler.py`
- Test: `tests/test_zip_integration/test_ats_filler.py`

- [ ] **Step 1-5: TDD** with mocked Playwright pages. Fuzzy label matching, field detection, form filling for Greenhouse/Lever/Ashby single-page forms.

### Task 8.3: Workday Form Controller

**Files:**
- Create: `backend/auto_apply/workday_filler.py`
- Test: `tests/test_zip_integration/test_workday_filler.py`

- [ ] **Step 1-5: TDD** with mocked Playwright pages. Multi-page Workday flow using `data-automation-id` selectors. `WorkdayFiller` class with `fill_application()`.

### Task 8.4: Playwright Apply + Orchestrator

**Files:**
- Create: `backend/auto_apply/playwright_apply.py`
- Create: `backend/auto_apply/orchestrator.py`
- Test: `tests/test_zip_integration/test_auto_apply_orchestrator.py`

- [ ] **Step 1-5: TDD.** `run_application()` function, `auto_apply()` orchestrator that routes to WorkdayFiller or GenericATSFiller based on ATS detection.

### Task 8.5: Auto-Apply Router

**Files:**
- Create: `backend/routers/auto_apply.py`
- Test: `tests/test_zip_integration/test_auto_apply_router.py`

- [ ] **Step 1-5: TDD.** 5 endpoints: run, analyze, pause, GET profile, POST profile. Wire to orchestrator and profile modules.

---

## Chunk 9: Integration Wiring

**Depends on:** All previous chunks

### Task 9.1: Copilot Router Enhancement

**Files:**
- Modify: `backend/routers/copilot.py` (add tailorResume + NLP delegation)
- Test: `tests/test_zip_integration/test_copilot_enhanced.py`

- [ ] **Step 1: Write failing tests** — test tailorResume tool type, NLP module delegation fallback.
- [ ] **Step 2: Run test, verify fails**
- [ ] **Step 3: Add `tailorResume` to TOOL_PROMPTS, add NLP module delegation logic** with try/import fallback to existing prompt templates.
- [ ] **Step 4: Run tests, verify pass**
- [ ] **Step 5: Run existing copilot tests**
- [ ] **Step 6: Commit**

### Task 9.2: Embedding Enhancement

**Files:**
- Modify: `backend/enrichment/embedding.py:68-106` (add tfidf_score computation)
- Test: `tests/test_zip_integration/test_embedding_enhanced.py`

- [ ] **Step 1: Write failing test** — `score_jobs_batch()` now also sets `tfidf_score` when NLP module available.
- [ ] **Step 2-5: Implement with import guard, test, commit.**

### Task 9.3: Scheduler Enhancement

**Files:**
- Modify: `backend/scheduler.py:209-264` (add tfidf_batch and dedup_backfill jobs)

- [ ] **Step 1: Add** `run_tfidf_batch()` function and `backfill_dedup_hashes()` function.
- [ ] **Step 2: Add scheduler jobs** after line 262:
```python
scheduler.add_job(run_tfidf_batch, 'interval', minutes=20, id='tfidf_batch', replace_existing=True)
scheduler.add_job(backfill_dedup_hashes, 'date', id='dedup_backfill', replace_existing=True)
```
- [ ] **Step 3: Test and commit**

### Task 9.4: Main.py + Router Init Wiring

**Files:**
- Modify: `backend/main.py:79-92` (add router imports)
- Modify: `backend/routers/__init__.py` (add imports)

- [ ] **Step 1: Add imports and router registrations**

In `backend/main.py`, add after line 92:
```python
app.include_router(resume.router)
app.include_router(auto_apply.router)
```

Add council-score endpoint to `backend/routers/jobs.py`.

- [ ] **Step 2: Run full test suite**

Run: `pytest tests/ -v --tb=short`
Expected: All tests pass (existing 822+ plus all new zip integration tests)

- [ ] **Step 3: Commit**

```bash
git add backend/main.py backend/routers/__init__.py backend/routers/jobs.py backend/routers/copilot.py backend/enrichment/embedding.py backend/scheduler.py
git commit -m "feat: wire zip integration — routers, embedding, scheduler, main.py"
```

---

### Task 9.5: Final Backward Compatibility Verification

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -v --tb=short 2>&1 | tail -20`
Expected: All tests pass

- [ ] **Step 2: Verify all new endpoints respond**

Run backend: `uvicorn backend.main:app --port 8000`
Test endpoints exist: `curl http://localhost:8000/api/resume/versions`, `curl http://localhost:8000/api/auto-apply/profile`

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: zip integration complete — 23 new files, 15 modified, full test coverage"
```

---

## Execution Summary

| Chunk | Tasks | Parallel? | Depends On |
|-------|-------|-----------|------------|
| 1. Foundation | 4 | First | — |
| 2. Scraper Infra | 2 | Yes | Chunk 1 |
| 3. Adapters | 5 | Yes | Chunk 1 |
| 4. Dedup | 1 | Yes | Chunk 1, 2 |
| 5. NLP Core | 2 | Yes | Chunk 1 |
| 6. Resume System | 4 | Yes | Chunk 1 |
| 7. NLP Tools | 4 | Yes | Chunk 5, 6 |
| 8. Auto-Apply | 5 | Yes | Chunk 3, 6 |
| 9. Wiring | 5 | Last | All |
| **Total** | **32 tasks** | | |

**Optimal subagent allocation:**
- Phase 1: 1 agent → Chunk 1 (Foundation)
- Phase 2: 5 parallel agents → Chunks 2, 3, 4, 5, 6
- Phase 3: 2 parallel agents → Chunks 7, 8
- Phase 4: 1 agent → Chunk 9 (Wiring)
