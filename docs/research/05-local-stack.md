# Local-First Open Source Stack — Technical Recommendations

> Full research output from local stack agent.

## Target Hardware

- **CPU:** Intel Core Ultra 9 275HX (24 cores, Arrow Lake, AMX/AVX-512)
- **RAM:** 64GB
- **GPU:** Intel Arc iGPU (integrated, shared memory)
- **OS:** Windows 11

## Winners By Category

### A. LLM Inference → Ollama + Qwen3

| Task | Model | Quant | RAM | Speed (CPU) |
|------|-------|-------|-----|-------------|
| Resume rewriting | Qwen3-8B | Q5_K_M | ~6GB | 15-25 tok/s |
| Cover letter gen | Qwen3-8B | Q5_K_M | ~6GB | 15-25 tok/s |
| Form field classify | Qwen3-4B | Q4_K_M | ~2.5GB | 35-50 tok/s |
| Job matching | Qwen3-8B | Q5_K_M | ~6GB | 15-25 tok/s |
| Interview questions | Qwen3-14B | Q4_K_M | ~9GB | 8-15 tok/s |

**Intel Arc iGPU:** IPEX-LLM can offload to iGPU (~30% faster than CPU-only for 7B-14B models). Setup via `ipex-llm[ollama]` package.

**Why not vLLM/llama.cpp directly:** Ollama wraps llama.cpp with model management and a clean REST API. vLLM wins on multi-user throughput (35x) but is overkill for single-user.

### B. Embeddings → nomic-embed-text (768d, ONNX)

| Model | Dims | Docs/sec | RAM | MTEB Score |
|-------|------|----------|-----|------------|
| nomic-embed-text | 768 | 300-500 | ~500MB | 86.2% |
| all-MiniLM-L6-v2 | 384 | 800-1200 | ~200MB | ~82% |

**Use nomic for quality, MiniLM for speed-sensitive paths** (typeahead search).
ONNX Runtime with Intel AMX/AVX-512 optimizations on Arrow Lake.

### C. Vector Search → pgvector (existing Postgres)

Already running. No new dependency. 2-5ms search on 100K vectors. Hybrid BM25+semantic in one SQL query.

**Why not ChromaDB/LanceDB/Qdrant:** All add a dependency when Postgres is already there. pgvectorscale achieves 471 QPS at 99% recall on 50M vectors.

### D. PDF Processing

| Operation | Tool | Speed |
|-----------|------|-------|
| Parse resume PDF | PyMuPDF4LLM | 120ms |
| Parse scanned PDF (OCR) | marker-pdf | 11s (fallback) |
| Extract tables | pdfplumber | 200ms |
| Generate resume PDF | WeasyPrint (HTML→PDF) | ~200ms |
| Generate fast PDF | Typst (Rust) | <50ms |
| Read/write DOCX | python-docx | ~50ms |
| Universal conversion | pandoc | varies |

### E. Browser Automation → Crawlee-Python + Playwright

Crawlee wraps Playwright with: fingerprint rotation, proxy rotation, crash-resilient queues, adaptive concurrency, session management.

| Anti-Detection Level | Tool |
|---------------------|------|
| Default (90% of sites) | Playwright via Crawlee |
| High detection | nodriver (driverless Chrome) |
| Maximum stealth | Camoufox (Firefox, 0% detection rate) |

### F. Data Processing → DuckDB + RapidFuzz

- DuckDB: embedded SQL analytics, larger-than-RAM, vectorized columnar engine
- RapidFuzz: 20-100x faster than FuzzyWuzzy, C++ with SIMD
- For 10K+ dedup: DuckDB (blocking) + RapidFuzz (pairwise scoring) = ~2-5 seconds

### G. Search → PostgreSQL FTS + pgvector Hybrid

```sql
-- Hybrid search: keyword BM25 + semantic vector similarity
SELECT *,
  0.4 * ts_rank(search_vector, query) +
  0.6 * (1 - (embedding <=> query_embedding)) AS score
FROM jobs
WHERE search_vector @@ query
ORDER BY score DESC LIMIT 20;
```

No MeiliSearch/Tantivy needed at this scale.

## Total Footprint

| Resource | Amount |
|----------|--------|
| Disk (all models + tools) | ~10GB |
| Peak RAM (all active) | ~17GB of 64GB |
| New external servers | 0 (Ollama = local daemon) |
| New Python packages | 8 |
