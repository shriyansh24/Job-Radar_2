# Open Items - JobRadar V2

## Blocking Bugs
- None verified in the current `2026-03-27` cleanup pass.

## Fixed Structural Gaps (2026-03-27)
- Reference-first frontend migration shipped across all routed pages.
- Shared shell, navigation, tokens, and page grammar now follow the reference-first command-center system.
- `SearchExpansion`, `Resume Studio`, `Compensation`, `Settings`, `Admin`, and `Targets` now align to the live backend contracts used by the app.
- Vault update integration coverage was added and passes in the targeted backend suite.
- Local Postgres schema was upgraded to Alembic `head` so the settings/integration surfaces match the current app.

## Remaining Frontend Gaps
- Route-by-route copy cleanup and page decomposition are still worth continuing on the largest remaining surfaces, but the main frontend sweep is now integrated and validated.
- Semantic search can still be made richer inside the Job Board beyond the current exact/semantic mode toggle.
- Auto-apply still has room for broader operator tooling and coverage beyond the current route surface.
- Saved-search alerts UI and scheduler UX remain a follow-up enhancement.
- Resume PDF generation and additional template flows remain deferred.

## Non-Blocking Residuals
- No blocking residual is currently tied to the frontend sweep; additional browser captures are incremental QA rather than a missing validation gate.
- Cookie-authenticated state-changing requests still do not have a dedicated CSRF token flow.
- Trusted-host enforcement is still not explicit in the FastAPI middleware stack.
- Migration replay now has a dedicated GitHub workflow, but rollback and backfill guidance remain a follow-up hardening task.

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
- Broader end-to-end Playwright coverage beyond the current smoke pass
- Longer-term vendoring or repackaging decisions for scraper dependencies

## Historical Planning Material
- Future design notes live in `docs/research/`.
- Feature spec reference is preserved in Claude memory.
