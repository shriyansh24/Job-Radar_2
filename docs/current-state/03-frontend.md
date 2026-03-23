# Frontend State - JobRadar V2

## Stack
- React 19
- Vite 6
- TypeScript
- Tailwind CSS v4
- Zustand
- TanStack Query
- Phosphor icons
- Geist Sans and Geist Mono

## UI/State Facts
- Theme state is persisted through `useUIStore`.
- Light mode and high-contrast dark mode are first-class themes.
- The root theme toggle applies a `.dark` class to the HTML element.
- Design tokens live in `frontend/src/index.css`.
- `@phosphor-icons/react` is the active icon set.

## Current Functional State
- Admin page no longer exposes a misleading "Rebuild Embeddings" action.
- Vault PATCH flows are present for editable document metadata.
- SSE uses credentialed transport instead of a token query parameter.
- Recent TypeScript nullability regressions are fixed.
- Current frontend lint, tests, coverage gate, and build all pass.

## Validation
- `cd frontend && npm audit --audit-level high`
- `cd frontend && npm run lint`
- `cd frontend && npm run test -- --run`
- `cd frontend && npm install --no-save @vitest/coverage-v8`
- `cd frontend && npm run test -- --run --coverage --coverage.thresholds.statements=40`
- `cd frontend && npm run build`
- Latest local result: `23` test files, `35` tests, coverage `43.19%` statements

## Non-Blocking Residual
- Vitest still prints `--localstorage-file was provided without a valid path` warnings.
- Those warnings are noisy but non-fatal and do not currently fail tests.
- Coverage intentionally excludes thin API wrappers, scraper/pipeline internals, and zero-value bootstrap files so the `40%` gate tracks the tested UI/runtime surface.

## Current Assessment
- No actionable frontend or dependency bugs remain in the current verified tree.
