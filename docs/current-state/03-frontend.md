# Frontend State - JobRadar V2

## Stack
- React 19
- Vite 6
- TypeScript
- Tailwind CSS v4
- Zustand
- TanStack Query
- Phosphor icons
- Inter and JetBrains Mono

## UI/State Facts
- Theme state is persisted through `useUIStore`.
- Light mode and jet-black dark mode are first-class themes.
- The root theme toggle applies a `.dark` class to the HTML element.
- Design tokens live in `frontend/src/index.css`.
- `@phosphor-icons/react` is the active icon set.
- `frontend/system.md` is the design-system source of truth.

## Current Functional State
- The reference-first command-center shell is route-complete across the frontend.
- Shared shell primitives now provide the fixed header, desktop rail, mobile drawer, and mobile bottom nav.
- `SearchExpansion` now uses the live backend expansion endpoint instead of a fake template inventory.
- `Resume Studio` consumes the backend `ResumeTailorResponse` contract directly.
- `Compensation` uses the backend salary percentile and offer-evaluation contract directly.
- `Settings` persists workspace settings, saved searches, integrations, password changes, account deletion, and data clear actions against real backend endpoints.
- `DocumentVault` edit flows are wired through the live PATCH endpoints.
- `Admin` and source-health surfaces now read the current backend status and diagnostics shape instead of stale frontend assumptions.

## Validation
- `cd frontend && npm run lint`
- `cd frontend && npm run test -- --run`
- `cd frontend && npm run build`
- Browser sweeps passed across all 21 authenticated routes on:
  - desktop
  - tablet light mode (`820x1180`)
  - phone dark mode (`390x844`)
- Representative screenshots for the current pass live in `output/playwright/`
- Latest local result: `24` test files, `39` tests

## Non-Blocking Residual
- Vitest still prints `--localstorage-file was provided without a valid path` warnings.
- Vite still prints a chunk-size warning during build.
- Login/auth bootstrap still produces transient `401` / `422` network noise before auth cookies exist.
- Browser-level QA still surfaces password `autocomplete` hints on Settings inputs.
- Recharts can still log width warnings when charts mount in hidden or zero-sized containers during automated sweeps.

## Current Assessment
- No blocking frontend bugs are currently known from the verified local pass.
- The shared system layer is the frontend source of truth for layout, typography, spacing, shell posture, and tokenized surfaces.
