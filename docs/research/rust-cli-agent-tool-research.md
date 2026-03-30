# Research: Building JobRadar as a Rust-Based CLI That AI Agents Can Use

**Date:** 2026-03-28
**Status:** Research document -- no code changes

---

## Table of Contents

1. [Rust CLI Framework Selection](#1-rust-cli-framework-selection)
2. [Agent-Friendly CLI Design](#2-agent-friendly-cli-design)
3. [Architecture: What Goes in Rust vs What Stays in Python](#3-architecture-what-goes-in-rust-vs-what-stays-in-python)
4. [CLI Command Structure for a Job Search OS](#4-cli-command-structure-for-a-job-search-os)
5. [MCP Server in Rust](#5-mcp-server-in-rust)
6. [Cross-Platform Distribution](#6-cross-platform-distribution)
7. [Real-World Examples](#7-real-world-examples)
8. [Performance Benchmarks](#8-performance-benchmarks)
9. [Concrete Recommendations](#9-concrete-recommendations)

---

## 1. Rust CLI Framework Selection

### The Landscape

| Framework | Stars | Approach | Status |
|-----------|-------|----------|--------|
| **clap** | 16,247 | Derive macros + builder API | Active, dominant |
| **argh** | ~1,600 | Derive-only, Google-originated | Stable, minimal |
| **bpaf** | ~600 | Combinators, no macros | Niche |

**Recommendation: clap v4 (derive mode)**. It is the de facto standard with 16k+ stars, active maintenance, and adoption by nearly every major Rust CLI project.

### clap v4: Derive vs Builder

clap offers two API styles that can be mixed:

**Derive (recommended for new projects):**
```rust
use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "jobradar", version, about = "Job search OS for humans and agents")]
struct Cli {
    /// Output format: human, json, jsonl
    #[arg(long, default_value = "human", global = true)]
    format: OutputFormat,

    /// Suppress non-essential output
    #[arg(long, short, global = true)]
    quiet: bool,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Search for jobs across all sources
    Search(SearchArgs),
    /// Manage scraping targets and schedules
    Scrape(ScrapeArgs),
    /// Pipeline and application tracking
    Pipeline(PipelineArgs),
    /// Configuration and auth
    Config(ConfigArgs),
}
```

**Builder (useful for dynamic/plugin commands):**
```rust
let cmd = Command::new("jobradar")
    .subcommand(Command::new("search").arg(arg!(--query <QUERY>)))
    .subcommand(Command::new("scrape").arg(arg!(--target <URL>)));
```

**Key derive advantages:**
- Type-safe argument parsing with automatic validation
- Help text generated from doc comments
- Subcommand hierarchies map naturally to enum variants
- Shell completion generation via `clap_complete`
- Value enums for constrained choices (`OutputFormat`, `SortOrder`)

**When to use builder:** dynamic subcommands from plugins, runtime-constructed CLIs, or when you need to avoid the proc-macro compile-time cost in very large builds.

### Essential Companion Crates for CLI Development

| Crate | Stars | Purpose |
|-------|-------|---------|
| `clap_complete` | (part of clap) | Shell completion generation (bash, zsh, fish, powershell) |
| `serde` / `serde_json` | 10,494 | JSON serialization for machine output |
| `indicatif` | 5,092 | Progress bars, spinners, multi-bar support |
| `dialoguer` | 1,565 | Interactive prompts, confirmations, selections |
| `console` | ~3,000 | Terminal colors, styling, terminal size detection |
| `tabled` | ~1,800 | Table formatting for human-readable output |
| `tracing` | ~6,000 | Structured logging and diagnostics |
| `anyhow` / `thiserror` | ~5k / ~4k | Error handling (anyhow for apps, thiserror for libraries) |
| `directories` | ~1,000 | XDG/platform-correct config/data/cache paths |
| `keyring` | ~500 | OS credential store (Windows Credential Manager, macOS Keychain, Linux Secret Service) |
| `tokio` | ~28,000 | Async runtime for concurrent operations |

### Architecture Patterns from Major Rust CLIs

**ripgrep (61,497 stars)** -- the gold standard for Rust CLI architecture:
- Workspace with 10 internal crates: `cli`, `core`, `globset`, `grep`, `ignore`, `matcher`, `pcre2`, `printer`, `regex`, `searcher`
- Each crate has a single, well-defined responsibility
- The `cli` crate is thin: it parses args, wires crates together, and manages output
- The `printer` crate handles both human and machine output formats
- Performance-critical paths are zero-allocation where possible

**starship (55,450 stars)** -- modular prompt with plugin architecture:
- Single binary with a `modules/` directory containing ~50 independent modules
- Each module implements a common trait
- Configuration via TOML with schema validation
- Good example of "many features, single binary" architecture

**bat (57,824 stars)** -- file viewer:
- Clean separation between input handling, syntax highlighting, and output formatting
- Multiple output modes (plain, paging, grid)

**fd (42,210 stars)** -- file finder:
- Parallel directory traversal with rayon
- Demonstrates how to handle streaming results with progress feedback

**delta (29,695 stars)** -- diff viewer:
- Demonstrates complex output formatting with terminal capabilities detection

**zoxide (34,974 stars)** -- smart cd:
- Demonstrates state management (frecency database in SQLite)
- Good model for a CLI that maintains local state/history

---

## 2. Agent-Friendly CLI Design

### Core Principle: The CLI is the API

The critical insight for agent-friendly design is that **the CLI must be a first-class programmatic interface**, not just a human convenience layer on top of an API. When Claude Code or Codex invoke a tool, they need:

1. **Structured output** -- JSON (not just pretty-printed tables)
2. **Predictable exit codes** -- 0 for success, non-zero with specific meanings
3. **Deterministic behavior** -- same input always produces same output shape
4. **Self-describing commands** -- rich help text that agents can parse
5. **No interactive prompts in non-TTY mode** -- auto-detect and fail gracefully
6. **Idempotent operations where possible** -- safe to retry

### The gh CLI Model (Gold Standard for Dual-Mode Design)

The GitHub CLI (`gh`) is the best existing reference for a CLI that serves both humans and machines. Its command structure (extracted from source):

```
gh
├── auth          # login, logout, status, token
├── repo          # create, clone, fork, view, list
├── issue         # create, list, view, close, reopen, edit
├── pr            # create, list, view, checkout, merge, diff, checks
├── codespace     # create, list, ssh, code, ports
├── project       # create, list, view, edit
├── release       # create, list, view, upload, download
├── workflow       # list, view, run, enable, disable
├── run           # list, view, watch, rerun, download
├── api           # raw API access (escape hatch)
├── search        # repos, issues, prs, code, commits
├── config        # get, set, list
├── extension     # install, remove, list, create
├── alias         # set, delete, list
├── secret        # set, list, delete
├── variable      # set, list, delete
├── status        # cross-repo dashboard
├── cache         # list, delete
└── attestation   # verify
```

**Key design decisions from gh that JobRadar should adopt:**

1. **`--json` flag with field selection:**
   ```bash
   gh pr list --json number,title,author,state
   # Output: [{"number":1,"title":"...","author":{"login":"..."},"state":"OPEN"}]
   ```

2. **`--jq` and `--template` for inline transformation:**
   ```bash
   gh pr list --json number,title --jq '.[].title'
   ```

3. **Consistent CRUD verbs:** `create`, `list`, `view`, `edit`, `delete`, `close`

4. **TTY detection for output mode:**
   - TTY (human): colorized tables, truncated fields, interactive prompts
   - Non-TTY (agent/pipe): plain text, full fields, no prompts, no color

5. **`api` escape hatch:** raw access to underlying API for anything the CLI doesn't cover

6. **Web fallback:** `--web` flag to open browser for complex operations

### How AI Agents Invoke CLI Tools

When Claude Code uses a tool, it runs a shell command and reads stdout/stderr. The agent needs:

```bash
# Agent invocation pattern:
jobradar search --query "rust engineer" --location "remote" --format json

# Expected structured response:
{
  "jobs": [...],
  "total": 42,
  "query": {"terms": "rust engineer", "location": "remote"},
  "cached": false,
  "timestamp": "2026-03-28T10:00:00Z"
}
```

**Critical design rules for agent consumption:**

| Rule | Rationale |
|------|-----------|
| Always include a top-level `"ok": true/false` or use exit codes | Agents need to know success/failure unambiguously |
| Include metadata (timestamp, pagination, cache status) | Agents need to know if data is fresh |
| Use consistent field names across all commands | Agents learn patterns; inconsistency causes errors |
| Error responses must be JSON too (with `--format json`) | Agents cannot parse "Error: something went wrong" reliably |
| Support `--format jsonl` for streaming large result sets | Agents can process line-by-line without buffering |
| Include `--dry-run` for destructive operations | Agents can verify before executing |

### MCP Tool Design Patterns

The Model Context Protocol (MCP) defines how AI agents discover and invoke tools. An MCP tool has:

```json
{
  "name": "search_jobs",
  "description": "Search for jobs matching criteria across all configured sources",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "Search terms"},
      "location": {"type": "string"},
      "remote": {"type": "boolean"},
      "limit": {"type": "integer", "default": 20}
    },
    "required": ["query"]
  }
}
```

A Rust CLI can expose the same interface in two modes:
1. **CLI mode:** `jobradar search --query "rust" --location "remote"`
2. **MCP mode:** `jobradar mcp serve` (starts stdio MCP server, tools map 1:1 to CLI subcommands)

This dual-mode approach means the same binary serves both direct CLI invocation and MCP-based agent interaction.

---

## 3. Architecture: What Goes in Rust vs What Stays in Python

### The Hybrid Architecture

Not everything should move to Rust. The right split is based on where Rust's strengths matter:

| Concern | Best in Rust | Best in Python | Why |
|---------|:---:|:---:|-----|
| HTTP scraping (concurrent) | **YES** | | tokio + reqwest: 10-100x throughput advantage |
| HTML parsing | **YES** | | scraper/lol_html: 5-50x faster, lower memory |
| ATS fingerprinting | **YES** | | Pattern matching, byte-level analysis |
| Text normalization | **YES** | | String processing, deduplication hashing |
| Job deduplication (SHA-256) | **YES** | | Already hash-based, pure computation |
| Resume PDF generation | **YES** | | typst or printpdf, no Python dependency hell |
| CLI interface + output | **YES** | | Native binary, instant startup |
| MCP server | **YES** | | Low-latency tool responses |
| LLM API calls | | **YES** | Python SDKs (openai, anthropic) are canonical |
| Database ORM/migrations | | **YES** | SQLAlchemy async + Alembic are battle-tested |
| ML inference (embeddings) | | **YES** | PyTorch/transformers ecosystem |
| Complex NLP pipelines | | **YES** | spaCy, NLTK, huggingface |
| Copilot/agent orchestration | | **YES** | LangChain, prompt engineering |
| Email sending | | **YES** | Simple HTTP, Python is fine |
| Admin dashboard/API | | **YES** | FastAPI already works, keep it |

### Interop Patterns: Rust Calling Python

There are three viable patterns for Rust-Python interop, each with distinct trade-offs:

#### Pattern 1: Subprocess (Recommended for v1)

```
jobradar CLI (Rust)
    │
    ├── Direct Rust: scraping, parsing, fingerprinting, dedup
    │
    └── subprocess ──> python -m jobradar.llm.enrich --stdin < job.json
                       python -m jobradar.llm.match --resume r.json --job j.json
```

**Pros:** Zero coupling, each side can be tested independently, Python environment is isolated.
**Cons:** Process startup overhead (~100ms per call), data serialization cost.
**Mitigation:** Batch operations, keep a Python subprocess pool, or use a local HTTP sidecar.

#### Pattern 2: Local HTTP Sidecar (Recommended for v2)

```
jobradar CLI (Rust)                    jobradar-brain (Python, FastAPI)
    │                                       │
    ├── Direct Rust work                    ├── POST /enrich
    │                                       ├── POST /match
    └── reqwest ──HTTP──> localhost:9999    ├── POST /embed
                                            └── POST /copilot
```

**Pros:** Python stays running (no startup cost), standard HTTP interface, can be deployed independently.
**Cons:** Need to manage the sidecar lifecycle.
**Implementation:** `jobradar brain start` launches the Python sidecar; `jobradar brain stop` kills it. Health check at `localhost:9999/health`.

#### Pattern 3: PyO3 Embedding (Advanced, v3+)

PyO3 (15,498 stars) allows calling Python directly from Rust:

```rust
use pyo3::prelude::*;

fn enrich_job(job_json: &str) -> Result<String> {
    Python::with_gil(|py| {
        let module = py.import("jobradar.llm.enrich")?;
        let result = module.call_method1("enrich", (job_json,))?;
        Ok(result.extract::<String>()?)
    })
}
```

**Pros:** No process boundary, shared memory, fastest interop.
**Cons:** Requires Python linked at compile time, complicates distribution (user needs matching Python), GIL contention for concurrent calls.
**When to use:** Only if the CLI must be a single binary AND LLM calls are on the hot path.

### Recommended Hybrid Crate Layout

```
jobradar/
├── Cargo.toml                    # Workspace root
├── crates/
│   ├── jr-cli/                   # Binary crate: CLI entry point
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── main.rs           # clap parse + dispatch
│   │       ├── commands/         # One module per top-level command
│   │       │   ├── search.rs
│   │       │   ├── scrape.rs
│   │       │   ├── pipeline.rs
│   │       │   ├── config.rs
│   │       │   └── mcp.rs
│   │       └── output/           # Human vs JSON vs JSONL formatting
│   │           ├── mod.rs
│   │           ├── human.rs
│   │           ├── json.rs
│   │           └── table.rs
│   ├── jr-scraper/               # Library crate: HTTP scraping engine
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── client.rs         # reqwest client pool with rate limiting
│   │       ├── ats.rs            # ATS fingerprinting
│   │       ├── parser.rs         # HTML parsing with scraper/lol_html
│   │       ├── sources/          # Per-ATS scrapers (greenhouse, lever, etc.)
│   │       └── scheduler.rs      # Crawl scheduling and prioritization
│   ├── jr-core/                  # Library crate: shared types and logic
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── job.rs            # Job struct, SHA-256 ID generation
│   │       ├── company.rs
│   │       ├── dedup.rs          # Deduplication logic
│   │       ├── normalize.rs      # Text normalization
│   │       └── config.rs         # Configuration types
│   ├── jr-store/                 # Library crate: storage abstraction
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── sqlite.rs         # Local SQLite for CLI state
│   │       ├── postgres.rs       # PostgreSQL for server mode
│   │       └── cache.rs          # On-disk cache for scraped pages
│   ├── jr-mcp/                   # Library crate: MCP server implementation
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── server.rs
│   │       ├── tools.rs          # MCP tool definitions
│   │       └── resources.rs      # MCP resource definitions
│   └── jr-resume/                # Library crate: resume generation
│       ├── Cargo.toml
│       └── src/
│           ├── lib.rs
│           ├── parser.rs         # Parse existing resumes
│           └── generator.rs      # Generate tailored PDFs
├── backend/                      # Existing Python backend (kept for LLM/DB/ML)
└── frontend/                     # Existing React frontend (secondary consumer)
```

---

## 4. CLI Command Structure for a Job Search OS

### Proposed Command Hierarchy

Informed by the command patterns of gh, terraform, kubectl, and docker:

```
jobradar [GLOBAL OPTIONS] <COMMAND> [SUBCOMMAND] [OPTIONS]

GLOBAL OPTIONS:
    --format <human|json|jsonl>    Output format (default: auto-detect TTY)
    --quiet / -q                   Suppress non-essential output
    --verbose / -v                 Increase verbosity (-vv for debug)
    --config <path>                Config file override
    --profile <name>               Named configuration profile
    --no-color                     Disable terminal colors

COMMANDS:

  Discovery & Search:
    search          Search for jobs across all configured sources
      search run    Execute a search query
      search saved  Manage saved searches
      search history View search history

    discover        Browse and explore job sources
      discover sources    List configured ATS sources
      discover companies  Browse companies in the database
      discover trends     Show hiring trends and insights

  Scraping & Data:
    scrape          Manage web scraping operations
      scrape run          Run a scrape against target(s)
      scrape target       Manage scrape targets (add, list, remove, test)
      scrape schedule     Manage scrape schedules
      scrape status       Show scraper health and queue status
      scrape history      View past scrape runs

    source          Manage ATS source configurations
      source list         List all known ATS types
      source fingerprint  Identify the ATS of a URL
      source health       Check source availability

  Pipeline & Tracking:
    pipeline        Manage your job application pipeline
      pipeline list       List jobs in pipeline (with stage filters)
      pipeline add        Add a job to the pipeline
      pipeline move       Move a job between stages
      pipeline view       View detailed job + pipeline info
      pipeline remove     Remove a job from pipeline
      pipeline stats      Pipeline analytics

    apply           Application management
      apply start         Begin application for a job
      apply track         Log an application action
      apply status        Check application status

  Preparation:
    resume          Resume management
      resume list         List stored resumes
      resume tailor       Generate a tailored resume for a job
      resume parse        Parse a resume file
      resume export       Export resume in various formats

    prep            Interview preparation
      prep questions      Generate interview questions for a job
      prep company        Company research brief
      prep salary         Salary intelligence for a role

  Intelligence:
    analyze         Analytics and insights
      analyze market      Market analysis for a role/location
      analyze fit         Job-resume fit scoring
      analyze trends      Hiring trend analysis

    copilot         AI-assisted operations (delegates to Python sidecar)
      copilot enrich      Enrich a job listing with AI analysis
      copilot match       Score job-resume match
      copilot suggest     Get next-action suggestions
      copilot chat        Interactive AI assistant

  Operations:
    config          Configuration management
      config init         Interactive first-time setup
      config show         Show current configuration
      config set          Set a configuration value
      config get          Get a configuration value
      config edit         Open config in editor

    auth            Authentication
      auth login          Authenticate (API key or OAuth)
      auth logout         Clear stored credentials
      auth status         Show auth status
      auth token          Display current token

    brain           Python sidecar management
      brain start         Start the Python AI sidecar
      brain stop          Stop the sidecar
      brain status        Health check
      brain logs          View sidecar logs

    server          Run as a server (REST API or MCP)
      server api          Start REST API server
      server mcp          Start MCP server (stdio or SSE)

    db              Database operations
      db migrate          Run database migrations
      db seed             Seed initial data
      db export           Export data
      db import           Import data

    version         Show version and build info
    completions     Generate shell completions
    doctor          Diagnose common issues
```

### Handling Long-Running Operations

Job scraping is inherently long-running. The CLI must handle this gracefully for both humans and agents:

**Pattern 1: Streaming progress (human mode)**
```
$ jobradar scrape run --target greenhouse
[1/4] Discovering job listing pages... ████████████████░░░░ 80% (120/150 pages)
[2/4] Extracting job details...         ████████░░░░░░░░░░░░ 40% (48/120 jobs)
[3/4] Deduplicating...                  (waiting)
[4/4] Storing results...                (waiting)
```

Implementation: `indicatif` crate with `MultiProgress` for concurrent progress bars.

**Pattern 2: Structured progress (agent/JSON mode)**
```jsonl
{"event":"progress","stage":"discover","current":120,"total":150}
{"event":"progress","stage":"extract","current":48,"total":120}
{"event":"job","data":{"id":"sha256:abc...","title":"Rust Engineer",...}}
{"event":"complete","jobs_found":120,"jobs_new":45,"duration_ms":8200}
```

Implementation: JSONL (one JSON object per line) on stdout, with progress events interleaved with data events.

**Pattern 3: Background jobs with polling**
```bash
# Start in background
$ jobradar scrape run --target greenhouse --background
Scrape job started: scrape_20260328_001
Use `jobradar scrape status scrape_20260328_001` to check progress.

# Poll (agents do this)
$ jobradar scrape status scrape_20260328_001 --format json
{"id":"scrape_20260328_001","status":"running","progress":0.65,"eta_seconds":12}
```

### Auth, Config, and State Management

**Configuration file** (`~/.config/jobradar/config.toml`):
```toml
[default]
format = "human"
database = "sqlite"  # or "postgres://..."

[profiles.work]
database = "postgres://..."
sources = ["greenhouse", "lever", "workday"]

[profiles.personal]
database = "sqlite"
sources = ["greenhouse", "lever"]

[scraping]
concurrent_requests = 10
rate_limit_per_domain = 2  # requests/second
user_agent = "JobRadar/1.0"
cache_dir = "~/.cache/jobradar"

[brain]
host = "127.0.0.1"
port = 9999
auto_start = true
python_path = "python3"
```

**Credential storage:** Use the `keyring` crate to store API keys in the OS credential store. Never store secrets in config files.

**Local state:** SQLite database at `~/.local/share/jobradar/jobradar.db` for:
- Pipeline state (jobs, stages, notes)
- Search history
- Scrape run history
- Cache metadata

The `directories` crate provides correct paths across platforms:
- Linux: `~/.config/jobradar/`, `~/.local/share/jobradar/`, `~/.cache/jobradar/`
- macOS: `~/Library/Application Support/jobradar/`
- Windows: `C:\Users\<user>\AppData\Roaming\jobradar\`

---

## 5. MCP Server in Rust

### The Official Rust MCP SDK: RMCP

The official Rust SDK for the Model Context Protocol is **rmcp** (3,227 stars, actively maintained, last updated 2026-03-27).

**Key facts:**
- Published on crates.io as `rmcp` version 0.16.0 (approaching 1.0)
- Built on tokio async runtime
- Supports both server and client roles
- Transport options: stdio, SSE (Server-Sent Events), HTTP streamable
- Uses `schemars` for JSON Schema generation from Rust types
- Proc-macro crate `rmcp-macros` for deriving tool implementations
- Conforms to MCP spec 2025-11-25

**Repository structure:**
```
modelcontextprotocol/rust-sdk/
├── crates/
│   ├── rmcp/              # Core protocol implementation
│   └── rmcp-macros/       # Proc macros for tool/prompt derivation
├── examples/
│   ├── clients/           # Example MCP clients
│   ├── servers/           # Example MCP servers
│   └── transport/         # Transport examples
└── conformance/           # Protocol conformance tests
```

**Dependencies (from Cargo.toml):**
- `tokio` (async runtime)
- `serde` / `serde_json` (serialization)
- `schemars` (JSON Schema generation)
- `reqwest` (HTTP client, optional)
- `tracing` (logging)
- `oauth2` (optional OAuth support)

### Building a JobRadar MCP Server

The MCP server would expose JobRadar's capabilities as tools that AI agents can discover and invoke:

```rust
use rmcp::{ServerHandler, ServiceExt, model::*, service::RequestContext, RoleServer};
use rmcp_macros::tool;
use schemars::JsonSchema;

#[derive(Clone)]
struct JobRadarMcp {
    scraper: jr_scraper::ScraperEngine,
    store: jr_store::Store,
}

// Using the rmcp-macros derive approach:
#[tool]
impl JobRadarMcp {
    /// Search for jobs matching the given criteria across all configured sources
    #[tool(params)]
    async fn search_jobs(
        &self,
        /// Search query terms (e.g., "rust engineer", "backend developer")
        query: String,
        /// Location filter (e.g., "remote", "San Francisco, CA")
        #[schemars(default)]
        location: Option<String>,
        /// Maximum number of results to return
        #[schemars(default = "default_limit")]
        limit: Option<u32>,
    ) -> Result<CallToolResult, McpError> {
        let results = self.store.search(&query, location.as_deref(), limit.unwrap_or(20)).await?;
        Ok(CallToolResult::text(serde_json::to_string_pretty(&results)?))
    }

    /// Fingerprint a URL to identify what ATS (Applicant Tracking System) it uses
    #[tool(params)]
    async fn fingerprint_ats(
        &self,
        /// The URL of a company's careers page
        url: String,
    ) -> Result<CallToolResult, McpError> {
        let result = self.scraper.fingerprint(&url).await?;
        Ok(CallToolResult::text(serde_json::to_string_pretty(&result)?))
    }

    /// Add a job to the application pipeline
    #[tool(params)]
    async fn pipeline_add(
        &self,
        /// The job ID (SHA-256 hash)
        job_id: String,
        /// Pipeline stage: discovered, interested, applied, interviewing, offer, rejected
        stage: String,
        /// Optional notes
        notes: Option<String>,
    ) -> Result<CallToolResult, McpError> {
        let entry = self.store.pipeline_add(&job_id, &stage, notes.as_deref()).await?;
        Ok(CallToolResult::text(serde_json::to_string_pretty(&entry)?))
    }

    /// Scrape jobs from a specific target URL or ATS
    #[tool(params)]
    async fn scrape_target(
        &self,
        /// Target URL or ATS identifier
        target: String,
        /// Maximum pages to crawl
        #[schemars(default = "default_max_pages")]
        max_pages: Option<u32>,
    ) -> Result<CallToolResult, McpError> {
        let result = self.scraper.scrape(&target, max_pages.unwrap_or(50)).await?;
        Ok(CallToolResult::text(serde_json::to_string_pretty(&result)?))
    }
}
```

**MCP Resources** the server would expose:

```rust
impl ServerHandler for JobRadarMcp {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            capabilities: ServerCapabilities::builder()
                .enable_tools()
                .enable_resources()
                .enable_prompts()
                .build(),
            server_info: Implementation {
                name: "jobradar".into(),
                version: env!("CARGO_PKG_VERSION").into(),
            },
            ..Default::default()
        }
    }

    async fn list_resources(&self, ..) -> Result<ListResourcesResult, McpError> {
        Ok(ListResourcesResult {
            resources: vec![
                RawResource::new("jobradar://pipeline", "Current job pipeline"),
                RawResource::new("jobradar://config", "Current configuration"),
                RawResource::new("jobradar://sources", "Configured job sources"),
                RawResource::new("jobradar://stats", "Search and scrape statistics"),
            ],
            ..Default::default()
        })
    }
}
```

### MCP Integration with Claude Code

Once built, the MCP server integrates with Claude Code via config:

```json
// ~/.claude/claude_desktop_config.json or MCP settings
{
  "mcpServers": {
    "jobradar": {
      "command": "jobradar",
      "args": ["server", "mcp"],
      "env": {
        "JOBRADAR_PROFILE": "work"
      }
    }
  }
}
```

Then Claude Code can naturally use it:
```
User: "Find me Rust backend jobs in the Bay Area and add the top 3 to my pipeline"

Claude Code:
1. Calls search_jobs(query="rust backend", location="Bay Area", limit=10)
2. Analyzes results, picks top 3
3. Calls pipeline_add(job_id="sha256:...", stage="interested") x3
4. Reports results to user
```

### spider-rs Also Has an MCP Server

Notable: spider-rs (the Rust web crawler) already ships an MCP server (`spider_mcp`) that can be installed via `cargo install spider_mcp`. This validates the pattern and could potentially be used as a dependency or reference for JobRadar's scraping MCP tools.

---

## 6. Cross-Platform Distribution

### Cross-Compilation Tools

| Tool | Stars | Purpose | Approach |
|------|-------|---------|----------|
| **cross-rs** | 8,077 | Cross-compilation via Docker | Docker containers with target toolchains |
| **cargo-dist** | 1,989 | Full release pipeline | CI-generated installers, GitHub Releases |
| **cargo-zigbuild** | ~1,500 | Cross-compile using Zig | Zig as a C cross-compiler |

### cargo-dist: The Recommended Distribution Tool

cargo-dist automates the entire release pipeline:

1. **Plan:** Detects workspace, determines targets
2. **Build:** Compiles for each platform (via CI matrix)
3. **Package:** Creates tarballs, zip files, installers
4. **Publish:** Uploads to GitHub Releases, Homebrew, npm, crates.io
5. **Announce:** Creates release notes

**Supported installer types:**
- Shell installer (curl | sh)
- PowerShell installer (irm | iex)
- Homebrew formula
- npm package (for `npx` usage)
- MSI installer (Windows)
- Debian/RPM packages

**Setup:**
```bash
cargo install cargo-dist
cargo dist init        # Interactive setup
# Generates .github/workflows/release.yml
git tag v0.1.0 && git push --tags   # Triggers release
```

### Target Matrix

| Target Triple | OS | Arch | Notes |
|---------------|-----|------|-------|
| `x86_64-unknown-linux-gnu` | Linux | x64 | Most common server/CI |
| `aarch64-unknown-linux-gnu` | Linux | ARM64 | AWS Graviton, Raspberry Pi |
| `x86_64-unknown-linux-musl` | Linux | x64 | Static binary, Alpine |
| `aarch64-unknown-linux-musl` | Linux | ARM64 | Static, container-friendly |
| `x86_64-apple-darwin` | macOS | Intel | Legacy Macs |
| `aarch64-apple-darwin` | macOS | Apple Silicon | M1/M2/M3/M4 |
| `x86_64-pc-windows-msvc` | Windows | x64 | Standard Windows |
| `aarch64-pc-windows-msvc` | Windows | ARM64 | Surface Pro X, Snapdragon |

### Binary Size Optimization

Rust binaries can be large. Optimization strategies:

```toml
# Cargo.toml
[profile.release]
opt-level = "z"         # Optimize for size
lto = true              # Link-time optimization
codegen-units = 1       # Better optimization, slower compile
strip = true            # Strip debug symbols
panic = "abort"         # Smaller than unwinding
```

**Expected sizes with optimization:**
- Minimal CLI (clap + serde + reqwest): ~5-8 MB
- Full CLI with scraping + MCP: ~10-15 MB
- With static musl linking: +2-3 MB

For comparison:
- ripgrep: ~5 MB
- bat: ~6 MB
- starship: ~8 MB
- GitHub CLI (Go): ~50 MB

### Installation Methods

```bash
# Homebrew (macOS/Linux)
brew install jobradar

# Cargo (Rust users)
cargo install jobradar

# Shell script (Linux/macOS)
curl -fsSL https://install.jobradar.dev | sh

# PowerShell (Windows)
irm https://install.jobradar.dev/install.ps1 | iex

# npm/npx (for agents in Node environments)
npx jobradar search --query "rust engineer"

# Docker
docker run --rm jobradar search --query "rust engineer"

# Direct download
# GitHub Releases: github.com/user/jobradar/releases
```

---

## 7. Real-World Examples

### spider-rs: Rust Web Scraping at Scale (2,362 stars)

spider-rs is the most relevant real-world reference for JobRadar's scraping needs:

**Performance claims (from benchmarks in README):**
- 185 pages crawled in 73ms (Apple M1 Max) vs 15s for node-crawler (205x faster)
- On Linux (2-core, 7GB): 50ms vs 3.4s for node-crawler (68x faster)
- Handles 100k+ pages in minutes where others take hours

**Architecture highlights:**
- Built on tokio for async I/O
- Lock-free data structures for concurrent crawling
- Optional io_uring support on Linux for even faster I/O
- Feature-gated: compile only what you need (HTTP, Chrome CDP, WebDriver)
- Streaming results via channels (process pages as they arrive)
- Built-in proxy rotation, rate limiting, caching
- AI agent integration for complex page interaction
- MCP server included (`spider_mcp`)

**Relevant crates from spider-rs ecosystem:**
- `spider` -- core crawling engine
- `spider_cli` -- CLI interface
- `spider_transformations` -- HTML to Markdown/text/structured
- `spider_agent` -- AI-powered web automation
- `spider_mcp` -- MCP server for AI agents

**Key takeaway:** JobRadar should use spider-rs as a dependency for its crawling engine rather than building from scratch. The crate is production-hardened, actively maintained, and already has the features needed (concurrent crawling, browser rendering, rate limiting, caching).

### How Anthropic's Claude Code Works Architecturally

Claude Code is a Node.js CLI that:
1. Runs as a terminal application with rich TUI
2. Invokes tools (file read/write, bash, search) via function calling
3. MCP integration allows external tools to be registered
4. Tools return structured text that Claude interprets
5. The agent loop: plan -> tool call -> observe -> plan -> ...

For JobRadar as a tool Claude Code uses:
- The CLI must be fast to start (Rust advantage: ~1ms vs Python ~200ms)
- Output must be parseable (JSON mode)
- Tools should be granular (one tool = one action, not "do everything")
- Errors must be informative (agents need to understand what went wrong to retry)

### Reference Architecture: How kubectl Structures Commands

kubectl uses a resource-verb pattern relevant to JobRadar:

```
kubectl get pods                  =>  jobradar get jobs
kubectl describe pod foo          =>  jobradar view job sha256:abc
kubectl apply -f manifest.yaml    =>  jobradar apply --config scrape.yaml
kubectl logs pod foo              =>  jobradar logs scrape-run-001
kubectl port-forward pod foo      =>  jobradar brain start
```

The "noun verb" vs "verb noun" question: gh uses "noun verb" (`gh pr list`), kubectl uses "verb noun" (`kubectl get pods`), docker uses "noun verb" (`docker container ls`). For JobRadar, **"noun verb"** (gh-style) is recommended because it groups related operations naturally and is more discoverable.

### Reference: terraform CLI Design

Terraform's design is relevant for JobRadar's scraping orchestration:

```
terraform init      =>  jobradar config init
terraform plan      =>  jobradar scrape plan (show what will be scraped)
terraform apply     =>  jobradar scrape run  (execute the plan)
terraform state     =>  jobradar db status
terraform output    =>  jobradar analyze market --format json
```

Terraform's "plan then apply" pattern is excellent for scraping: show the user what targets will be hit, estimated time, and page count before executing.

---

## 8. Performance Benchmarks

### Rust vs Python: HTTP Scraping Throughput

Based on spider-rs benchmarks and community data:

| Metric | Rust (reqwest + tokio) | Python (aiohttp / httpx) | Multiplier |
|--------|----------------------|--------------------------|------------|
| Concurrent HTTP requests/sec (single core) | ~10,000-50,000 | ~500-2,000 | 10-25x |
| 185 pages crawled | 73ms (spider-rs) | ~3-15s (scrapy/aiohttp) | 40-200x |
| Memory per 1000 concurrent connections | ~50 MB | ~200-500 MB | 4-10x |
| Cold start time | ~1ms | ~200-500ms | 200-500x |

**Why the gap is so large for scraping:**
1. **No GIL:** Rust's async runtime uses all cores without the Global Interpreter Lock
2. **Zero-cost abstractions:** No runtime type checking, no garbage collection pauses
3. **Memory layout:** Struct-of-arrays vs Python's object-per-everything
4. **io_uring:** spider-rs can use Linux kernel-level async I/O
5. **Connection pooling:** reqwest's hyper-based pool is highly optimized

### Rust vs Python: HTML Parsing Speed

| Parser | Language | Parse time (1MB HTML) | Memory |
|--------|----------|----------------------|---------|
| lol_html (streaming) | Rust | ~0.5ms | ~constant (streaming) |
| scraper (DOM) | Rust | ~2-5ms | ~10-20 MB |
| selectolax | Python (Cython) | ~5-15ms | ~20-50 MB |
| BeautifulSoup4 | Python | ~50-200ms | ~50-100 MB |
| lxml | Python (C) | ~10-30ms | ~20-40 MB |

**Key insight:** lol_html (from Cloudflare, 1,957 stars) is a streaming HTML rewriter that processes HTML in a single pass without building a DOM tree. This is ideal for extracting specific elements (job titles, descriptions, links) from large pages.

### Rust vs Python: Text Processing and Deduplication

| Operation | Rust | Python | Notes |
|-----------|------|--------|-------|
| SHA-256 hash (1KB) | ~2 microseconds | ~15 microseconds | ring/sha2 vs hashlib |
| String normalization (lowercase, strip, collapse whitespace) | ~100ns per string | ~2-5 microseconds | 20-50x |
| Regex matching | ~10ns per match | ~100-500ns per match | regex crate vs re module |
| JSON serialization (1KB struct) | ~1-5 microseconds | ~10-50 microseconds | serde vs json module |

### Practical Impact for JobRadar

For a typical scraping run of 1,000 job pages:

| Phase | Rust Estimate | Python Estimate |
|-------|--------------|-----------------|
| HTTP fetching (concurrent) | ~2-5 seconds | ~30-120 seconds |
| HTML parsing (all pages) | ~1-3 seconds | ~15-60 seconds |
| Text normalization + dedup | ~50ms | ~2-5 seconds |
| JSON serialization | ~10ms | ~500ms |
| **Total (scraping + parsing)** | **~3-8 seconds** | **~50-180 seconds** |

The LLM enrichment step (calling OpenAI/Anthropic APIs) dominates wall-clock time regardless of language (~1-3 seconds per job * 1000 jobs = 15-50 minutes with batching). This is why the hybrid approach makes sense: use Rust for the fast parts, keep Python for the parts bottlenecked by external API calls.

---

## 9. Concrete Recommendations

### Phase 1: Rust CLI Shell + Scraping Core (4-6 weeks)

**Goal:** Ship a Rust binary that can scrape jobs faster than the Python backend, with JSON output for agent consumption.

**Crate dependencies:**
```toml
[workspace.dependencies]
clap = { version = "4", features = ["derive", "env"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tokio = { version = "1", features = ["full"] }
reqwest = { version = "0.12", features = ["json", "gzip", "brotli"] }
scraper = "0.21"           # CSS selector-based HTML parsing
lol_html = "2"             # Streaming HTML rewriting (for extraction)
spider = { version = "2", default-features = false }  # Consider as dep
anyhow = "1"               # Error handling
thiserror = "2"             # Typed errors for library crates
tracing = "0.1"
tracing-subscriber = "0.3"
indicatif = "0.17"         # Progress bars
tabled = "0.17"            # Table output
directories = "6"          # Platform paths
keyring = "3"              # Credential storage
rusqlite = { version = "0.32", features = ["bundled"] }  # Local state
sha2 = "0.10"              # Job ID generation
```

**Deliverables:**
- `jobradar search` -- search local SQLite database
- `jobradar scrape run` -- scrape targets with concurrent HTTP
- `jobradar scrape target add/list/remove` -- manage targets
- `jobradar config init/show/set` -- configuration
- `jobradar --format json` everywhere
- Shell completions via `clap_complete`

### Phase 2: MCP Server + Agent Integration (2-3 weeks)

**Additional dependencies:**
```toml
rmcp = { version = "0.16", features = ["server", "transport-sse", "transport-io"] }
rmcp-macros = "0.16"
schemars = "1.0"
```

**Deliverables:**
- `jobradar server mcp` -- stdio MCP server
- MCP tools: `search_jobs`, `scrape_target`, `fingerprint_ats`, `pipeline_add/list/move`
- MCP resources: `jobradar://pipeline`, `jobradar://config`
- Claude Code integration config

### Phase 3: Python Sidecar + Full Feature Parity (3-4 weeks)

**Deliverables:**
- `jobradar brain start/stop/status` -- manage Python sidecar
- `jobradar copilot enrich/match/suggest` -- LLM operations via sidecar
- `jobradar resume tailor` -- AI-enhanced resume generation
- `jobradar analyze market/fit` -- market intelligence

### Phase 4: Distribution + Polish (2 weeks)

**Deliverables:**
- cargo-dist setup with GitHub Actions
- Homebrew formula, shell/PowerShell installers
- npm package for `npx jobradar`
- Binary size optimization
- Comprehensive `--help` text (agents read this!)
- `jobradar doctor` for diagnosing setup issues

### Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CLI framework | clap v4 derive | Industry standard, 16k stars, best ergonomics |
| Async runtime | tokio | Required by rmcp, reqwest, spider-rs |
| HTTP client | reqwest | 11.5k stars, mature, built on hyper |
| HTML parsing | scraper + lol_html | DOM queries + streaming extraction |
| Web crawling | spider-rs (optional dep) | 200-1000x faster than alternatives, battle-tested |
| MCP SDK | rmcp (official) | 3.2k stars, official Anthropic/MCP SDK |
| Local storage | rusqlite | Embedded, no server needed for CLI |
| Config format | TOML | Rust ecosystem standard, human-readable |
| Error handling | anyhow (binary) + thiserror (libs) | Standard Rust pattern |
| Logging | tracing | Structured, async-aware, spans |
| Python interop | HTTP sidecar (v2), subprocess (v1) | Clean boundary, independent deployment |
| Distribution | cargo-dist | Automated CI, multi-platform installers |
| Cross-compilation | cross-rs (local), GitHub Actions (CI) | Covers all targets |

### What NOT to Rewrite in Rust

1. **The FastAPI backend:** Keep it running for the web frontend. The Rust CLI talks to the same PostgreSQL database or uses its own SQLite for standalone mode.
2. **Database migrations:** Keep Alembic. Rust's migration tooling (sqlx, diesel) is good but switching mid-project is high risk for no gain.
3. **LLM orchestration:** Keep Python. The OpenAI/Anthropic SDKs are Python-first, and prompt engineering iteration is faster in Python.
4. **The React frontend:** It consumes the FastAPI API. The Rust CLI is a parallel interface, not a replacement.

### The Big Picture: Three Interfaces, One Data Layer

```
                        ┌─────────────────────┐
                        │   PostgreSQL / SQLite │
                        │   (shared data layer) │
                        └──────────┬──────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                     │
    ┌─────────▼──────────┐ ┌──────▼───────┐ ┌──────────▼──────────┐
    │   Rust CLI (jobradar)│ │ FastAPI API  │ │  MCP Server (rmcp)  │
    │   Human terminal     │ │ Web frontend │ │  AI agent interface  │
    │   Agent tool calls   │ │ React SPA    │ │  Claude Code, Codex  │
    └──────────────────────┘ └──────────────┘ └─────────────────────┘
```

All three interfaces read/write to the same data. The Rust CLI and MCP server can optionally run in "standalone" mode with just SQLite for users who do not want to run PostgreSQL.

---

## Appendix A: Key GitHub Repositories Referenced

| Repository | Stars | Relevance |
|-----------|-------|-----------|
| [clap-rs/clap](https://github.com/clap-rs/clap) | 16,247 | CLI framework |
| [modelcontextprotocol/rust-sdk](https://github.com/modelcontextprotocol/rust-sdk) | 3,227 | MCP server in Rust |
| [spider-rs/spider](https://github.com/spider-rs/spider) | 2,362 | Rust web crawler/scraper |
| [BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep) | 61,497 | CLI architecture reference |
| [starship/starship](https://github.com/starship/starship) | 55,450 | Modular CLI reference |
| [sharkdp/bat](https://github.com/sharkdp/bat) | 57,824 | Output formatting reference |
| [sharkdp/fd](https://github.com/sharkdp/fd) | 42,210 | Parallel processing reference |
| [ajeetdsouza/zoxide](https://github.com/ajeetdsouza/zoxide) | 34,974 | State management reference |
| [dandavison/delta](https://github.com/dandavison/delta) | 29,695 | Terminal output reference |
| [eza-community/eza](https://github.com/eza-community/eza) | 20,860 | Modern CLI patterns |
| [PyO3/pyo3](https://github.com/PyO3/pyo3) | 15,498 | Rust-Python interop |
| [seanmonstar/reqwest](https://github.com/seanmonstar/reqwest) | 11,507 | HTTP client |
| [cross-rs/cross](https://github.com/cross-rs/cross) | 8,077 | Cross-compilation |
| [console-rs/indicatif](https://github.com/console-rs/indicatif) | 5,092 | Progress bars |
| [causal-agent/scraper](https://github.com/causal-agent/scraper) | 2,354 | HTML parsing |
| [axodotdev/cargo-dist](https://github.com/axodotdev/cargo-dist) | 1,989 | Release automation |
| [cloudflare/lol-html](https://github.com/cloudflare/lol-html) | 1,957 | Streaming HTML parser |
| [console-rs/dialoguer](https://github.com/console-rs/dialoguer) | 1,565 | Interactive prompts |
| [cli/cli](https://github.com/cli/cli) | ~40,000 | gh CLI design reference |

## Appendix B: Minimum Viable Cargo.toml

```toml
[workspace]
resolver = "2"
members = ["crates/*"]

[workspace.package]
version = "0.1.0"
edition = "2024"
license = "MIT"
repository = "https://github.com/user/jobradar"

[workspace.dependencies]
# CLI
clap = { version = "4", features = ["derive", "env", "wrap_help"] }
clap_complete = "4"

# Serialization
serde = { version = "1", features = ["derive"] }
serde_json = "1"
toml = "0.8"

# Async
tokio = { version = "1", features = ["full"] }
futures = "0.3"

# HTTP & Scraping
reqwest = { version = "0.12", default-features = false, features = ["json", "gzip", "brotli", "rustls-tls"] }
scraper = "0.21"
lol_html = "2"
url = "2"

# MCP
rmcp = { version = "0.16", features = ["server"] }
rmcp-macros = "0.16"
schemars = "1.0"

# Storage
rusqlite = { version = "0.32", features = ["bundled"] }

# Crypto
sha2 = "0.10"

# Terminal
indicatif = "0.17"
tabled = "0.17"
console = "0.15"
dialoguer = "0.11"

# Logging
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }

# Error handling
anyhow = "1"
thiserror = "2"

# Platform
directories = "6"
keyring = "3"

# Time
chrono = { version = "0.4", features = ["serde"] }
```
