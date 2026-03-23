# Open Items - JobRadar V2

## Blocking Bugs
- None verified in the current `2026-03-23` full validation pass.

## Fixed Structural Gaps (2026-03-23)
- All 10 P2 DB tables created via consolidation migration `005`
- `email` and `outcomes` routers mounted in `main.py` (23 routers total)
- `ir_schema.py`, `renderer.py` recovered; `professional.html` template created
- `users.created_at`/`updated_at` fixed to `timestamp with time zone`
- Ruff clean, 716 backend tests pass

## Remaining Frontend Gaps
- No API modules or pages for: email, networking, outcomes, copilot chat
- No-op stubs: change password, delete account, clear data (no backend endpoints)
- API keys collected in Settings/Onboarding but never persisted to backend
- Auto-apply run/pause/applySingle defined but no UI triggers
- Semantic search endpoint exists but not wired into Job Board

## Non-Blocking Residuals
- Vitest still prints `--localstorage-file was provided without a valid path` warnings during frontend tests.
- Repo-wide strict backend mypy is still deferred; the current CI gate is intentionally scoped to `app/auth/service.py`, `app/config.py`, `app/shared/middleware.py`, `app/scraping/deduplication.py`, and `app/scraping/port.py`.

## Coverage TODOs
- `backend/app/auto_apply/ats_detector.py`, `backend/app/auto_apply/ats_filler.py`, `backend/app/auto_apply/orchestrator.py`, `backend/app/auto_apply/portal_config.py`, `backend/app/auto_apply/question_engine.py`, `backend/app/auto_apply/service.py`, `backend/app/auto_apply/validator.py`, and `backend/app/auto_apply/workday_filler.py` remain below `50%` coverage.
- `backend/app/canonical_jobs/service.py`, `backend/app/companies/service.py`, `backend/app/copilot/prompts.py`, and `backend/app/copilot/service.py` remain below `50%` coverage.
- `backend/app/enrichment/llm_client.py`, `backend/app/enrichment/tfidf.py`, `backend/app/interview/evaluator.py`, `backend/app/nlp/core.py`, and `backend/app/nlp/cover_letter.py` remain below `50%` coverage.
- `backend/app/resume/council.py`, `backend/app/resume/gap_analyzer.py`, `backend/app/resume/service.py`, and `backend/app/salary/service.py` remain below `50%` coverage.
- `backend/app/scraping/ops.py`, `backend/app/scraping/router.py`, `backend/app/scraping/scrapers/adaptive_parser.py`, `backend/app/scraping/scrapers/ai_scraper.py`, `backend/app/scraping/scrapers/apify.py`, `backend/app/scraping/scrapers/career_page.py`, `backend/app/scraping/scrapers/detail_extractor.py`, `backend/app/scraping/scrapers/greenhouse.py`, `backend/app/scraping/scrapers/jobspy.py`, `backend/app/scraping/scrapers/scrapling.py`, `backend/app/scraping/scrapers/serpapi.py`, and `backend/app/scraping/scrapers/theirstack.py` remain below `50%` coverage.
- `backend/app/source_health/service.py` also remains below `50%` coverage, along with zero-covered migration and worker modules that are excluded from the immediate execution queue but still need future direct tests.

## Deferred Feature Work
- Resume PDF generation and additional template flows
- Saved-search alerts UI and related UX
- Further parser tuning for difficult JS-heavy career pages
- End-to-end Playwright coverage
- Longer-term vendoring/repackaging decisions for scraper dependencies
- Rebase feat/p2-polish-advanced onto current main

## Historical Planning Material
- Future design notes live in `docs/research/`.
- Feature spec reference preserved in Claude memory (`reference_spec_features.md`).
