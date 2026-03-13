# Zip Integration — Surgical Merge Design Spec

**Date:** 2026-03-13
**Branch:** `phase7a/db-migrations-core` (or new feature branch)
**Source:** `jobradar_project.zip` (TypeScript/Express implementation)
**Strategy:** Approach A — Surgical Merge. Enhance existing architecture in-place.
**Scope:** 23 new files, 15 modified files, 5 new packages.

---

## 1. Scraper Layer Enhancements

### 1.1 BaseScraper Enhancements (`backend/scrapers/base.py` — MODIFY)

Add to `normalize()` output:
- `dedup_hash`: SHA256 of `f"{title.lower().strip()}|{company.lower().strip()}|{location.lower().strip()}"`. Always computed — never None. This flows through the existing insert path (`deduplicate_and_insert()`) without glue code since it's part of the normalized dict.
- `tech_stack`: pre-enrichment extraction via `extract_tech_stack(description_clean)`
- `experience_level`: inferred via `_infer_seniority(title)` if not already set

New methods:
```python
@staticmethod
def extract_tech_stack(description: str) -> list[str]:
    """Regex match against ~40 tech terms, return top 15."""

@staticmethod
def _infer_seniority(title: str) -> str | None:
    """Keyword-based: intern/entry/mid/senior/lead/staff/principal/exec."""

@staticmethod
def _normalize_salary(min_val, max_val, interval="year") -> tuple[float, float]:
    """Hourly → annual (×2080), cents → dollars if needed."""
```

### 1.2 GreenhouseScraper (`backend/scrapers/greenhouse_scraper.py` — MODIFY)

- Add `pay_transparency=true` to API URL
- Parse `pay_input_ranges[0].{min_cents, max_cents}` → divide by 100 → salary_min/max
- Parse `questions[]` array → store as `apply_questions` JSON
- Department already handled

### 1.3 LeverScraper (`backend/scrapers/lever_scraper.py` — MODIFY)

- Parse `workplaceType` field → direct remote_type mapping ("remote"/"hybrid"/"onsite")
- Fallback to location text detection (existing behavior) if workplaceType absent
- Better commitment edge cases

### 1.4 AshbyScraper (`backend/scrapers/ashby_scraper.py` — MODIFY)

- Parse `compensationTiers[].components[]`:
  - `compensationType == "Salary"` → salary_min/max
  - `compensationType == "EquityPercentage"` → stored in new fields (future)
  - `compensationType == "Bonus"` → has_bonus flag
- Use `isRemote` boolean in addition to location text
- Multi-part location from `addressLocality/addressRegion/addressCountry`
- Fallback to `compensationTierSummary` or `scrapeableCompensationSalarySummary`

### 1.5 Rate Limiter (`backend/scrapers/rate_limiter.py` — NEW)

Token bucket + circuit breaker pattern from zip's `server/adapters/rate_limit.py`.

```python
@dataclass
class RatePolicy:
    rps: float                    # requests per second
    backoff_base: float           # exponential backoff base (seconds)
    max_retries: int              # max retry attempts
    circuit_threshold: int        # consecutive failures to open circuit
    circuit_cooldown: float       # seconds before half-open retry (default 300)

class RateLimiter:
    async def acquire() -> None        # token bucket + circuit check
    def record_success() -> None       # reset failure counter
    def record_failure() -> None       # increment; open circuit if threshold hit
    async def with_retry(coro_factory) # execute with exponential backoff

class CircuitOpenError(Exception): ...

def get_limiter(source_id: str) -> RateLimiter  # factory with cached instances
```

Per-site policies (production-calibrated):
- Greenhouse, Lever: 10 RPS, 1.0s backoff, 3 retries
- Ashby: 5 RPS, 1.5s backoff, 3 retries
- SerpApi: 2 RPS, 1.0s backoff, 3 retries
- Generic fallback: 0.1 RPS, 5.0s backoff, 2 retries
- Future (not yet implemented): Workday 1 RPS, iCIMS 1 RPS, LinkedIn 0.25 RPS

All scrapers replace `await asyncio.sleep(self.rate_limit_delay)` with `await limiter.acquire()`.

---

## 2. 3-Layer Deduplication Upgrade

### `backend/enrichment/deduplicator.py` — MODIFY

**Layer 1 — Exact Hash:**
- Compare `dedup_hash` field (SHA256 of title|company|location normalized)
- O(1) lookup against existing hash set
- Confidence: 1.0

**Layer 2 — SimHash (64-bit):**
- Compute fingerprint from `description_clean[:500]` using 3-gram shingles → MD5 → bit vector
- Hamming distance <= 3 bits → near-duplicate
- Confidence: `1.0 - distance / 64.0`
- In-memory, no DB query

**Layer 3 — Fuzzy Blocking:**
- Bucket by first 2 chars of company + first 2 chars of location
- Within bucket: `rapidfuzz.token_sort_ratio(title_a, title_b)`
- Score >= 90: confidence = score/100
  - >= 0.95: auto-merge (keep richer description)
  - 0.70-0.95: flag as possible_duplicate
- O(n/k^2) instead of O(n^2)

New functions:
```python
@dataclass
class DedupResult:
    kept: list[dict]
    duplicates: list[tuple]  # (dup, canonical, confidence, layer)
    stats: dict              # input, output, l1/l2/l3 counts

def deduplicate_batch(jobs: list[dict], existing_hashes: set[str]) -> DedupResult
def compute_simhash(text: str) -> int  # 64-bit fingerprint
def hamming_distance(a: int, b: int) -> int
```

Existing `deduplicate_and_insert()` preserved — calls `deduplicate_batch()` internally.

---

## 3. New Modules

### 3.1 ATS Detector (`backend/adapters/ats_detector.py` — NEW)

URL pattern matching for 15 ATS providers.

```python
def detect_ats_provider(url: str) -> str | None
def get_company_slug_from_url(url: str, ats: str) -> str | None
def build_api_url(ats: str, slug: str) -> str | None
```

Patterns: greenhouse, lever, ashby, workday, icims, smartrecruiters, workable, jobvite, bamboohr, taleo, successfactors, linkedin, indeed, ziprecruiter, glassdoor.

### 3.2 Job Filter DSL (`backend/adapters/job_filter.py` — NEW)

```python
@dataclass
class JobFilter:
    keywords_include: list[str]
    keywords_include_any: list[str]
    keywords_exclude: list[str]
    locations: list[str]
    remote_types: list[str]
    employment_types: list[str]
    seniority_levels: list[str]
    salary_min: float | None
    salary_max: float | None
    posted_within_days: int | None
    companies_include: list[str]
    companies_exclude: list[str]
    tech_stack_all: list[str]
    tech_stack_any: list[str]
    min_match_score: float | None

    def evaluate(self, job) -> tuple[bool, list[str]]
    def filter_jobs(self, jobs) -> list
    @classmethod
    def from_dict(cls, d: dict) -> "JobFilter"
```

### 3.3 Resume Parser (`backend/resume/parser.py` — NEW)

Layout-aware PDF extraction + parallel LLM structured extraction.

```python
def extract_resume_text(file_path: str) -> str
    # PDF: pdfplumber + bounding box reordering
    # DOCX: python-docx paragraphs
    # MD/TXT: direct read
    # LaTeX: pylatexenc (latex2text module)

async def parse_resume_layout_aware(text: str, api_key: str, model: str) -> dict
    # 5 parallel sub-tasks: basic_info, work_experience, education, skills, projects
```

### 3.4 Council Scorer (`backend/resume/council.py` — NEW)

3-stage, 3-model parallel evaluation.

```python
@dataclass
class DimensionScore:
    grade: str          # A/B/C/D
    score: int          # 0-100
    rationale: str
    gaps: list[str]
    suggestions: list[str]

@dataclass
class CouncilScore:
    skill_alignment: DimensionScore
    experience_level: DimensionScore
    impact_language: DimensionScore
    ats_keyword_density: DimensionScore
    structural_quality: DimensionScore
    cultural_signals: DimensionScore
    growth_trajectory: DimensionScore
    overall_grade: str
    overall_score: int
    top_gaps: list[str]
    missing_keywords: list[str]
    strong_points: list[str]
    suggested_bullets: list[str]
    council_consensus: float  # 0-1

async def evaluate_resume_council(resume_text, job_description, api_key) -> CouncilScore
```

Models via OpenRouter: `anthropic/claude-3-5-haiku` + `openai/gpt-4o-mini` + `google/gemini-flash-1.5` (~$0.004/eval).
Triggered on-demand via `POST /api/jobs/{job_id}/council-score` (handled in `backend/routers/jobs.py` — MODIFY).

### 3.5 Resume Document Manager (`backend/resume/document_manager.py` — NEW)

Multi-format resume storage + rendering.

**Storage:** Resume files are stored on disk at `data/resumes/{id}.{ext}` with the DB `ResumeVersion` record storing the relative path (no blobs in SQLite — avoids DB bloat for 5MB+ files). The `data/resumes/` directory is created on startup.

```python
@dataclass
class ResumeDocument:
    id: str             # ULID
    filename: str
    format: str         # pdf/docx/md/tex
    file_path: str      # relative path: data/resumes/{id}.{ext}
    parsed_text: str
    parsed_structured: dict
    version_label: str
    is_default: bool

def ingest_resume(file_bytes: bytes, filename: str) -> ResumeDocument
def render_resume(document_id, output_format, tailored_data=None) -> bytes
    # MD → Jinja2 template
    # PDF → markdown → fpdf2 (pure Python, no system deps) or WeasyPrint if available
    # DOCX → python-docx builder
    # LaTeX → Jinja2 LaTeX template
```

**PDF rendering note:** WeasyPrint requires system-level libraries (Pango, Cairo) that are difficult to install on Windows. Primary PDF renderer is `fpdf2` (pure Python, pip-installable). WeasyPrint is an optional enhanced renderer — used if detected, graceful fallback to fpdf2 if not.

### 3.6 Playwright Browser Lifecycle (`backend/auto_apply/` — lifecycle notes)

- Playwright uses a persistent browser context stored at `data/browser_profile/`
- Browser is launched on first auto-apply request, reused across applications
- `headless=False` — user always sees the visible browser
- Browser context is closed after 5 minutes of inactivity (background task)
- If user closes the browser window, the next auto-apply request launches a fresh instance
- Session cookies and login state persist across fills within the same context

---

## 4. NLP Engine (`backend/nlp/`)

### 4.1 Core Utilities (`backend/nlp/core.py` — NEW)

```python
def tokenize(text: str) -> list[str]
def build_freq_map(tokens: list[str]) -> dict[str, int]
def cosine_similarity(doc_a: dict, doc_b: dict) -> float
def tfidf_vectors(corpus: list[str]) -> list[dict]
def extract_keyphrases(text: str, top_n=20) -> list[str]
def semantic_similarity(text_a: str, text_b: str) -> float
def extract_entities(text: str) -> dict
```

### 4.2 TF-IDF Scorer (`backend/nlp/tfidf_scorer.py` — NEW)

4-component algorithm with assembly formula:

1. **Base cosine** — TF-IDF cosine similarity between resume and job description
2. **Skill overlap bonus** — +3 per direct skill match, +2 per mention match (found in description but not in required list)
3. **Tech weight adjustments** — AI/ML multipliers (2.5-3.0x), disqualifier penalties (-5 to -10)
4. **Assembly:** `raw = (base_cosine × 0.4) + (skill_bonus × 1.2) + (weight_adj × 0.5) + 40`, clamped to 10-99

The formula is empirically tuned, not a normalized weighted average — the +40 constant ensures a reasonable baseline, and the multipliers are calibrated so typical scores land in the 40-90 range.

```python
@dataclass
class ScoringResult:
    score: int
    skill_matches: list[str]
    skill_gaps: list[str]
    keyword_overlaps: list[str]
    disqualifiers: list[str]
    weight_breakdown: dict

def compute_tfidf_score(job, resume) -> ScoringResult
```

### 4.3 Gap Analyzer (`backend/nlp/gap_analyzer.py` — NEW)

```python
@dataclass
class GapAnalysis:
    matched_skills: list[dict]          # {skill, confidence}
    missing_skills: list[str]
    transferable_skills: list[dict]     # {have, need, relevance}
    keyword_density: float
    experience_fit: float
    ats_optimization_suggestions: list[str]
    strongest_bullets: list[str]
    weakest_sections: list[str]

def analyze_gaps(resume_parsed, job_data) -> GapAnalysis
```

Bullet-level cosine similarity — compares each resume bullet against each JD requirement.

### 4.4 Resume Tailor (`backend/nlp/resume_tailor.py` — NEW)

```python
@dataclass
class TailoredResume:
    summary: str
    reordered_experience: list[dict]
    enhanced_bullets: list[dict]
    skills_section: list[str]
    ats_score_before: int
    ats_score_after: int

async def tailor_resume(resume_parsed, job_data, gap_analysis, api_key) -> TailoredResume
```

LLM fills specific identified gaps. Never fabricates experience.

### 4.5 Cover Letter Generator (`backend/nlp/cover_letter.py` — NEW)

```python
@dataclass
class CoverLetter:
    content: str
    key_points_addressed: list[str]
    skills_highlighted: list[str]
    company_research_notes: list[str]
    word_count: int
    reading_level: str

async def generate_cover_letter(resume_parsed, job_data, gap_analysis, style, api_key) -> CoverLetter
```

Styles: "professional" | "conversational" | "technical" | "storytelling".
NLP-driven: uses gap_analysis.matched_skills, strongest_bullets, keyword_overlaps.

### 4.6 Interview Prep (`backend/nlp/interview_prep.py` — NEW)

```python
@dataclass
class InterviewPrep:
    likely_questions: list[dict]
    star_stories: list[dict]
    technical_topics: list[str]
    company_talking_points: list[str]
    questions_to_ask: list[str]
    red_flag_responses: list[dict]

async def generate_interview_prep(resume_parsed, job_data, gap_analysis, api_key) -> InterviewPrep
```

---

## 5. Auto-Apply System (`backend/auto_apply/`)

### 5.1 Playwright Form Filler (`backend/auto_apply/playwright_apply.py` — NEW)

```python
@dataclass
class ApplicationResult:
    success: bool
    fields_filled: dict
    fields_missed: list[str]
    screenshots: list[str]      # base64
    ats_provider: str
    error: str | None

async def run_application(apply_url, profile, resume_bytes, cover_letter_text, submit=False) -> ApplicationResult
```

Default `submit=False`. Fetches resume PDF render from ResumeVersion. Uses ats_detector for routing.

### 5.2 Workday Form Controller (`backend/auto_apply/workday_filler.py` — NEW)

Dedicated multi-page Workday automation (visible browser, user can watch/intervene).

```python
class WorkdayFiller:
    async def fill_application(url, auto_advance=True, submit=False) -> WorkdayResult

@dataclass
class WorkdayResult:
    pages_completed: list[str]
    fields_filled: dict
    fields_skipped: list[str]
    custom_questions_answered: list[dict]
    screenshots: list[str]
    needs_review: list[str]
    browser_session_id: str
```

Multi-page flow: My Information → My Experience → My Education → Application Questions → Resume/CV → Review.
Uses `data-automation-id` selectors (stable). Work experience + education auto-filled from resume_parsed.
500ms delays, yellow highlight on each field, pause capability.

### 5.3 Generic ATS Filler (`backend/auto_apply/ats_filler.py` — NEW)

Single-page form filler for Greenhouse/Lever/Ashby. Fuzzy label matching for field detection.

### 5.4 Orchestrator (`backend/auto_apply/orchestrator.py` — NEW)

```python
async def auto_apply(job_id, resume_id=None, submit=False) -> ApplicationResult
    # 1. Fetch job URL
    # 2. detect_ats_provider(url)
    # 3. Route to WorkdayFiller or GenericATSFiller
    # 4. Generate cover letter if needed
    # 5. Select best resume version
    # 6. Run filler
    # 7. Store ApplicationAttempt
```

### 5.5 Profile (`backend/auto_apply/profile.py` — NEW)

`ApplicationProfile` dataclass: name, email, phone, linkedin, github, portfolio, location, work_authorization, years_experience, education_summary, current_title, desired_salary.

---

## 6. Schema Changes

### Modified Models

**Job** — add columns:
- `dedup_hash` String(64), nullable (backfilled on next scrape)
- `tfidf_score` Float, nullable
- `council_scores` JSON, nullable
- `apply_questions` JSON, nullable

**UserProfile** — add columns:
- `resume_parsed` JSON, nullable
- `application_profile` JSON, nullable

### New Models

**ResumeVersion:**
```
id              String(26) PK (ULID)
filename        String(255)
format          String(8)
file_path       String(512)     # relative path: data/resumes/{id}.{ext}
parsed_text     Text
parsed_structured JSON
version_label   String(255)
is_default      Boolean default=False
created_at      DateTime
updated_at      DateTime
```

Note: File bytes stored on disk at `data/resumes/`, not in the DB. This avoids SQLite bloat from 5MB+ resume files.

**ApplicationAttempt:**
```
id              Integer PK auto
job_id          String(64) FK → jobs.job_id
resume_version_id String(26) FK → resume_versions.id, nullable
ats_provider    String(32)
status          String(32)
fields_filled   JSON
fields_skipped  JSON
screenshots     JSON
custom_answers  JSON
started_at      DateTime
completed_at    DateTime nullable
error           Text nullable
```

### Migration

Via Phase 7A migration runner pattern — `ALTER TABLE ADD COLUMN` with `PRAGMA table_info` guard.

---

## 7. API Endpoints (New & Modified)

### New Endpoints

#### Council Score
```
POST /api/jobs/{job_id}/council-score
  Request:  (no body — uses job + resume from DB)
  Response: CouncilScoreResponse {
    skill_alignment: DimensionScoreSchema
    experience_level: DimensionScoreSchema
    impact_language: DimensionScoreSchema
    ats_keyword_density: DimensionScoreSchema
    structural_quality: DimensionScoreSchema
    cultural_signals: DimensionScoreSchema
    growth_trajectory: DimensionScoreSchema
    overall_grade: str
    overall_score: int
    top_gaps: list[str]
    missing_keywords: list[str]
    strong_points: list[str]
    suggested_bullets: list[str]
    council_consensus: float
  }
```
Where `DimensionScoreSchema = { grade: str, score: int, rationale: str, gaps: list[str], suggestions: list[str] }`

Added to `backend/routers/jobs.py` (MODIFY) — a new route handler within the existing jobs router.

#### Resume Endpoints (new router: `backend/routers/resume.py`)
```
POST /api/resume/upload
  Request:  multipart file (PDF/DOCX/MD/TEX, max 10MB)
  Response: ResumeVersionResponse { id, filename, format, version_label, is_default, parsed_text_preview: str (first 500 chars), created_at }

GET /api/resume/versions
  Response: list[ResumeVersionResponse]

GET /api/resume/{id}/preview
  Response: { html: str }  # rendered HTML for display

GET /api/resume/{id}/preview/tailored?job_id=xxx
  Response: { html: str, ats_score_before: int, ats_score_after: int }

GET /api/resume/{id}/download?format=pdf|docx|md|tex
  Response: file download (Content-Disposition: attachment)

PATCH /api/resume/{id}
  Request:  { version_label?: str, is_default?: bool }
  Response: ResumeVersionResponse

DELETE /api/resume/{id}
  Response: { deleted: true }
```

**Route conflict resolution:** The existing `POST /api/settings/resume/upload` in `backend/routers/settings.py` is **removed** (lines 89-135 deleted). The new `POST /api/resume/upload` in `backend/routers/resume.py` replaces it with multi-format support and ResumeVersion creation. Existing frontend calls to the old endpoint must be updated to the new path.

#### Auto-Apply Endpoints (new router: `backend/routers/auto_apply.py`)
```
POST /api/auto-apply/run
  Request:  AutoApplyRunRequest { job_id: str, resume_id?: str, submit: bool = false }
  Response: ApplicationResultResponse { success, fields_filled, fields_missed, ats_provider, error?, screenshots: list[str] }

POST /api/auto-apply/analyze
  Request:  { job_id: str }
  Response: AutoApplyAnalysis { ats_provider, form_fields_detected: list[str], estimated_fill_rate: float, requires_login: bool }

POST /api/auto-apply/pause
  Request:  (no body)
  Response: { paused: true }

GET /api/auto-apply/profile
  Response: ApplicationProfileResponse { name, email, phone, linkedin, github, portfolio, location, work_authorization, years_experience, education_summary, current_title, desired_salary }

POST /api/auto-apply/profile
  Request:  ApplicationProfileRequest { same fields as response }
  Response: ApplicationProfileResponse
```

### Modified Endpoints

#### Copilot Enhancement (`backend/routers/copilot.py` — MODIFY)

Add `tailorResume` to the tool types. When tool is `tailorResume`, `gapAnalysis`, `coverLetter`, or `interviewPrep`, the copilot router delegates to the NLP modules (`backend/nlp/`) instead of using inline prompt templates. The existing 3 prompt templates are preserved as fallback for when NLP modules are not yet available. Flow:

1. Copilot receives request with tool type
2. If NLP module exists for the tool → call NLP module → stream result
3. Else → use existing prompt template approach (backward compatible)

`CopilotRequest` schema in `backend/schemas.py` updated to accept `tailorResume` as a valid tool type.

### New Pydantic Schemas (`backend/schemas.py` — MODIFY)

Add these schemas:
- `DimensionScoreSchema`, `CouncilScoreResponse`
- `ResumeVersionResponse`, `ResumeUploadResponse`
- `AutoApplyRunRequest`, `ApplicationResultResponse`, `AutoApplyAnalysis`
- `ApplicationProfileRequest`, `ApplicationProfileResponse`
- Update `CopilotRequest.tool` Literal to include `"tailorResume"`

### New Routers Registration (`backend/main.py` — MODIFY)

```python
from backend.routers import resume, auto_apply
app.include_router(resume.router)
app.include_router(auto_apply.router)
```

### Router Init (`backend/routers/__init__.py` — MODIFY)

Add imports for `resume` and `auto_apply` routers.

---

## 8. Scheduler Changes (`backend/scheduler.py` — MODIFY)

Add new scheduled jobs:
```python
# TF-IDF scoring batch — scores unenriched jobs (runs after enrichment)
scheduler.add_job(run_tfidf_batch, 'interval', minutes=20, id='tfidf_batch', replace_existing=True)

# Dedup hash backfill — one-time on startup for existing jobs missing dedup_hash
scheduler.add_job(backfill_dedup_hashes, 'date', id='dedup_backfill', replace_existing=True)
```

The `run_tfidf_batch()` function queries jobs where `tfidf_score IS NULL AND is_enriched = TRUE`, computes TF-IDF scores using the NLP core module against the active resume, and updates in batches of 50.

---

## 9. Embedding Changes (`backend/enrichment/embedding.py` — MODIFY)

After computing the existing sentence-transformer `match_score`, also compute `tfidf_score` using `backend.nlp.tfidf_scorer.compute_tfidf_score()` if the NLP module is available. Both scores are stored on the Job model — `match_score` (embedding-based, always-on) and `tfidf_score` (NLP-based, when resume is active). Frontend can display either or both.

Import guard: `try: from backend.nlp.tfidf_scorer import compute_tfidf_score` with graceful skip if NLP module not yet built.

---

## 10. New Dependencies

```
# requirements.txt additions
playwright==1.49.0
python-docx==1.1.0
fpdf2==2.8.0           # Pure Python PDF renderer (primary, no system deps)
weasyprint==62.0        # Optional enhanced PDF renderer (requires Pango/Cairo system libs)
pylatexenc==2.10        # LaTeX to text conversion (provides latex2text)
pdfplumber==0.11.0
```

Post-install: `playwright install chromium`

**System dependency notes:**
- `fpdf2` is pure Python, works everywhere — primary PDF renderer
- `weasyprint` requires Pango, Cairo, GDK-PixBuf (easy on Linux: `apt install libpango-1.0-0 libcairo2`; on Windows: requires GTK3 runtime or MSYS2). Optional — used when detected.
- `playwright` requires `playwright install chromium` after pip install

---

## 11. File Inventory

**23 new files:**
- `backend/scrapers/rate_limiter.py`
- `backend/adapters/__init__.py`
- `backend/adapters/ats_detector.py`
- `backend/adapters/job_filter.py`
- `backend/resume/__init__.py`
- `backend/resume/parser.py`
- `backend/resume/council.py`
- `backend/resume/document_manager.py`
- `backend/nlp/__init__.py`
- `backend/nlp/core.py`
- `backend/nlp/tfidf_scorer.py`
- `backend/nlp/gap_analyzer.py`
- `backend/nlp/resume_tailor.py`
- `backend/nlp/cover_letter.py`
- `backend/nlp/interview_prep.py`
- `backend/auto_apply/__init__.py`
- `backend/auto_apply/playwright_apply.py`
- `backend/auto_apply/ats_filler.py`
- `backend/auto_apply/workday_filler.py`
- `backend/auto_apply/orchestrator.py`
- `backend/auto_apply/profile.py`
- `backend/routers/auto_apply.py`
- `backend/routers/resume.py`

**15 modified files:**
- `backend/scrapers/base.py` — add dedup_hash, extract_tech_stack, _infer_seniority, _normalize_salary
- `backend/scrapers/greenhouse_scraper.py` — pay_transparency, questions parsing
- `backend/scrapers/lever_scraper.py` — workplaceType mapping
- `backend/scrapers/ashby_scraper.py` — full compensation parsing
- `backend/enrichment/deduplicator.py` — 3-layer upgrade with SimHash
- `backend/enrichment/embedding.py` — add tfidf_score computation alongside match_score
- `backend/models.py` — 4 new Job columns, 2 new UserProfile columns, 2 new tables
- `backend/schemas.py` — new schemas for council, resume, auto-apply; update CopilotRequest
- `backend/main.py` — register resume and auto_apply routers
- `backend/scheduler.py` — add tfidf_batch and dedup_backfill jobs
- `backend/routers/jobs.py` — add POST council-score endpoint
- `backend/routers/copilot.py` — add tailorResume tool, NLP module delegation
- `backend/routers/settings.py` — remove old resume upload route (moved to resume router)
- `backend/routers/__init__.py` — add resume and auto_apply imports
- `backend/requirements.txt` — add new packages

---

## 12. Test Strategy

Per CLAUDE.md mandatory rules, every module requires:
1. **Unit tests** — each new file gets a `tests/test_{module}.py`
2. **Integration tests** — cross-module boundaries (NLP → copilot, dedup → scheduler)
3. **Edge cases** — empty inputs, malformed data, API failures, circuit breaker triggers
4. **Backward compatibility** — existing 822+ tests must continue passing

Test files follow existing pattern: `tests/test_*.py` with pytest + pytest-asyncio.
Key test areas:
- Rate limiter: token bucket timing, circuit breaker open/half-open/closed
- 3-layer dedup: SimHash collision rates, fuzzy blocking accuracy
- Resume parser: multi-format ingestion (PDF, DOCX, MD, TEX)
- Council scorer: mocked LLM responses, score aggregation
- Auto-apply: mocked Playwright pages, form field detection
- NLP core: tokenize, cosine_similarity, tfidf correctness
