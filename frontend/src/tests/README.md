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
  app/         App-level boot and auth-boundary coverage
  api/         frontend API client contract wrappers
  components/  shared component behavior and rendering
  hooks/       reusable hook behavior
  pages/       route-level page behavior
  support/     test bootstrap and render helpers
```

## Notes
- `support/` owns shared helpers and should be preferred over inline render wrappers when practical.
- `pages/` protects route behavior, not visual snapshots.
- Browser/e2e coverage is still a planned separate lane and does not live under this tree yet.
