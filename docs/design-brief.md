# Personal Learning & Knowledge Base System — Architecture Design

**Status:** Design brief / brainstorm
**Date:** 2026-03-20
**Scope:** JobRadar V2 feature — learns from the user's job search journey

---

## 1. Existing Assets Audit

Before designing anything new, here is what already exists in the codebase and can be reused directly:

| Asset | Location | Reuse |
|-------|----------|-------|
| **pgvector** | `pyproject.toml` dep, Job.embedding column (384-dim) | Extend for all vector storage |
| **EmbeddingService** | `app/enrichment/embedding.py` — `all-MiniLM-L6-v2` via sentence-transformers | Reuse, add ONNX backend |
| **TF-IDF scorer** | `app/enrichment/tfidf.py` + `app/nlp/core.py` | Reuse for keyword-level analytics |
| **ModelRouter** | `app/nlp/model_router.py` — OpenRouter fallback chain | Extend with local Ollama backend |
| **Application pipeline** | `app/pipeline/models.py` — Application + ApplicationStatusHistory | Already tracks status transitions |
| **ResumeVersion** | `app/resume/models.py` — versioned resumes with parsed text | Already links to applications |
| **CoverLetter** | `app/copilot/models.py` — style + content per job | Already links to jobs |
| **InterviewSession** | `app/interview/models.py` — questions, answers, scores | Already per-job |
| **SalaryCache** | `app/salary/models.py` — market data per title/company/location | Extend with personal outcomes |
| **Company** | `app/companies/models.py` — canonical companies with ATS info | Extend with user-specific patterns |
| **UserProfile** | `app/profile/models.py` — full profile with answer bank | Already stores structured profile |
| **FollowupReminder** | `app/followup/models.py` — reminders per application | Reuse for feedback loop nudges |

**Key insight:** ~70% of the data model already exists. The learning system is mostly *analytics and inference on top of existing tables*, not a new data silo.

---

## 2. Architecture: The Simplest Thing That Works

### Core Principle: SQL-first, vectors for search, LLM for narrative

```
                     ┌─────────────────────────────────┐
                     │         LEARNING ENGINE          │
                     │                                  │
  Structured Data    │  ┌───────────┐  ┌────────────┐  │
  (SQL analytics) ───┼─>│  Pattern   │  │  Prediction │  │
                     │  │  Detector  │  │  Engine     │  │
  Vector Search      │  └─────┬─────┘  └──────┬─────┘  │
  (pgvector) ────────┼────────┤               │        │
                     │        v               v        │
  Local LLM          │  ┌─────────────────────────┐    │
  (Ollama) ──────────┼─>│  Insight Generator      │    │
                     │  │  (narratives + advice)   │    │
                     │  └─────────────────────────┘    │
                     └─────────────────────────────────┘
```

**Three layers, each independently useful:**

1. **SQL Analytics** (works day 1, zero new deps): Aggregate queries over existing tables. "Your callback rate is 23%." "Companies in fintech respond 3x faster." Pure PostgreSQL.

2. **Vector Similarity** (works day 1, pgvector already installed): "This JD is 87% similar to one where you got an offer." Semantic matching across JDs, resumes, cover letters.

3. **Local LLM Narratives** (added later, requires Ollama): "Based on your 47 applications, here are 3 things to change..." Natural language insights from structured data.

---

## 3. Data Model Extensions

### 3A. New Tables

```python
# app/learning/models.py

class ApplicationOutcome(Base):
    """Extended outcome data beyond status tracking.
    Links to existing Application but adds learning-specific fields."""
    __tablename__ = "application_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), unique=True
    )
    # Which stage did it fail?
    failure_stage: Mapped[str | None] = mapped_column(String(30))
    # User annotation: why did it fail?
    failure_reason: Mapped[str | None] = mapped_column(Text)
    # User annotation: what went well?
    success_factors: Mapped[str | None] = mapped_column(Text)
    # Days from applied to each stage transition
    days_to_screening: Mapped[int | None] = mapped_column(Integer)
    days_to_interview: Mapped[int | None] = mapped_column(Integer)
    days_to_offer: Mapped[int | None] = mapped_column(Integer)
    days_to_rejection: Mapped[int | None] = mapped_column(Integer)
    # Salary negotiation
    salary_expected: Mapped[Decimal | None] = mapped_column(Numeric)
    salary_offered: Mapped[Decimal | None] = mapped_column(Numeric)
    salary_accepted: Mapped[Decimal | None] = mapped_column(Numeric)
    # Interview feedback
    interview_rounds: Mapped[int | None] = mapped_column(Integer)
    interview_types: Mapped[list | None] = mapped_column(JSONB)  # ["phone", "technical", "behavioral"]
    interview_difficulty: Mapped[int | None] = mapped_column(Integer)  # 1-5
    # Metadata
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class CompanyInsight(Base):
    """User-specific company intelligence, built from their application history."""
    __tablename__ = "company_insights"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    company_name: Mapped[str] = mapped_column(String(300), nullable=False)
    # Aggregated stats (recomputed periodically)
    total_applications: Mapped[int] = mapped_column(Integer, default=0)
    total_callbacks: Mapped[int] = mapped_column(Integer, default=0)
    total_interviews: Mapped[int] = mapped_column(Integer, default=0)
    total_offers: Mapped[int] = mapped_column(Integer, default=0)
    total_rejections: Mapped[int] = mapped_column(Integer, default=0)
    total_ghosted: Mapped[int] = mapped_column(Integer, default=0)
    avg_response_days: Mapped[Decimal | None] = mapped_column(Numeric)
    # Qualitative
    interview_style_notes: Mapped[str | None] = mapped_column(Text)
    culture_notes: Mapped[str | None] = mapped_column(Text)
    # Updated by learning engine
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class LearningInsight(Base):
    """Computed insights from the learning engine. Shown on dashboard."""
    __tablename__ = "learning_insights"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    category: Mapped[str] = mapped_column(String(30))
        # "match_score", "resume", "company", "timing", "salary", "interview"
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2))  # 0.00 - 1.00
    data_points: Mapped[int] = mapped_column(Integer)  # how many records support this
    is_actionable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
```

### 3B. Extend Existing Tables (via Alembic migration)

```python
# Add to Job model:
# embedding column already exists (Vector(384))
# No changes needed.

# Add to Application model:
resume_version_id  # already exists
cover_letter_id    # already exists
# These FK links are the key to learning "which resume version -> which outcome"

# Add to ResumeVersion model:
embedding: Vector(384)  # embed parsed_text for similarity search

# Add to CoverLetter model:
embedding: Vector(384)  # embed content for similarity search
```

### 3C. New pgvector Embeddings (added to existing embedding column pattern)

```sql
-- Embeddings we want (all 384-dim via all-MiniLM-L6-v2):
-- jobs.embedding           — already exists
-- resume_versions.embedding — NEW: embed parsed resume text
-- cover_letters.embedding   — NEW: embed cover letter content
-- No separate vector table needed. pgvector on Postgres, skip on SQLite.
```

---

## 4. The Learning Engine

### 4A. Pattern Detector (SQL-based, zero LLM cost)

These are pure SQL aggregate queries. They work from day 1 with zero new dependencies.

```python
# app/learning/patterns.py

class PatternDetector:
    """Detect actionable patterns from application history using SQL."""

    def __init__(self, db: AsyncSession, user_id: uuid.UUID):
        self.db = db
        self.user_id = user_id

    async def callback_rate(self) -> dict:
        """Overall and per-resume callback rate."""
        # SELECT resume_version_id,
        #        COUNT(*) as total,
        #        COUNT(*) FILTER (WHERE status IN ('screening','interview','offer','accepted')) as callbacks
        # FROM applications WHERE user_id = :uid
        # GROUP BY resume_version_id

    async def stage_conversion_funnel(self) -> dict:
        """Conversion rates between pipeline stages."""
        # saved -> applied -> screening -> interview -> offer -> accepted
        # Each step: COUNT at stage / COUNT at previous stage

    async def company_response_patterns(self) -> dict:
        """Average response time and ghosting rate per company."""
        # JOIN application_status_history to compute days between transitions
        # Flag as "ghosted" if applied > 14 days ago and still "applied"

    async def timing_analysis(self) -> dict:
        """Does application timing correlate with callbacks?"""
        # Compare days_since_posted at application time vs callback rate
        # Bucket: 0-2 days, 3-7 days, 8-14 days, 15+ days

    async def skill_gap_analysis(self) -> dict:
        """Which required skills appear in rejections but not in callbacks?"""
        # JOIN jobs.skills_required with application outcomes
        # Compare skill frequency in successful vs unsuccessful applications

    async def salary_benchmarks(self) -> dict:
        """Personal salary data vs market data."""
        # Compare salary_offered in ApplicationOutcome vs SalaryCache market_data
```

**Minimum data points before generating insights:**

| Insight Type | Min Applications | Confidence Boost |
|-------------|-----------------|-----------------|
| Overall callback rate | 5 | Per 10 more: +0.1 |
| Per-company patterns | 2 at same company | Per 3 more: +0.15 |
| Resume comparison | 5 per version | Per 10 more: +0.1 |
| Timing analysis | 15 | Per 25 more: +0.1 |
| Skill gap | 10 with enriched JDs | Per 20 more: +0.1 |
| Salary prediction | 3 offers | Per 5 more: +0.15 |

### 4B. Prediction Engine (lightweight ML, no deep learning)

For match score prediction, use a **gradient-boosted tree** trained on the user's own data. This is scikit-learn (already an optional dep), not a neural network.

```python
# app/learning/predictor.py

class OutcomePredictor:
    """Predict application outcomes using user's historical data.

    Uses a lightweight GBT model trained incrementally on the user's
    application history. No cloud APIs, no GPU needed.
    """

    FEATURE_COLUMNS = [
        "tfidf_score",           # existing Job.tfidf_score
        "match_score",           # existing Job.match_score
        "days_since_posted",     # computed from Job.posted_at
        "resume_version_id",     # which resume was used (one-hot)
        "cover_letter_style",    # cover letter style category
        "company_prev_apps",     # how many times applied to this company before
        "company_prev_callbacks",# callbacks from this company before
        "skills_overlap_pct",    # % of required skills in user's resume
        "experience_level_match",# does user's seniority match JD?
        "remote_type_match",     # does user's preference match?
        "salary_in_range",       # is expected salary in JD range?
    ]

    def train(self, applications: list[dict]) -> None:
        """Retrain on all user applications with known outcomes.

        Called periodically (after every 5 new outcomes) or on-demand.
        Uses HistGradientBoostingClassifier (fast, handles missing values natively).
        """
        from sklearn.ensemble import HistGradientBoostingClassifier
        # Target: binary — did user get past screening? (callback = 1, no = 0)
        # Secondary model: did user get an offer? (smaller dataset)

    def predict_callback_probability(self, job_features: dict) -> float:
        """Probability of getting a callback for this job."""
        # Returns 0.0-1.0

    def predict_offer_probability(self, job_features: dict) -> float:
        """Probability of getting an offer (if enough data)."""
        # Only available after 3+ offers in history
```

**Why GBT over a neural network:** With 50-200 training examples (typical for a job search), a gradient-boosted tree will vastly outperform any neural approach. It handles missing features natively, trains in milliseconds, and is interpretable (feature importances tell you which factors matter most).

### 4C. Semantic Search Layer (pgvector, already in stack)

```python
# app/learning/search.py

class SemanticSearch:
    """Vector similarity search over personal job search documents."""

    async def find_similar_jobs(self, job_id: str, top_k: int = 10) -> list[dict]:
        """Find jobs similar to a given job by JD embedding.
        Used for: 'jobs like this one where you got callbacks.'
        """
        # SELECT j2.id, j2.title, j2.company_name,
        #        1 - (j1.embedding <=> j2.embedding) AS similarity
        # FROM jobs j1, jobs j2
        # WHERE j1.id = :job_id AND j2.user_id = :uid
        # ORDER BY j1.embedding <=> j2.embedding LIMIT :k

    async def find_similar_successful_jobs(self, job_embedding: list[float]) -> list[dict]:
        """Find historically successful applications with similar JDs.
        Used for: 'Based on your history, you have X% chance at this role.'
        """
        # JOIN jobs + applications WHERE status IN ('interview','offer','accepted')
        # ORDER BY embedding <=> :query_embedding

    async def match_resume_to_jd(self, resume_embedding: list[float], jd_embedding: list[float]) -> float:
        """Cosine similarity between resume and JD embeddings.
        Used for: semantic match score (complements TF-IDF).
        """
        # 1 - (resume_embedding <=> jd_embedding)

    async def find_cover_letter_templates(self, jd_embedding: list[float], top_k: int = 3) -> list[dict]:
        """Find cover letters from successful applications with similar JDs.
        Used for: 'This cover letter style worked for similar roles.'
        """
        # JOIN cover_letters + applications WHERE status IN ('interview','offer')
        # ORDER BY cover_letters.embedding <=> :jd_embedding
```

### 4D. Insight Generator (LLM layer — optional, adds narratives)

```python
# app/learning/insights.py

class InsightGenerator:
    """Generate natural language insights from structured pattern data.

    Uses local LLM (Ollama) when available, falls back to template-based
    string formatting when not. The system is fully functional without LLM.
    """

    async def generate_insights(self, patterns: dict) -> list[LearningInsight]:
        """Convert raw pattern data into user-facing insights.

        Template fallback examples (no LLM needed):
        - "Your callback rate with Resume v3 (34%) is 2x higher than Resume v1 (17%)"
        - "You've been ghosted 4 out of 5 times by companies in banking sector"
        - "Applications submitted within 48h of posting have 41% callback rate vs 12% for later"

        LLM-enhanced (when Ollama available):
        - Takes the same data but generates more nuanced, personalized advice
        - "Consider emphasizing your distributed systems experience — the 3 offers
          you received all had that as a top-3 requirement, but it's buried in
          your current resume."
        """
```

---

## 5. Feedback Loop Design

### 5A. Data Collection (mostly passive)

```
USER ACTIONS                         SIGNALS CAPTURED
─────────────                        ─────────────────
Saves a job                    →     Job saved (interest signal)
Applies to job                 →     Application created + resume_version_id + timestamp
Marks "got screening call"     →     ApplicationStatusHistory transition
Marks "rejected"               →     Outcome recorded, failure_stage computed
Marks "got offer"              →     Salary data captured
Annotates "rejected because X" →     failure_reason stored (richest signal)
Does nothing for 14 days       →     Auto-flagged as "likely ghosted" (implicit)
```

### 5B. Periodic Nudges (reuse existing FollowupReminder)

```python
# app/learning/feedback_loop.py

class FeedbackLoop:
    """Proactive nudges to collect outcome data."""

    async def check_stale_applications(self) -> list[dict]:
        """Find applications with no status change for >14 days.

        Returns list of applications to nudge user about:
        'You applied to {company} for {title} 16 days ago. Any update?'

        Options: Got callback | Rejected | No response yet | Withdrew
        """
        # SELECT * FROM applications
        # WHERE status = 'applied'
        # AND applied_at < NOW() - INTERVAL '14 days'
        # AND NOT EXISTS (SELECT 1 FROM followup_reminders
        #                 WHERE application_id = applications.id
        #                 AND is_sent = true)

    async def suggest_outcome_annotation(self, application_id: uuid.UUID) -> dict:
        """After a rejection/ghosting, prompt user for brief annotation.

        'What do you think went wrong? (Optional)'
        - [ ] Missing required skill
        - [ ] Overqualified/underqualified
        - [ ] Salary mismatch
        - [ ] Culture fit
        - [ ] Ghosted (no response)
        - [ ] Other: ___________
        """
```

### 5C. Automatic Pattern Refresh Schedule

```
After every 5 new outcomes    →  Recompute callback rates, skill gaps
After every 10 applications   →  Retrain prediction model
After every new offer/salary  →  Update salary benchmarks
Weekly (if active)            →  Generate fresh insights for dashboard
Monthly                       →  Full pattern refresh + stale insight cleanup
```

---

## 6. Technical Decisions

### 6A. Vector Store: pgvector (already in stack)

**Decision: Use pgvector. Do not add ChromaDB, LanceDB, or any other vector DB.**

Rationale:
- pgvector is already a dependency (`pyproject.toml` line 28: `pgvector>=0.3.0`)
- Job embeddings already use it (`Job.embedding` column comment in models)
- The dataset is small (hundreds to low thousands of vectors per user)
- pgvector handles exact nearest neighbor search well at this scale
- HNSW indexing available if needed later (`CREATE INDEX ... USING hnsw`)
- One fewer service to manage, backup, migrate
- Transactional consistency with relational data (JOIN vectors with outcomes in one query)

**Scale check:** pgvector with IVFFlat handles 100K vectors in <10ms. A job seeker will have at most a few thousand. No bottleneck.

### 6B. Embedding Model: all-MiniLM-L6-v2 via ONNX Runtime

**Decision: Keep all-MiniLM-L6-v2, switch from sentence-transformers to ONNX Runtime.**

Rationale:
- Already using `all-MiniLM-L6-v2` in `EmbeddingService` (app/enrichment/embedding.py)
- 384 dimensions, ~23M parameters, fast enough for real-time on CPU
- ONNX Runtime is ~10x faster inference than PyTorch-based sentence-transformers
- ONNX model is ~90MB vs ~250MB for full sentence-transformers with PyTorch
- No GPU needed for embedding at this scale
- bge-small-en and gte-small are marginally better on benchmarks but the difference is negligible for job-search similarity matching

```python
# Migration path: dual-backend EmbeddingService
class EmbeddingService:
    def __init__(self, db, backend="auto"):
        # backend="auto": try ONNX first, fall back to sentence-transformers
        # backend="onnx": ONNX only (faster, smaller)
        # backend="sentence-transformers": original (heavier, more flexible)
```

**ONNX setup:**
```bash
pip install onnxruntime  # CPU-only, ~15MB
# Download quantized model once (~33MB):
# huggingface-cli download sentence-transformers/all-MiniLM-L6-v2 --include onnx/*
```

### 6C. Local LLM: Ollama with Qwen2.5-7B (Q4_K_M)

**Decision: Ollama with Qwen2.5-7B-Instruct-Q4_K_M as primary, with cloud fallback.**

Rationale:
- Qwen2.5-7B is the best 7B model for structured reasoning tasks
- Q4_K_M quantization: ~4.7GB VRAM/RAM, minimal quality loss from full precision
- On CPU (Intel Core Ultra 9 275HX, 24 cores): ~5-10 tokens/sec — usable for batch insights
- On GPU (if available): 30-50 tokens/sec — fast enough for interactive use
- Ollama provides a clean OpenAI-compatible API, so the existing `ModelRouter` can route to it

**GPU question:** The Intel Core Ultra 9 275HX has an integrated Intel Arc GPU (Xe-LPG, ~8 execution units). Ollama does NOT support Intel Arc GPUs well as of early 2026 — it only accelerates on NVIDIA CUDA and Apple Metal. If the machine has a discrete NVIDIA GPU, Ollama will use it automatically. Otherwise, inference will be CPU-only, which is adequate for batch processing (insights generated in background, not blocking the UI).

**Integration with existing ModelRouter:**

```python
# Extend TASK_MODELS in app/nlp/model_router.py:
TASK_MODELS: dict[str, list[str]] = {
    "learning_insight": [
        "ollama/qwen2.5:7b",           # Try local first (free, private)
        "anthropic/claude-3-5-haiku",   # Fall back to cloud if Ollama down
    ],
    "learning_analysis": [
        "ollama/qwen2.5:14b",          # Bigger model for complex analysis
        "ollama/qwen2.5:7b",           # Fall back to smaller
        "anthropic/claude-3-5-haiku",
    ],
    # ... existing tasks unchanged
}
```

**LLMClient extension for Ollama:**

```python
# Ollama exposes OpenAI-compatible API at http://localhost:11434/v1
# The existing LLMClient (httpx-based) can hit this directly.
# Just add OLLAMA_BASE_URL=http://localhost:11434/v1 to .env
```

### 6D. RAG Pipeline: Custom (no LangChain/LlamaIndex)

**Decision: Build a minimal custom RAG pipeline. Do not add LangChain or LlamaIndex.**

Rationale:
- LangChain/LlamaIndex add 50+ transitive dependencies
- The RAG use case here is simple: embed query -> pgvector search -> stuff context into prompt
- The codebase already has all the building blocks (EmbeddingService, pgvector, ModelRouter, LLMClient)
- A custom pipeline is ~100 lines of code and fully debuggable

```python
# app/learning/rag.py

class PersonalRAG:
    """Minimal RAG over user's job search documents."""

    async def query(self, question: str, context_types: list[str] = None) -> str:
        """Answer a question using the user's personal job search data.

        1. Embed the question
        2. Search pgvector for relevant documents (JDs, resumes, cover letters, notes)
        3. Fetch structured context (application outcomes, company stats)
        4. Build prompt with retrieved context
        5. Send to local LLM (Ollama) or cloud fallback

        context_types: filter to specific doc types
            ["jobs", "resumes", "cover_letters", "interview_notes", "outcomes"]
        """
        # Step 1: Embed
        query_embedding = self.embedding_service.embed_text(question)

        # Step 2: Vector search (top-5 from each relevant table)
        contexts = []
        if "jobs" in context_types:
            similar_jobs = await self.search.find_similar_jobs_by_embedding(
                query_embedding, top_k=5
            )
            contexts.extend(self._format_job_context(similar_jobs))

        # Step 3: Structured context
        patterns = await self.pattern_detector.get_relevant_patterns(question)
        contexts.append(self._format_pattern_context(patterns))

        # Step 4: Build prompt
        prompt = self._build_prompt(question, contexts)

        # Step 5: LLM call
        return await self.model_router.complete("learning_analysis", [
            {"role": "system", "content": LEARNING_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])
```

### 6E. Analytics: PostgreSQL (no DuckDB)

**Decision: Use PostgreSQL for all analytics. Do not add DuckDB.**

Rationale:
- The analytics queries are straightforward aggregations (GROUP BY, COUNT, AVG, FILTER)
- PostgreSQL handles them efficiently at this scale (hundreds of rows, not millions)
- Adding DuckDB creates a dual-database complexity for marginal benefit
- If analytics queries become slow later, add materialized views or summary tables

---

## 7. Structured vs Unstructured: Decision Matrix

| Question | Use Structured (SQL) | Use Unstructured (Vector) |
|----------|---------------------|--------------------------|
| "What's my callback rate?" | Yes — `COUNT/GROUP BY` | No |
| "Which resume version works best?" | Yes — join applications + outcomes | No |
| "Find jobs like the one I got an offer for" | No | Yes — embedding similarity |
| "What skills am I missing?" | Yes — set difference on arrays | No |
| "How does this JD compare to ones I succeeded at?" | No | Yes — semantic similarity |
| "Average days to hear back from X company?" | Yes — `AVG(days_to_screening)` | No |
| "Draft a cover letter like the one that worked for Y" | No | Yes — retrieve similar + LLM |
| "What salary should I expect for this role?" | Hybrid — SQL for ranges, vector to find comparable | Both |

**Rule of thumb:** If you can express it as a SQL query, use SQL. Vectors are for "similar to" questions. LLM is for generating natural language from either.

---

## 8. V1 to V2 Migration Path

### V1 (Current): Cloud LLM via OpenRouter

```
User Action → FastAPI → OpenRouter API → Claude/GPT → Response
                          (cloud, paid, data leaves machine)
```

### V2 (Target): Hybrid Local-First

```
                    ┌─ Embeddings: ONNX Runtime (local, CPU)
User Action → API → ├─ Analytics: PostgreSQL (local)
                    ├─ Predictions: scikit-learn (local, CPU)
                    └─ Narratives: Ollama → Qwen2.5 (local, CPU/GPU)
                         ↓ fallback if Ollama unavailable
                       OpenRouter → Claude/GPT (cloud)
```

### Migration Steps (incremental, each step delivers value):

**Phase 1 — SQL Analytics (0 new deps, 1-2 days)**
- Add `ApplicationOutcome`, `CompanyInsight`, `LearningInsight` tables
- Add `PatternDetector` with 6 core queries
- Add dashboard endpoint: `GET /api/v1/learning/insights`
- Value: Users see callback rates, timing patterns, company stats immediately

**Phase 2 — Enhanced Embeddings (add onnxruntime, 1 day)**
- Add ONNX backend to `EmbeddingService`
- Add `embedding` column to `resume_versions` and `cover_letters`
- Add `SemanticSearch` service
- Value: "Find jobs like this" and "find cover letters that worked for similar roles"

**Phase 3 — Prediction Model (scikit-learn already optional dep, 1-2 days)**
- Add `OutcomePredictor` with GBT model
- Train after user has 10+ applications with outcomes
- Show prediction on job cards: "73% callback probability"
- Value: Personalized match scores that improve with data

**Phase 4 — Local LLM (add Ollama, 1-2 days)**
- Extend `ModelRouter` with Ollama backend
- Add `InsightGenerator` with LLM narratives
- Add `PersonalRAG` for Q&A over personal data
- Value: Natural language insights and advice, fully local

**Phase 5 — Feedback Loop (1 day)**
- Add stale application detection
- Add outcome annotation prompts in UI
- Add periodic insight refresh worker
- Value: System gets smarter automatically as user provides feedback

### Minimum Viable Local Setup

```bash
# Phase 1-3: No new services needed
pip install onnxruntime  # ~15MB, CPU-only

# Phase 4: Add Ollama
# Windows: winget install Ollama
ollama pull qwen2.5:7b-instruct-q4_k_m  # ~4.7GB download, one-time
# Ollama runs as a system service, always available at localhost:11434
```

**GGUF Quantization Tradeoffs:**

| Quantization | Size | Quality (vs FP16) | Speed (CPU, 24-core) | Recommendation |
|-------------|------|-------------------|---------------------|----------------|
| Q4_K_M | 4.7 GB | ~95% | ~8 tok/s | **Best default** |
| Q5_K_M | 5.3 GB | ~97% | ~6 tok/s | If quality matters more |
| Q6_K | 5.9 GB | ~99% | ~5 tok/s | Overkill for this use case |
| Q8_0 | 7.7 GB | ~99.5% | ~4 tok/s | Waste of RAM |

**Recommendation:** Q4_K_M for Qwen2.5-7B. The quality difference between Q4_K_M and Q8_0 is imperceptible for generating job search insights. Save the RAM for PostgreSQL and the application itself.

---

## 9. Privacy & Security

### All Data Stays Local

```
✓ PostgreSQL: local database, no cloud replication
✓ pgvector: embeddings stored in same local Postgres
✓ Ollama: local LLM inference, no data sent to cloud
✓ ONNX Runtime: local embedding generation
✓ scikit-learn: local model training

⚠ OpenRouter fallback: sends prompt to cloud API
  → Only used when Ollama is unavailable
  → User setting: "Allow cloud LLM fallback" (default: true for V1 compat)
  → When disabled, insight generation gracefully degrades to template-based
```

### Encryption at Rest

```python
# PostgreSQL: enable native encryption
# pg_hba.conf: hostssl only (no unencrypted connections)
# Or use full-disk encryption (BitLocker on Windows, which is likely already on)

# Sensitive fields (salary, interview notes) can use application-level encryption
# via Fernet (already available from python-jose dependency):
from cryptography.fernet import Fernet
# Key stored in .env as LEARNING_ENCRYPTION_KEY
```

### Export/Import

```python
# app/learning/export.py

class DataExporter:
    """Export/import personal learning data for backup or migration."""

    async def export_all(self, user_id: uuid.UUID) -> dict:
        """Export all learning data as JSON.

        Includes: applications, outcomes, insights, company_insights,
                  resume_versions (metadata, not files), cover_letters,
                  interview_sessions, salary data.

        Embeddings are NOT exported (regenerated on import).
        """

    async def import_all(self, user_id: uuid.UUID, data: dict) -> dict:
        """Import learning data from JSON export."""

    async def delete_all(self, user_id: uuid.UUID) -> dict:
        """GDPR-style deletion of all personal learning data."""
```

---

## 10. File Structure

```
app/learning/
├── __init__.py
├── models.py           # ApplicationOutcome, CompanyInsight, LearningInsight
├── patterns.py          # PatternDetector (SQL analytics)
├── predictor.py         # OutcomePredictor (scikit-learn GBT)
├── search.py            # SemanticSearch (pgvector queries)
├── insights.py          # InsightGenerator (template + LLM)
├── rag.py               # PersonalRAG (minimal custom RAG)
├── feedback_loop.py     # FeedbackLoop (nudges + auto-detection)
├── export.py            # DataExporter (backup/GDPR)
├── router.py            # FastAPI endpoints
└── schemas.py           # Pydantic request/response models

# Modified existing files:
app/enrichment/embedding.py  # Add ONNX backend
app/nlp/model_router.py      # Add Ollama model entries
```

---

## 11. API Endpoints

```
GET  /api/v1/learning/dashboard         # All insights for user
GET  /api/v1/learning/insights          # Paginated insights list
POST /api/v1/learning/insights/dismiss   # Dismiss an insight

GET  /api/v1/learning/stats             # Funnel, rates, averages
GET  /api/v1/learning/stats/companies   # Per-company breakdown
GET  /api/v1/learning/stats/resumes     # Per-resume-version breakdown

POST /api/v1/learning/predict           # Predict outcome for a job
POST /api/v1/learning/similar           # Find similar successful jobs

POST /api/v1/learning/ask               # RAG Q&A over personal data

POST /api/v1/learning/outcomes          # Record application outcome
PATCH /api/v1/learning/outcomes/:id     # Update outcome annotation

GET  /api/v1/learning/export            # Export all data (JSON)
POST /api/v1/learning/import            # Import data
DELETE /api/v1/learning/data            # GDPR delete
```

---

## 12. What NOT to Build

| Temptation | Why Skip It |
|-----------|-------------|
| Fine-tuning a custom model on user data | 50-200 data points is too few; GBT is better |
| Graph database for relationships | PostgreSQL foreign keys handle all relationships |
| Separate vector database (Chroma, Lance, etc.) | pgvector is already deployed and sufficient |
| LangChain/LlamaIndex framework | 100 lines of custom RAG beats 50 new dependencies |
| Real-time streaming insights | Batch is fine; insights change weekly, not per-second |
| Multi-user collaborative learning | Privacy nightmare; each user's data is siloed |
| Complex recommendation algorithm | Similarity search + simple stats outperform at this scale |
| Automated resume rewriting | Too risky; show insights, let user decide |

---

## 13. Success Metrics

The system is working if:

1. **After 10 applications:** User sees their first callback rate and timing insights
2. **After 20 applications:** User sees per-resume comparison and skill gap analysis
3. **After 30 applications:** Prediction model gives meaningful callback probabilities
4. **After 50 applications:** Company-level patterns emerge; salary predictions available
5. **User engagement:** >50% of stale application nudges get responses
6. **Accuracy:** Predicted callback probability within 15% of actual rate (after 50+ data points)

---

## Summary: The One-Page Version

**Store everything in PostgreSQL** (relational data + pgvector embeddings). **Analyze with SQL** for structured patterns. **Search with pgvector** for similarity questions. **Predict with scikit-learn** GBT trained on user's own outcomes. **Narrate with Ollama** (Qwen2.5-7B local) for natural language insights, falling back to string templates when LLM is unavailable. **No new databases, no frameworks, no cloud dependencies** for the core learning loop. Each phase delivers standalone value. The system gets smarter with every application the user tracks.
