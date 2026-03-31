# V2 Pipeline Research Index - JobRadar

> **Date:** 2026-03-20 (updated 2026-03-30) | **Agents:** 5+6 | **Coverage:** Dedup, Resume, Form Filling, Learning/KB, Local Stack, Firecrawl, Guardrails/Evals, Stealth Scraping, Rust CLI/MCP, ML/NLP/DL Assessment, Rust/Go/C++ Optimization
>
> Historical note on `2026-03-27`: parts of the dedup/search, resume, and form-filling roadmap are no longer purely exploratory. Company/title/location normalization, freshness scoring, the first hybrid-search slice, multi-format resume parsing plus ATS validation, analytics patterns, resume preview/export, and the recovered auto-apply extractor/adapter/safety path were selectively promoted into the live branch and are now tracked in `docs/current-state/02-backend.md` plus `docs/repo-hardening/05-implementation-traceability-matrix.md`. The non-promoted branch-era variants below are historical/archive material unless explicitly reintroduced.

## How to Use This Index

1. Read this file first to understand the landscape.
2. Open only the segment file relevant to your current work.
3. Treat these files as exploratory or archived material unless a capability is explicitly promoted into `docs/current-state/`.
4. Treat the phase checklists below as historical research sequencing notes, not live commitments.

## Segment Files

| File | Domain | Key Decisions |
|------|--------|---------------|
| [01-smart-dedup.md](01-smart-dedup.md) | Job deduplication pipeline | ATS native IDs, RapidFuzz, ONNX embeddings, company blocking |
| [02-resume-pipeline.md](02-resume-pipeline.md) | Resume/cover letter lifecycle | Multi-format parsing, Typst/WeasyPrint, 4-stage tailoring, learning loop |
| [03-form-filling.md](03-form-filling.md) | Auto-apply and form filling | A11y tree extraction, ATS adapters, Lever API, Workday shadow DOM |
| [04-learning-kb.md](04-learning-kb.md) | Personal learning and knowledge base | SQL analytics, pgvector, scikit-learn predictions, custom RAG |
| [05-local-stack.md](05-local-stack.md) | Open-source local-first tooling | Ollama+Qwen3, nomic-embed, pgvector, PyMuPDF4LLM, Typst, Crawlee |
| [06-firecrawl-site-mapping.md](06-firecrawl-site-mapping.md) | One-time site profiling with Firecrawl | `/map` + `/extract` for CSS selectors, tier classification, Crawl4AI alternative, $83 one-time cost |
| [07-prompt-guardrails-and-evals.md](07-prompt-guardrails-and-evals.md) | Resume/cover letter guardrails and eval | Guardrails AI validators, no-fabrication pipeline, promptfoo + DeepEval, golden test sets (145 cases) |
| [08-stealth-scraping-at-scale.md](08-stealth-scraping-at-scale.md) | Stealth scraping 1,500 sites on 16GB RAM | camoufox/nodriver tiers, memory budget, 30-min staggered batches, anti-bot evasion, legal analysis |
| [09-rust-cli-and-mcp.md](09-rust-cli-and-mcp.md) | Rust CLI architecture + MCP server | clap v4, rmcp MCP SDK, agent-friendly JSON output, Rust/Python sidecar boundary |
| [10-ml-nlp-dl-agents-assessment.md](10-ml-nlp-dl-agents-assessment.md) | ML/NLP/DL/Agents honest assessment | ML MAYBE after 200+ apps, NLP NO, DL YES (embeddings only), Agents YES (deterministic hybrid) |
| [11-rust-go-cpp-backend-optimization.md](11-rust-go-cpp-backend-optimization.md) | Rust/Go/C++ backend optimization | I/O vs CPU analysis, Rust for scraping/PDF/CLI, Go NOT NEEDED, C++ NOT NEEDED |
| [rust-cli-agent-tool-research.md](rust-cli-agent-tool-research.md) | Earlier Rust CLI / agent tooling draft | Archived overlap with `09-rust-cli-and-mcp.md`; kept only for traceability |

## Promotion Status Snapshot

- `01-smart-dedup.md`: `PARTIALLY_ADOPTED`
  - normalization, freshness scoring, the first hybrid-search slice, and ATS identity persistence on `jobs` are now live on `main`
- `02-resume-pipeline.md`: `PARTIALLY_ADOPTED`
  - multi-format parsing, structured IR persistence, ATS validation, template preview, and PDF export are live; the branch-era proposal/session model is archived
- `03-form-filling.md`: `PARTIALLY_ADOPTED`
  - form extraction, field mapping, Workday plus Greenhouse/Lever adapter coverage, safety-layer wiring, and operator run/pause/list/stats coverage are live; broader operator UX and checkpointing are not
- `04-learning-kb.md`: `EXPLORATORY`
- `05-local-stack.md`: `ARCHIVED_RESEARCH`
- `06-firecrawl-site-mapping.md`: `EXPLORATORY` - one-time site profiling pattern for 1,500 targets
- `07-prompt-guardrails-and-evals.md`: `EXPLORATORY` - guardrail + eval architecture for resume/cover letter generation
- `08-stealth-scraping-at-scale.md`: `EXPLORATORY` - stealth scraping at scale within 16GB RAM / 30-min cycle constraint
- `09-rust-cli-and-mcp.md`: `EXPLORATORY` - Rust CLI + MCP server architecture for agent-friendly interface
- `10-ml-nlp-dl-agents-assessment.md`: `EXPLORATORY` - honest assessment of ML/NLP/DL/Agents need at single-user scale
- `11-rust-go-cpp-backend-optimization.md`: `EXPLORATORY` - Rust/Go/C++ cost-benefit for backend performance paths
- `rust-cli-agent-tool-research.md`: `ARCHIVED_RESEARCH` - older overlapping Rust CLI/agent-tooling draft kept for branch-history traceability

## Archived Branch-Era Variants

- The branch-era `HybridLLMRouter` / local-first fallback stack remains historical research and is not part of the committed live runtime.
- The branch-era 4-stage resume proposal/session approval flow is archived in favor of the current direct tailor + preview/export + council workflow.
- The branch-era interview prep-package persistence model is archived in favor of the current interview prep/session flow.
- `rust-cli-agent-tool-research.md` is retained as an archived precursor to `09-rust-cli-and-mcp.md`, not as a co-equal active research document.

## Unified Local Stack (Cross-Segment Winners)

| Category | Tool | Used By |
|----------|------|---------|
| LLM Inference | Ollama + Qwen3-8B (Q5_K_M) | Resume, Form Filling, Learning |
| Fast LLM | Qwen3-4B (Q4_K_M) | Form field classification |
| Embeddings | nomic-embed-text (768d, ONNX) | Dedup, Resume KB, Learning |
| Vector Search | pgvector (existing Postgres) | All segments |
| PDF Reading | PyMuPDF4LLM | Resume ingestion |
| PDF Generation | WeasyPrint (server) + `@react-pdf/renderer` (client) | Resume rendering |
| Browser Automation | Crawlee-Python + Playwright | Form filling, scraping |
| Anti-Detection | Camoufox / nodriver (fallback) | Form filling |
| Fuzzy Matching | RapidFuzz | Dedup, form field matching |
| Analytics | DuckDB (optional) / SQL on Postgres | Learning system |
| Full-Text Search | PostgreSQL FTS + pgvector hybrid | Job search |

## New Dependencies Summary

| Package | Size | Why |
|---------|------|-----|
| `rapidfuzz>=3.0` | ~2MB | Fuzzy string matching (dedup + forms) |
| `onnxruntime>=1.17` | ~15MB | Fast CPU embeddings |
| `pymupdf4llm` | ~5MB | PDF parsing for resumes |
| `crawlee[playwright]` | ~10MB | Production browser automation |
| `weasyprint` | ~20MB | Server-side PDF generation |
| Ollama (daemon) | ~50MB + models | Local LLM inference |
| Qwen3-8B Q5_K_M (model) | ~6GB | Primary LLM |
| nomic-embed-text (model) | ~500MB | Embeddings |

**Total new footprint:** ~7GB (mostly LLM model weights)
**Peak RAM (all active):** ~17GB of 64GB available

## Implementation Priority (Historical Research View Only)

These checklists are preserved as research sequencing notes. They do not override `docs/current-state/`, `docs/audit/`, or `docs/repo-hardening/`.

### Phase 1 - Foundation (Week 1-2)
- [ ] Add `rapidfuzz`, `onnxruntime` to deps
- [x] Smart dedup: ATS ID extraction in live Greenhouse, Lever, and Workday scrapers plus persisted ATS identity columns on `jobs`
- [x] Smart dedup: Company/title normalization + blocking (partially promoted to the live dedup/search path)
- [ ] Learning: SQL PatternDetector on existing tables

### Phase 2 - Resume Pipeline (Week 3-4)
- [ ] Multi-format resume parsing (PDF, DOCX, LaTeX)
- [ ] Structured IR (JSON Resume extended schema)
- [ ] Template-based PDF rendering (WeasyPrint)
- [ ] React-pdf live preview in frontend

### Phase 3 - Form Filling Core (Week 5-6)
- [ ] ATS detector + A11y tree form extractor
- [ ] Static field mapping KB (regex patterns)
- [ ] Lever API adapter (no browser needed)
- [ ] Greenhouse browser adapter
- [ ] Wizard handler with checkpointing

### Phase 4 - Local LLM Integration (Week 7-8)
- [ ] Ollama setup + Qwen3 model download
- [ ] HybridLLMRouter (local-first, cloud fallback) [archived historical variant]
- [ ] LLM-powered field classification for unknown forms
- [ ] 4-stage resume tailoring with local LLM [archived historical variant]
- [ ] Cover letter generation

### Phase 5 - Learning Loop (Week 9-10)
- [ ] Outcome tracking (which resume -> which result)
- [ ] HistGradientBoosting match predictor
- [ ] RAG over personal docs (custom 100-line pipeline)
- [ ] Insight generation on dashboard

### Phase 6 - Polish and Hard ATS (Week 11-12)
- [ ] Workday adapter (shadow DOM, multi-step)
- [ ] iCIMS adapter (iframes)
- [ ] Simhash replacement with embedding-based near-dedup
- [ ] Dedup feedback loop + admin review UI
