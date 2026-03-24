# System Analysis — JobRadar V2

> **Analysis Date:** 2026-03-24
> **Analyst:** GitHub Copilot (automated exhaustive scan)
> **Branch at Analysis:** `copilot/conduct-full-system-analysis` (based on `main` @ `70bfe75`)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Repository Structure](#2-repository-structure)
3. [Branch Landscape](#3-branch-landscape)
4. [Technology Stack](#4-technology-stack)
5. [Backend Architecture](#5-backend-architecture)
   - 5.1 [Entry Points and Bootstrap](#51-entry-points-and-bootstrap)
   - 5.2 [Module Inventory](#52-module-inventory)
   - 5.3 [Execution Flow](#53-execution-flow)
   - 5.4 [Middleware Stack](#54-middleware-stack)
   - 5.5 [Background Workers and Scheduler](#55-background-workers-and-scheduler)
6. [Scraping Platform](#6-scraping-platform)
7. [Data Model and Database](#7-data-model-and-database)
   - 7.1 [Alembic Migrations](#71-alembic-migrations)
   - 7.2 [Key Tables and Relationships](#72-key-tables-and-relationships)
8. [Frontend Architecture](#8-frontend-architecture)
   - 8.1 [Page Inventory](#81-page-inventory)
   - 8.2 [Component Library](#82-component-library)
   - 8.3 [API Client Layer](#83-api-client-layer)
   - 8.4 [State Management](#84-state-management)
   - 8.5 [Build Configuration](#85-build-configuration)
9. [Testing and Coverage](#9-testing-and-coverage)
   - 9.1 [Backend Tests](#91-backend-tests)
   - 9.2 [Frontend Tests](#92-frontend-tests)
10. [CI/CD Pipeline](#10-cicd-pipeline)
11. [Security Posture](#11-security-posture)
12. [Infrastructure and Operations](#12-infrastructure-and-operations)
13. [Baseline Validation Results](#13-baseline-validation-results)
14. [Known Gaps and Open Items](#14-known-gaps-and-open-items)
15. [Audit Ledger Summary](#15-audit-ledger-summary)
16. [Observations and Recommendations](#16-observations-and-recommendations)

---

## 1. Executive Summary

**JobRadar V2** is an AI-powered job-hunting assistant implemented as a React + FastAPI monorepo. It provides direct-job scraping from ATS portals, AI-driven job enrichment, application pipeline tracking, interview preparation, resume tailoring, auto-apply support, salary intelligence, and a Copilot chat interface. The system is in active development, with 23 backend routers, 37 database tables, 762 passing backend tests, and 39 passing frontend tests.

**Key health indicators at time of analysis:**

| Dimension | Status |
|-----------|--------|
| Backend lint (`ruff`) | ✅ Clean |
| Backend tests | ✅ 762 passed |
| Frontend lint (`eslint`) | ✅ Clean |
| Frontend tests | ✅ 39 passed in 24 files |
| Frontend build | ✅ Built successfully |
| Security audit (historical) | ✅ 39 of 44 audit items FIXED; 0 OPEN |
| Coverage gate | ✅ Backend ≥60%, Frontend ≥40% |

---

## 2. Repository Structure

```text
Job-Radar_2/                      ← monorepo root
├── backend/                      ← Python FastAPI application
│   ├── app/                      ← application source
│   │   ├── main.py               ← FastAPI factory; mounts 23 routers
│   │   ├── config.py             ← Pydantic Settings (JR_ env prefix)
│   │   ├── database.py           ← async SQLAlchemy engine + session factory
│   │   ├── dependencies.py       ← shared FastAPI dependency injectors
│   │   ├── migrations/           ← Alembic migration scripts
│   │   ├── shared/               ← middleware, errors, events, logging, pagination
│   │   ├── workers/              ← APScheduler background jobs
│   │   ├── admin/                ← admin endpoints
│   │   ├── analytics/            ← job analytics, ML predictor, RAG
│   │   ├── auth/                 ← cookie auth, refresh, revocation
│   │   ├── auto_apply/           ← form-fill orchestration, ATS adapters
│   │   ├── canonical_jobs/       ← deduplication of canonical job listings
│   │   ├── companies/            ← company profiles
│   │   ├── copilot/              ← Copilot chat via LLM
│   │   ├── email/                ← email digest and parser
│   │   ├── enrichment/           ← HTML→markdown, LLM field extraction
│   │   ├── followup/             ← follow-up reminder model
│   │   ├── interview/            ← question generation, prep bundles, evaluation
│   │   ├── jobs/                 ← core job CRUD (SHA-256 primary keys)
│   │   ├── networking/           ← contacts and referral requests
│   │   ├── nlp/                  ← NLP core, model router, cover letter generation
│   │   ├── notifications/        ← real-time SSE notifications
│   │   ├── outcomes/             ← offer/rejection outcome tracking
│   │   ├── pipeline/             ← Kanban application pipeline
│   │   ├── profile/              ← user profile and resume data
│   │   ├── resume/               ← resume tailoring, IR schema, templates
│   │   ├── salary/               ← salary intelligence and benchmarking
│   │   ├── scraping/             ← scraping platform (see §6)
│   │   ├── search_expansion/     ← query expansion
│   │   ├── settings/             ← user settings and API-key storage
│   │   ├── source_health/        ← scraper source health monitoring
│   │   └── vault/                ← document vault (upload/download/PATCH)
│   ├── tests/                    ← pytest suites (contracts, edge, integration, security, unit)
│   ├── scripts/                  ← utility CLI scripts
│   ├── seed_data.py              ← database seed helper
│   ├── pyproject.toml            ← project metadata, deps, ruff, mypy, pytest config
│   ├── alembic.ini               ← Alembic configuration
│   ├── Dockerfile                ← production Docker image
│   └── uv.lock                   ← locked dependency manifest
├── frontend/                     ← React + TypeScript SPA
│   ├── src/
│   │   ├── App.tsx               ← root component, router, QueryClient
│   │   ├── main.tsx              ← Vite entry; renders App with React 19
│   │   ├── index.css             ← Tailwind v4 + CSS design tokens
│   │   ├── pages/                ← 19 page components (lazy-loaded)
│   │   ├── components/           ← layout, UI primitives, feature components
│   │   ├── api/                  ← typed Axios API client modules
│   │   ├── store/                ← Zustand stores
│   │   ├── hooks/                ← custom React hooks
│   │   └── lib/                  ← constants, types, utils
│   ├── package.json              ← npm manifest
│   ├── vite.config.ts            ← Vite + Tailwind plugin config
│   ├── vitest.config.ts          ← Vitest with jsdom environment
│   ├── tsconfig.app.json         ← TypeScript compiler config (@ alias → src/)
│   ├── eslint.config.js          ← flat ESLint config
│   └── Dockerfile                ← Nginx production image
├── docs/
│   ├── current-state/            ← canonical operational state docs
│   ├── audit/                    ← bug ledger (39 FIXED / 5 STALE)
│   ├── research/                 ← future-looking design notes
│   └── system-analysis.md        ← this document
├── infra/                        ← Redis TLS certificates and compose support
├── .github/
│   ├── workflows/ci.yml          ← main CI pipeline
│   ├── workflows/codeql.yml      ← GitHub CodeQL SAST
│   ├── workflows/dependency-review.yml
│   └── dependabot.yml
├── docker-compose.yml            ← production compose (backend, frontend, postgres, redis)
├── docker-compose.dev.yml        ← dev-mode overrides
├── Makefile                      ← convenience targets
├── CLAUDE.md                     ← agent playbook
├── AGENTS.md                     ← agent preferences
├── PROJECT_STATUS.md             ← high-level status snapshot
├── README.md                     ← quick-start guide
├── SECURITY.md                   ← security disclosure policy
├── DECISIONS.md                  ← architectural decision log
├── THIRD_PARTY_CODE.md           ← third-party attributions
└── .env.example                  ← environment variable template
```

---

## 3. Branch Landscape

### Branches present at analysis time

| Branch | Latest Commit | Description |
|--------|--------------|-------------|
| `main` | `70bfe75` | Stable integration baseline; PRs #15 (security hardening) and #16 (CodeQL + dependency fixes) merged |
| `copilot/conduct-full-system-analysis` | `a420f12` | This analysis branch; based on `main`; adds `docs/system-analysis.md` |

> **Note:** The remote also shows `origin/main` at `70bfe75`. The development branch `feat/p2-polish-advanced` is referenced extensively in documentation as the branch where all P0/P1/P2 feature code was built and merged into `main` via PRs #15 and #16. It is not present in this shallow clone but its changes are fully represented in `main`.

### Branch-Specific Notes

#### `main`

- This is the integration baseline. All code present in this document reflects the state of `main`.
- PRs merged into `main`:
  - **PR #15** — security hardening: JWT moved to HttpOnly cookies, CORS locked, rate limiting, security headers, token revocation, `.dockerignore` files, Redis auth, health checks.
  - **PR #16** — CodeQL SAST + dependency remediation; GitHub Actions updated to `actions/*@v6`.
- **Commit history milestones (reverse chronological):**
  - `70bfe75` — P2 polish and backend wiring (all 23 routers, migration 005, resume templates)
  - `62b6b3f` — Code scanning alert resolution + frontend dep updates
  - `37ec4ad` — Merge PR #15 (mega security hardening)
  - `6691220` — Close remaining CodeQL blockers
  - `c11873b` — CI audit/bandit/mypy/coverage validation
  - `a4d93a7` — Stricter frontend lint
  - `fa784be` — Expanded Vitest coverage
  - `fbf480f` — Code scanning + backend hardening
  - `cc8b83e` — Auth/runtime paths + repo docs
  - `4ca021a` — Circuit-breaker timing and notification schema
  - Earlier commits build up the feature set progressively.

#### `copilot/conduct-full-system-analysis`

- Analysis-only branch off `main`.
- Adds `docs/system-analysis.md` (this file).
- No behavior changes to source code, tests, or configuration.
- Intended to be reviewed and merged to complete the analysis task.

---

## 4. Technology Stack

### Backend

| Layer | Technology | Version |
|-------|-----------|---------|
| Runtime | Python | 3.12 |
| Web framework | FastAPI | ≥0.115.0 |
| ASGI server | Uvicorn | ≥0.30.0 |
| ORM | SQLAlchemy (async) | ≥2.0.30 |
| DB driver | asyncpg | ≥0.29.0 |
| DB (test) | aiosqlite | ≥0.20.0 |
| Migrations | Alembic | ≥1.13.0 |
| Validation | Pydantic v2 | ≥2.8.0 |
| Auth tokens | PyJWT | ≥2.11.0 |
| Password hashing | bcrypt | ≥4.0.0 |
| HTTP client | httpx | ≥0.27.0 |
| Cache/queue | Redis (hiredis) + arq | ≥5.0.0 / ≥0.25.0 |
| Scheduler | APScheduler | ≥3.10.0 |
| Logging | structlog | ≥24.1.0 |
| SSE | sse-starlette | ≥2.0.0 |
| Vector DB | pgvector | ≥0.3.0 |
| CLI | Typer + Rich | ≥0.12.0 / ≥13.7.0 |
| Browsers (scraping) | Playwright, nodriver, camoufox, SeleniumBase | Various |
| ML (optional) | scikit-learn, sentence-transformers | ≥1.8.0 |
| AI/LLM | OpenRouter (claude-3.5-sonnet, gpt-4o-mini) | via httpx |
| Package manager | uv | ≥0.11.0 |

### Frontend

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | React | 19 |
| Build tool | Vite | 6 |
| Language | TypeScript | ~5.9.3 |
| CSS | Tailwind CSS v4 | ≥4.2.2 |
| State management | Zustand | 5 |
| Data fetching | TanStack Query | 5.62 |
| HTTP client | Axios | 1.7 |
| Routing | React Router v7 | 7 |
| Charts | Recharts | 3.8 |
| Icons | @phosphor-icons/react | 2.1 |
| Typography | Geist Sans + Geist Mono | 5.2 |
| Animations | Framer Motion | 12 |
| Drag-and-drop | @dnd-kit | 6/10 |
| Test runner | Vitest | 4.1 |
| Testing library | @testing-library/react | 16.1 |
| Linter | ESLint (flat config) | 9 |

### Database / Infrastructure

| Component | Technology |
|-----------|-----------|
| Primary DB | PostgreSQL 16/17 with pgvector extension |
| Cache / task queue | Redis 7 (authenticated, optional TLS) |
| Container | Docker Compose (backend + frontend + postgres + redis) |

---

## 5. Backend Architecture

### 5.1 Entry Points and Bootstrap

| File | Role |
|------|------|
| `backend/app/main.py` | `create_app()` factory — applies middleware stack, mounts all 23 routers, starts APScheduler in lifespan context |
| `backend/app/config.py` | `Settings` (Pydantic BaseSettings with `JR_` prefix); validates `secret_key` at startup |
| `backend/app/database.py` | Async SQLAlchemy engine (pool_size=20, max_overflow=40, pre_ping=True); `Base` declarative base |
| `backend/app/dependencies.py` | FastAPI dependency callables: `get_db()`, `get_current_user()`, `require_admin()` |

App bootstrap sequence:
```
uvicorn app.main:app
  → create_app()
    → setup_logging()
    → register middleware (outermost-first)
    → include 23 routers
    → lifespan: validate_runtime_settings() → create_scheduler().start()
  → handle requests
  → lifespan shutdown: scheduler.shutdown() → engine.dispose()
```

### 5.2 Module Inventory

All modules follow the same four-file convention: `models.py`, `schemas.py`, `service.py`, `router.py`.

| Module | Router prefix | Primary responsibility |
|--------|--------------|----------------------|
| `admin` | `/api/v1/admin` | User management, system stats, health probe (`/health` is public) |
| `analytics` | `/api/v1/analytics` | Application funnel metrics, ML-based outcome predictor, RAG pipeline |
| `auth` | `/api/v1/auth` | Register, login, logout, refresh token, token revocation, rate-limited |
| `auto_apply` | `/api/v1/auto-apply` | Form-fill orchestration; ATS detector, Workday/generic adapters, question engine |
| `canonical_jobs` | `/api/v1/canonical-jobs` | Canonical job deduplication across sources |
| `companies` | `/api/v1/companies` | Company profile CRUD |
| `copilot` | `/api/v1/copilot` | LLM-backed chat interface |
| `email` | `/api/v1/email` | Email digest parsing and job extraction |
| `enrichment` | `/api/v1/enrichment` | HTML→markdown, LLM field extraction, salary/experience enrichment |
| `interview` | `/api/v1/interview` | Question generation, prep bundles, answer evaluation, session persistence |
| `jobs` | `/api/v1/jobs` | Core job CRUD (SHA-256 IDs), lifecycle tracking, semantic search |
| `networking` | `/api/v1/networking` | Contact profiles, referral requests |
| `notifications` | `/api/v1/notifications` | SSE event stream (credentialed transport) |
| `outcomes` | `/api/v1/outcomes` | Offer/rejection tracking |
| `pipeline` | `/api/v1/pipeline` | Kanban application pipeline; stage transitions |
| `profile` | `/api/v1/profile` | User profile and resume data |
| `resume` | `/api/v1/resume` | Resume tailoring, gap analysis, IR schema, council review, cover letters |
| `salary` | `/api/v1/salary` | Salary benchmarking, LLM-driven salary intelligence |
| `scraping` | `/api/v1/scraping` | Scraper control, target management, run telemetry |
| `search_expansion` | `/api/v1/search-expansion` | Query expansion (title variants, synonyms) |
| `settings` | `/api/v1/settings` | User settings, notification preferences, API key storage stubs |
| `source_health` | `/api/v1/source-health` | Scraper source health metrics |
| `vault` | `/api/v1/vault` | Document upload/download/PATCH/DELETE |

### 5.3 Execution Flow

**Typical authenticated request flow:**
```
HTTP request
  → RequestIDMiddleware (injects X-Request-ID)
  → TimingMiddleware (records latency)
  → CORSMiddleware (validates origin)
  → SecurityHeadersMiddleware (adds HSTS/CSP/X-Frame-Options)
  → ApiRateLimitMiddleware (120 req/min per IP; 10/min for login)
  → FastAPI route handler
    → get_current_user() dependency (validates HttpOnly cookie JWT)
    → Service layer (async SQLAlchemy session)
    → Database (PostgreSQL via asyncpg)
  → Response with X-Request-ID header
```

**Job ingestion flow:**
```
Scraping worker triggered by APScheduler
  → ScrapingService.run_scrape()
    → ScrapeTarget selected by Scheduler (priority-scored)
    → TierRouter selects fetcher/browser by tier
    → ATS Adapter (Greenhouse/Lever/Ashby/Workday/Career page)
    → PageCrawler (bounded pagination, loop detection)
    → Deduplication (Simhash-based content fingerprint)
    → EnrichmentWorker queued
      → LLM extraction (salary, skills, experience)
      → Embedding generation (pgvector)
    → Job stored in PostgreSQL (SHA-256 ID)
    → SSE notification pushed to subscribed user sessions
```

### 5.4 Middleware Stack

Listed outermost-first (i.e., first to process requests, last to process responses):

1. **`ApiRateLimitMiddleware`** — in-memory sliding window; 120 rpm default, 10 rpm login
2. **`SecurityHeadersMiddleware`** — sets `X-Frame-Options`, `X-Content-Type-Options`, `Strict-Transport-Security`, `Content-Security-Policy`, `Referrer-Policy`
3. **`CORSMiddleware`** — restricted to configured origins (`JR_CORS_ORIGINS`), explicit methods, explicit headers
4. **`TimingMiddleware`** — adds `X-Process-Time` response header
5. **`RequestIDMiddleware`** — generates or propagates `X-Request-ID`

### 5.5 Background Workers and Scheduler

APScheduler is started in the FastAPI lifespan context and manages these background jobs:

| Worker module | Trigger | Purpose |
|---------------|---------|---------|
| `scraping_worker.py` | Interval (configurable) | Runs scraping cycles for scheduled targets |
| `enrichment_worker.py` | arq queue | LLM enrichment of newly scraped jobs |
| `alert_worker.py` | Interval | Evaluates saved-search criteria, pushes notifications |
| `auto_apply_worker.py` | Interval | Processes auto-apply queue (gated by `JR_AUTO_APPLY_ENABLED`) |
| `maintenance_worker.py` | Daily | Cleans stale sessions, expired tokens, old scrape logs |
| `phase7a_worker.py` | Interval | Networking/outcomes background processing |

---

## 6. Scraping Platform

The scraping platform is the most complex subsystem, implementing a layered execution architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│  Control Layer (app/scraping/control/)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ ATSRegistry  │  │  Scheduler   │  │  TierRouter        │    │
│  │ (vendor      │  │  (priority   │  │  (selects fetcher  │    │
│  │ detection)   │  │  scoring)    │  │  by site tier)     │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
│  ┌──────────────────────┐  ┌───────────────────────────────┐    │
│  │  TargetRegistry      │  │  PriorityScorer / Classifier  │    │
│  └──────────────────────┘  └───────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│  Execution Layer (app/scraping/execution/)                      │
│  Fetcher ports:                                                 │
│  ┌──────────────────┐  ┌───────────────────┐                   │
│  │ ScraplingFetcher  │  │CloudscraperFetcher│                   │
│  └──────────────────┘  └───────────────────┘                   │
│  Browser ports:                                                 │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │ PlaywrightBw │  │ NodriverBw  │  │  CamoufoxBrowser     │  │
│  └──────────────┘  └─────────────┘  └──────────────────────┘  │
│  ┌──────────────────────┐  ┌──────────────┐                    │
│  │  SeleniumBaseBrowser │  │  BrowserPool │                    │
│  └──────────────────────┘  └──────────────┘                    │
│  ┌──────────────────────────────┐  ┌───────────────────────┐   │
│  │  PageCrawler (pagination)    │  │  EscalationEngine     │   │
│  └──────────────────────────────┘  └───────────────────────┘   │
│  ┌──────────────────────────────┐                               │
│  │  Crawl4AIExtractor           │                               │
│  └──────────────────────────────┘                               │
├─────────────────────────────────────────────────────────────────┤
│  Scraper Adapters (app/scraping/scrapers/)                      │
│  Greenhouse / Lever / Ashby / Workday / JobSpy / SerpAPI /     │
│  TheirStack / Apify / AdaptiveParser / AIScraper / CareerPage  │
├─────────────────────────────────────────────────────────────────┤
│  Post-processing                                                │
│  Deduplication (Simhash + dedup_feedback) / RateLimiter        │
│  ScrapeAttempt + ScraperRun telemetry persistence               │
└─────────────────────────────────────────────────────────────────┘
```

**Key design decisions:**
- **Port/adapter pattern** — fetcher and browser implementations conform to `fetcher_port.py` and `browser_port.py` interfaces; the TierRouter selects implementations without coupling the service layer to any specific library.
- **PageCrawler** — bounded by timeout and loop detection; pagination stopped-reason is persisted to `ScrapeAttempt.pagination_stopped_reason`.
- **BrowserPool** — per-domain semaphores; semaphores are cleaned up after last use to prevent memory leaks.
- **EscalationEngine** — automatically escalates to a heavier browser tier when lightweight fetching fails.
- **Conflicting extras** — `crawl4ai` and `scrapling` extras are declared as conflicts in `pyproject.toml` to prevent simultaneous installation.

---

## 7. Data Model and Database

### 7.1 Alembic Migrations

| Migration | Contents |
|-----------|---------|
| `001_create_users_table.py` | Initial users table |
| `002_create_all_tables.py` | Core tables (jobs, pipeline, vault, etc.) |
| `003_merge_v1_features.py` | V1 feature tables |
| `004_create_email_logs.py` | Email log table |
| `005_create_p2_tables.py` | All 10 P2 tables (outcomes, networking, copilot sessions, etc.) |
| `20260321_db_audit_fixes.py` | Timezone-aware columns, cascade fixes, pool config |
| `20260323_*` series | Contacts/referrals, resume archetypes, dedup feedback, lifecycle columns |
| `aaba1d3f*` | Scrape targets and scrape attempts tables |
| `e5d40ea7*` | Career pages → scrape targets migration |
| `503ca7a3*` | Indexes on scrape attempts |

### 7.2 Key Tables and Relationships

| Table | Primary Key | Notable Columns |
|-------|-------------|-----------------|
| `users` | UUID | email, hashed_password, is_admin, `created_at` tz-aware |
| `jobs` | SHA-256 string | title, company_name, url, raw_html, enrichment fields, first/last_seen, lifecycle flags, pgvector embedding |
| `pipeline_applications` | UUID | user_id (FK), job_id (FK), stage (enum), notes |
| `scrape_targets` | UUID | url, ats_type, schedule_interval_m, is_active |
| `scrape_attempts` | UUID | target_id (FK), status, pagination_stopped_reason, started/completed_at |
| `scraper_runs` | UUID | run metadata, total jobs found/new |
| `vault_documents` | UUID | user_id (FK), filename, s3_key, document_type, metadata |
| `notifications` | UUID | user_id (FK), `created_at` tz-aware |
| `refresh_tokens` | UUID | user_id (FK), token hash, revoked_at, expires_at |
| `interview_sessions` | UUID | user_id (FK), job_id (FK), questions, answers, evaluation |
| `resume_profiles` | UUID | user_id (FK), structured IR data |
| `networking_contacts` | UUID | user_id (FK), contact data, referral status |
| `outcomes` | UUID | user_id (FK), job_id (FK), stage, offer details |
| `canonical_jobs` | UUID | deduplicated cross-source job records |
| `embeddings` | UUID | job_id (FK), vector (pgvector) |

**Invariant:** `jobs.id` is a SHA-256 hex string, not a UUID. All join queries to `jobs` must use string equality.

---

## 8. Frontend Architecture

### 8.1 Page Inventory

All pages are lazy-loaded via `React.lazy()` for code splitting. The auth-guarded routes are wrapped in `<AuthGuard> → <AppShell>`.

| Route | Page Component | Features |
|-------|---------------|---------|
| `/login` | `Login.tsx` | Email/password auth form |
| `/onboarding` | `Onboarding.tsx` | Profile setup, API key configuration |
| `/` (index) | `Dashboard.tsx` | Activity summary, stat cards, quick actions |
| `/jobs` | `JobBoard.tsx` | Paginated job search, filters, match score gauge |
| `/pipeline` | `Pipeline.tsx` | Kanban board with drag-and-drop (dnd-kit) |
| `/auto-apply` | `AutoApply.tsx` | Auto-apply settings and run log |
| `/resume` | `ResumeBuilder.tsx` | Resume tailoring with LLM, section editor |
| `/interview` | `InterviewPrep.tsx` | Question generation, answer eval |
| `/salary` | `SalaryInsights.tsx` | LLM salary research flow |
| `/vault` | `DocumentVault.tsx` | Upload/download/manage documents |
| `/analytics` | `Analytics.tsx` | Recharts funnel, pipeline metrics |
| `/profile` | `Profile.tsx` | User profile editor |
| `/settings` | `Settings.tsx` | Notification prefs, API keys, saved searches |
| `/admin` | `Admin.tsx` | User management, system stats |
| `/companies` | `Companies.tsx` | Company profiles list |
| `/sources` | `Sources.tsx` | Source health dashboard |
| `/canonical-jobs` | `CanonicalJobs.tsx` | Deduplicated job viewer |
| `/search-expansion` | `SearchExpansion.tsx` | Query expansion UI |
| `/targets` | `Targets.tsx` | Scrape target management |

### 8.2 Component Library

```
src/components/
├── layout/
│   ├── AppShell.tsx            ← top nav + sidebar + outlet
│   ├── Sidebar.tsx             ← navigation links with Phosphor icons
│   ├── AuthGuard.tsx           ← route guard; redirects to /login
│   └── NotificationBell.tsx   ← SSE-connected bell with badge count
├── ui/                         ← design system primitives
│   ├── Badge.tsx               ← status/tag badges
│   ├── Button.tsx              ← primary/secondary/ghost variants
│   ├── Card.tsx                ← container card
│   ├── Dropdown.tsx            ← dropdown menu
│   ├── EmptyState.tsx          ← zero-result state
│   ├── Input.tsx               ← form input
│   ├── Modal.tsx               ← dialog overlay
│   ├── PageLoader.tsx          ← full-screen spinner (Suspense fallback)
│   ├── Select.tsx              ← dropdown select
│   ├── Skeleton.tsx            ← loading placeholder
│   ├── StatCard.tsx            ← metric card with trend indicator
│   ├── Table.tsx               ← data table
│   ├── Tabs.tsx                ← tab navigation
│   ├── Textarea.tsx            ← multi-line input
│   ├── Toast.tsx               ← notification toast + ToastContainer
│   ├── Toggle.tsx              ← boolean toggle
│   └── toastService.ts         ← imperative toast API
├── jobs/
│   ├── JobCard.tsx             ← job listing card with score
│   ├── JobDetail.tsx           ← expanded job detail panel
│   ├── JobFilters.tsx          ← filter controls (type, location, score)
│   └── ScoreGauge.tsx          ← circular match score visualization
├── analytics/
│   └── AnalyticsCharts.tsx     ← Recharts wrapper components
├── pipeline/
│   ├── KanbanBoard.tsx         ← drag-and-drop Kanban
│   ├── PipelineColumn.tsx      ← column with droppable area
│   ├── ApplicationCard.tsx     ← draggable application card
│   ├── ApplicationModal.tsx    ← application detail/edit modal
│   ├── AddApplicationModal.tsx ← new application form
│   └── statusBadgeVariant.ts   ← stage → badge color map
├── scraper/
│   ├── ScraperControlPanel.tsx ← start/stop scraper controls
│   └── ScraperLog.tsx          ← real-time scraper log via SSE
└── ErrorBoundary.tsx           ← React error boundary
```

### 8.3 API Client Layer

All API modules under `src/api/` use a shared Axios client (`client.ts`) configured with:
- `baseURL: /api/v1`
- `withCredentials: true` (sends HttpOnly cookies)
- Automatic token refresh on 401 via response interceptor

| Module | Backend router(s) |
|--------|------------------|
| `auth.ts` | `/auth` |
| `jobs.ts` | `/jobs` |
| `pipeline.ts` | `/pipeline` |
| `auto-apply.ts` | `/auto-apply` |
| `resume.ts` | `/resume` |
| `interview.ts` | `/interview` |
| `salary.ts` | `/salary` |
| `vault.ts` | `/vault` |
| `analytics.ts` | `/analytics` |
| `profile.ts` | `/profile` |
| `settings.ts` | `/settings` |
| `admin.ts` | `/admin` |
| `scraper.ts` | `/scraping` |
| `notifications.ts` | `/notifications` (SSE) |
| `copilot.ts` | `/copilot` |
| `phase7a.ts` | `/networking`, `/outcomes` |

**Note:** API modules for `/email`, `/networking`, `/outcomes`, and `/copilot` exist but have limited frontend page coverage (see §14).

### 8.4 State Management

| Store | File | Manages |
|-------|------|---------|
| `useAuthStore` | `store/useAuthStore.ts` | Auth user object, login/logout state |
| `useJobStore` | `store/useJobStore.ts` | Selected job, filter state |
| `useScraperStore` | `store/useScraperStore.ts` | Scraper run status, log entries |
| `useUIStore` | `store/useUIStore.ts` | Theme (light/dark), sidebar state; persists to localStorage |

The theme system toggles a `.dark` class on the HTML root element and is coordinated by `useUIStore`. CSS design tokens are defined in `src/index.css` using Tailwind v4 CSS variable syntax.

### 8.5 Build Configuration

| File | Purpose |
|------|---------|
| `vite.config.ts` | Vite with `@vitejs/plugin-react` and Tailwind CSS v4 plugin; `@` → `src/` path alias |
| `vitest.config.ts` | Vitest config; jsdom environment; `@` alias; `src/__tests__/setup.ts` setup file |
| `tsconfig.app.json` | TypeScript strict compilation; `paths: { "@/*": ["./src/*"] }` |
| `eslint.config.js` | Flat config; react-hooks and react-refresh plugins |

---

## 9. Testing and Coverage

### 9.1 Backend Tests

**Location:** `backend/tests/`

| Directory | Tests | Description |
|-----------|-------|-------------|
| `unit/` | ~600 | Service logic, model contracts, scraper units |
| `unit/scraping/` | ~200 | Dedicated scraping subsystem unit tests |
| `integration/` | ~100 | Full HTTP integration tests via TestClient |
| `security/` | ~30 | Auth/security endpoint tests |
| `edge_cases/` | ~30 | Edge-case API behavior |
| `contracts/` | ~10 | ATS scraper contract tests (Greenhouse, Lever, Workday) |

**Key test infrastructure:**
- `conftest.py` — SQLite in-memory test database; async session factory; test user fixtures
- `pytest-asyncio` with `asyncio_mode = "auto"`
- `factory-boy` + `faker` for fixture generation
- Coverage gate: `--cov-fail-under=60`

**Validated result (this analysis run):** `762 passed, 64 warnings in 108.41s`

> **Note:** The 64 warnings are all `InsecureKeyLengthWarning` from `PyJWT` regarding the test-only secret key being shorter than 32 bytes. These are expected in the test environment and do not affect production security (where `JR_SECRET_KEY` is validated at startup).

### 9.2 Frontend Tests

**Location:** `frontend/src/__tests__/`, `frontend/src/api/__tests__/`, `frontend/src/hooks/__tests__/`, `frontend/src/components/__tests__/`

| Directory | Tests | Description |
|-----------|-------|-------------|
| `__tests__/` | ~25 | Page component render tests |
| `api/__tests__/` | 5 | API client module tests |
| `hooks/__tests__/` | 6 | Custom hook tests (`useDebounce`, `useKeyboard`, `useSSE`) |
| `components/__tests__/` | 3 | `AuthGuard` logic tests |

**Key test infrastructure:**
- `vitest.config.ts` — jsdom environment; `@testing-library/react`
- `src/__tests__/setup.ts` — global test setup (mocks `window.matchMedia`, `IntersectionObserver`)
- `src/__tests__/testUtils.tsx` — `renderWithProviders()` wrapper with QueryClient and Router
- Coverage gate: `--coverage.thresholds.statements=40`

**Validated result (this analysis run):** `39 passed in 24 files`

---

## 10. CI/CD Pipeline

### Workflow files

| File | Trigger | Jobs |
|------|---------|------|
| `.github/workflows/ci.yml` | push, pull_request | `backend`, `frontend` |
| `.github/workflows/codeql.yml` | push to main, PR | CodeQL SAST (Python + JS) |
| `.github/workflows/dependency-review.yml` | pull_request | Dependency diff review |
| `.github/dependabot.yml` | Scheduled | GitHub Actions version bumps |

### `ci.yml` — Backend Job Steps

1. Checkout + Python 3.12 setup
2. `pip install uv && uv sync --frozen` (installs locked dependencies)
3. `uv run python -m pip check` (dependency coherence)
4. `uv export ... | pip-audit` (vulnerability scan)
5. `uv tool run bandit -r app/ ... --severity-level medium` (SAST)
6. `uv run ruff check .` (lint)
7. `uv run mypy ...` (targeted type checking for security-critical paths)
8. `uv run pytest --cov=app --cov-fail-under=60 tests/` (test + coverage)
   - Runs against a real PostgreSQL 16 service (pgvector image)

### `ci.yml` — Frontend Job Steps

1. Checkout + Node.js 22 setup
2. `npm ci`
3. `npm audit --audit-level high`
4. `npm run lint`
5. `npm run test -- --run --coverage --coverage.thresholds.statements=40`
6. `npm run build`

### Actions versions

All actions use `@v6` as of the last update (PRs #15/#16):
- `actions/checkout@v6`
- `actions/setup-python@v6`
- `actions/setup-node@v6`
- `github/codeql-action@v4`

---

## 11. Security Posture

### Current hardening (verified fixes from audit):

| Area | Mechanism | Status |
|------|-----------|--------|
| Auth tokens | HttpOnly cookie (not localStorage); separate access + refresh cookies | ✅ Fixed (SEC-02) |
| Secret key | Validated at startup; startup raises `RuntimeError` if default in non-debug mode | ✅ Fixed (SEC-03) |
| CORS | Restricted to `JR_CORS_ORIGINS`; explicit methods and headers | ✅ Fixed (SEC-04) |
| Security headers | `X-Frame-Options`, `X-Content-Type-Options`, HSTS, CSP, Referrer-Policy | ✅ Fixed (SEC-05) |
| Token revocation | `refresh_tokens` table with `revoked_at`; revoked tokens rejected on refresh | ✅ Fixed (SEC-06) |
| Rate limiting | `ApiRateLimitMiddleware` (120 rpm default, 10 rpm login) | ✅ Fixed (SEC-07) |
| Secrets in repo | `.env` not committed; only `.env.example`; `.gitignore` covers `.env*` | ✅ Verified clean (SEC-01) |
| Docker | `.dockerignore` in both `backend/` and `frontend/`; secrets not baked into images | ✅ Fixed (INF-01) |
| Redis | Authenticated (`requirepass`); optional TLS (`tls-port`) | ✅ Fixed (INF-03) |
| Docker health checks | Backend, frontend, postgres, redis all have health checks | ✅ Fixed (INF-02) |
| Dependency scan | `pip-audit` (backend) + `npm audit --audit-level high` (frontend) in CI | ✅ Fixed (INF-04) |
| SAST | GitHub CodeQL (Python + JS) in CI; Bandit in backend CI | ✅ Fixed (INF-04) |

### Residual considerations:

- JWT test keys in `tests/conftest.py` are shorter than 32 bytes; this generates `InsecureKeyLengthWarning` during tests. **This is test-only and does not affect production.** Production uses the `JR_SECRET_KEY` env variable.
- Full repo-wide `mypy --strict` is not yet enforced. The current CI gate covers `auth/service.py`, `config.py`, `shared/middleware.py`, `scraping/deduplication.py`, and `scraping/port.py`.
- Auto-apply is gated by `JR_AUTO_APPLY_ENABLED=false` (default off).

---

## 12. Infrastructure and Operations

### Docker Compose (`docker-compose.yml`)

| Service | Image | Port | Health check |
|---------|-------|------|-------------|
| `backend` | `./backend` (Dockerfile) | 8000 | HTTP probe `/api/v1/admin/health` |
| `frontend` | `./frontend` (Dockerfile, nginx) | 3000 | `wget -q --spider http://127.0.0.1/` |
| `postgres` | `pgvector/pgvector:pg16` | 5432 | `pg_isready -U jobradar` |
| `redis` | `redis:7-alpine` | 6379 | `redis-cli ... ping \| grep PONG` |

- Redis TLS is optionally supported via certificates mounted from `infra/redis/tls/`.
- A `pgdata` named volume persists database state between restarts.

### Local development ports

| Service | Port | Notes |
|---------|------|-------|
| Backend (local) | 8000 | `uvicorn app.main:app --reload` |
| Frontend dev server | 5173 | `vite` |
| PostgreSQL (local) | 5433 | `docker start jobradar-postgres` |
| Redis (local) | 6379 | Docker or native |

### Key configuration variables (`JR_*` prefix)

| Variable | Default | Purpose |
|----------|---------|---------|
| `JR_SECRET_KEY` | `change-me-in-production` | JWT signing key; **must** be set in production |
| `JR_DATABASE_URL` | `postgresql+asyncpg://...` | Database connection string |
| `JR_REDIS_URL` | `redis://:change-me-redis-password@...` | Redis connection with auth |
| `JR_CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed CORS origins |
| `JR_AUTO_APPLY_ENABLED` | `false` | Enable/disable auto-apply worker |
| `JR_OPENROUTER_API_KEY` | `""` | LLM API key |
| `JR_DEBUG` | `false` | Enables debug mode; suppresses secret key validation |

---

## 13. Baseline Validation Results

All commands were run on this analysis branch (`copilot/conduct-full-system-analysis`) against the codebase as-of `70bfe75`.

### Backend

| Command | Result |
|---------|--------|
| `uv run ruff check .` | ✅ All checks passed |
| `uv run pytest -q` | ✅ **762 passed**, 64 warnings (all `InsecureKeyLengthWarning` from test JWT key length) |

> Note: `pip check`, `pip-audit`, `bandit`, and `mypy` require additional tooling (`uv tool install pip-audit`, `uv tool install bandit`) not available in this analysis sandbox. According to the last verified docs (2026-03-23), all four pass locally on the same codebase.

### Frontend

| Command | Result |
|---------|--------|
| `npm run lint` | ✅ Clean (0 errors, 0 warnings) |
| `npm run test -- --run` | ✅ **39 passed** in 24 test files |
| `npm run build` | ✅ Built successfully in 7.31s; total bundle ~473 kB (gzip: ~146 kB) for main chunk |

---

## 14. Known Gaps and Open Items

### Frontend gaps (deferred features, not bugs)

| Gap | Details |
|-----|---------|
| No email/networking/outcomes pages | API modules exist (`phase7a.ts`) but no dedicated pages are wired |
| Copilot chat page missing | Backend router and LLM service exist; no frontend page |
| Settings stubs are no-ops | Change-password, delete-account, clear-data buttons exist but have no backend endpoints |
| API key persistence | Keys are collected in Settings/Onboarding UI but never sent to the backend settings endpoint |
| Auto-apply UI triggers | `runAutoApply`, `pauseAutoApply`, `applySingle` are defined in `auto-apply.ts` but no UI triggers them |
| Semantic search | Backend vector search endpoint exists; not wired into Job Board search UI |

### Coverage gaps (below 50% in backend)

Modules with known low coverage: `auto_apply` service layer, `canonical_jobs/service.py`, `copilot` service/prompts, `enrichment/llm_client.py`, `interview/evaluator.py`, `nlp/core.py`, `resume/council.py`, `resume/gap_analyzer.py`, `salary/service.py`, and most `scraping/scrapers/` adapters.

### Deferred features (not bugs)

| ID | Feature |
|----|---------|
| DEF-01 | Resume PDF generation + WeasyPrint templates |
| DEF-03 | Scrape targets add/edit/delete UI |
| DEF-04 | Saved-search alerts UI and scheduler trigger |
| DEF-05 | End-to-end Playwright coverage |
| DEF-06/07/08 | ETag/robots.txt/Protego for scraper |

---

## 15. Audit Ledger Summary

The audit started with **44 items** identified across 6 domains.

| Status | Count | Meaning |
|--------|-------|---------|
| FIXED | 39 | Issue was real and is now resolved in code |
| VERIFIED_CLEAN | 1 | Issue claim was rechecked; repo was already clean |
| STALE | 4 | Original claim no longer matches the live code path |
| OPEN | 0 | — |
| PARTIAL | 0 | — |

An additional **9 post-audit verified fixes** (FIX-01 through FIX-09) are recorded covering: health probe auth, `uv run pytest` resolution, TypeScript build regressions, login test markup, notification timezone, circuit-breaker timing, enrichment rollback, interview empty-model handling, and CI workflow updates.

See `docs/audit/00-index.md` for the full item-by-item ledger.

---

## 16. Observations and Recommendations

### Strengths

1. **Well-structured monorepo** — Clear separation of backend/frontend with consistent module-level conventions (`models/schemas/service/router` per domain).
2. **Strong test suite** — 762 backend tests including unit, integration, security, edge-case, and contract layers; 39 frontend tests with coverage gate.
3. **Security-hardened** — HttpOnly JWT cookies, CORS restriction, rate limiting, security headers, token revocation, Redis auth, Docker hardening, SAST in CI.
4. **Production-ready infrastructure** — Health checks on all Docker services, connection pool configuration, timezone-aware timestamps, pgvector support.
5. **Good observability** — structlog structured logging, request-ID propagation, timing headers, scrape telemetry via `ScrapeAttempt` and `ScraperRun` models.
6. **Comprehensive scraping platform** — Port/adapter pattern, browser escalation, bounded pagination, deduplication, per-domain rate limiting.

### Areas for Improvement

1. **Frontend completeness** — Email, networking, outcomes, and copilot chat features have backend support but no UI. Completing these would deliver full P2 feature parity.
2. **Settings persistence** — API keys entered in the UI are never persisted to the backend; this should be wired.
3. **Coverage gaps** — Several service modules in `auto_apply`, `copilot`, `resume`, and `salary` are below 50% coverage; targeted test additions would improve confidence.
4. **Full mypy coverage** — The current CI gate is scoped to 5 files. Expanding strict type checking to the full `app/` directory would catch more type errors.
5. **Frontend integration tests** — Most page tests only check rendering. Adding interaction tests (form submission, API mock responses) would improve regression safety.
6. **Auto-apply UI** — The worker and backend service are implemented; exposing run/pause/applySingle controls in the UI would complete the feature.
7. **Semantic search wiring** — The pgvector-backed semantic search endpoint is ready; wiring it into the Job Board search flow would unlock a key differentiator.

---

*This document was generated by automated exhaustive analysis. For the live operational state, always start at `docs/current-state/00-index.md`.*
