# Rust, Go, and C++ for Backend Optimization: Honest Cost-Benefit Analysis

**Date: 2026-03-28 | Research basis: Web search + training knowledge**

---

## 1. Where Python is the Bottleneck (And Where It Isn't)

### The Critical Insight: Most of JobRadar is I/O-Bound

| Operation | Bound By | Language Impact |
|-----------|----------|----------------|
| API calls to LLM providers | Network I/O | **None** -- waiting for HTTP response |
| Database queries | PostgreSQL I/O | **None** -- DB is the bottleneck |
| Redis operations | Network I/O | **None** |
| HTTP scraping (API ATS) | Network I/O | **Minimal** -- 2-5x gain from Rust |
| Browser automation | Browser rendering | **None** -- Playwright is the bottleneck |
| HTML parsing | **CPU** | **10-50x gain from Rust** |
| PDF generation | **CPU** | **100-400x gain from Rust (Typst)** |
| SimHash computation | **CPU** | **20x gain from Rust** |
| Embedding generation | **CPU/GPU** | ONNX runtime is C++ under the hood either way |
| Text processing (normalize, clean) | **CPU** | **5-10x gain from Rust** |
| JSON serialization | **CPU** | **10x gain from Rust (serde)** |

**Conclusion**: Only CPU-bound operations benefit from a language rewrite. Most of JobRadar's operations are I/O-bound.

---

## 2. Rust: The Clear Winner for Performance-Critical Paths

### Benchmarks (from web research)

| Task | Python | Rust | Speedup | Memory |
|------|--------|------|---------|--------|
| Scrape 10K pages (HTTP) | ~200-400s | ~45s | 5-10x | Rust: 50MB vs Python: 400MB |
| HTML parse (large doc) | ~50ms | ~1-5ms | 10-50x | Rust: flat, Python: grows |
| PDF generation (resume) | ~500-2000ms (WeasyPrint) | ~5ms (Typst) | 100-400x | Rust: 20MB vs Python: 200MB |
| JSON parse (10MB) | ~100ms | ~10ms | 10x | |
| Pydantic validation | Baseline | 17x (pydantic-core) | 17x | |
| Python linting | Baseline | 10-100x (Ruff) | 10-100x | |

### Rust Integration Patterns

**Option A: PyO3 + maturin (Rust extension for Python)**
- Write performance-critical functions in Rust
- Call directly from Python (no HTTP overhead)
- Used by: Pydantic-core, Ruff, uv, Polars
- Best for: HTML parsing, SimHash, text processing
- **6x performance boost** demonstrated in production (dependency graph algorithms)

**Option B: HTTP Sidecar (separate process)**
- Rust binary runs as a separate service
- Python calls via localhost HTTP
- Used by: completion program's original design
- Best for: scraping engine, PDF generation, MCP server
- Adds ~1ms latency per call (negligible)

**Option C: Subprocess (CLI)**
- Python calls Rust binary via `subprocess`
- Best for: one-off operations (PDF export, batch scrape)
- Adds ~50-100ms startup overhead per invocation

**Recommendation**: Option B (sidecar) for scraping + PDF gen, Option A (PyO3) for hot-path string ops.

Sources:
- [JetBrains: Rust vs Python](https://blog.jetbrains.com/rust/2025/11/10/rust-vs-python-finding-the-right-balance-between-speed-and-simplicity/)
- [Medium: Python vs Rust API Performance](https://medium.com/@puneetpm/python-vs-rust-our-api-performance-story-will-shock-you-73269866e0c4)
- [The New Stack: Rust Python's Performance Engine](https://thenewstack.io/rust-pythons-new-performance-engine/)
- [Talk Python: Building Rust Extensions](https://talkpython.fm/episodes/show/487/building-rust-extensions-for-python)

---

## 3. Go: The Middle Ground

### Where Go Shines

- **Goroutines**: Lighter than Python coroutines, easier than Rust async
- **Fast compilation**: Seconds vs minutes for Rust
- **Simple concurrency model**: No borrow checker, no lifetime annotations
- **Cross-compilation**: Built-in, trivial (`GOOS=windows GOARCH=amd64 go build`)
- **Single binary output**: Like Rust, no runtime dependencies

### Go vs Rust for This Project

| Criterion | Go | Rust |
|-----------|-----|------|
| HTTP scraping speed | 3-7x faster than Python | 5-15x faster than Python |
| Memory efficiency | Good | Better (no GC pauses) |
| Learning curve | Moderate (Shriyansh is learning) | Steep (borrow checker) |
| Development speed | 2-3x faster than Rust | Slower |
| PDF generation | No Typst equivalent | Typst is Rust-native |
| MCP server | No official SDK | Official rmcp crate |
| Binary size | ~10-20MB | ~5-15MB |
| Error handling | Verbose (`if err != nil`) | Elegant (`Result<T, E>`) |
| Ecosystem for scraping | Colly (mature) | spider-rs (fast but smaller ecosystem) |

### Go-Specific Tools

- **Colly**: Web scraping framework, ~20K stars, mature, well-documented
- **go-rod**: Chrome DevTools Protocol for browser automation
- **Fiber/Gin**: Fast HTTP frameworks

### Verdict on Go

Go would be a **reasonable choice** if:
- Shriyansh finds Rust's learning curve too steep
- The primary need is concurrent HTTP scraping (goroutines are simpler than Rust async)
- No need for Typst PDF generation or MCP server (which favor Rust)

**But**: Since the completion program already specifies Rust, and Typst + MCP are both Rust-native, **Rust is the better strategic choice** despite the steeper learning curve.

Sources:
- [Dev.to: Golang vs Rust vs Python](https://dev.to/firfircelik/golang-vs-rust-vs-python-battle-of-backend-can)
- [iWebScraping: Fastest Language for Scraping](https://www.iwebscraping.com/fastest-web-scraping-language.php)

---

## 4. C++: Is It Even Relevant?

### Short Answer: No

For this specific project, C++ adds nothing that Rust doesn't do better:

| Criterion | C++ | Rust | Winner |
|-----------|-----|------|--------|
| Performance | Equivalent | Equivalent | Tie |
| Memory safety | Manual (use-after-free, buffer overflow) | Compiler-enforced | **Rust** |
| Build system | CMake (complex) | Cargo (simple) | **Rust** |
| Package manager | vcpkg/Conan (fragmented) | crates.io (unified) | **Rust** |
| Cross-compilation | Complex | cross-rs (simple) | **Rust** |
| Python interop | pybind11 | PyO3 (more ergonomic) | **Rust** |
| Learning curve | Extreme (UB, templates) | Steep (borrow checker) | **Rust** |
| New projects in 2025+ | Declining for new work | Growing rapidly | **Rust** |

### Where C++ IS Under the Hood

- **ONNX Runtime**: C++ core with Python bindings. You're already using it via Python. No need to call it from C++ directly.
- **PostgreSQL**: Written in C. You interact via SQL, not C APIs.
- **Chromium/Playwright**: C++ browser engine. You interact via CDP, not C++.

**Recommendation**: Do not write any C++ for JobRadar. All C++ benefits are already captured through existing tools' Python bindings.

Source:
- [JetBrains: Rust vs C++ 2026](https://blog.jetbrains.com/rust/2025/12/16/rust-vs-cpp-comparison-for-2026/)

---

## 5. The 2026 Polyglot Pattern

### Emerging Industry Consensus

From the web research, a clear pattern emerges for AI-heavy backends in 2026:

```
Python  -> Rapid model development, LLM integration, ORM, business logic
Rust    -> Efficient inference serving, performance-critical data processing
Go      -> Orchestration, control planes, infrastructure tooling
```

### For JobRadar Specifically

```
Python (keep existing)
  |-- FastAPI API server
  |-- LLM API calls (Anthropic, OpenAI, OpenRouter, Ollama)
  |-- SQLAlchemy ORM + Alembic migrations
  |-- ML inference (scikit-learn, ONNX via Python bindings)
  |-- Guardrails pipeline
  |-- arq workers (queue management)
  |-- Business logic (all domain services)

Rust (new sidecar + CLI)
  |-- Scraping engine (reqwest + tokio, 5-10x faster)
  |-- HTML parsing (scraper/lol_html, 10-50x faster)
  |-- PDF generation (Typst, 100-400x faster)
  |-- CLI interface (clap v4)
  |-- MCP server (rmcp)
  |-- ATS fingerprinting
  |-- SimHash / dedup computation
  |-- Content hashing

Go: NOT NEEDED
  |-- Everything Go does, Rust does better for this project
  |-- Only consider if Rust learning curve is unacceptable

C++: NOT NEEDED
  |-- All C++ benefits already captured via Python bindings
```

---

## 6. Specific Component Analysis

### a. Scraping Engine: Rust Sidecar (reqwest + tokio)

**Current**: Python httpx + asyncio + Playwright
**Proposed**: Rust reqwest + tokio for HTTP, keep Playwright for JS-heavy sites
**Gain**: 5-10x speed, 8x less memory for HTTP scraping
**Effort**: 2-3 weeks (building from spider-rs patterns)
**Verdict**: **DO IT** -- highest ROI optimization

### b. HTML Parsing: Rust (scraper / lol_html)

**Current**: Python BeautifulSoup / lxml
**Proposed**: Rust scraper crate or Cloudflare's lol_html (streaming)
**Gain**: 10-50x faster, constant memory (lol_html streams)
**Effort**: 1 week (integrate into scraping sidecar)
**Verdict**: **DO IT** -- natural part of the scraping sidecar

### c. PDF Generation: Typst (Rust)

**Current**: WeasyPrint (Python, 500ms-2000ms per resume)
**Proposed**: Typst as Rust library (5ms per resume, better typography)
**Gain**: 100-400x faster, better output quality
**Effort**: 1-2 weeks
**Verdict**: **DO IT** -- dramatic improvement for trivial effort

### d. Deduplication: Rust SimHash

**Current**: Python SimHash
**Proposed**: Rust SimHash implementation
**Gain**: ~20x faster
**Effort**: 1 week
**Verdict**: **MAYBE** -- only matters at high volume. Current Python version works fine for 1,500 sites.

### e. API Server: Keep FastAPI

**Current**: FastAPI (Python)
**Proposed**: Axum (Rust) or Gin (Go)
**Gain**: ~5-6% faster (Axum vs FastAPI benchmark), but FastAPI achieves 80-90% of Rust practical performance
**Effort**: 8-12 weeks (full rewrite)
**Verdict**: **DON'T DO IT** -- 5% gain doesn't justify months of rewrite. DB is the bottleneck anyway.

### f. Queue Workers: Keep Python arq

**Current**: Python arq workers
**Proposed**: Rust/Go workers
**Gain**: Minimal -- workers are I/O-bound (waiting for scrape results, LLM responses)
**Effort**: 4-6 weeks
**Verdict**: **DON'T DO IT** -- workers spend 95% of time waiting on I/O

### g. Embedding Computation: Keep Python + ONNX

**Current**: sentence-transformers with ONNX runtime
**Proposed**: Calling ONNX from Rust
**Gain**: ~0% (ONNX runtime is C++ regardless of caller)
**Effort**: 2-3 weeks
**Verdict**: **DON'T DO IT** -- same C++ engine underneath

### h. Database Queries: Language Doesn't Matter

**Current**: SQLAlchemy async (Python)
**Proposed**: sqlx (Rust) or pgx (Go)
**Gain**: ~0% for I/O-bound queries. SQLAlchemy's ORM features (relationships, migrations) would be lost.
**Effort**: 6-8 weeks
**Verdict**: **ABSOLUTELY DON'T DO IT**

---

## 7. Real-World Case Studies

### Discord: Go -> Rust (2020)
- Rewrote a critical service from Go to Rust
- Eliminated GC-related latency spikes
- **Lesson**: Relevant for real-time systems with strict latency requirements. JobRadar is not real-time.

### Dropbox: Python -> Rust (2020)
- Rewrote file sync engine in Rust
- Dramatic performance and reliability improvement
- **Lesson**: Relevant for CPU-intensive file processing. Partially applicable to scraping/parsing.

### Pydantic-core: Python -> Rust (2023)
- Rewrote validation core in Rust via PyO3
- 17x faster validation
- **Lesson**: Most applicable -- keep Python interface, rewrite hot paths in Rust.

### Ruff/uv: Pure Rust replacing Python tools
- 10-100x performance improvements
- **Lesson**: When the entire tool is CPU-bound (linting, package resolution), full Rust rewrite makes sense.

---

## 8. Honest Assessment: Is It Worth It?

### For a Single-User App on 16GB RAM

The actual bottleneck is almost certainly **NOT** Python's speed. It's:
1. **Network latency** (LLM API calls, scraping HTTP requests)
2. **Database I/O** (PostgreSQL queries)
3. **Browser rendering** (Playwright page loads)
4. **LLM inference time** (waiting for Claude/GPT response)

Python with asyncio handles all of these fine. The 2,000 RPS that a tuned FastAPI achieves is far more than a single user will ever need.

### Where Rewriting IS Justified

| Component | Justification |
|-----------|--------------|
| Scraping engine | Memory efficiency (8x) matters on 16GB. Speed (5-10x) enables 30-min cycles. |
| PDF generation | 100-400x speedup makes resume preview feel instant instead of sluggish. |
| CLI + MCP | Rust produces a single static binary. Agent-friendly. Cross-platform. |
| HTML parsing | 10-50x speedup with constant memory. Natural part of scraping engine. |

### Where Rewriting is NOT Justified

| Component | Why Not |
|-----------|---------|
| API server | 5% gain. DB is the bottleneck. |
| Queue workers | I/O-bound. Language doesn't matter. |
| LLM integration | Python SDKs are better. Network-bound. |
| Database ORM | SQLAlchemy is irreplaceable for productivity. |
| ML/embeddings | ONNX runtime is C++ regardless. |
| Guardrails | Python-only library. |

### Development Velocity Cost

Maintaining 2 languages (Python + Rust) adds:
- ~30% overhead in build/CI complexity
- Need for clear interface boundaries
- Two sets of error handling patterns
- Two sets of testing frameworks

**This is acceptable** if the Rust scope is well-bounded (scraping, PDF, CLI). It becomes a problem if it creeps into business logic.

---

## 9. Recommended Implementation Order

### Phase 1: Rust Scraping Sidecar (Highest ROI)
- reqwest + tokio for HTTP scraping
- scraper for HTML parsing
- axum for localhost API (`POST /batch-scrape`, `GET /health`)
- Replaces the Python scraping execution layer for HTTP-only sites
- **Expected gain**: 5-10x speed, 8x less memory, enables 1,500 sites in <15 min

### Phase 2: Typst PDF Generation
- typst as Rust library, called via sidecar API
- `POST /render-pdf` endpoint
- Replace WeasyPrint
- **Expected gain**: 100-400x faster resume PDF generation

### Phase 3: Rust CLI + MCP Server
- clap v4 CLI wrapping sidecar + Python backend
- rmcp MCP server for agent integration
- **Expected gain**: Agent-friendly interface, cross-platform binary

### Phase 4: PyO3 Extensions (Optional)
- If specific Python hot paths are identified via profiling
- String normalization, SimHash, content hashing
- **Expected gain**: 5-20x for targeted hot paths

Sources:
- [Medium: FastAPI gives Rust a good run](https://medium.com/@almirx101/fastapi-the-surprising-performance-workhorse-that-gives-rust-a-good-run-23fc52dd815c)
- [Jonvet: Python vs Rust web servers](https://www.jonvet.com/blog/benchmarking-python-rust-web-servers)
- [FastAPI vs Axum GitHub benchmark](https://github.com/zachcoleman/fastapi-vs-axum)
- [PyO3 Maturin Guide](https://www.maturin.rs/)
- [Slideshare: Rustifying Python 2025](https://www.slideshare.net/slideshow/rustifying-a-python-package-in-2025-with-pyo3-and-maturin/278593335)
