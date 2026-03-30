# Frontend Test Taxonomy

## Purpose
Document the committed frontend test layout so page, hook, component, and API coverage stay discoverable as the UI changes.

## Source-Of-Truth Status
- Status: `LIVE_LAYOUT`
- Scope: frontend unit-level and route-level tests under `frontend/src/tests/`
- Last validation basis: taxonomy move plus `npm run test -- --run` on `2026-03-27`

## Layout
```text
frontend/src/tests/
  app/             App-level boot and auth-boundary coverage
  api/             frontend API client contract wrappers
  components/
    jobs/          focused job-detail and job-surface component behavior
    layout/        shell and layout behavior
    ui/            shared presentation primitives
  hooks/           reusable hook behavior named after the hook under test
  pages/           route-level page behavior
    targets/       targets route behavior and operator exposure coverage
  support/         setupTests bootstrap and renderWithProviders helpers
```

## Notes
- `support/setupTests.ts` is the shared Vitest bootstrap entrypoint.
- `support/renderWithProviders.tsx` owns the shared router/query-client render helper and should be preferred over inline wrappers when practical.
- `pages/` protects route behavior, not visual snapshots.
- Route-specific folders under `pages/` are preferred once a surface has more than one suite.
- Current route-level coverage now includes dedicated suites for dashboard, jobs, pipeline, profile, settings, sources, companies, auto-apply, analytics, interview prep, resume builder, compensation, search expansion, networking, email, onboarding, outcomes, copilot, canonical jobs, and targets.
- API client tests should stay named `*.api.test.ts` so boundary intent is visible at the path level.
- Component suites should prefer a subsystem folder like `components/jobs/`, `components/layout/`, or `components/ui/` once they stop being generic umbrella files.
- Hook suites should stay named after the hook, without extra `.hook` markers in the filename.
- Browser/e2e coverage now lives under `frontend/e2e/` with `smoke/`, `flows/`, `theme-matrix/`, and `support/` lanes.
