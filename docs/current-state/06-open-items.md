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
- Semantic search now uses the live hybrid backend path and can be launched from Search Expansion, but the ranking model is still intentionally conservative and can be made richer.
- Auto-apply backend now includes recovered form extraction, Greenhouse/Lever adapters, a pre-flight safety layer, live manual/batch service wiring, and worker-level batch execution, but broader operator tooling and end-to-end coverage are still partial.
- Saved-search alerts UI and scheduler UX remain a follow-up enhancement.
- Resume upload parsing, tailoring, ATS validation, and renderer/template coverage are live, but richer preview/export flows and additional operator polish remain the largest resume-family gap.
- Interview prep now returns richer company/role context in the live branch, but deeper persistence/history packaging from `feat/p1-core-value` is still not promoted.

## Non-Blocking Residuals
- No blocking residual is currently tied to the frontend sweep; additional browser captures are incremental QA rather than a missing validation gate.
- Migration replay now has a dedicated GitHub workflow and a canonical migration-ops runbook, but only one downgrade path is explicitly exercised in tests.
- Scheduler isolation is now queue-backed through ARQ, and queue telemetry now includes depth / retry metadata, but alerting and broader worker-lane coverage still need hardening.
- Auth lifecycle logging now carries request correlation and normalized reason codes through the main app log stream, but a separate audit-focused sink remains deferred.

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
- Broader end-to-end Playwright coverage beyond the current smoke, shell, recovered interview/search, route-family, prepare/intelligence/outcomes, operations/admin/data, profile/settings/auth, and theme-matrix passes
- Longer-term vendoring or repackaging decisions for scraper dependencies

## Historical Planning Material
- Future design notes live in `docs/research/`.
- Feature spec reference is preserved in Claude memory.
