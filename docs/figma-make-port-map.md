# Figma Make Port Map

## Source

- Figma Make file: `https://www.figma.com/make/BTSWvIKqvJxLLEHdE8DOwC/Improve-Job-Radar-UI-UX`
- Secondary code source: `origin/feature/ui/figma/neo-brutalist-themes`
- Current branch: `codex/ui-changes`

## Decision

Use the Figma Make project as the visual source of truth for:

- typography
- theme families
- shell composition
- spacing rhythm
- page framing
- primitive styling

Keep the current repo as the source of truth for:

- routing
- auth guards
- API contracts
- Zustand state
- React Query prefetching
- backend-connected behavior
- route-specific product logic

Use `origin/feature/ui/figma/neo-brutalist-themes` only as a secondary code donor for:

- shell markup ideas
- page-level JSX structure
- selected primitive styling details

Do not use that branch as a merge target or replacement branch.

Reasons:

- it diverges from `codex/ui-changes` instead of building on top of it
- it deletes the current shared system layer under `frontend/src/components/system`
- it deletes `frontend/src/lib/navigation.tsx`
- it deletes `frontend/system.md`
- it removes current routed surfaces such as `Copilot`, `Email`, `Networking`, and `Outcomes`
- it does not include the richer 4-family Figma Make theme runtime

Working hierarchy:

1. Figma Make sets the visual system and multi-theme model.
2. `origin/feature/ui/figma/neo-brutalist-themes` can donate selected code patterns.
3. `codex/ui-changes` remains authoritative for behavior, route coverage, auth, API wiring, and current-only widgets.

## Theme Strategy

The Make file contains 4 theme families, each with light and dark mode:

- `default`
- `terminal`
- `blueprint`
- `phosphor`

That means 8 visual combinations in total.

### Recommendation

Keep all 4 theme families, but roll them out in phases.

### Phase 1

Ship:

- `default/light`
- `default/dark`

Reason:

- this gets the main Make visual language into production quickly
- it avoids multiplying QA across all routes before the port is stable

### Phase 2

Extend runtime theme state to support:

- `themeFamily`
- `mode`

Then enable:

- `terminal/light`
- `terminal/dark`
- `blueprint/light`
- `blueprint/dark`
- `phosphor/light`
- `phosphor/dark`

### Runtime Change Required

Current runtime state in [useUIStore.ts](D:/jobradar-v2/frontend/src/store/useUIStore.ts) only supports:

- `theme: "light" | "dark"`

It must become something like:

- `mode: "light" | "dark"`
- `themeFamily: "default" | "terminal" | "blueprint" | "phosphor"`

The Make file currently does this in:

- `src/app/theme-provider.tsx`
- `src/styles/theme.css`

## Files To Port

### Theme And Tokens

Port from Make:

- `src/styles/theme.css`
- `src/styles/fonts.css`
- `src/styles/index.css`

Adapt into current repo:

- [index.css](D:/jobradar-v2/frontend/src/index.css)
- [system.md](D:/jobradar-v2/frontend/system.md)
- [useUIStore.ts](D:/jobradar-v2/frontend/src/store/useUIStore.ts)
- [Settings.tsx](D:/jobradar-v2/frontend/src/pages/Settings.tsx)

### Shell

Port from Make:

- `src/app/AppShell.tsx`
- `src/app/routes.tsx`

Adapt into current repo:

- [AppShell.tsx](D:/jobradar-v2/frontend/src/components/layout/AppShell.tsx)
- [Sidebar.tsx](D:/jobradar-v2/frontend/src/components/layout/Sidebar.tsx)
- [navigation.tsx](D:/jobradar-v2/frontend/src/lib/navigation.tsx)

Important:

- keep current route URLs
- keep current route group metadata and prefetch logic
- keep current `AuthGuard`
- keep current `ToastContainer`
- keep current `NotificationBell` unless explicitly replaced

### Shared System Components

Port from Make:

- `src/app/components/system/PageHeader.tsx`
- `src/app/components/system/SectionHeader.tsx`
- `src/app/components/system/Surface.tsx`
- `src/app/components/system/MetricStrip.tsx`
- `src/app/components/system/SplitWorkspace.tsx`
- `src/app/components/system/StateBlock.tsx`

Adapt into current repo:

- [PageHeader.tsx](D:/jobradar-v2/frontend/src/components/system/PageHeader.tsx)
- [SectionHeader.tsx](D:/jobradar-v2/frontend/src/components/system/SectionHeader.tsx)
- [Surface.tsx](D:/jobradar-v2/frontend/src/components/system/Surface.tsx)
- [MetricStrip.tsx](D:/jobradar-v2/frontend/src/components/system/MetricStrip.tsx)
- [SplitWorkspace.tsx](D:/jobradar-v2/frontend/src/components/system/SplitWorkspace.tsx)
- [StateBlock.tsx](D:/jobradar-v2/frontend/src/components/system/StateBlock.tsx)

### Shared UI Components

Port or selectively adapt from Make:

- `src/app/components/ui/button.tsx`
- `src/app/components/ui/card.tsx`
- `src/app/components/ui/badge.tsx`
- `src/app/components/ui/input.tsx`
- `src/app/components/ui/select.tsx`
- `src/app/components/ui/tabs.tsx`
- `src/app/components/ui/textarea.tsx`
- `src/app/components/ui/sidebar.tsx`
- `src/app/components/ui/sheet.tsx`
- `src/app/components/ui/dialog.tsx`
- `src/app/components/ui/table.tsx`
- `src/app/components/ui/skeleton.tsx`

Map into:

- [Button.tsx](D:/jobradar-v2/frontend/src/components/ui/Button.tsx)
- [buttonVariants.ts](D:/jobradar-v2/frontend/src/components/ui/buttonVariants.ts)
- [Card.tsx](D:/jobradar-v2/frontend/src/components/ui/Card.tsx)
- [Badge.tsx](D:/jobradar-v2/frontend/src/components/ui/Badge.tsx)
- [Input.tsx](D:/jobradar-v2/frontend/src/components/ui/Input.tsx)
- [Select.tsx](D:/jobradar-v2/frontend/src/components/ui/Select.tsx)
- [Tabs.tsx](D:/jobradar-v2/frontend/src/components/ui/Tabs.tsx)
- [Textarea.tsx](D:/jobradar-v2/frontend/src/components/ui/Textarea.tsx)
- [Modal.tsx](D:/jobradar-v2/frontend/src/components/ui/Modal.tsx)
- [Table.tsx](D:/jobradar-v2/frontend/src/components/ui/Table.tsx)
- [Skeleton.tsx](D:/jobradar-v2/frontend/src/components/ui/Skeleton.tsx)

## Route Mapping

### Direct Page Ports

These Make pages map directly to current repo pages:

- `Dashboard.tsx` -> [Dashboard.tsx](D:/jobradar-v2/frontend/src/pages/Dashboard.tsx)
- `Jobs.tsx` -> [JobBoard.tsx](D:/jobradar-v2/frontend/src/pages/JobBoard.tsx)
- `Pipeline.tsx` -> [Pipeline.tsx](D:/jobradar-v2/frontend/src/pages/Pipeline.tsx)
- `Settings.tsx` -> [Settings.tsx](D:/jobradar-v2/frontend/src/pages/Settings.tsx)
- `Login.tsx` -> [Login.tsx](D:/jobradar-v2/frontend/src/pages/Login.tsx)
- `Analytics.tsx` -> [Analytics.tsx](D:/jobradar-v2/frontend/src/pages/Analytics.tsx)
- `Copilot.tsx` -> [Copilot.tsx](D:/jobradar-v2/frontend/src/pages/Copilot.tsx)
- `Admin.tsx` -> [Admin.tsx](D:/jobradar-v2/frontend/src/pages/Admin.tsx)
- `AutoApply.tsx` -> [AutoApply.tsx](D:/jobradar-v2/frontend/src/pages/AutoApply.tsx)
- `CanonicalJobs.tsx` -> [CanonicalJobs.tsx](D:/jobradar-v2/frontend/src/pages/CanonicalJobs.tsx)
- `Companies.tsx` -> [Companies.tsx](D:/jobradar-v2/frontend/src/pages/Companies.tsx)
- `DocumentVault.tsx` -> [DocumentVault.tsx](D:/jobradar-v2/frontend/src/pages/DocumentVault.tsx)
- `Email.tsx` -> [Email.tsx](D:/jobradar-v2/frontend/src/pages/Email.tsx)
- `Onboarding.tsx` -> [Onboarding.tsx](D:/jobradar-v2/frontend/src/pages/Onboarding.tsx)
- `Networking.tsx` -> [Networking.tsx](D:/jobradar-v2/frontend/src/pages/Networking.tsx)
- `ResumeBuilder.tsx` -> [ResumeBuilder.tsx](D:/jobradar-v2/frontend/src/pages/ResumeBuilder.tsx)
- `Profile.tsx` -> [Profile.tsx](D:/jobradar-v2/frontend/src/pages/Profile.tsx)
- `InterviewPrep.tsx` -> [InterviewPrep.tsx](D:/jobradar-v2/frontend/src/pages/InterviewPrep.tsx)
- `SalaryInsights.tsx` -> [SalaryInsights.tsx](D:/jobradar-v2/frontend/src/pages/SalaryInsights.tsx)
- `Outcomes.tsx` -> [Outcomes.tsx](D:/jobradar-v2/frontend/src/pages/Outcomes.tsx)
- `Sources.tsx` -> [Sources.tsx](D:/jobradar-v2/frontend/src/pages/Sources.tsx)
- `Targets.tsx` -> [Targets.tsx](D:/jobradar-v2/frontend/src/pages/Targets.tsx)
- `SearchExpansion.tsx` -> [SearchExpansion.tsx](D:/jobradar-v2/frontend/src/pages/SearchExpansion.tsx)

### No Direct Port

Make includes:

- `GenericPage.tsx`

Current repo should not use that as a real production page.

## Components Missing From Make

These components are not represented in the Make project and must be kept or rebuilt manually.

### Runtime-Critical

- [AuthGuard.tsx](D:/jobradar-v2/frontend/src/components/layout/AuthGuard.tsx)
- [ErrorBoundary.tsx](D:/jobradar-v2/frontend/src/components/ErrorBoundary.tsx)
- [PageLoader.tsx](D:/jobradar-v2/frontend/src/components/ui/PageLoader.tsx)
- [Toast.tsx](D:/jobradar-v2/frontend/src/components/ui/Toast.tsx)
- [toastService.ts](D:/jobradar-v2/frontend/src/components/ui/toastService.ts)
- [JobDetail.tsx](D:/jobradar-v2/frontend/src/components/jobs/JobDetail.tsx)
- [AnalyticsCharts.tsx](D:/jobradar-v2/frontend/src/components/analytics/AnalyticsCharts.tsx)
- [SettingsSection.tsx](D:/jobradar-v2/frontend/src/components/system/SettingsSection.tsx)

### Product-Specific Ops Widgets

- [ScraperControlPanel.tsx](D:/jobradar-v2/frontend/src/components/scraper/ScraperControlPanel.tsx)
- [ScraperLog.tsx](D:/jobradar-v2/frontend/src/components/scraper/ScraperLog.tsx)

Important:

The Make shell does not include the current floating scraper log or the scraper run controls. If we port the Make shell, these must be reattached manually.

### Current Repo Components With No Make Equivalent

- [NotificationBell.tsx](D:/jobradar-v2/frontend/src/components/layout/NotificationBell.tsx)
- [WorkspaceShell.tsx](D:/jobradar-v2/frontend/src/components/system/WorkspaceShell.tsx)
- [WorkspaceSidebar.tsx](D:/jobradar-v2/frontend/src/components/system/WorkspaceSidebar.tsx)
- [CommandBar.tsx](D:/jobradar-v2/frontend/src/components/system/CommandBar.tsx)
- [ActivityFeed.tsx](D:/jobradar-v2/frontend/src/components/system/ActivityFeed.tsx)
- [DataList.tsx](D:/jobradar-v2/frontend/src/components/system/DataList.tsx)
- [EntitySheet.tsx](D:/jobradar-v2/frontend/src/components/system/EntitySheet.tsx)

### Older Or Dormant Repo Widgets Not Present In Make

- [JobCard.tsx](D:/jobradar-v2/frontend/src/components/jobs/JobCard.tsx)
- [JobFilters.tsx](D:/jobradar-v2/frontend/src/components/jobs/JobFilters.tsx)
- [ScoreGauge.tsx](D:/jobradar-v2/frontend/src/components/jobs/ScoreGauge.tsx)
- [AddApplicationModal.tsx](D:/jobradar-v2/frontend/src/components/pipeline/AddApplicationModal.tsx)
- [ApplicationCard.tsx](D:/jobradar-v2/frontend/src/components/pipeline/ApplicationCard.tsx)
- [ApplicationModal.tsx](D:/jobradar-v2/frontend/src/components/pipeline/ApplicationModal.tsx)
- [KanbanBoard.tsx](D:/jobradar-v2/frontend/src/components/pipeline/KanbanBoard.tsx)
- [PipelineColumn.tsx](D:/jobradar-v2/frontend/src/components/pipeline/PipelineColumn.tsx)

These are not necessarily blockers if the live route implementation has already moved on.

## Must-Keep Local Behavior

Do not replace these local systems with Make code:

- [App.tsx](D:/jobradar-v2/frontend/src/App.tsx)
- [useAuthStore.ts](D:/jobradar-v2/frontend/src/store/useAuthStore.ts)
- [useUIStore.ts](D:/jobradar-v2/frontend/src/store/useUIStore.ts)
- [navigation.tsx](D:/jobradar-v2/frontend/src/lib/navigation.tsx)
- all files in [api](D:/jobradar-v2/frontend/src/api)

Keep:

- React Query usage
- Suspense boundaries
- lazy route loading
- route protection
- backend-connected forms
- toast behavior
- current route URLs

## Exact Port Order

### Step 1

Port Make visual tokens into:

- [index.css](D:/jobradar-v2/frontend/src/index.css)
- [useUIStore.ts](D:/jobradar-v2/frontend/src/store/useUIStore.ts)
- [Settings.tsx](D:/jobradar-v2/frontend/src/pages/Settings.tsx)

Do not expose all 4 families yet. Wire the runtime for them first.

### Step 2

Port Make shell into:

- [AppShell.tsx](D:/jobradar-v2/frontend/src/components/layout/AppShell.tsx)
- [Sidebar.tsx](D:/jobradar-v2/frontend/src/components/layout/Sidebar.tsx)

Then reattach:

- [NotificationBell.tsx](D:/jobradar-v2/frontend/src/components/layout/NotificationBell.tsx)
- [ScraperLog.tsx](D:/jobradar-v2/frontend/src/components/scraper/ScraperLog.tsx)

### Step 3

Port shared primitives:

- `Surface`
- `PageHeader`
- `SectionHeader`
- `MetricStrip`
- `SplitWorkspace`
- `StateBlock`
- button/input/badge/select/tabs/textarea/table/skeleton

### Step 4

Port primary routes first:

- [Dashboard.tsx](D:/jobradar-v2/frontend/src/pages/Dashboard.tsx)
- [JobBoard.tsx](D:/jobradar-v2/frontend/src/pages/JobBoard.tsx)
- [Pipeline.tsx](D:/jobradar-v2/frontend/src/pages/Pipeline.tsx)
- [Settings.tsx](D:/jobradar-v2/frontend/src/pages/Settings.tsx)
- [Login.tsx](D:/jobradar-v2/frontend/src/pages/Login.tsx)

### Step 5

Port the remaining routes in descending product importance:

- [AutoApply.tsx](D:/jobradar-v2/frontend/src/pages/AutoApply.tsx)
- [Analytics.tsx](D:/jobradar-v2/frontend/src/pages/Analytics.tsx)
- [Copilot.tsx](D:/jobradar-v2/frontend/src/pages/Copilot.tsx)
- [Admin.tsx](D:/jobradar-v2/frontend/src/pages/Admin.tsx)
- [Targets.tsx](D:/jobradar-v2/frontend/src/pages/Targets.tsx)
- all remaining pages

### Step 6

Reapply current-only product widgets where needed:

- [JobDetail.tsx](D:/jobradar-v2/frontend/src/components/jobs/JobDetail.tsx) on jobs detail flow
- [AnalyticsCharts.tsx](D:/jobradar-v2/frontend/src/components/analytics/AnalyticsCharts.tsx) on analytics
- [ScraperControlPanel.tsx](D:/jobradar-v2/frontend/src/components/scraper/ScraperControlPanel.tsx) on operations surface
- [SettingsSection.tsx](D:/jobradar-v2/frontend/src/components/system/SettingsSection.tsx) where settings/profile need denser grouped forms

### Step 7

After `default` theme is stable, enable the other Make families inside:

- [useUIStore.ts](D:/jobradar-v2/frontend/src/store/useUIStore.ts)
- [Settings.tsx](D:/jobradar-v2/frontend/src/pages/Settings.tsx)
- [index.css](D:/jobradar-v2/frontend/src/index.css)

## QA Requirements

Minimum QA before exposing all 4 families:

- desktop light/dark on all routes
- tablet light/dark on all routes
- phone light/dark on all routes
- chart visibility in all active themes
- badges and semantic colors in all active themes
- auth, settings, targets, admin, analytics, and pipeline flows

Additional QA before enabling the 3 non-default families:

- all semantic badges in every family
- chart palettes in every family
- destructive and warning surfaces in every family
- scraper widgets in every family

## Next Execution Target

Implement in this order:

1. theme runtime upgrade
2. shell port
3. shared primitive port
4. dashboard/jobs/pipeline/settings/login
5. current-only widgets reattachment
6. secondary theme family rollout
