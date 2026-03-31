# JobRadar V2: Completion Program Gap Analysis & Strategic Future Bets

## Context
Shriyansh has a comprehensive "JobRadar V2 Repository Completion Program" document (10 sections, ~8,000 words) that describes the full vision for a local-first job search OS. This file is a comparative analysis of that document versus the repository as it exists now: (1) what was already built, (2) what remained outside live scope at the time of analysis, (3) what would have duplicated existing work, and (4) what strategic future opportunities the original document did not cover.

It is not the active live backlog. The current live operational truth and remaining repo-local items are tracked in `docs/current-state/06-open-items.md` and `docs/audit/00-index.md`.

This analysis is the result of an exhaustive audit of every directory in the repo, all docs, the audit ledger, the research index, PROJECT_STATUS.md, and competitive web research across 30+ job search platforms.

---

## PART 1: Historical Doc vs. Repo Delta (Not Live Backlog)

### Section 1 — Scraper Engine: Rust Sidecar

| Doc Requirement | Status | Detail |
|-----------------|--------|--------|
| Rust sidecar binary (`sidecar/` directory) | **NOT STARTED** | No `sidecar/` dir, no Cargo.toml, no Rust code exists anywhere |
| spider-rs / reqwest+tokio high-throughput fetcher | **NOT STARTED** | Scraping is 100% Python (Playwright, httpx, cloudscraper, scrapling, nodriver, camoufox) |
| `POST /batch-scrape` localhost HTTP API | **NOT STARTED** | No sidecar API; Python backend calls scrapers directly |
| `GET /health` sidecar endpoint | **NOT STARTED** | |
| Per-domain rate limit (1 req/s/domain in Rust) | **PYTHON EQUIVALENT EXISTS** | `rate_limiter.py` handles this in Python |
| robots.txt parsing + Protego | **DONE** | Non-ATS target batches now evaluate `robots.txt` with Protego and block disallowed fetches before execution |
| User-Agent rotation pool | **PARTIAL** | camoufox/nodriver handle UA rotation at browser level, not HTTP level |
| Cross-compile CI for 3 platforms | **NOT STARTED** | No Rust CI at all |
| Site discovery via Google dorking | **NOT IMPLEMENTED** | Operator-managed target creation is live on `/targets`; discovery automation remains future scope rather than a missing live feature |
| `scrape_targets` health monitoring dashboard | **PARTIAL** | `source_health` module exists with monitoring, but no dedicated scrape-target failure alerting UI |
| 1,400 sites / 30-min staggered batch scheduling | **NOT AT SCALE** | Scheduler + ARQ workers exist, but not tested at 1,400-site scale with staggered batches |

### Section 2 — Auto-Apply Engine

| Doc Requirement | Status | Detail |
|-----------------|--------|--------|
| Greenhouse API adapter (boards-api POST) | **EXISTS** | `greenhouse_adapter.py` — browser-based, not pure API POST |
| Lever API adapter (multipart/form-data) | **EXISTS** | `lever_adapter.py` — API-based with docx support |
| Workday browser adapter (shadow DOM) | **EXISTS** | `workday_adapter.py` with dedicated `workday/` submodule |
| ATSAdapter Protocol interface | **EXISTS** | `detect()`, `get_form_schema()`, `fill_and_review()`, `submit()` pattern |
| CAPTCHA handling (reCAPTCHA Enterprise for Greenhouse) | **NOT IMPLEMENTED** | No CAPTCHA token generation or user-pause flow |
| Unseen question pipeline (LLM → user review → store) | **PARTIAL** | `question_engine.py` exists but no explicit "present to user for review before submit" UI flow |
| Question answer learning schema (`question_answers` table) | **NOT VERIFIED** | `form_learning.py` exists but learning schema may differ from doc spec |
| Resume generation per-application (on-the-fly) | **PARTIAL** | Resume tailoring exists, but not auto-triggered per application submission |
| Typst rendering engine | **NOT IMPLEMENTED** | Only WeasyPrint (PDF) and HTML; no Typst binary |
| LaTeX → PDF rendering | **NOT IMPLEMENTED** | No `pdflatex` or LaTeX templates |
| DOCX output format (python-docx) | **PARTIAL** | Lever adapter uses docx; no general DOCX export from resume builder |
| `generated_resumes` storage schema | **PARTIAL** | `ResumeVersion` model exists, linked to jobs but not exactly matching doc schema |
| Application status workflow (draft→reviewing→submitted→acknowledged→rejected/interview/offer) | **EXISTS** | Pipeline has stages including `rejected` and `withdrawn`, bounded drag/drop |
| "Your applications mentioning X skill get 2x more callbacks" insights | **NOT IMPLEMENTED** | Analytics patterns exist but not this specific correlation surface |

### Section 3 — LLM Prompt System

| Doc Requirement | Status | Detail |
|-----------------|--------|--------|
| YAML prompt registry (`prompts/` directory) | **NOT IMPLEMENTED** | Prompts are Python-embedded in `resume/prompts.py`, `copilot/prompts.py`, `interview/prompts.py` |
| Centralized PromptTemplate schema with versioning | **NOT IMPLEMENTED** | No version tracking, no prompt metadata |
| LLMRouter class with task_type routing | **PARTIAL** | `nlp/model_router.py` exists with model selection, but not the full spec interface |
| Provider fallback chain (primary → secondary → Ollama) | **PARTIAL** | Model router exists; no explicit fallback chain with Ollama local |
| promptfoo evaluation harness | **NOT IMPLEMENTED** | No eval directory, no golden test sets, no promptfoo integration |
| Golden test sets (145 cases across 5 task types) | **NOT IMPLEMENTED** | |
| Per-request cost tracking and logging | **NOT IMPLEMENTED** | No LLM cost/token logging table |
| `no_fabrication` guardrail (compare output vs profile) | **NOT IMPLEMENTED** | Resume `validator.py` exists but not a fabrication-check guardrail |
| `pii_redaction` guardrail | **NOT IMPLEMENTED** | No PII scanning on LLM I/O |
| Temperature/few-shot best practices enforcement | **NOT SYSTEMATIZED** | Individual prompts set params ad-hoc |

### Section 4 — Google Workspace Integration

| Doc Requirement | Status | Detail |
|-----------------|--------|--------|
| googleworkspace/cli (`gws`) binary integration | **NOT IMPLEMENTED** | Live Google support uses direct OAuth + Gmail API calls, not the Google Workspace CLI |
| Gmail monitoring (inbox triage, auto-status update) | **IMPLEMENTED (GMAIL-FIRST)** | Google OAuth-backed Gmail sync now lands selected hiring communications in the existing email module and can apply conservative pipeline transitions or review-required notifications |
| Calendar integration (interview scheduling) | **NOT IMPLEMENTED** | Gmail-first is live; Calendar remains explicitly out of current live scope |
| Drive integration (resume storage in Drive folders) | **NOT IMPLEMENTED** | Gmail-first is live; Drive remains explicitly out of current live scope |
| OAuth credential management for Google | **IMPLEMENTED** | `UserIntegrationSecret` now stores OAuth metadata (`auth_type`, `secret_json`, account/scopes, validation/sync/error fields), and Settings exposes connect/reconnect/disconnect/sync flows |

### Section 5 — Repository Completion Program (6 Lanes)

| Lane | Status | Detail |
|------|--------|--------|
| Godel (scheduler decoupling) | **DONE** | ARQ-backed scheduler, 3 worker roles, queue telemetry |
| Ramanujan (capability recovery) | **MOSTLY DONE** | Auto-apply, resume, interview, dedup, search all recovered |
| Turing (frontend completion) | **MOSTLY DONE** | 22 routes, 152 components, 8-mode theme matrix in e2e |
| Raman (test taxonomy) | **DONE** | Backend: contracts/infra/migrations/security/workers; Frontend: tests/ + e2e/ |
| Hegel (CI/security) | **MOSTLY DONE** | 6 CI workflows, CSRF middleware, security headers, CodeQL, dep review |
| Leibniz (docs/closure) | **MOSTLY DONE** | 3-layer doc system, gap report closed for repo scope |

### Section 6-7 — Constraints & Execution Rules

| Requirement | Status |
|-------------|--------|
| Structured JSON logging (structlog) | **DONE** — `shared/logging.py` |
| CSRF protection | **DONE** — `CsrfProtectionMiddleware` |
| Trusted-host enforcement | **DONE** — `TrustedHostMiddleware` |
| Total RSS < 12 GB | **NOT TESTED** — No profiling done |
| Cross-platform (Win/Mac/Linux) | **MOSTLY** — Docker Compose works; Rust sidecar not built |

### Section 8 — Additional Features

| Feature | Status | Detail |
|---------|--------|--------|
| Splink probabilistic dedup | **NOT IMPLEMENTED** | Uses SimHash + ATS composite key instead |
| Hybrid search (pgvector + tsvector) | **EXISTS** | Live backend path via enrichment embeddings + search |
| Embedding backfill worker | **EXISTS** | `enrichment_worker.py` handles batch embedding |
| Interview prep engine | **EXISTS** | Full module with generation, evaluation, sessions |
| Salary negotiation | **EXISTS** | Research, offer evaluation, brief endpoints |
| Networking messages | **EXISTS** | Contacts, referrals, outreach |
| Email module | **EXISTS** | Webhook, parser, status inference |
| Browser extension (M10) | **NOT STARTED** | Explicitly marked as future in doc |
| Analytics and insights | **EXISTS** | Overview, daily, patterns, application funnel |

---

## PART 2: Historical / Strategic Items Outside Live Repo Scope

### Audit Ledger: 4 STALE Items
These are items from the original 44-issue audit that no longer match the live code path:

| ID | Severity | Item | Why Stale |
|----|----------|------|-----------|
| SC-03 | CRIT | Circuit breaker stuck in half-open | Code path changed; CB timing now uses monotonic clock with regression tests (FIX-06) |
| SC-05 | HIGH | EventBus.publish() — one dead subscriber blocks all | EventBus pattern may have been refactored or removed |
| SC-07 | HIGH | Simhash threshold too aggressive — false positive dedup | Dedup now uses ATS composite key as primary; SimHash is secondary |
| SC-14 | LOW | Apify scraper: 65 lines, never used | Historical stale-item reference; not an active live backlog item |

### Deferred Work Items (from audit)
| ID | Feature | Status |
|----|---------|--------|
| DEF-01 | Resume PDF generation + templates | **DONE** — WeasyPrint + 3 HTML templates |
| DEF-03 | Targets add/edit/delete career page UI | **DONE** — `/targets` now exposes operator-facing career-page create/edit/delete flows over the existing career-page API |
| DEF-04 | Saved Search Alerts UI + scheduler trigger | **DONE** — saved searches now expose alert status, manual checks, worker notifications, and scheduled alert execution |
| DEF-06 | Conditional requests (ETag/If-Modified-Since) | **DONE** â€” fetcher tiers now send conditional headers from target cache metadata and refresh cache state after successful fetches |
| DEF-07 | robots.txt checking via Protego | **DONE** â€” non-ATS target batches now evaluate `robots.txt` before fetches and surface block/warn outcomes in logs and attempts |
| DEF-08 | Protego library wired into execution loop | **DONE** â€” Protego policy now runs inside the live target-batch execution path with deterministic regression coverage |

### Research Items Still Exploratory
| Item | Status |
|------|--------|
| Learning KB (D1-D4): SQL patterns, outcome ML predictor, personal RAG | `EXPLORATORY` — analytics/rag.py exists as a start, but no HistGradientBoosting predictor, no structured learning loop |
| Local LLM stack (E1): GPU acceleration, HybridLLMRouter | `ARCHIVED_RESEARCH` — not being pursued |
| Simhash → embedding-based near-dedup replacement | `NOT DONE` |
| iCIMS adapter (iframe handling) | `NOT DONE` |

### External/Deployment Follow-Through (Not Repo Bugs)
- GitHub branch protection enforcement (configured outside repo)
- Dedicated auth audit log routing (deployment infrastructure)
- Long-window queue alert dashboards (deployment infrastructure)
- Production restore strategy (operator concern)

---

## PART 3: Overlap Analysis — What NOT to Redo

These doc sections describe things that **already exist** in the codebase. Implementing them would be duplicate work:

| Doc Section | What Already Exists | Do NOT Redo |
|-------------|---------------------|-------------|
| 1.2 ATS Detection/Fingerprinting | `ats_detector.py`, `classifier.py`, `ats_registry.py` — URL pattern, HTML signal, JS global, API probe all implemented | ATS detection pipeline |
| 1.2.2 Known ATS URL Patterns | Greenhouse, Lever, Ashby, Workday scrapers all exist with URL pattern matching | ATS URL patterns |
| 1.4 Site Registry Schema | `ScrapeTarget` model exists with all specified fields | Registry table |
| 1.4.2 Health Monitoring | `source_health/` module, `ScrapeAttempt` model, consecutive failure tracking | Health monitoring |
| 1.5 Scheduling (arq migration) | ARQ workers live with 3 roles (scraping/analysis/ops), Redis queue, health checks | Scheduler decoupling |
| 2.1 Auto-Apply Adapters | Greenhouse, Lever, Workday adapters exist with form extraction, field mapping, safety | Per-ATS adapters |
| 2.2 Form Schema Understanding | `form_extractor.py`, `field_mapper.py`, `question_engine.py` | Form parsing |
| 2.4 Application Tracking | Pipeline with full status workflow, `ApplicationStatusHistory` model | Pipeline tracking |
| 5.1-5.2 Six Lanes + Phases | Godel, Raman, most of Hegel/Turing/Ramanujan/Leibniz are done | 6-lane execution |
| 8.2 Hybrid Search | pgvector + enrichment embeddings + semantic search endpoint | Search system |
| 8.3 Interview Prep | Full interview module with generation, evaluation, sessions | Interview prep |
| 8.4 Salary Intelligence | Research, offer evaluation, brief endpoints | Salary module |
| 8.5 Networking Messages | Contacts, referrals, outreach, company scan | Networking |
| 8.6 Analytics | Overview, daily, patterns, application funnel | Analytics |

---

## PART 4: What the Doc MISSED (Competitive Feature Gaps)

Based on web research across 30+ job search platforms (Teal, Huntr, Simplify, Jobscan, Careerflow, Rezi, Final Round AI, LockedIn AI, etc.):

### High-Leverage Missing Features

These are product-expansion opportunities, not missing committed live functionality.

| Feature | Why It Matters | Effort |
|---------|---------------|--------|
| **Ghost Job Detection Score** | Platform already has `first_seen`/`last_seen`/disappearance data. Add a scoring surface: posting age, repost count, company hiring signals. Jobright monetizes this. No consumer tool has it natively. | Low |
| **Resume Version → Interview Conversion Analytics** | Pipeline + resume versions exist. Wire "which resume version → which outcome" to close the feedback loop competitors don't close. | Low |
| **Company Hiring Signal Feed** | WARN Act filings, SEC 8-Ks, Crunchbase funding rounds are public data. Surface a "hiring health" badge per job card. No competitor does this. | Medium |
| **Referral Finder ("Who do I know here?")** | Referred candidates are 4x more likely to be hired. Platform has networking but no "find my connections at Company X" surface. | Medium |
| **Visa Sponsorship Filter (H-1B/OPT)** | USCIS LCA dataset is public CSV. Map company names to sponsor history. H1BGrader charges for this as a Chrome extension. | Low |
| **ATS Keyword Score per Application** | Jobscan's core feature. Show 0-100 match score with keyword gaps before submission. Resume tailoring exists but no explicit numeric score surface. | Low |
| **LinkedIn Profile Optimizer** | Every major competitor has this. Score per-section, keyword gap vs target roles. | Medium |
| **Live Interview Copilot** | Final Round AI has 10M+ users. Real-time transcription + suggested answers during live interviews. Distinct from existing prep. | High |
| **Browser Extension (Job Capture + Universal Autofill)** | Simplify has 1M+ users. One-click job save from any website. Extends auto-apply beyond configured ATS. | High |
| **Offer Comparison Calculator (Total Comp)** | Side-by-side multi-offer comparison with equity, bonus, benefits, COL adjustment. Salary research exists but no structured comparison. | Low |
| **Follow-Up Email Sequence Templates** | Initial email, 5-day follow-up, 14-day check-in, post-rejection exit, post-offer thanks. Low effort, high retention. | Very Low |
| **Skills Gap Analyzer with Learning Links** | Compare skills vs target role, link to Coursera/Udemy for each gap. | Medium |
| **Career Journal / Accomplishment Log** | Log wins throughout the year, feed into resume generation. Prevents "blank resume" problem. | Low |

### Table-Stakes Features the Doc Already Covers
The doc correctly identifies: Rust sidecar (performance), Google Workspace (productivity), promptfoo eval (quality), and YAML prompt registry (maintainability). These are infrastructure improvements, not competitive gaps.

---

## PART 5: Optional Future Opportunities (Not Active Live Backlog)

The live repo-local backlog is intentionally narrow in `docs/current-state/06-open-items.md`. The tiers below are preserved as optional follow-on work if scope is reopened; they are not current committed implementation obligations.

### Tier 0 — Already Done (Skip)
- ATS detection, scraping infrastructure, ARQ scheduler, auto-apply adapters, resume pipeline, interview prep, salary, networking, email, analytics, pipeline, CSRF, structured logging, security headers, test taxonomy, docs system

### Tier 1 — Low-Effort High-Value Future Bets
1. Ghost job detection score (scoring surface on existing data)
2. Resume version → conversion analytics (wire pipeline outcomes to resume versions)
3. ATS keyword match score per application (expose numeric score before submit)
4. Follow-up email sequence templates (5 templates, very fast)
5. Offer comparison calculator (TC breakdown surface)
6. Visa sponsorship filter (USCIS public data cross-reference)
7. Career accomplishment journal (structured input capture)

### Tier 2 — Medium-Effort Follow-On Work If Scope Reopens
1. YAML prompt registry + versioning migration
2. Broader Google Workspace follow-through (Calendar, Drive, or `googleworkspace/cli` adoption beyond the live Gmail-first scope)
3. LLM cost/token tracking and logging
4. CAPTCHA handling for Greenhouse API submissions
5. Unseen question review UI flow (present LLM answers for approval before submit)
6. Parser tuning for difficult JS-heavy career pages and source-specific anti-bot recovery
7. Alert delivery depth beyond in-app saved-search notifications

### Tier 3 — High-Effort Strategic Follow-On Work
1. Rust sidecar binary for high-throughput scraping
2. promptfoo evaluation harness with golden test sets
3. Site discovery automation (Google dorking, BuiltWith)
4. Learning KB (SQL patterns, ML predictor, personal RAG maturity)
5. Typst + LaTeX resume rendering engines
6. DOCX resume export format
7. iCIMS adapter

### Tier 4 — High-Effort Competitive Differentiation
1. LinkedIn profile optimizer
2. Referral finder ("who do I know here")
3. Company hiring signal feed (WARN Act, SEC, Crunchbase)
4. Browser extension (Chrome MV3)
5. Live interview copilot
6. Skills gap analyzer with learning pathways
7. Mobile app / PWA

---

## Verification Plan
After implementation of any tier:
- Backend: `cd backend && uv run pytest` (must stay >1025 passed)
- Frontend: `cd frontend && npm run lint && npm run test -- --run && npm run build`
- E2E: `cd frontend && npm run e2e`
- Docker: `docker compose up -d` and verify all services healthy
- Browser sweep: authenticate and verify new surfaces render correctly
