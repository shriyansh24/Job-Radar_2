# Smart Deduplication Pipeline — Technical Design

> Full research output from dedup agent. Self-contained reference.

## Problem

Current 3-layer dedup (MD5 hash, URL normalization, simhash) is insufficient:
- Same job from two sources has different URLs but identical content
- "Sr. ML Engineer" vs "Senior Machine Learning Engineer" = different hashes
- Simhash threshold of 3 bits is too aggressive, catches almost nothing
- ATS native IDs (req IDs, internal job IDs) are scraped but **never captured**

## Architecture: 6-Stage Pipeline

```
Stage 0: ATS Identity Resolution → ats_composite_key match = auto-merge
Stage 1: Company Blocking → group by normalized company (2500x fewer comparisons)
Stage 2: Fast Reject → title similarity < 60% = skip (no embedding needed)
Stage 3: Embedding Similarity → batch ONNX encode, cosine within blocks
Stage 4: Disambiguation → same-company pairs: check dept, location, req ID
Stage 5: Merge Execution → update CanonicalJob + RawJobSource records
```

## Key Components

### ATS ID Extraction (add to each scraper)

| ATS | Field | Maps To |
|-----|-------|---------|
| Greenhouse | `internal_job_id` | `ats_job_id` |
| Lever | posting `id` (UUID) | `ats_job_id` |
| Ashby | `id` from GraphQL | `ats_job_id` |
| Workday | `externalPath` → extract `REQ-12345` | `ats_requisition_id` |

Composite key: `SHA256(company_domain|ats_provider|ats_job_id)` → O(1) lookup.

### New Model Fields (Job table)

```python
ats_job_id: Mapped[str | None] = mapped_column(String(200))
ats_requisition_id: Mapped[str | None] = mapped_column(String(100))
ats_provider: Mapped[str | None] = mapped_column(String(50))
ats_composite_key: Mapped[str | None] = mapped_column(String(64), index=True)
```

### Company/Title Normalization (RapidFuzz)

- Company: strip suffixes (Inc, LLC, Corp), alias table (Amazon.com Services → Amazon), fuzzy match ≥90
- Title: expand abbreviations (Sr.→Senior, ML→Machine Learning), strip level indicators (I/II/III/L5)
- Location: alias table (SF→San Francisco, NYC→New York City), strip country suffixes

### Embedding Similarity (ONNX MiniLM)

- Model: all-MiniLM-L6-v2 with ONNX backend (already in codebase)
- Batch 10K descriptions in ~15 seconds on 24-core CPU
- Thresholds: ≥0.97 auto-merge, 0.85-0.97 flag for review (same company), <0.70 keep separate

### Same-Company Disambiguation

- Different `ats_requisition_id` → definitely separate roles
- Same `ats_job_id` → same role, merge
- Different locations → likely different roles (unless embedding ≥0.95)
- Compare responsibilities section separately from benefits

### Learning from Corrections

New `DedupFeedback` table stores user corrections. After 100+ records, train logistic regression to replace hardcoded thresholds.

## Libraries

| Tool | Purpose |
|------|---------|
| RapidFuzz (>=3.0) | Company/title fuzzy matching, C++ SIMD, 10x faster |
| onnxruntime (>=1.17) | ONNX embedding acceleration |
| FAISS-cpu (optional) | ANN search if dataset > 50K |
| sentence-transformers | Already in deps, add `backend="onnx"` |

## Performance Budget (10K jobs, 24-core/64GB)

| Stage | Time | Memory |
|-------|------|--------|
| ATS key lookup | <1ms | negligible |
| Blocking + fast reject | ~50ms | negligible |
| Batch embed ~2K descriptions | ~8-15s | ~500MB |
| Pairwise cosine within blocks | ~100ms | ~50MB |
| DB writes | ~2-5s | negligible |
| **Total** | **~15-25s** | **~600MB peak** |
