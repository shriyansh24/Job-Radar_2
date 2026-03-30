# Pipeline

## Route
- Path: `/pipeline`
- File: `src/pages/Pipeline.tsx`

## Figma Status: IN_FIGMA

## Layout Structure
- Outer container (space-y-6, px-4 py-4 sm:px-6 sm:py-6)
  - Hero section (HERO_PANEL, grid xl:grid-cols-[1.4fr_0.8fr])
    - Left: chips (Execute, tracked count, late-stage count) + "Pipeline" h1 + description + 3 buttons
    - Right: 2 SummaryTile cards (Board health, Follow-up load)
  - Summary tiles row (grid md:grid-cols-3): Board health, Follow-up load, Late-stage momentum
  - Two-column section (grid xl:grid-cols-[1.5fr_0.8fr])
    - Left: Board (HERO_PANEL)
      - Header: "Stage columns" title + "Touch friendly" chip
      - Content: horizontally scrollable stage columns (xl:flex xl:overflow-x-auto)
        - 6 StageColumn components (one per pipeline stage)
        - Each column: colored top bar (h-2) + stage label + count chip + StageCard list
        - Each StageCard: status label + title + company + "Advance" button
    - Right (xl:sticky xl:top-6): Detail sheet (HERO_PANEL)
      - Selected application: status, title, company, source, salary, notes
      - Advance + Reset selection buttons
      - Empty: "Select an application" prompt

## Components Used
- `Button` (ui): primary/secondary with BUTTON_BASE
- `StageColumn` (local): pipeline column with colored header bar
- `StageCard` (local): application card with advance action
- `SummaryTile` (local): metric with icon and hint text
- Icons: ArrowRight, Buildings, CheckCircle, Clock, Funnel, Kanban, Play, Sparkle

## Theme & Styling
- HERO_PANEL: border-2 bg-bg-secondary shadow-[4px_4px_0_0]
- INSET_PANEL: border-2 bg-bg-tertiary shadow-[4px_4px_0_0]
- Stage colors: bg-text-muted (saved), bg-accent-primary (applied), bg-accent-primary/70 (screening), bg-accent-warning (interviewing), bg-accent-success (offer/accepted)
- StageCard hover: translate(-1px,-1px), selected bg-accent-primary/8
- Empty column: border-2 border-dashed bg-bg-tertiary

## Typography
- Page title: text-4xl sm:text-5xl lg:text-6xl, font-semibold, tracking-[-0.06em]
- Stage label: text-sm, font-semibold, uppercase, tracking-[-0.04em]
- Card title: text-lg, font-semibold, tracking-[-0.05em], truncate
- Status chip: text-[10px] font-semibold uppercase tracking-[0.18em]
- Detail title: text-2xl, font-semibold, tracking-[-0.05em]

## Data/Content Shape
- pipelineApi.pipeline(): object with keys: saved, applied, screening, interviewing, offer, accepted
- Each key maps to Application[]: id, position_title, company_name, status, source, salary_offered, notes, updated_at
- Transition: pipelineApi.transition(id, {new_status, note})
- NEXT_STAGE map: saved→applied→screening→interviewing→offer→accepted

## Responsive Behavior
- Hero: stacked on mobile, xl side-by-side
- Summary row: stacked, md:grid-cols-3
- Board columns: stacked md:grid-cols-2, xl:flex horizontal scroll
- Each column: xl:min-w-[18rem] xl:flex-[0_0_18rem]
- Detail pane: xl:sticky xl:top-6
