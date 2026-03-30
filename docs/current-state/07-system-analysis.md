# System Analysis Report - Repository-Wide

> Generated for issue request on 2026-03-24.

## 1) Directory Structure (Exhaustive)

- `.github` — GitHub automation and repository policies.
- `.github/workflows` — CI/CD workflows (lint, tests, security, dependency checks).
- `backend` — Python FastAPI backend, DB migrations, workers, and tests.
- `backend/app` — Core backend application modules by domain.
- `backend/app/admin` — Backend domain package for admin (routes, schemas, services, models, or helpers).
- `backend/app/analytics` — Backend domain package for analytics (routes, schemas, services, models, or helpers).
- `backend/app/auth` — Backend domain package for auth (routes, schemas, services, models, or helpers).
- `backend/app/auto_apply` — Backend domain package for auto apply (routes, schemas, services, models, or helpers).
- `backend/app/canonical_jobs` — Backend domain package for canonical jobs (routes, schemas, services, models, or helpers).
- `backend/app/companies` — Backend domain package for companies (routes, schemas, services, models, or helpers).
- `backend/app/copilot` — Backend domain package for copilot (routes, schemas, services, models, or helpers).
- `backend/app/email` — Backend domain package for email (routes, schemas, services, models, or helpers).
- `backend/app/enrichment` — Backend domain package for enrichment (routes, schemas, services, models, or helpers).
- `backend/app/followup` — Backend domain package for followup (routes, schemas, services, models, or helpers).
- `backend/app/interview` — Backend domain package for interview (routes, schemas, services, models, or helpers).
- `backend/app/jobs` — Backend domain package for jobs (routes, schemas, services, models, or helpers).
- `backend/app/migrations` — Alembic migration environment and scripts.
- `backend/app/migrations/versions` — Versioned database schema migrations.
- `backend/app/networking` — Backend domain package for networking (routes, schemas, services, models, or helpers).
- `backend/app/nlp` — Backend domain package for nlp (routes, schemas, services, models, or helpers).
- `backend/app/notifications` — Backend domain package for notifications (routes, schemas, services, models, or helpers).
- `backend/app/outcomes` — Backend domain package for outcomes (routes, schemas, services, models, or helpers).
- `backend/app/pipeline` — Backend domain package for pipeline (routes, schemas, services, models, or helpers).
- `backend/app/profile` — Backend domain package for profile (routes, schemas, services, models, or helpers).
- `backend/app/resume` — Backend domain package for resume (routes, schemas, services, models, or helpers).
- `backend/app/resume/templates` — Backend domain package for templates (routes, schemas, services, models, or helpers).
- `backend/app/salary` — Backend domain package for salary (routes, schemas, services, models, or helpers).
- `backend/app/scraping` — Backend domain package for scraping (routes, schemas, services, models, or helpers).
- `backend/app/scraping/control` — Backend domain package for control (routes, schemas, services, models, or helpers).
- `backend/app/scraping/execution` — Backend domain package for execution (routes, schemas, services, models, or helpers).
- `backend/app/scraping/scrapers` — Backend domain package for scrapers (routes, schemas, services, models, or helpers).
- `backend/app/search_expansion` — Backend domain package for search expansion (routes, schemas, services, models, or helpers).
- `backend/app/settings` — Backend domain package for settings (routes, schemas, services, models, or helpers).
- `backend/app/shared` — Backend domain package for shared (routes, schemas, services, models, or helpers).
- `backend/app/source_health` — Backend domain package for source health (routes, schemas, services, models, or helpers).
- `backend/app/vault` — Backend domain package for vault (routes, schemas, services, models, or helpers).
- `backend/app/workers` — Backend domain package for workers (routes, schemas, services, models, or helpers).
- `backend/scripts` — Backend utility scripts for data import/probing.
- `backend/tests` — Backend automated test suites and fixtures.
- `backend/tests/contracts` — Contract tests for ATS scraper outputs.
- `backend/tests/edge_cases` — Edge-case API and robustness tests.
- `backend/tests/fixtures` — Static fixture payloads/HTML for deterministic tests.
- `backend/tests/fixtures/ashby` — Project subdirectory containing scoped implementation files.
- `backend/tests/fixtures/career_pages` — Project subdirectory containing scoped implementation files.
- `backend/tests/fixtures/greenhouse` — Project subdirectory containing scoped implementation files.
- `backend/tests/fixtures/lever` — Project subdirectory containing scoped implementation files.
- `backend/tests/fixtures/workday` — Project subdirectory containing scoped implementation files.
- `backend/tests/integration` — Integration tests for API/service flows.
- `backend/tests/security` — Security-focused backend tests.
- `backend/tests/unit` — Unit tests for backend domains.
- `backend/tests/unit/scraping` — Unit tests for scraping control/execution stack.
- `docs` — Project documentation root.
- `docs/audit` — Bug-audit ledger and issue status tracking.
- `docs/current-state` — Canonical current operational state documentation.
- `docs/research` — Future-looking design/research notes.
- `frontend` — React frontend app, build config, and UI tests.
- `frontend/src` — Frontend source code (pages, components, API clients, state).
- `frontend/src/__tests__` — Frontend page/app-level tests.
- `frontend/src/api` — Typed API client modules by backend domain.
- `frontend/src/api/__tests__` — API client behavior tests.
- `frontend/src/components` — Reusable UI and feature components.
- `frontend/src/components/__tests__` — Component-level tests.
- `frontend/src/components/analytics` — Analytics visualization components.
- `frontend/src/components/jobs` — Job list/detail and filtering components.
- `frontend/src/components/layout` — Application shell, nav, and auth gate components.
- `frontend/src/components/pipeline` — Pipeline/Kanban interaction components.
- `frontend/src/components/scraper` — Scraper status/control UI components.
- `frontend/src/components/ui` — Design-system primitives and helpers.
- `frontend/src/hooks` — Reusable React hooks.
- `frontend/src/hooks/__tests__` — Hook unit tests.
- `frontend/src/lib` — Frontend shared types, constants, and utility helpers.
- `frontend/src/pages` — Route-level pages.
- `frontend/src/store` — Zustand stores for app-level state.
- `infra` — Infrastructure support artifacts.
- `infra/redis` — Redis infra layout.
- `infra/redis/tls` — Placeholder for Redis TLS assets.

## 2) File-by-File Analysis (Exhaustive High-Level)

### `.`
- `.env.example` — Example environment variable template for local setup.
- `.gitignore` — Git ignore rules for build artifacts, env files, and local state.
- `AGENTS.md` — Agent-facing preferences and workspace facts.
- `CLAUDE.md` — Agent/operator playbook and canonical command surface.
- `DECISIONS.md` — Architecture and implementation decision log.
- `Makefile` — Convenience command wrappers for common dev tasks.
- `PROJECT_STATUS.md` — Snapshot summary of branch health and current status.
- `README.md` — Primary project overview, setup, and command reference.
- `SECURITY.md` — Security disclosure and policy guidance.
- `THIRD_PARTY_CODE.md` — Attribution for third-party incorporated code/assets.
- `docker-compose.dev.yml` — Container orchestration for development environment.
- `docker-compose.yml` — Container orchestration for default deployment stack.

### `.github`
- `.github/dependabot.yml` — GitHub repository configuration.

### `.github/workflows`
- `.github/workflows/ci.yml` — Main CI workflow for linting, testing, building, and dependency checks.
- `.github/workflows/codeql.yml` — CodeQL static analysis workflow for security scanning.
- `.github/workflows/dependency-review.yml` — Dependency review workflow for pull requests.

### `backend`
- `backend/.dockerignore` — Backend Docker build context exclusions.
- `backend/Dockerfile` — Backend container build definition.
- `backend/alembic.ini` — Alembic runtime configuration for DB migrations.
- `backend/pyproject.toml` — Backend package/dependency/tooling configuration (uv, ruff, pytest, mypy).
- `backend/seed_data.py` — Database seed utility for development/testing.
- `backend/start-dev.cjs` — Backend dev startup helper script.
- `backend/uv.lock` — Backend dependency lockfile for reproducible installs.

### `backend/app`
- `backend/app/__init__.py` — Python package marker for backend __init__.py module.
- `backend/app/config.py` — Typed runtime settings and environment variable parsing/validation.
- `backend/app/database.py` — Async SQLAlchemy engine/session factory and DB primitives.
- `backend/app/dependencies.py` — FastAPI dependency injection providers (DB session, auth user, etc.).
- `backend/app/main.py` — FastAPI application bootstrap, middleware, router mounting, scheduler lifecycle.

### `backend/app/admin`
- `backend/app/admin/__init__.py` — Python package marker for backend admin module.
- `backend/app/admin/router.py` — FastAPI endpoints for this domain.
- `backend/app/admin/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/analytics`
- `backend/app/analytics/__init__.py` — Python package marker for backend analytics module.
- `backend/app/analytics/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/analytics/predictor.py` — Backend module implementing domain-specific functionality.
- `backend/app/analytics/rag.py` — Backend module implementing domain-specific functionality.
- `backend/app/analytics/router.py` — FastAPI endpoints for this domain.
- `backend/app/analytics/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/analytics/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/auth`
- `backend/app/auth/__init__.py` — Python package marker for backend auth module.
- `backend/app/auth/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/auth/router.py` — FastAPI endpoints for this domain.
- `backend/app/auth/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/auth/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/auto_apply`
- `backend/app/auto_apply/__init__.py` — Python package marker for backend auto_apply module.
- `backend/app/auto_apply/ats_detector.py` — Backend module implementing domain-specific functionality.
- `backend/app/auto_apply/ats_filler.py` — Backend module implementing domain-specific functionality.
- `backend/app/auto_apply/employers.yaml` — Static employer/application mapping data for auto-apply behavior.
- `backend/app/auto_apply/engine.py` — Backend module implementing domain-specific functionality.
- `backend/app/auto_apply/field_mapper.py` — Backend module implementing domain-specific functionality.
- `backend/app/auto_apply/form_learning.py` — Backend module implementing domain-specific functionality.
- `backend/app/auto_apply/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/auto_apply/orchestrator.py` — Backend module implementing domain-specific functionality.
- `backend/app/auto_apply/portal_config.py` — Backend module implementing domain-specific functionality.
- `backend/app/auto_apply/question_engine.py` — Backend module implementing domain-specific functionality.
- `backend/app/auto_apply/router.py` — FastAPI endpoints for this domain.
- `backend/app/auto_apply/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/auto_apply/service.py` — Business logic/orchestration layer for this domain.
- `backend/app/auto_apply/validator.py` — Backend module implementing domain-specific functionality.
- `backend/app/auto_apply/workday_adapter.py` — Backend module implementing domain-specific functionality.
- `backend/app/auto_apply/workday_filler.py` — Backend module implementing domain-specific functionality.

### `backend/app/canonical_jobs`
- `backend/app/canonical_jobs/__init__.py` — Python package marker for backend canonical_jobs module.
- `backend/app/canonical_jobs/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/canonical_jobs/router.py` — FastAPI endpoints for this domain.
- `backend/app/canonical_jobs/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/canonical_jobs/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/companies`
- `backend/app/companies/__init__.py` — Python package marker for backend companies module.
- `backend/app/companies/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/companies/router.py` — FastAPI endpoints for this domain.
- `backend/app/companies/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/companies/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/copilot`
- `backend/app/copilot/__init__.py` — Python package marker for backend copilot module.
- `backend/app/copilot/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/copilot/prompts.py` — LLM/system prompt templates used by AI-driven features.
- `backend/app/copilot/router.py` — FastAPI endpoints for this domain.
- `backend/app/copilot/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/copilot/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/email`
- `backend/app/email/__init__.py` — Python package marker for backend email module.
- `backend/app/email/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/email/parser.py` — Backend module implementing domain-specific functionality.
- `backend/app/email/router.py` — FastAPI endpoints for this domain.
- `backend/app/email/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/email/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/enrichment`
- `backend/app/enrichment/__init__.py` — Python package marker for backend enrichment module.
- `backend/app/enrichment/embedding.py` — Backend module implementing domain-specific functionality.
- `backend/app/enrichment/gpu_accelerator.py` — Backend module implementing domain-specific functionality.
- `backend/app/enrichment/llm_client.py` — Backend module implementing domain-specific functionality.
- `backend/app/enrichment/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/enrichment/router.py` — FastAPI endpoints for this domain.
- `backend/app/enrichment/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/enrichment/service.py` — Business logic/orchestration layer for this domain.
- `backend/app/enrichment/tfidf.py` — Backend module implementing domain-specific functionality.

### `backend/app/followup`
- `backend/app/followup/__init__.py` — Python package marker for backend followup module.
- `backend/app/followup/models.py` — SQLAlchemy ORM models for persistent domain entities.

### `backend/app/interview`
- `backend/app/interview/__init__.py` — Python package marker for backend interview module.
- `backend/app/interview/evaluator.py` — Backend module implementing domain-specific functionality.
- `backend/app/interview/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/interview/prompts.py` — LLM/system prompt templates used by AI-driven features.
- `backend/app/interview/router.py` — FastAPI endpoints for this domain.
- `backend/app/interview/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/interview/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/jobs`
- `backend/app/jobs/__init__.py` — Python package marker for backend jobs module.
- `backend/app/jobs/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/jobs/router.py` — FastAPI endpoints for this domain.
- `backend/app/jobs/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/jobs/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/migrations`
- `backend/app/migrations/__init__.py` — Schema migration script to evolve database structure.
- `backend/app/migrations/env.py` — Alembic migration environment setup and metadata binding.
- `backend/app/migrations/script.py.mako` — Backend module implementing domain-specific functionality.

### `backend/app/migrations/versions`
- `backend/app/migrations/versions/001_create_users_table.py` — Schema migration script to evolve database structure.
- `backend/app/migrations/versions/002_create_all_tables.py` — Schema migration script to evolve database structure.
- `backend/app/migrations/versions/003_merge_v1_features.py` — Schema migration script to evolve database structure.
- `backend/app/migrations/versions/004_create_email_logs.py` — Schema migration script to evolve database structure.
- `backend/app/migrations/versions/005_create_p2_tables.py` — Schema migration script to evolve database structure.
- `backend/app/migrations/versions/20260321_db_audit_fixes.py` — Schema migration script to evolve database structure.
- `backend/app/migrations/versions/20260323_add_contacts_and_referral_requests.py` — Schema migration script to evolve database structure.
- `backend/app/migrations/versions/20260323_add_resume_archetypes.py` — Schema migration script to evolve database structure.
- `backend/app/migrations/versions/20260323_create_dedup_feedback.py` — Schema migration script to evolve database structure.
- `backend/app/migrations/versions/20260323_form_learning_tables.py` — Schema migration script to evolve database structure.
- `backend/app/migrations/versions/45613a5a2f78_add_job_lifecycle_columns_and_tier_.py` — Schema migration script to evolve database structure.
- `backend/app/migrations/versions/503ca7a300d9_add_indexes_to_scrape_attempts.py` — Schema migration script to evolve database structure.
- `backend/app/migrations/versions/7021f28ab5e0_merge_heads.py` — Schema migration script to evolve database structure.
- `backend/app/migrations/versions/__init__.py` — Schema migration script to evolve database structure.
- `backend/app/migrations/versions/aaba1d3f957f_create_scrape_targets_and_scrape_.py` — Schema migration script to evolve database structure.
- `backend/app/migrations/versions/e5d40ea7c9db_migrate_career_pages_to_scrape_targets_.py` — Schema migration script to evolve database structure.

### `backend/app/networking`
- `backend/app/networking/__init__.py` — Python package marker for backend networking module.
- `backend/app/networking/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/networking/router.py` — FastAPI endpoints for this domain.
- `backend/app/networking/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/networking/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/nlp`
- `backend/app/nlp/__init__.py` — Python package marker for backend nlp module.
- `backend/app/nlp/core.py` — NLP/LLM feature module for text generation or analysis.
- `backend/app/nlp/cover_letter.py` — NLP/LLM feature module for text generation or analysis.
- `backend/app/nlp/cover_letter_templates.py` — Cover-letter template fragments and defaults.
- `backend/app/nlp/model_router.py` — Model selection/router abstraction for LLM calls.

### `backend/app/notifications`
- `backend/app/notifications/__init__.py` — Python package marker for backend notifications module.
- `backend/app/notifications/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/notifications/router.py` — FastAPI endpoints for this domain.
- `backend/app/notifications/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/notifications/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/outcomes`
- `backend/app/outcomes/__init__.py` — Python package marker for backend outcomes module.
- `backend/app/outcomes/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/outcomes/router.py` — FastAPI endpoints for this domain.
- `backend/app/outcomes/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/outcomes/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/pipeline`
- `backend/app/pipeline/__init__.py` — Python package marker for backend pipeline module.
- `backend/app/pipeline/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/pipeline/router.py` — FastAPI endpoints for this domain.
- `backend/app/pipeline/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/pipeline/service.py` — Business logic/orchestration layer for this domain.
- `backend/app/pipeline/state_machine.py` — Backend module implementing domain-specific functionality.

### `backend/app/profile`
- `backend/app/profile/__init__.py` — Python package marker for backend profile module.
- `backend/app/profile/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/profile/router.py` — FastAPI endpoints for this domain.
- `backend/app/profile/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/profile/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/resume`
- `backend/app/resume/__init__.py` — Python package marker for backend resume module.
- `backend/app/resume/archetypes.py` — Resume feature core logic supporting schema, analysis, generation, or rendering.
- `backend/app/resume/council.py` — Resume feature core logic supporting schema, analysis, generation, or rendering.
- `backend/app/resume/gap_analyzer.py` — Resume feature core logic supporting schema, analysis, generation, or rendering.
- `backend/app/resume/ir_schema.py` — Resume feature core logic supporting schema, analysis, generation, or rendering.
- `backend/app/resume/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/resume/prompts.py` — LLM/system prompt templates used by AI-driven features.
- `backend/app/resume/renderer.py` — Resume feature core logic supporting schema, analysis, generation, or rendering.
- `backend/app/resume/router.py` — FastAPI endpoints for this domain.
- `backend/app/resume/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/resume/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/resume/templates`
- `backend/app/resume/templates/minimal.html` — HTML template used for resume rendering/export styles.
- `backend/app/resume/templates/modern.html` — HTML template used for resume rendering/export styles.
- `backend/app/resume/templates/professional.html` — HTML template used for resume rendering/export styles.

### `backend/app/salary`
- `backend/app/salary/__init__.py` — Python package marker for backend salary module.
- `backend/app/salary/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/salary/router.py` — FastAPI endpoints for this domain.
- `backend/app/salary/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/salary/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/scraping`
- `backend/app/scraping/__init__.py` — Python package marker for backend scraping module.
- `backend/app/scraping/constants.py` — Module-level constants/enums and default values.
- `backend/app/scraping/dedup_feedback.py` — Feedback and accuracy tracking models/schemas for dedup review loop.
- `backend/app/scraping/deduplication.py` — Deduplication logic for scraped job normalization and merge decisions.
- `backend/app/scraping/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/scraping/ops.py` — CLI/ops helpers for scraping operations.
- `backend/app/scraping/port.py` — Protocol/dataclass interfaces for scraper integrations.
- `backend/app/scraping/rate_limiter.py` — Token-bucket limiter and circuit-breaker primitives for scraper stability.
- `backend/app/scraping/router.py` — FastAPI endpoints for this domain.
- `backend/app/scraping/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/scraping/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/scraping/control`
- `backend/app/scraping/control/__init__.py` — Python package marker for backend scraping module.
- `backend/app/scraping/control/ats_registry.py` — ATS pattern registry and detector-to-adapter mapping.
- `backend/app/scraping/control/classifier.py` — Target/source classification logic.
- `backend/app/scraping/control/priority_scorer.py` — Target priority scoring heuristics.
- `backend/app/scraping/control/scheduler.py` — Target selection and next-run scheduling policy logic.
- `backend/app/scraping/control/target_registry.py` — Target registration and lookup helpers.
- `backend/app/scraping/control/tier_router.py` — Execution tier routing strategy for scraping targets.

### `backend/app/scraping/execution`
- `backend/app/scraping/execution/__init__.py` — Python package marker for backend scraping module.
- `backend/app/scraping/execution/adapter_registry.py` — Runtime registration of scraper adapters by ATS/vendor.
- `backend/app/scraping/execution/browser_pool.py` — Managed browser context pool and semaphores for heavy scraping.
- `backend/app/scraping/execution/browser_port.py` — Protocol interfaces for browser automation implementations.
- `backend/app/scraping/execution/camoufox_browser.py` — Browser adapter implementation for advanced anti-bot scraping paths.
- `backend/app/scraping/execution/cloudscraper_fetcher.py` — Fetcher adapter implementation for anti-bot aware HTTP retrieval.
- `backend/app/scraping/execution/crawl4ai_extractor.py` — Extraction adapter leveraging Crawl4AI when available.
- `backend/app/scraping/execution/escalation_engine.py` — Escalation path selection across fetch/browser tiers.
- `backend/app/scraping/execution/extractor_port.py` — Protocol interfaces for content extraction implementations.
- `backend/app/scraping/execution/fetcher_port.py` — Protocol interfaces for HTTP fetcher implementations.
- `backend/app/scraping/execution/nodriver_browser.py` — Browser adapter implementation for advanced anti-bot scraping paths.
- `backend/app/scraping/execution/page_crawler.py` — Pagination/page crawling orchestration and stop-condition tracking.
- `backend/app/scraping/execution/scrapling_fetcher.py` — Fetcher adapter implementation for anti-bot aware HTTP retrieval.
- `backend/app/scraping/execution/seleniumbase_browser.py` — Browser adapter implementation for advanced anti-bot scraping paths.

### `backend/app/scraping/scrapers`
- `backend/app/scraping/scrapers/__init__.py` — Python package marker for backend scraping module.
- `backend/app/scraping/scrapers/adaptive_parser.py` — Heuristic parser fallback for non-standard job payloads.
- `backend/app/scraping/scrapers/ai_scraper.py` — ATS/source-specific scraper implementation.
- `backend/app/scraping/scrapers/apify.py` — ATS/source-specific scraper implementation.
- `backend/app/scraping/scrapers/ashby.py` — ATS/source-specific scraper implementation.
- `backend/app/scraping/scrapers/base.py` — Base scraper contracts/utilities for ATS-specific scrapers.
- `backend/app/scraping/scrapers/career_page.py` — ATS/source-specific scraper implementation.
- `backend/app/scraping/scrapers/content_hasher.py` — Content hashing utility for dedup/signature calculations.
- `backend/app/scraping/scrapers/detail_extractor.py` — Extracts richer job detail fields from raw payloads/pages.
- `backend/app/scraping/scrapers/greenhouse.py` — ATS/source-specific scraper implementation.
- `backend/app/scraping/scrapers/jobspy.py` — ATS/source-specific scraper implementation.
- `backend/app/scraping/scrapers/lever.py` — ATS/source-specific scraper implementation.
- `backend/app/scraping/scrapers/scrapling.py` — ATS/source-specific scraper implementation.
- `backend/app/scraping/scrapers/serpapi.py` — ATS/source-specific scraper implementation.
- `backend/app/scraping/scrapers/theirstack.py` — ATS/source-specific scraper implementation.
- `backend/app/scraping/scrapers/workday.py` — ATS/source-specific scraper implementation.

### `backend/app/search_expansion`
- `backend/app/search_expansion/__init__.py` — Python package marker for backend search_expansion module.
- `backend/app/search_expansion/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/search_expansion/router.py` — FastAPI endpoints for this domain.
- `backend/app/search_expansion/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/search_expansion/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/settings`
- `backend/app/settings/__init__.py` — Python package marker for backend settings module.
- `backend/app/settings/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/settings/router.py` — FastAPI endpoints for this domain.
- `backend/app/settings/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/settings/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/shared`
- `backend/app/shared/__init__.py` — Python package marker for backend shared module.
- `backend/app/shared/errors.py` — Shared domain error classes mapped to API behavior.
- `backend/app/shared/events.py` — In-process event bus for publish/subscribe async notifications.
- `backend/app/shared/logging.py` — Structured logging setup and configuration.
- `backend/app/shared/middleware.py` — Custom middleware for security headers, rate limiting, timing, request IDs.
- `backend/app/shared/pagination.py` — Reusable pagination schema/helpers.

### `backend/app/source_health`
- `backend/app/source_health/__init__.py` — Python package marker for backend source_health module.
- `backend/app/source_health/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/source_health/router.py` — FastAPI endpoints for this domain.
- `backend/app/source_health/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/source_health/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/vault`
- `backend/app/vault/__init__.py` — Python package marker for backend vault module.
- `backend/app/vault/models.py` — SQLAlchemy ORM models for persistent domain entities.
- `backend/app/vault/router.py` — FastAPI endpoints for this domain.
- `backend/app/vault/schemas.py` — Pydantic request/response schemas for API boundaries.
- `backend/app/vault/service.py` — Business logic/orchestration layer for this domain.

### `backend/app/workers`
- `backend/app/workers/__init__.py` — Python package marker for backend workers module.
- `backend/app/workers/alert_worker.py` — Backend module implementing domain-specific functionality.
- `backend/app/workers/auto_apply_worker.py` — Backend module implementing domain-specific functionality.
- `backend/app/workers/enrichment_worker.py` — Backend module implementing domain-specific functionality.
- `backend/app/workers/maintenance_worker.py` — Backend module implementing domain-specific functionality.
- `backend/app/workers/phase7a_worker.py` — Backend module implementing domain-specific functionality.
- `backend/app/workers/scheduler.py` — Backend module implementing domain-specific functionality.
- `backend/app/workers/scraping_worker.py` — Backend module implementing domain-specific functionality.

### `backend/scripts`
- `backend/scripts/__init__.py` — Operational helper script for backend data or diagnostics tasks.
- `backend/scripts/import_h1b_targets.py` — Operational helper script for backend data or diagnostics tasks.
- `backend/scripts/probe_unknown_targets.py` — Operational helper script for backend data or diagnostics tasks.

### `backend/tests`
- `backend/tests/__init__.py` — Test package marker.
- `backend/tests/conftest.py` — Shared pytest fixtures and test configuration.

### `backend/tests/contracts`
- `backend/tests/contracts/__init__.py` — Test package marker.
- `backend/tests/contracts/test_greenhouse_contract.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/contracts/test_lever_contract.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/contracts/test_workday_contract.py` — Automated test validating behavior for the related module/feature.

### `backend/tests/edge_cases`
- `backend/tests/edge_cases/test_api_edge_cases.py` — Automated test validating behavior for the related module/feature.

### `backend/tests/fixtures/ashby`
- `backend/tests/fixtures/ashby/expected_jobs.json` — Fixture payload used by tests for deterministic cases.
- `backend/tests/fixtures/ashby/ramp_graphql.json` — Fixture payload used by tests for deterministic cases.

### `backend/tests/fixtures/career_pages`
- `backend/tests/fixtures/career_pages/cloudflare_challenge.html` — Fixture payload used by tests for deterministic cases.
- `backend/tests/fixtures/career_pages/generic_no_json_ld.html` — Fixture payload used by tests for deterministic cases.
- `backend/tests/fixtures/career_pages/generic_with_json_ld.html` — Fixture payload used by tests for deterministic cases.
- `backend/tests/fixtures/career_pages/js_heavy_blank.html` — Fixture payload used by tests for deterministic cases.

### `backend/tests/fixtures/greenhouse`
- `backend/tests/fixtures/greenhouse/expected_jobs.json` — Fixture payload used by tests for deterministic cases.
- `backend/tests/fixtures/greenhouse/gitlab_board.json` — Fixture payload used by tests for deterministic cases.

### `backend/tests/fixtures/lever`
- `backend/tests/fixtures/lever/expected_jobs.json` — Fixture payload used by tests for deterministic cases.
- `backend/tests/fixtures/lever/plaid_postings.json` — Fixture payload used by tests for deterministic cases.

### `backend/tests/fixtures/workday`
- `backend/tests/fixtures/workday/expected_jobs.json` — Fixture payload used by tests for deterministic cases.
- `backend/tests/fixtures/workday/microsoft_xhr.json` — Fixture payload used by tests for deterministic cases.

### `backend/tests/integration`
- `backend/tests/integration/__init__.py` — Test package marker.
- `backend/tests/integration/test_admin_api.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/integration/test_analytics_api.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/integration/test_auth_api.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/integration/test_enrichment.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/integration/test_jobs_api.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/integration/test_notifications_api.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/integration/test_pipeline_api.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/integration/test_profile_api.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/integration/test_scraping_service.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/integration/test_settings_api.py` — Automated test validating behavior for the related module/feature.

### `backend/tests/security`
- `backend/tests/security/test_api_security.py` — Automated test validating behavior for the related module/feature.

### `backend/tests/unit`
- `backend/tests/unit/__init__.py` — Test package marker.
- `backend/tests/unit/test_admin_service.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_analytics_service.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_archetypes.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_ats_detector.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_auth_service.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_auto_apply_orchestrator.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_config.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_cover_letter_v2.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_database.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_dedup_feedback.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_deduplication.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_email_parser.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_embedding_service.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_form_learning.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_gpu_accelerator.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_interview_service.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_job_lifecycle.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_job_model.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_job_service.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_migrations.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_ml_predictor.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_model_contracts.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_model_router.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_networking.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_notifications_service.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_pipeline_service.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_profile_service.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_rag_pipeline.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_rate_limiter.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_resume_templates.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_rule_engine.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_salary_intel.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_scraper_normalization.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_settings_service.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_shared_events.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_shared_pagination.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/test_workday_adapter.py` — Automated test validating behavior for the related module/feature.

### `backend/tests/unit/scraping`
- `backend/tests/unit/scraping/__init__.py` — Test package marker.
- `backend/tests/unit/scraping/test_adapter_registry.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_ats_registry.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_ats_validation.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_attempt_model.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_browser_pool.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_camoufox_browser.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_classifier.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_cloudscraper_fetcher.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_constants.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_crawl4ai_extractor.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_escalation_engine.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_execution_ports.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_nodriver_browser.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_ops_cli.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_page_crawler.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_priority_scorer.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_run_scrape.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_run_target_batch.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_scheduler.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_scraper_run_model.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_scrapling_fetcher.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_seleniumbase_browser.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_simhash_deterministic.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_target_model.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_target_registry.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_tier_router.py` — Automated test validating behavior for the related module/feature.
- `backend/tests/unit/scraping/test_workday_scraper.py` — Automated test validating behavior for the related module/feature.

### `docs`
- `docs/design-brief.md` — Documentation for architecture, audits, state, or research context.

### `docs/audit`
- `docs/audit/00-index.md` — Index document that links and summarizes this documentation section.
- `docs/audit/01-security.md` — Documentation for architecture, audits, state, or research context.
- `docs/audit/02-backend.md` — Documentation for architecture, audits, state, or research context.
- `docs/audit/03-scraper.md` — Documentation for architecture, audits, state, or research context.
- `docs/audit/04-database.md` — Documentation for architecture, audits, state, or research context.
- `docs/audit/05-frontend.md` — Documentation for architecture, audits, state, or research context.
- `docs/audit/06-infra.md` — Documentation for architecture, audits, state, or research context.

### `docs/current-state`
- `docs/current-state/00-index.md` — Index document that links and summarizes this documentation section.
- `docs/current-state/01-repo-map.md` — Documentation for architecture, audits, state, or research context.
- `docs/current-state/02-backend.md` — Documentation for architecture, audits, state, or research context.
- `docs/current-state/03-frontend.md` — Documentation for architecture, audits, state, or research context.
- `docs/current-state/04-data-and-scraping.md` — Documentation for architecture, audits, state, or research context.
- `docs/current-state/05-ops-and-ci.md` — Documentation for architecture, audits, state, or research context.
- `docs/current-state/06-open-items.md` — Documentation for architecture, audits, state, or research context.

### `docs/research`
- `docs/research/00-index.md` — Index document that links and summarizes this documentation section.
- `docs/research/01-smart-dedup.md` — Documentation for architecture, audits, state, or research context.
- `docs/research/02-resume-pipeline.md` — Documentation for architecture, audits, state, or research context.
- `docs/research/03-form-filling.md` — Documentation for architecture, audits, state, or research context.
- `docs/research/04-learning-kb.md` — Documentation for architecture, audits, state, or research context.
- `docs/research/05-local-stack.md` — Documentation for architecture, audits, state, or research context.

### `frontend`
- `frontend/.dockerignore` — Frontend Docker build context exclusions.
- `frontend/Dockerfile` — Frontend container build definition.
- `frontend/eslint.config.js` — ESLint linting rules for the frontend codebase.
- `frontend/index.html` — Frontend bootstrap or local development startup helper.
- `frontend/package-lock.json` — Frontend lockfile for reproducible npm installs.
- `frontend/package.json` — Frontend package manifest (scripts, dependencies, metadata).
- `frontend/start-dev.cjs` — Frontend bootstrap or local development startup helper.
- `frontend/tsconfig.app.json` — TypeScript compiler configuration.
- `frontend/tsconfig.json` — TypeScript compiler configuration.
- `frontend/tsconfig.node.json` — TypeScript compiler configuration.
- `frontend/vite.config.ts` — Vite/Vitest build and test tooling configuration.
- `frontend/vitest.config.ts` — Vite/Vitest build and test tooling configuration.

### `frontend/src`
- `frontend/src/App.tsx` — Top-level route tree, providers, and app shell composition.
- `frontend/src/index.css` — Global styles, design tokens, and theme variables.
- `frontend/src/main.tsx` — Frontend React entrypoint mounting App and global styles.
- `frontend/src/vite-env.d.ts` — Vite ambient TypeScript declarations.

### `frontend/src/__tests__`
- `frontend/src/__tests__/Admin.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/__tests__/Analytics.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/__tests__/App.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/__tests__/AutoApply.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/__tests__/Dashboard.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/__tests__/DocumentVault.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/__tests__/InterviewPrep.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/__tests__/JobBoard.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/__tests__/JobDetail.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/__tests__/Login.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/__tests__/Phase7aPages.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/__tests__/Pipeline.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/__tests__/Profile.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/__tests__/ResumeBuilder.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/__tests__/SalaryInsights.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/__tests__/Settings.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/__tests__/Targets.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/__tests__/setup.ts` — Vitest/testing-library setup hooks and globals.
- `frontend/src/__tests__/testUtils.tsx` — Shared frontend test rendering/providers utilities.

### `frontend/src/api`
- `frontend/src/api/admin.ts` — API module for backend endpoint integration in this feature area.
- `frontend/src/api/analytics.ts` — API module for backend endpoint integration in this feature area.
- `frontend/src/api/auth.ts` — API module for backend endpoint integration in this feature area.
- `frontend/src/api/auto-apply.ts` — API module for backend endpoint integration in this feature area.
- `frontend/src/api/client.ts` — Shared API client wrapper/interceptors for HTTP requests.
- `frontend/src/api/copilot.ts` — API module for backend endpoint integration in this feature area.
- `frontend/src/api/interview.ts` — API module for backend endpoint integration in this feature area.
- `frontend/src/api/jobs.ts` — API module for backend endpoint integration in this feature area.
- `frontend/src/api/notifications.ts` — API module for backend endpoint integration in this feature area.
- `frontend/src/api/phase7a.ts` — API module for backend endpoint integration in this feature area.
- `frontend/src/api/pipeline.ts` — API module for backend endpoint integration in this feature area.
- `frontend/src/api/profile.ts` — API module for backend endpoint integration in this feature area.
- `frontend/src/api/resume.ts` — API module for backend endpoint integration in this feature area.
- `frontend/src/api/salary.ts` — API module for backend endpoint integration in this feature area.
- `frontend/src/api/scraper.ts` — API module for backend endpoint integration in this feature area.
- `frontend/src/api/settings.ts` — API module for backend endpoint integration in this feature area.
- `frontend/src/api/vault.ts` — API module for backend endpoint integration in this feature area.

### `frontend/src/api/__tests__`
- `frontend/src/api/__tests__/analytics.test.ts` — Frontend automated test for UI/component/page behavior.
- `frontend/src/api/__tests__/jobs.test.ts` — Frontend automated test for UI/component/page behavior.
- `frontend/src/api/__tests__/scraper.test.ts` — Frontend automated test for UI/component/page behavior.

### `frontend/src/components`
- `frontend/src/components/ErrorBoundary.tsx` — Feature-oriented reusable frontend component.

### `frontend/src/components/__tests__`
- `frontend/src/components/__tests__/AuthGuard.test.tsx` — Frontend automated test for UI/component/page behavior.

### `frontend/src/components/analytics`
- `frontend/src/components/analytics/AnalyticsCharts.tsx` — Feature-oriented reusable frontend component.

### `frontend/src/components/jobs`
- `frontend/src/components/jobs/JobCard.tsx` — Feature-oriented reusable frontend component.
- `frontend/src/components/jobs/JobDetail.tsx` — Feature-oriented reusable frontend component.
- `frontend/src/components/jobs/JobFilters.tsx` — Feature-oriented reusable frontend component.
- `frontend/src/components/jobs/ScoreGauge.tsx` — Feature-oriented reusable frontend component.

### `frontend/src/components/layout`
- `frontend/src/components/layout/AppShell.tsx` — Feature-oriented reusable frontend component.
- `frontend/src/components/layout/AuthGuard.tsx` — Feature-oriented reusable frontend component.
- `frontend/src/components/layout/NotificationBell.tsx` — Feature-oriented reusable frontend component.
- `frontend/src/components/layout/Sidebar.tsx` — Feature-oriented reusable frontend component.

### `frontend/src/components/pipeline`
- `frontend/src/components/pipeline/AddApplicationModal.tsx` — Feature-oriented reusable frontend component.
- `frontend/src/components/pipeline/ApplicationCard.tsx` — Feature-oriented reusable frontend component.
- `frontend/src/components/pipeline/ApplicationModal.tsx` — Feature-oriented reusable frontend component.
- `frontend/src/components/pipeline/KanbanBoard.tsx` — Feature-oriented reusable frontend component.
- `frontend/src/components/pipeline/PipelineColumn.tsx` — Feature-oriented reusable frontend component.
- `frontend/src/components/pipeline/statusBadgeVariant.ts` — Feature-oriented reusable frontend component.

### `frontend/src/components/scraper`
- `frontend/src/components/scraper/ScraperControlPanel.tsx` — Feature-oriented reusable frontend component.
- `frontend/src/components/scraper/ScraperLog.tsx` — Feature-oriented reusable frontend component.

### `frontend/src/components/ui`
- `frontend/src/components/ui/Badge.tsx` — Reusable UI primitive component for the design system.
- `frontend/src/components/ui/Button.tsx` — Reusable UI primitive component for the design system.
- `frontend/src/components/ui/Card.tsx` — Reusable UI primitive component for the design system.
- `frontend/src/components/ui/Dropdown.tsx` — Reusable UI primitive component for the design system.
- `frontend/src/components/ui/EmptyState.tsx` — Reusable UI primitive component for the design system.
- `frontend/src/components/ui/Input.tsx` — Reusable UI primitive component for the design system.
- `frontend/src/components/ui/Modal.tsx` — Reusable UI primitive component for the design system.
- `frontend/src/components/ui/PageLoader.tsx` — Reusable UI primitive component for the design system.
- `frontend/src/components/ui/Select.tsx` — Reusable UI primitive component for the design system.
- `frontend/src/components/ui/Skeleton.tsx` — Reusable UI primitive component for the design system.
- `frontend/src/components/ui/StatCard.tsx` — Reusable UI primitive component for the design system.
- `frontend/src/components/ui/Table.tsx` — Reusable UI primitive component for the design system.
- `frontend/src/components/ui/Tabs.tsx` — Reusable UI primitive component for the design system.
- `frontend/src/components/ui/Textarea.tsx` — Reusable UI primitive component for the design system.
- `frontend/src/components/ui/Toast.tsx` — Reusable UI primitive component for the design system.
- `frontend/src/components/ui/Toggle.tsx` — Reusable UI primitive component for the design system.
- `frontend/src/components/ui/index.ts` — Barrel exports for UI primitives.
- `frontend/src/components/ui/toastService.ts` — Imperative helper for global toast notifications.

### `frontend/src/hooks`
- `frontend/src/hooks/useDebounce.ts` — Reusable React hook encapsulating side effects or interactions.
- `frontend/src/hooks/useKeyboard.ts` — Reusable React hook encapsulating side effects or interactions.
- `frontend/src/hooks/useSSE.ts` — Reusable React hook encapsulating side effects or interactions.

### `frontend/src/hooks/__tests__`
- `frontend/src/hooks/__tests__/useDebounce.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/hooks/__tests__/useKeyboard.test.tsx` — Frontend automated test for UI/component/page behavior.
- `frontend/src/hooks/__tests__/useSSE.test.tsx` — Frontend automated test for UI/component/page behavior.

### `frontend/src/lib`
- `frontend/src/lib/constants.ts` — Frontend constants and static configuration values.
- `frontend/src/lib/types.ts` — Shared TypeScript domain and API type definitions.
- `frontend/src/lib/utils.ts` — Shared utility helper functions used across UI modules.

### `frontend/src/pages`
- `frontend/src/pages/Admin.tsx` — Route-level page component for a major product surface.
- `frontend/src/pages/Analytics.tsx` — Route-level page component for a major product surface.
- `frontend/src/pages/AutoApply.tsx` — Route-level page component for a major product surface.
- `frontend/src/pages/CanonicalJobs.tsx` — Route-level page component for a major product surface.
- `frontend/src/pages/Companies.tsx` — Route-level page component for a major product surface.
- `frontend/src/pages/Dashboard.tsx` — Route-level page component for a major product surface.
- `frontend/src/pages/DocumentVault.tsx` — Route-level page component for a major product surface.
- `frontend/src/pages/InterviewPrep.tsx` — Route-level page component for a major product surface.
- `frontend/src/pages/JobBoard.tsx` — Route-level page component for a major product surface.
- `frontend/src/pages/Login.tsx` — Route-level page component for a major product surface.
- `frontend/src/pages/Onboarding.tsx` — Route-level page component for a major product surface.
- `frontend/src/pages/Pipeline.tsx` — Route-level page component for a major product surface.
- `frontend/src/pages/Profile.tsx` — Route-level page component for a major product surface.
- `frontend/src/pages/ResumeBuilder.tsx` — Route-level page component for a major product surface.
- `frontend/src/pages/SalaryInsights.tsx` — Route-level page component for a major product surface.
- `frontend/src/pages/SearchExpansion.tsx` — Route-level page component for a major product surface.
- `frontend/src/pages/Settings.tsx` — Route-level page component for a major product surface.
- `frontend/src/pages/Sources.tsx` — Route-level page component for a major product surface.
- `frontend/src/pages/Targets.tsx` — Route-level page component for a major product surface.

### `frontend/src/store`
- `frontend/src/store/useAuthStore.ts` — Zustand state store for auth/UI/jobs/scraper application state.
- `frontend/src/store/useJobStore.ts` — Zustand state store for auth/UI/jobs/scraper application state.
- `frontend/src/store/useScraperStore.ts` — Zustand state store for auth/UI/jobs/scraper application state.
- `frontend/src/store/useUIStore.ts` — Zustand state store for auth/UI/jobs/scraper application state.

### `infra/redis/tls`
- `infra/redis/tls/.gitkeep` — Infrastructure support artifact or placeholder file.

## 3) Execution Flow
1. **Backend boot**: `backend/app/main.py` creates FastAPI app, validates settings, installs middleware, mounts routers, and starts APScheduler lifecycle jobs via `backend/app/workers/scheduler.py`.
2. **Frontend boot**: `frontend/src/main.tsx` mounts React app; `frontend/src/App.tsx` configures React Query, routing, auth-guarded shell, and lazy-loaded pages.
3. **User authentication**: cookie-based auth endpoints in `backend/app/auth/router.py` and service logic in `backend/app/auth/service.py`; frontend integrates through `frontend/src/api/auth.ts` and `frontend/src/store/useAuthStore.ts`.
4. **Scrape triggering**: manual trigger via `POST /scraper/run` in `backend/app/scraping/router.py`; scheduled triggers via APScheduler jobs in `backend/app/workers/scheduler.py` calling `backend/app/workers/scraping_worker.py`.
5. **Scraping execution**: `ScrapingService.run_scrape()` in `backend/app/scraping/service.py` iterates source adapters, applies per-source rate limiter + circuit breaker, fetches jobs with timeout, deduplicates via `backend/app/scraping/deduplication.py`, and persists to `backend/app/jobs/models.py`.
6. **Target pipeline**: `run_target_batch_job()` in `backend/app/workers/scraping_worker.py` selects due targets with `backend/app/scraping/control/scheduler.py`, builds adapter registry (`execution/adapter_registry.py`), executes target batch, and computes next run times with backoff.
7. **Enrichment flow**: enrichment workers call `backend/app/enrichment/service.py`, which cleans HTML, calls LLM through `backend/app/enrichment/llm_client.py`, parses JSON output, restores snapshots on failure, and commits successful enrichments.
8. **Downstream features**: pipeline, resume, interview, salary, analytics, auto-apply, notifications, source health, networking/outcomes/email domains each expose routers/services and persist through SQLAlchemy models.
9. **Frontend data consumption**: route pages in `frontend/src/pages/*` call domain API clients in `frontend/src/api/*`, cache via React Query, and render with component libraries under `frontend/src/components/*`.
10. **Realtime updates**: scraper events are streamed through SSE endpoint `/scraper/stream` (`backend/app/scraping/router.py`) and consumed by `frontend/src/hooks/useSSE.ts`.

## 4) Core Logic & Design Patterns
- **Layered domain structure**: each backend domain commonly uses `models.py` + `schemas.py` + `service.py` + `router.py` pattern for separation of persistence, contracts, business logic, and transport.
- **Adapter/port abstractions**: scraping runtime defines ports (`scraping/port.py`, `execution/*_port.py`) and concrete adapters (`scraping/scrapers/*.py`, browser/fetcher/extractor adapters).
- **Registry pattern**: `scraping/execution/adapter_registry.py`, `scraping/control/ats_registry.py`, and `target_registry.py` centralize runtime mapping of ATS/vendor to execution strategy.
- **Scheduler + policy pattern**: APScheduler periodic jobs plus target-level scoring/scheduling in `scraping/control/scheduler.py` and `priority_scorer.py`.
- **Resilience pattern**: token bucket rate limiting and circuit breaker in `scraping/rate_limiter.py`; per-source timeout in `ScrapingService.SOURCE_FETCH_TIMEOUT_S`; retries/backoff behavior encoded via next-run computation.
- **Stable dedup identity**: jobs persisted with deterministic SHA-256 IDs from source/title/company/location (`ScrapingService._compute_job_id()`).
- **Event-driven updates**: async event bus (`shared/events.py`) + SSE endpoint for frontend live progress.
- **Frontend composition pattern**: route-centric pages + reusable primitives + Zustand stores + React Query for server state.

## 5) Pain Points / Bottlenecks
- **Browser-heavy scraping cost**: Browser pool tiers (`scraping/execution/browser_pool.py`, `*_browser.py`) are CPU/RAM expensive compared to pure HTTP adapters.
- **Sequential source loop in `run_scrape()`**: sources are processed one-by-one in `ScrapingService.run_scrape()`; this improves safety but can increase total scrape latency.
- **LLM enrichment latency/cost**: enrichment calls per job (`enrichment/service.py`) are external-model dependent and can be throughput bottlenecks in large batches.
- **Coverage sensitivity in CI for frontend**: CI enforces statement coverage threshold (`.github/workflows/ci.yml`), making tests a frequent failure point when UI grows faster than coverage.
- **Known residual frontend gaps**: docs (`docs/current-state/06-open-items.md`) note missing frontend surfaces for some backend domains (email/networking/outcomes/copilot chat).

## 6) Technology Stack
- **Backend language/runtime**: Python 3.12 (`backend/pyproject.toml`).
- **Backend framework**: FastAPI + Uvicorn + SQLAlchemy async + Alembic + PostgreSQL/pgvector + Redis (`backend/pyproject.toml`, `backend/app/main.py`).
- **Backend key libraries**: structlog, APScheduler, sse-starlette, Playwright, cloudscraper, nodriver, camoufox, seleniumbase, BeautifulSoup, markdownify, scikit-learn, PyJWT, bcrypt.
- **Frontend language/runtime**: TypeScript + React 19 + Vite 6 (`frontend/package.json`).
- **Frontend key libraries**: TanStack Query, Zustand, React Router, Framer Motion, Recharts, Phosphor Icons, Geist fonts, Testing Library, Vitest, ESLint, Tailwind CSS v4.
- **Tooling**: `uv` for backend dependency/runtime commands; `npm` for frontend; GitHub Actions for CI/CodeQL/dependency review.

## 7) Configuration & Extensibility
- **Configuration model**: runtime settings loaded via `backend/app/config.py` and `.env` patterns (`.env.example`).
- **Scraper extensibility**: add new scraper by implementing scraper port/base, registering in `_init_scrapers()` (`scraping/service.py`) and/or adapter registries (`execution/adapter_registry.py`, `control/ats_registry.py`).
- **Target scheduling knobs**: interval/backoff in `scraping/control/scheduler.py`; APScheduler intervals in `workers/scheduler.py` (hours/minutes per job).
- **Frontend API extensibility**: add domain API module under `frontend/src/api`, add page in `frontend/src/pages`, and route entry in `frontend/src/App.tsx`.
- **Hard-coded vs configurable**: many scheduler intervals are currently coded constants in `workers/scheduler.py`; API keys and environment behavior are settings-driven via config/env.

## 8) Observability & Error Handling
- **Structured logging**: ubiquitous `structlog` usage (`shared/logging.py`, routers/services/workers) with event-style logs and contextual fields.
- **Middleware observability**: request IDs and timing middleware in `shared/middleware.py` provide per-request traceability and timing visibility.
- **Failure containment**: scraping catches source failures, records sanitized error messages, and continues other sources (`scraping/service.py`).
- **Circuit breaking/rate limiting**: scraper failures influence circuit breaker state and request pacing (`scraping/rate_limiter.py`).
- **Transactional safeguards**: enrichment snapshots/restores mutated fields on failure (`enrichment/service.py`), and DB rollback logic is used in persistence paths.
- **SSE/event error tolerance**: event callback failures are logged and do not abort scrape flow (`scraping/service.py`).

## 9) Current State (Working vs Partial vs Active Development)
- **Working**: backend tests/lint and frontend lint/test/build pass locally in this environment.
- **Partially complete**: frontend still has documented gaps for some backend features (email/networking/outcomes/copilot chat, settings action wiring) per `CLAUDE.md` and `PROJECT_STATUS.md`.
- **Active development context**: docs identify `feat/p2-polish-advanced` as feature-rich active branch; this current branch focuses on documentation analysis output.

## 10) Additional Findings
- **CI failures investigated**: recent failing run on `codex/career-os-overhaul` was due to frontend coverage threshold miss and backend Ruff issues; this branch validates green locally.
- **Repository inventory**: 76 tracked directories and 502 tracked files analyzed.
- **Security posture**: dedicated `SECURITY.md`, CI `codeql.yml`, dependency review workflow, and backend bandit/pip-audit checks in CI.

## Branch-Unique Notes (kept separate)
- `main` — Protected baseline branch; stable reference with security/dependency hardening merged.
- `codex/career-os-overhaul` — Ahead of main by 3 commits; major frontend Career OS overhaul plus backend settings/account actions and docs updates.
- `feat/p0-spec-features` — Ahead of main by 3 commits; foundational P0 feature and migration work around analytics/enrichment/scraping model fields.
- `feat/p1-core-value` — Ahead of main by 6 commits; P1 feature expansion (interview/auto-apply/pipeline improvements and fixes).
- `phase7a/db-migrations-core` — No merge-base with current main; historical lineage with different top-level architecture and legacy files.
- `shriyansh24-patch-1` — One unique commit adding `.github/workflows/summary.yml` for issue summarization.
- `v1-archive` — No merge-base with current main; archival snapshot preserving earlier monolithic/phase7a structure.
- `claude/add-claude-documentation-Di27V` — No merge-base with current main; docs-focused branch adding comprehensive `CLAUDE.md` in older layout.
- `cursor/development-environment-setup-29c7` — No merge-base with current main; setup/instructions branch adding `AGENTS.md` in older layout.
