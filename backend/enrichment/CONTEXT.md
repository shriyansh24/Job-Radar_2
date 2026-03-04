# Enrichment Module Context

## Purpose
Transform raw job postings into structured, scored, and deduplicated records using LLM extraction, embedding similarity, and fuzzy matching.

## Current Status
- LLM Enricher: Implemented (OpenRouter, claude-3-5-haiku / gpt-4o-mini fallback)
- Embedding Matcher: Implemented (all-MiniLM-L6-v2, 384-dim, CPU)
- Deduplicator: Implemented (SHA256 hash + rapidfuzz cross-source)

## Data Schema

### LLM Enrichment Output
```python
{
    "skills_required": ["Python", "AWS", ...],
    "skills_nice_to_have": ["Kubernetes", ...],
    "tech_stack": ["React", "PostgreSQL", ...],
    "experience_level": "entry" | "mid" | "senior" | "exec",
    "job_type": "full-time" | "part-time" | "contract" | "internship",
    "remote_type": "remote" | "hybrid" | "onsite",
    "seniority_score": 0-100,
    "remote_score": 0-100,
    "summary_ai": "2-3 sentence plain English summary",
    "red_flags": ["max 3 items"],
    "green_flags": ["max 3 items"],
}
```

### Embedding Output
```python
match_score: float  # 0-100, cosine similarity * 100
```

### Deduplication Output
```python
(is_new: bool, job_id: str)  # is_new=False means duplicate_of set
```

## Key Functions

### llm_enricher.py
- `enrich_job(job_dict)` -> `dict` (enrichment fields)
- `run_enrichment_batch()` -> `None` (processes 10 unenriched jobs)
- Fallback: primary model failure -> retry with fallback model

### embedding.py
- `load_model()` -> `SentenceTransformer` (lazy-loaded, cached)
- `load_resume_embedding(resume_text)` -> `None` (caches globally)
- `compute_match_score(job_text)` -> `float | None` (cosine sim * 100)
- `score_jobs_batch()` -> `None` (scores 50 jobs without match_score)

### deduplicator.py
- `check_duplicate(session, job_dict)` -> `Optional[str]` (existing job_id)
- `deduplicate_and_insert(session, job_dict)` -> `(bool, str)` (is_new, job_id)

## Dependencies
- openai==1.57.0 (OpenRouter via base_url swap)
- sentence-transformers==3.3.0 (all-MiniLM-L6-v2)
- rapidfuzz==3.10.0 (fuzzy string matching)

## Known Limitations
- Enrichment: 1000 max_tokens may truncate complex responses
- Embeddings: CPU-only, ~0.5s per batch of 50 jobs
- Dedup: Cross-source matching requires company_domain or company_name match
- No retry queue: If both LLM models fail, job stays unenriched until next batch
