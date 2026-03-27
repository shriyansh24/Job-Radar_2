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
- Buttons are intentionally shadowless; structural elevation belongs to panels and surfaces.

## Current Functional State
- The reference-first command-center shell is route-complete across the frontend.
- Shared shell primitives now provide the fixed header, desktop rail, mobile drawer, and mobile bottom nav.
- The latest frontend sweep simplified the shell chrome and removed fake promo/system blocks from the header and sidebar.
- `Login` is now a lean auth surface instead of a marketing-style two-column screen.
- `Settings` is a cleaner operator page with smaller extracted sections, fewer dead imports, and the live settings/data flows intact.
- `Dashboard`, `Jobs`, `Pipeline`, and `Copilot` have been stripped of the most obvious generated copy and fake system commentary.
- `SearchExpansion` now uses the live backend expansion endpoint instead of a fake template inventory.
- `Resume Studio` consumes the backend `ResumeTailorResponse` contract directly.
- `Compensation` uses the backend salary percentile and offer-evaluation contract directly.
- `Settings` persists workspace settings, saved searches, integrations, password changes, account deletion, and data clear actions against real backend endpoints.
- `DocumentVault` edit flows are wired through the live PATCH endpoints.
- `Admin` and source-health surfaces now read the current backend status and diagnostics shape instead of stale frontend assumptions.
- The largest routed surfaces have been partially decomposed into dedicated component groups under `frontend/src/components/`, including `admin`, `copilot`, `dashboard`, `email`, `interview`, `jobs`, `networking`, `onboarding`, `outcomes`, `pipeline`, `profile`, `resume`, `salary`, `settings`, and `vault`.

## Validation
- `cd frontend && npm run lint`
- `cd frontend && npm run test -- --run`
- `cd frontend && npm run build`
- Authenticated browser QA was rerun after the decomposition/copy-cleanup pass, covering the routed app with representative captures in `.claude/ui-captures/`.
- Frontend test suites now live under `frontend/src/tests/` with `app/`, `api/`, `components/`, `hooks/`, `pages/`, and `support/` lanes.

## Non-Blocking Residual
- Route-by-route visual polish remains iterative work on some larger surfaces, but no blocking frontend issue is currently known from the latest validated pass.

## Current Assessment
- No blocking frontend bugs are currently known from the verified local pass.
- The shared system layer is the frontend source of truth for layout, typography, spacing, shell posture, and tokenized surfaces.
