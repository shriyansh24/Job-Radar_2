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
- Theme family plus mode is persisted through `useUIStore`.
- Light mode and near-black default dark mode are first-class themes; alternate theme families may push darker than the default token set.
- The root theme toggle applies a `.dark` class to the HTML element.
- Design tokens live in `frontend/src/index.css`.
- `@phosphor-icons/react` is the active icon set.
- `frontend/system.md` is the design-system source of truth.
- Buttons are intentionally shadowless; structural elevation belongs to panels and surfaces.

## Current Functional State
- The reference-first command-center shell is route-complete across the frontend.
- Shared shell primitives now provide the fixed header, desktop rail, mobile drawer, and mobile bottom nav.
- The latest frontend sweep simplified the shell chrome and removed fake promo/system blocks from the header and sidebar.
- `Login` is now a lean auth surface instead of a marketing-style two-column screen.
- `Settings` is a cleaner operator page with smaller extracted sections, fewer dead imports, and the live settings/data flows intact.
- `Dashboard`, `Jobs`, `Pipeline`, and `Copilot` have been stripped of the most obvious generated copy and fake system commentary.
- `AutoApply` now exposes real operator controls for refresh, pause, and run-now instead of a passive status-only surface, and the latest-run/history panels surface review-note diagnostics for missed fields and manual-confirmation prompts.
- `Pipeline` now renders `rejected` and `withdrawn` stages and supports bounded drag/drop transitions that respect the workflow transition map.
- `SearchExpansion` now uses the live backend expansion endpoint instead of a fake template inventory.
- `Resume Studio` consumes the backend `ResumeTailorResponse` contract directly and now exposes live template preview plus PDF export through the resume API.
- `Compensation` uses the backend salary percentile and offer-evaluation contract directly.
- `Analytics` now consumes the live analytics patterns endpoint alongside the overview, funnel, source, and skill datasets.
- `Settings` persists workspace settings, saved searches, integrations, password changes, account deletion, and data clear actions against real backend endpoints, including saved-search alert status and manual check execution. The Integrations panel now includes a Google Gmail card with connect/reconnect, manual sync, disconnect, account-email, scopes, last-sync, and last-error state alongside the existing API-key-backed providers.
- `DocumentVault` edit flows are wired through the live PATCH endpoints.
- `Admin` and source-health surfaces now read the current backend status and diagnostics shape instead of stale frontend assumptions.
- `Targets` now exposes manual career-page create/edit/delete flows alongside bulk import, batch controls, and per-target trigger/release actions, and the manual modal now applies the same safe `http`/`https` URL normalization baseline used by target import.
- The largest routed surfaces have been partially decomposed into dedicated component groups under `frontend/src/components/`, including `admin`, `copilot`, `dashboard`, `email`, `interview`, `jobs`, `networking`, `onboarding`, `outcomes`, `pipeline`, `profile`, `resume`, `salary`, `settings`, and `vault`.

## Validation
- `cd frontend && npm run lint`
- `cd frontend && npm run test -- --run`
- `cd frontend && npm run build`
- Authenticated browser QA was rerun after the decomposition/copy-cleanup pass, covering the routed app with representative captures in `.claude/ui-captures/`.
- The current validated route-family browser pass also covers Auto Apply operator controls, the updated pipeline board flow, live analytics patterns, and the resume preview/export flow.
- Settings coverage now also includes the Google Gmail integration card and manual sync path on top of the existing saved-search and API-key provider coverage.
- Frontend test suites now live under `frontend/src/tests/` with `app/`, `api/`, `components/`, `hooks/`, `pages/`, and `support/` lanes.
- Additional targeted local result on `2026-03-30`: the `AutoApply` page test now covers persisted review-note diagnostics, idle-vs-triggered run handling, and null-safe run rendering, and `npm run build` remained green after the updated operator contract landed.

## Non-Blocking Residual
- Route-by-route visual polish remains iterative work on some larger surfaces, but no blocking frontend issue is currently known from the latest validated pass.

## Current Assessment
- No blocking frontend bugs are currently known from the verified local pass.
- The shared system layer is the frontend source of truth for layout, typography, spacing, shell posture, and tokenized surfaces.
- Gmail-derived communications still land in the existing email intelligence surfaces; the frontend does not expose or promise a general inbox client.
