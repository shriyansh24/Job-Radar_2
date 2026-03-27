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
- `flows/route-family-outcomes.spec.ts` is the current route-family baseline for dashboard/jobs/pipeline/settings/targets outcomes and persisted theme changes.
- `flows/prepare-intelligence-outcomes.spec.ts` protects the prepare and intelligence route family on a fresh account.
- `flows/operations-admin-data.spec.ts` protects admin and operations data surfaces that should stay safe to load without destructive actions.
- `flows/profile-settings-auth.spec.ts` protects the profile/settings/auth roundtrip without relying on external providers.
- `theme-matrix/` is the canonical home for 8-mode coverage as it expands.
- `theme-matrix/route-theme-matrix.spec.ts` is the desktop representative-route check for all 8 theme combinations across home, discover, execute, prepare, intelligence, and operations.
- `flows/shell-responsive.spec.ts` is the shell behavior check for desktop, tablet, and phone chrome without screenshot assertions.
