# Backend Audit - JobRadar V2

## BE-01 - CRITICAL: Hardcoded `/tmp` Path
- **File:** `backend/app/auto_apply/orchestrator.py`
- **Detail:** Fixed. Screenshot paths now use the system temp directory instead of a Linux-only hardcoded `/tmp` path.
- **Evidence:** `backend/tests/unit/test_auto_apply_orchestrator.py`
- **Status:** FIXED

## BE-02 - CRITICAL: Silent Exception Swallowing in Worker
- **File:** `backend/app/workers/scraping_worker.py`
- **Detail:** Fixed. The dead helper that contained the audited bare `except Exception: pass` blocks has been removed, leaving the worker on the shared registry builder path only.
- **Evidence:** `backend/app/workers/scraping_worker.py`
- **Status:** FIXED

## BE-03 - HIGH: Partial Failure Commit
- **File:** `backend/app/scraping/service.py`
- **Detail:** Fixed. Batch execution now inspects `asyncio.gather()` results, rolls back on task failures, and avoids committing partial target batches.
- **Evidence:** `backend/tests/workers/scraping/test_target_batch_worker.py`
- **Status:** FIXED

## BE-04 - HIGH: LLM Failures Return Empty Dict
- **File:** `backend/app/enrichment/service.py`
- **Detail:** Fixed. Enrichment now raises an explicit `EnrichmentError` for empty or unparsable LLM responses instead of silently returning `{}` and marking the job enriched.
- **Evidence:** `backend/tests/integration/test_enrichment.py`
- **Status:** FIXED

## BE-05 - HIGH: Placeholder Questions on LLM Failure
- **File:** `backend/app/interview/service.py`
- **Detail:** Fixed. Question generation now raises a `502` `AppError` on model failure instead of persisting fake placeholder interview questions.
- **Evidence:** `backend/tests/unit/test_interview_service.py`
- **Status:** FIXED

## BE-06 - HIGH: No Timeout on `run_scrape()`
- **File:** `backend/app/scraping/service.py`
- **Detail:** Fixed. The legacy source-fetch path is now wrapped in `asyncio.wait_for()`, so a hung scraper cannot block the run indefinitely.
- **Evidence:** `backend/tests/workers/scraping/test_scrape_run_worker.py`
- **Status:** FIXED

## BE-07 - MEDIUM: Assertion in Production
- **File:** `backend/app/scraping/rate_limiter.py`
- **Detail:** Fixed. The production `assert` has been replaced with an explicit runtime error fallback.
- **Evidence:** `backend/tests/security/test_rate_limiter.py`
- **Status:** FIXED

## BE-08 - MEDIUM: Event Callback Failure = Scraper Failure
- **File:** `backend/app/scraping/service.py`
- **Detail:** Fixed. Progress callback failures are now isolated and logged instead of being treated as scraper failures.
- **Evidence:** `backend/tests/workers/scraping/test_scrape_run_worker.py`
- **Status:** FIXED

## BE-09 - LOW: Adapter Registry Logs at DEBUG
- **File:** `backend/app/scraping/execution/adapter_registry.py`
- **Detail:** Fixed. Skipped adapter registration now logs at warning level so the signal is visible in normal production logs.
- **Evidence:** `backend/tests/unit/scraping/test_adapter_registry.py`
- **Status:** FIXED

## Verified Fixes Since Initial Audit

## BE-F01 - FIXED: Admin Health Endpoint Was Incorrectly Auth-Protected
- **Files:** `backend/app/admin/router.py`, `backend/tests/integration/test_auth_api.py`
- **Detail:** `GET /api/v1/admin/health` no longer requires auth, which restores health probes and the backend integration check.
- **Status:** FIXED

## BE-F02 - FIXED: Failed Enrichment No Longer Persists Partial Job Mutations
- **Files:** `backend/app/enrichment/service.py`, `backend/tests/integration/test_enrichment.py`
- **Detail:** The enrichment pipeline now snapshots and restores the mutable enrichment fields on failure, so a job that fails LLM enrichment does not commit cleaned-description or partial enrichment state.
- **Status:** FIXED

## BE-F03 - FIXED: Interview Generation / Prep Reject Empty Model Payloads
- **Files:** `backend/app/interview/service.py`, `backend/app/nlp/model_router.py`, `backend/tests/unit/test_interview_service.py`, `backend/tests/unit/test_model_router.py`
- **Detail:** Empty JSON results now raise out of the model router, question generation no longer persists empty sessions, and interview prep now surfaces empty model payloads as `502` failures.
- **Status:** FIXED

## BE-F04 - FIXED: Interview Job Context Uses `company_name`
- **Files:** `backend/app/interview/service.py`, `backend/tests/unit/test_interview_service.py`
- **Detail:** The interview service now loads company context from `jobs.company_name` instead of the non-existent `jobs.company` attribute.
- **Status:** FIXED
