# Test Taxonomy

## Purpose
Define and track the purpose-driven test layout used by the repository.

## Source-Of-Truth Status
- Status: `IMPLEMENTED`
- Scope: test naming, location, and protection-goal taxonomy
- Last validation basis: taxonomy moves plus targeted runner validation on `2026-03-27`

## Current State
- Frontend support files, page suites, hook suites, component suites, and API client suites now live under `frontend/src/tests/`.
- Frontend browser/e2e coverage now has a committed home under `frontend/e2e/`.
- Frontend browser/e2e coverage now includes auth/shell smoke, shell navigation, responsive shell behavior, recovered interview/search flows, route-family outcomes, route-family communications/setup coverage, route-family prepare/intelligence/outcomes coverage, route-family operations/admin/data coverage, route-family profile/settings/auth coverage, the resume preview/export flow, live analytics pattern surfaces through the intelligence route family, and route-family theme matrix checks across all 8 theme combinations.
- Backend runtime, migration, security, contract, and worker-lifecycle suites now have dedicated directories under `backend/tests/`.
- Backend auto-apply extractor, adapter, and safety coverage now has explicit unit suites under `backend/tests/unit/auto_apply/`.
- Backend auto-apply operator integration coverage now has an explicit API suite under `backend/tests/integration/auto_apply/`.
- Backend interview, search, dedup, and auto-apply worker coverage now has explicit subsystem buckets under `backend/tests/unit/{interview,search,dedup}/` and `backend/tests/workers/auto_apply/`.
- Backend ATS identity and scrape-target identity lineage now have explicit migration and integration coverage under `backend/tests/migrations/` and `backend/tests/integration/scraping/`.
- Backend digest-worker follow-through now has a dedicated worker suite under `backend/tests/workers/`.
- Backend contract suites are now split between `backend/tests/contracts/providers/` and `backend/tests/contracts/models/`, and `backend/tests/unit/` no longer leaves subsystem suites flat at the filesystem root.

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

frontend/e2e/
  flows/       critical authenticated workflows
  smoke/       boot/login/shell health checks
  support/     Playwright helpers
  theme-matrix/ theme family and mode persistence coverage
```

### Backend
```text
backend/tests/
  contracts/   schema and adapter contract assertions
  edge_cases/  route-owned API edge cases and unusual input-path coverage
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
  - `frontend/src/tests/support/setupTests.ts`
  - `frontend/src/tests/support/renderWithProviders.tsx`
- App boundary suite renamed:
  - `frontend/src/tests/app/App.auth-boundary.test.tsx`
- Route suites moved into `frontend/src/tests/pages/`
- API client suites moved into `frontend/src/tests/api/`
- Hook suites moved into `frontend/src/tests/hooks/`
- Component suites moved into `frontend/src/tests/components/`
- The former phase-based ops coverage is now split across route-owned suites:
  - `frontend/src/tests/pages/Admin.page.test.tsx`
  - `frontend/src/tests/pages/Companies.page.test.tsx`
  - `frontend/src/tests/pages/SearchExpansion.page.test.tsx`
  - `frontend/src/tests/pages/Sources.page.test.tsx`
  - `frontend/src/tests/pages/targets/Targets.page.test.tsx`
- Focused operator exposure coverage is now in:
  - `frontend/src/tests/components/layout/AppShell.scraper-operator.test.tsx`
  - `frontend/src/tests/pages/targets/Targets.operator-exposure.test.tsx`
- Committed browser coverage now includes:
  - `frontend/e2e/smoke/auth-shell.spec.ts`
  - `frontend/e2e/flows/route-shell-navigation.spec.ts`
  - `frontend/e2e/flows/route-family-outcomes.spec.ts`
  - `frontend/e2e/flows/communications-setup.spec.ts`
  - `frontend/e2e/flows/interview-search-recovered.spec.ts`
  - `frontend/e2e/flows/prepare-intelligence-outcomes.spec.ts`
  - `frontend/e2e/flows/operations-admin-data.spec.ts`
  - `frontend/e2e/flows/profile-settings-auth.spec.ts`
  - `frontend/e2e/flows/resume-template-preview.spec.ts`
  - `frontend/e2e/flows/shell-responsive.spec.ts`
  - `frontend/e2e/theme-matrix/theme-persistence.spec.ts`
  - `frontend/e2e/theme-matrix/route-theme-matrix.spec.ts`

### Backend
- Migration regression suite moved:
  - `backend/tests/migrations/test_alembic_revisions.py`
- Infra/runtime suites moved:
  - `backend/tests/infra/test_runtime_config.py`
  - `backend/tests/infra/test_database.py`
  - `backend/tests/infra/test_queue_runtime_compose.py`
  - `backend/tests/infra/cli/test_scraping_ops_cli.py`
- Contract/security suites moved:
  - `backend/tests/contracts/models/test_sqlalchemy_model_contracts.py`
  - `backend/tests/security/test_rate_limiter.py`
- Provider contract suites moved:
  - `backend/tests/contracts/providers/test_greenhouse_contract.py`
  - `backend/tests/contracts/providers/test_lever_contract.py`
  - `backend/tests/contracts/providers/test_workday_contract.py`
- Worker lifecycle suites moved:
  - `backend/tests/workers/scraping/test_scrape_run_worker.py`
  - `backend/tests/workers/scraping/test_target_batch_worker.py`
  - `backend/tests/workers/scraping/test_scrape_scheduler.py`
  - `backend/tests/workers/auto_apply/test_auto_apply_worker.py`
  - `backend/tests/workers/test_digest_worker.py`
- Auto-apply capability recovery suites added:
  - `backend/tests/unit/auto_apply/test_form_extractor.py`
  - `backend/tests/unit/auto_apply/test_greenhouse_adapter.py`
  - `backend/tests/unit/auto_apply/test_lever_adapter.py`
  - `backend/tests/unit/auto_apply/test_safety_layer.py`
- Auto-apply operator/API suites added:
  - `backend/tests/integration/auto_apply/test_auto_apply_api.py`
- Interview/search/dedup suites moved into subsystem buckets:
  - `backend/tests/unit/interview/test_interview_service.py`
  - `backend/tests/unit/interview/test_interview_contextual_service.py`
  - `backend/tests/unit/search/test_hybrid_search.py`
  - `backend/tests/unit/search/test_freshness.py`
  - `backend/tests/unit/search/test_normalization.py`
  - `backend/tests/unit/search/test_ats_composite_key.py`
  - `backend/tests/unit/dedup/test_deduplication.py`
- ATS identity lineage suites added:
  - `backend/tests/integration/scraping/test_scraping_identity.py`
  - `backend/tests/migrations/test_job_ats_identity_migration.py`
  - `backend/tests/migrations/test_scrape_target_identity_migrations.py`

## Optional Further Refinement

### Frontend
- `frontend/src/tests/pages/*.page.test.tsx` still communicate route ownership better than behavior; some should later be narrowed into more behavior-specific suites when the page APIs stabilize.
- UI primitive coverage is now split across `frontend/src/tests/components/ui/Card.test.tsx`, `frontend/src/tests/components/ui/Dropdown.test.tsx`, and `frontend/src/tests/components/ui/StatCard.test.tsx`; buttons, inputs, tables, and toggles still need first-class suites.
- Several page suites still define inline `renderWithProviders` helpers and should converge on `support/renderWithProviders.tsx`.
- `frontend/e2e/flows/` now protects shell/auth, recovered interview/search, route-family outcomes, prepare/intelligence/outcomes, operations/admin/data, profile/settings/auth, resume preview/export, and the current analytics-pattern route family, but it still needs deeper task-level workflows and failure-state coverage.
- `frontend/e2e/theme-matrix/` now covers route-family 8-mode assertions across home, communications, setup, prepare, intelligence, operations, search, and settings surfaces. Keep deeper task-level failure-state coverage in `flows/`, not in theme-matrix assertions.

### Backend
- `backend/tests/edge_cases/` is now split by route family. Further splits should happen only when a subsystem gains a clear ownership boundary rather than out of style pressure.
- Non-scraping workers from deferred or retained branches still have no dedicated `backend/tests/workers/` coverage.

## Coverage Gaps That Need First-Class Homes
- Browser e2e route depth across cross-route state transitions, richer task flows, and failure states beyond the current committed route-family coverage
- Migration replay and rollback safety beyond the current targeted replay suite
- Worker lifecycle and queue-owned execution behavior beyond the current enqueue/runtime coverage and role-lane probes
- Auto-apply orchestration, service wiring, and browser/integration coverage beyond the current unit plus worker-level extractor/adapter/safety tests
- Scraper failure handling and conditional request behavior
- Provider-backed ATS flows, destructive admin actions, and seeded-data-heavy PDF/layout checks still rely on targeted/manual validation outside the committed Playwright tree

## Safe Execution Order
1. Keep the new support directories stable and update runners/docs in the same batch as moves.
2. Split mixed frontend component/page suites only after the destination taxonomy is stable.
3. Keep backend subsystem buckets stable and split them only when ownership becomes meaningfully clearer than the current filesystem.
4. Expand the committed Playwright tree by route family without duplicating the manual screenshot lane.

## Non-Goals For This Batch
- No weak snapshot theater.
- No conversion of integration tests into fake unit tests just to reduce runtime.
- No noisy browser suite until the selector and startup story is strong enough to keep it trustworthy.
