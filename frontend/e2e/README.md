# Frontend Browser Test Taxonomy

## Purpose
Document the committed Playwright layout so browser coverage stays low-noise and route ownership stays obvious.

## Source-Of-Truth Status
- Status: `LIVE_LAYOUT`
- Scope: browser/e2e coverage under `frontend/e2e/`
- Last validation basis: committed Playwright scaffolding plus local config review on `2026-03-27`

## Layout
```text
frontend/e2e/
  flows/         critical authenticated workflows across multiple routes
  smoke/         boot/login/shell health checks
  support/       shared auth and theme helpers
  theme-matrix/  theme family and mode persistence coverage
```

## Notes
- `smoke/` should fail fast on auth/bootstrap or shell regressions.
- `flows/` should protect real route transitions and user-visible outcomes, not pixel snapshots.
- `theme-matrix/` is the canonical home for 8-mode coverage as it expands.
