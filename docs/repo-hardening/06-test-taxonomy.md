# Test Taxonomy

## Purpose
Define and track the purpose-driven test layout used by the repository.

## Source-Of-Truth Status
- Status: `PARTIALLY_IMPLEMENTED`
- Scope: test naming, location, and protection-goal taxonomy
- Last validation basis: taxonomy moves plus targeted runner validation on `2026-03-27`

## Current State
- Frontend support files, page suites, hook suites, component suites, and API client suites now live under `frontend/src/tests/`.
- Backend runtime, migration, security, contract, and worker-lifecycle suites now have dedicated directories under `backend/tests/`.
- Several older service/model suites still remain in broad backend `unit/` buckets, and some frontend page/component files still cover multiple behaviors inside one suite.
- There is still no committed browser/e2e test tree.

## Live Taxonomy

### Frontend
```text
frontend/src/tests/
  app/         App-level auth and boot boundaries
  api/         frontend API client wrappers
  components/  shared UI and shell components
  hooks/       reusable hook behavior
  pages/       route-level page behavior
  support/     setup/bootstrap and render helpers

frontend/e2e/  (planned)
```

### Backend
```text
backend/tests/
  contracts/   schema and adapter contract assertions
  edge_cases/  catch-all edge cases still awaiting split
  fixtures/    shared fixtures and factories
  infra/       config, database bootstrap, and operational CLI behavior
  integration/ API and cross-module integration coverage
  migrations/  Alembic and schema replay safety
  security/    auth, rate limiting, and security behavior
  unit/        remaining subsystem-local unit suites
  workers/     background execution and scheduler behavior
```

## Implemented In This Batch

### Frontend
- Support files moved:
  - `frontend/src/tests/support/setup.ts`
  - `frontend/src/tests/support/test-utils.tsx`
- App boundary suite renamed:
  - `frontend/src/tests/app/App.auth-boundary.test.tsx`
- Route suites moved into `frontend/src/tests/pages/`
- API client suites moved into `frontend/src/tests/api/`
- Hook suites moved into `frontend/src/tests/hooks/`
- Component suites moved into `frontend/src/tests/components/`
- The misleading phase-based suite now lives at:
  - `frontend/src/tests/pages/OperationsPages.contract.test.tsx`

### Backend
- Migration regression suite moved:
  - `backend/tests/migrations/test_alembic_revisions.py`
- Infra/runtime suites moved:
  - `backend/tests/infra/test_runtime_config.py`
  - `backend/tests/infra/test_database_bootstrap.py`
  - `backend/tests/infra/cli/test_scraping_ops_cli.py`
- Contract/security suites moved:
  - `backend/tests/contracts/test_sqlalchemy_models.py`
  - `backend/tests/security/test_rate_limiter.py`
- Worker lifecycle suites moved:
  - `backend/tests/workers/scraping/test_scrape_run_worker.py`
  - `backend/tests/workers/scraping/test_target_batch_worker.py`
  - `backend/tests/workers/scraping/test_scrape_scheduler.py`

## Remaining Rename / Split Candidates

### Frontend
- `frontend/src/tests/pages/*.page.test.tsx` still communicate route ownership better than behavior; some should later be narrowed into more behavior-specific suites when the page APIs stabilize.
- `frontend/src/tests/components/UiPrimitives.rendering.test.tsx` still protects multiple primitives in one file and should eventually be split by component.
- Several page suites still define inline `renderWithProviders` helpers and should converge on `support/test-utils.tsx`.

### Backend
- `backend/tests/unit/` still contains broad service/model suites that should eventually be regrouped by subsystem ownership.
- `backend/tests/edge_cases/test_api_edge_cases.py` remains a catch-all lane and should be split by API behavior when touched next.
- Non-scraping workers from deferred or retained branches still have no dedicated `backend/tests/workers/` coverage.

## Coverage Gaps That Need First-Class Homes
- Browser e2e route smoke and theme coverage
- Migration replay and rollback safety beyond the current targeted replay suite
- Worker lifecycle and scheduler execution behavior for non-scraping jobs
- Auto-apply adapters and form extraction
- Scraper failure handling and conditional request behavior
- Frontend critical flows that currently rely on manual browser QA artifacts rather than committed tests

## Safe Execution Order
1. Keep the new support directories stable and update runners/docs in the same batch as moves.
2. Split mixed frontend component/page suites only after the destination taxonomy is stable.
3. Continue draining broad backend `unit/` and `edge_cases/` suites into role-based directories.
4. Add the first committed browser/e2e lane only when selectors and boot flow are stable enough to stay low-noise.

## Non-Goals For This Batch
- No weak snapshot theater.
- No conversion of integration tests into fake unit tests just to reduce runtime.
- No noisy browser suite until the selector and startup story is strong enough to keep it trustworthy.
