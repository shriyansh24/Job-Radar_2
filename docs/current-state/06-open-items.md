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
- Auto-apply backend now includes recovered form extraction, Greenhouse/Lever adapters, a pre-flight safety layer, live manual/batch service wiring, worker-level batch execution, and operator-facing run/pause/list/stats coverage, but broader operator tooling and deeper browser coverage are still partial.
- Resume upload parsing, tailoring, ATS validation, preview, export, and renderer/template coverage are live; remaining branch-era session-model variants are historical rather than active live-scope gaps.
- Interview prep now returns richer company/role context in the live branch; the branch-era prep-package persistence model is historical rather than committed live scope.
- Enrichment no longer has placeholder API routes: single-job enrichment is live and batch enrichment now queues onto the analysis lane.

## Non-Blocking Residuals
- No blocking residual is currently tied to the frontend sweep; additional browser captures are incremental QA rather than a missing validation gate.
- Migration replay now has a dedicated GitHub workflow and a canonical migration-ops runbook, and targeted downgrade coverage now exists for the base `002` lineage plus the ATS-identity migration slice.
- Scheduler isolation is now queue-backed through ARQ, and queue telemetry now includes depth, oldest-job age, alert state, truthful `retry_exhausted` final-failure logs, and request/job correlation on queue-triggered operator paths.
- Auth lifecycle logging now carries request correlation and normalized reason codes through the main app log stream, but a separate audit-focused sink remains deferred.

## Coverage TODOs
- `backend/app/auto_apply/ats_detector.py`, `backend/app/auto_apply/ats_filler.py`, `backend/app/auto_apply/orchestrator.py`, `backend/app/auto_apply/portal_config.py`, `backend/app/auto_apply/question_engine.py`, `backend/app/auto_apply/service.py`, `backend/app/auto_apply/validator.py`, and `backend/app/auto_apply/workday_filler.py` remain below `50%` coverage.
- `backend/app/canonical_jobs/service.py`, `backend/app/companies/service.py`, `backend/app/copilot/prompts.py`, and `backend/app/copilot/service.py` remain below `50%` coverage.
- `backend/app/enrichment/llm_client.py`, `backend/app/enrichment/tfidf.py`, `backend/app/interview/evaluator.py`, `backend/app/nlp/core.py`, and `backend/app/nlp/cover_letter.py` remain below `50%` coverage.
- `backend/app/resume/council.py`, `backend/app/resume/gap_analyzer.py`, `backend/app/resume/service.py`, and `backend/app/salary/service.py` remain below `50%` coverage.
- `backend/app/scraping/ops.py`, `backend/app/scraping/router.py`, `backend/app/scraping/scrapers/adaptive_parser.py`, `backend/app/scraping/scrapers/ai_scraper.py`, `backend/app/scraping/scrapers/apify.py`, `backend/app/scraping/scrapers/career_page.py`, `backend/app/scraping/scrapers/detail_extractor.py`, `backend/app/scraping/scrapers/greenhouse.py`, `backend/app/scraping/scrapers/jobspy.py`, `backend/app/scraping/scrapers/scrapling.py`, `backend/app/scraping/scrapers/serpapi.py`, and `backend/app/scraping/scrapers/theirstack.py` remain below `50%` coverage.
- `backend/app/source_health/service.py` also remains below `50%` coverage, along with zero-covered migration and worker modules that are excluded from the immediate execution queue but still need future direct tests.

## External Or Non-Goal Follow-Through
- Provider-backed ATS submission flows, destructive admin operations, and seeded-data-heavy PDF fidelity remain environment-specific validation concerns rather than missing repo-local implementation.
- Further parser tuning for difficult JS-heavy career pages remains an ongoing quality-improvement area, not a live-scope contradiction.
- Long-window queue alert routing, dashboards, and dedicated auth audit sinks depend on deployment/log-routing infrastructure outside this repository.

## Historical Planning Material
- Future design notes live in `docs/research/`.
- Feature spec reference is preserved in Claude memory.
