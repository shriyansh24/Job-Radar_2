# Personal Learning & Knowledge Base — Technical Design

> Full research output from learning/KB agent.

## Design Principle: Three Independently Useful Layers

Each layer works standalone. No layer depends on a later layer being implemented.

## Layer 1: SQL Analytics (Phase 1, Zero New Deps)

`PatternDetector` runs aggregate queries over existing tables:

| Insight | Query |
|---------|-------|
| Callback rate by company size | Applications grouped by company.employee_count buckets |
| Conversion funnel | Count at each pipeline stage (saved→applied→screening→interview→offer) |
| Response time patterns | AVG(days between applied_at and first status change) |
| Skill gap detection | JD required skills NOT IN resume skills (text matching) |
| Best application timing | Day-of-week / time-of-day correlation with callback rate |
| Company ghosting rate | % of applications with no response after 14 days |

**Works from day 1 on existing data. No ML needed.**

## Layer 2: Vector Similarity (Phase 2, Add onnxruntime)

Extend existing `EmbeddingService` with ONNX backend:
- Add `embedding vector(768)` columns to `resume_versions` and `cover_letters`
- pgvector handles all vector search (no ChromaDB/LanceDB needed)
- Queries: "Find resume bullets most similar to this JD requirement"
- Queries: "Which of my past cover letters best matches this company's style?"

## Layer 3: Predictions (Phase 3, scikit-learn)

`HistGradientBoostingClassifier` — trains in milliseconds on 50-200 examples.

**Feature vector for match prediction:**
```
[
  title_similarity,        # RapidFuzz score: resume title vs JD title
  skill_overlap_ratio,     # % of JD skills found in resume
  experience_delta,        # years_experience - JD_required_years
  company_size_bucket,     # 0-4 (startup→enterprise)
  salary_alignment,        # expected/offered ratio
  application_timing,      # days since job posted
  resume_tailoring_score,  # how much was tailored (0=base, 1=fully)
  past_company_success,    # historical callback rate at this company
]
```

**Output:** P(interview) = 0.0-1.0, shown as "Match Score" on job cards.

## Layer 4: Local LLM Narratives (Phase 4, Add Ollama)

Extend existing `ModelRouter` to route to Ollama:
- Primary: Ollama + Qwen2.5-7B (Q4_K_M, ~4.7GB)
- Fallback: OpenRouter (cloud) when Ollama unavailable
- Custom 100-line RAG pipeline (NOT LangChain/LlamaIndex)

**RAG Pipeline:**
```python
# 1. Embed query
query_emb = embed("What made my Amazon application successful?")
# 2. Retrieve relevant context from pgvector
contexts = db.execute("SELECT content FROM insights ORDER BY embedding <=> %s LIMIT 5")
# 3. Generate narrative
prompt = f"Based on these facts:\n{contexts}\n\nAnswer: {query}"
response = ollama.generate(model="qwen2.5:7b", prompt=prompt)
```

## New Tables (Only 3)

```sql
-- Extended outcome annotations
ApplicationOutcome (
  application_id FK,
  stage_reached,           -- furthest pipeline stage
  rejection_reason,        -- user-annotated
  days_to_response,
  interviewer_feedback,    -- notes
  offer_amount,
  negotiated_amount
)

-- Per-company user-specific stats
CompanyInsight (
  company_id FK,
  applications_count,
  callback_rate,
  avg_response_days,
  interview_style_notes,   -- user notes
  salary_data_points JSONB
)

-- Computed insights shown on dashboard
LearningInsight (
  type,                    -- "skill_gap", "timing", "resume_tip"
  title,
  description,
  confidence,
  data_points_used,
  generated_at
)
```

## What Was Deliberately Excluded

| Excluded | Why |
|----------|-----|
| Fine-tuning | Not enough data (need 10K+ examples) |
| Graph databases | Overkill for single-user relationships |
| Separate vector DB | pgvector already available |
| LangChain/LlamaIndex | 50+ deps for what 100 lines of code does |
| DuckDB | Postgres handles analytics fine at this scale |
| Real-time streaming | Insights generated in batch, not real-time |
| Multi-user learning | Single user, personal data only |
