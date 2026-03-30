# Rust CLI Architecture + MCP Server for Agent-Friendly Job Search OS

**Date: 2026-03-28 | Research basis: Web search + training knowledge**

---

## 1. Why a Rust CLI?

### The Vision
Build JobRadar's core operations as a Rust CLI binary so that:
- AI agents (Claude Code, Codex) can invoke it as a tool
- Humans can use it directly from the terminal
- The React frontend consumes the same interface via HTTP
- Performance-critical paths (scraping, parsing, PDF gen) run at native speed

### The Precedent
Major Python ecosystem tools have been rewritten in Rust with dramatic results:
- **Ruff** (linter): 10-100x faster than existing Python linters
- **uv** (package manager): orders of magnitude faster than pip
- **Pydantic-core**: 17x faster validation after Rust rewrite
- **Polars**: DataFrames in Rust with Python bindings, 10-30x faster than pandas

Sources:
- [JetBrains: Rust vs Python](https://blog.jetbrains.com/rust/2025/11/10/rust-vs-python-finding-the-right-balance-between-speed-and-simplicity/)
- [The New Stack: Rust Python's Performance Engine](https://thenewstack.io/rust-pythons-new-performance-engine/)

---

## 2. Rust CLI Framework: clap v4

### Why clap
- **De facto standard**: Used by ripgrep, bat, fd, delta, starship, cargo itself
- **Derive macros**: Describe CLI as a Rust struct, clap generates the parser
- **Subcommand architecture**: `jobradar scrape`, `jobradar apply`, `jobradar resume generate`
- **Performance**: 30% faster parsing than previous versions, 20% faster startup with subcommands
- **Shell completions**: Auto-generated for bash, zsh, fish, PowerShell

### Architecture Pattern

```
jobradar (binary)
  |-- scrape
  |     |-- run          # Run a scrape cycle
  |     |-- status       # Check scraper health
  |     |-- targets      # List/add/remove targets
  |     |-- profile      # Profile a new site (Firecrawl/Crawl4AI)
  |
  |-- apply
  |     |-- run          # Auto-apply to a job
  |     |-- review       # Review pending applications
  |     |-- history      # Application history
  |
  |-- resume
  |     |-- generate     # Generate tailored resume
  |     |-- preview      # Preview in terminal (Markdown)
  |     |-- export       # Export to PDF/DOCX/LaTeX
  |     |-- list         # List resume versions
  |
  |-- jobs
  |     |-- list         # List jobs with filters
  |     |-- search       # Semantic + keyword search
  |     |-- detail       # Show job details
  |     |-- score        # Score job-profile match
  |
  |-- pipeline
  |     |-- view         # Kanban-style pipeline view
  |     |-- move         # Move application between stages
  |     |-- stats        # Pipeline analytics
  |
  |-- interview
  |     |-- prep         # Generate interview prep bundle
  |     |-- practice     # Interactive practice session
  |
  |-- copilot
  |     |-- ask          # Ask the AI copilot
  |
  |-- config
  |     |-- init         # Initialize configuration
  |     |-- set          # Set config values
  |     |-- show         # Show current config
  |
  |-- serve
  |     |-- api          # Start HTTP API server
  |     |-- mcp          # Start MCP server
```

Sources:
- [Rust CLI Patterns 2026](https://dasroot.net/posts/2026/02/rust-cli-patterns-clap-cargo-configuration/)
- [Hemaks: Production-Ready CLI in Rust](https://hemaks.org/posts/building-production-ready-cli-tools-in-rust-with-clap-from-zero-to-hero/)
- [Clap v4 Tutorial](https://www.rustadventure.dev/introducing-clap/clap-v4/initializing-a-new-rust-cli-project)

---

## 3. Agent-Friendly CLI Design

### JSON Output Mode (Critical for Agents)

Every command MUST support `--output json` (or `--json`) for machine-parseable output:

```
# Human mode (default)
$ jobradar jobs list --limit 5
ID        Title                    Company      Score
abc123    Backend Engineer         Acme Corp    0.87
def456    Senior SWE               BigCo        0.82

# Machine mode (for agents)
$ jobradar jobs list --limit 5 --json
[{"id":"abc123","title":"Backend Engineer","company":"Acme Corp","score":0.87},...]
```

### Structured Errors

```json
{"error": true, "code": "SCRAPE_TIMEOUT", "message": "Timed out after 10s", "target": "careers.acme.com", "retry_safe": true}
```

### Design Principles (from GitHub CLI `gh`)

The GitHub CLI is the gold standard for agent-friendly CLI design:
- Every command has `--json` flag with field selection (`--json name,url`)
- Structured exit codes (0 = success, 1 = error, 2 = usage error)
- `--jq` flag for inline JSON filtering
- No interactive prompts when `--json` is set
- Consistent flag naming across all subcommands

---

## 4. MCP Server in Rust

### Official Rust MCP SDK

The `rmcp` crate provides the official Model Context Protocol SDK for Rust:
- **GitHub**: modelcontextprotocol/rust-sdk
- **Features**: Server implementation, procedural macros, stdio transport
- **Protocol version**: 2025-11-25 spec (latest)

### Key MCP Features for JobRadar

- **Tools**: Each CLI command becomes an MCP tool that agents can call
- **Resources**: Job listings, resume versions, pipeline state as MCP resources
- **Tasks**: Long-running operations (scrape cycles) as async MCP tasks with progress reporting
- **Elicitation**: Structured mechanism for server to request user input mid-operation (e.g., CAPTCHA solving, application review)

### Template: mcp-rs-template

- **GitHub**: linux-china/mcp-rs-template
- Demonstrates implementing MCP CLI server in Rust
- Covers stdio transport (for Claude Code integration)

### 2026 MCP Roadmap

The MCP spec continues to evolve with new features:
- OAuth 2.1 for standardized auth flows
- Tasks for long-running operations
- Elicitation for structured user prompts

Sources:
- [MCP Rust SDK](https://github.com/modelcontextprotocol/rust-sdk)
- [MCP Server Template](https://github.com/linux-china/mcp-rs-template)
- [2026 MCP Roadmap](http://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/)
- [Why Rust for MCP (Stackademic)](https://stackademic.com/blog/why-rust-is-the-right-language-for-the-model-context-protocol-mcp)
- [MCP Build Server Docs](https://modelcontextprotocol.io/docs/develop/build-server)

---

## 5. What Goes in Rust vs What Stays in Python

### Rust (Performance-Critical, Stateless)

| Component | Crate | Speedup vs Python |
|-----------|-------|-------------------|
| HTTP scraping | reqwest + tokio | 5-15x, 60% less memory |
| HTML parsing | scraper / lol_html | 10-50x |
| ATS fingerprinting | Custom (regex + string matching) | 10x |
| PDF generation | typst (as library) | 100x+ (5ms vs 500ms+) |
| SimHash / dedup | Custom | 20x |
| JSON parsing | serde_json | 10x |
| CLI argument parsing | clap | N/A (Rust-only) |
| MCP server | rmcp | N/A (Rust-only) |

### Python (LLM/ML/ORM, Stateful)

| Component | Library | Why Python |
|-----------|---------|-----------|
| LLM API calls | httpx + Anthropic/OpenAI SDKs | SDK ecosystem, prompt engineering |
| Database ORM | SQLAlchemy async | Mature, async, migration support |
| ML inference | scikit-learn, ONNX | Model ecosystem |
| Embedding generation | sentence-transformers | HuggingFace ecosystem |
| Job queue management | arq | Redis-backed, Python-native |
| Guardrails | guardrails-ai | Python-only library |
| Prompt evaluation | promptfoo (subprocess) | Node.js CLI called from Python |

### Integration Pattern: HTTP Sidecar

```
Rust CLI (jobradar binary)
  |-- Handles: scraping, parsing, PDF gen, CLI, MCP server
  |-- Calls: Python backend via localhost HTTP for LLM/ML/DB operations
  |
Python Backend (FastAPI, existing)
  |-- Handles: LLM calls, DB operations, ML inference, guardrails
  |-- Accessed: via localhost:8000/api/v1/*
```

This is the same pattern as the completion program's "Rust sidecar" design, but inverted:
- The Rust binary is the **primary interface** (CLI + MCP)
- The Python backend is the **service layer** (LLM + DB)

---

## 6. Cross-Platform Distribution

### Build Targets

| Target | Triple | Notes |
|--------|--------|-------|
| Windows x64 | x86_64-pc-windows-msvc | Primary dev machine |
| macOS Intel | x86_64-apple-darwin | |
| macOS Apple Silicon | aarch64-apple-darwin | |
| Linux x64 | x86_64-unknown-linux-gnu | CI and Docker |

### Tools

- **cross-rs**: Cross-compilation without native toolchains (Docker-based)
- **cargo-dist**: Automated release builds + GitHub release artifacts
- **cargo-release**: Version bumping and release workflow

### Binary Size Optimization

- `opt-level = "z"` (optimize for size)
- `lto = true` (link-time optimization)
- `strip = true` (strip debug symbols)
- Typical CLI binary: 5-15MB (single static binary, no runtime dependencies)

### Distribution Channels

- **GitHub Releases**: cargo-dist automates this
- **cargo install jobradar**: For Rust users
- **Docker**: Multi-stage build, final image ~20MB

---

## 7. Performance Benchmarks (from web research)

### HTTP Scraping

- **Rust (reqwest + tokio)**: 10,000 pages in ~45 seconds
- **Python (httpx + asyncio)**: 10,000 pages in ~200-400 seconds
- **spider-rs**: 100K+ pages in minutes, 60% less memory than Puppeteer
- **Ratio**: Rust is 5-10x faster, but for I/O-bound tasks the gap narrows to 2-5x

### Memory Usage

- **Rust scraper**: Holds steady at ~50MB on large jobs
- **Python scraper**: Can balloon to ~400MB
- **Ratio**: 8x less memory in Rust

### PDF Generation

- **Typst (Rust)**: 5ms per document (as library), 100ms with font discovery
- **WeasyPrint (Python)**: 500ms-2000ms per document (simple resume)
- **Ratio**: 100-400x faster

### API Server

- **Axum (Rust)**: ~5-6% faster than FastAPI in benchmarks, but FastAPI achieves 80-90% of Rust practical performance for CRUD
- **For DB-bound operations**: Language barely matters -- DB is the bottleneck

Sources:
- [WebScraping.AI: Rust vs Python scraping](https://webscraping.ai/faq/rust/how-does-rust-compare-to-python-for-web-scraping-tasks)
- [spider-rs benchmarks](https://github.com/spider-rs/spider/blob/main/benches/BENCHMARKS.md)
- [Typst automated PDF generation](https://typst.app/blog/2025/automated-generation/)
- [FastAPI vs Axum benchmarks](https://github.com/zachcoleman/fastapi-vs-axum)
- [Evomi: Rust web scraping 2025](https://evomi.com/blog/rust-web-scraping-2025-steps-tools-proxies)

---

## 8. Recommended Crate Stack

| Category | Crate | Purpose |
|----------|-------|---------|
| CLI | clap v4 | Argument parsing, subcommands |
| HTTP | reqwest | Async HTTP client |
| Async runtime | tokio | Async runtime |
| HTML parsing | scraper | CSS selector-based extraction |
| Streaming HTML | lol_html | Cloudflare's streaming parser (memory-efficient) |
| JSON | serde + serde_json | Serialization |
| HTTP server | axum | For MCP server and optional API |
| MCP | rmcp | Model Context Protocol SDK |
| PDF | typst (as library) | Resume PDF generation |
| Logging | tracing | Structured logging |
| Error handling | anyhow + thiserror | Error types |
| Config | config + toml | Configuration files |
| Progress | indicatif | Progress bars and spinners |
| Database | sqlx | Direct PostgreSQL queries (optional, or call Python) |

---

## 9. Implementation Strategy

### Phase 1: Scraping Sidecar (Highest ROI)
- Build `jobradar scrape` subcommand
- reqwest + tokio for API-backed ATS (Greenhouse, Lever, Ashby)
- scraper for HTML parsing
- JSON output for Python backend to consume
- ~2-3 weeks for Shriyansh (learning Rust)

### Phase 2: PDF Generation
- Integrate typst as library
- `jobradar resume export --format pdf`
- Replace WeasyPrint for 100x speedup
- ~1 week

### Phase 3: MCP Server
- `jobradar serve mcp` using rmcp crate
- Expose scraping, resume gen, job search as MCP tools
- Claude Code can then use JobRadar directly
- ~2 weeks

### Phase 4: Full CLI
- Remaining subcommands (jobs, pipeline, apply, interview, copilot)
- These call into the Python backend via HTTP
- Rust handles CLI UX, Python handles business logic
- ~4-6 weeks

---

## 10. Honest Assessment

### Worth doing in Rust
- **Scraping engine**: Clear 5-10x performance + 8x memory win. This is the highest-ROI rewrite.
- **PDF generation**: Typst is 100x faster and produces better typography.
- **MCP server**: Rust is ideal for a long-running server process with low memory footprint.
- **CLI binary**: Single static binary, instant startup, cross-platform.

### Not worth rewriting in Rust
- **LLM API calls**: I/O-bound, language doesn't matter. Python SDKs are better maintained.
- **Database ORM**: SQLAlchemy is mature and powerful. sqlx works but requires manual SQL.
- **ML inference**: Python ecosystem (scikit-learn, ONNX) is unmatched.
- **Prompt engineering**: Needs rapid iteration; Python is faster to develop.
- **React frontend**: Obviously stays as-is.

### The Hybrid is the Right Answer
Don't rewrite the whole backend. Build a Rust CLI that handles the performance-critical paths and delegates to the existing Python backend for everything else. This is exactly what Ruff, uv, and Pydantic-core did -- and it worked.
