# Job Board

## Route
- Path: `/jobs`
- File: `src/pages/JobBoard.tsx`

## Figma Status: IN_FIGMA (as "Jobs")

## Layout Structure
- Outer container (space-y-6, px-4 py-4 sm:px-6 sm:py-6)
  - Hero section (motion.section, HERO_PANEL with shadow)
    - Left: chips (Discover, results count, active filters) + "Jobs" h1 + description + search mode buttons (Exact/Semantic/Filters)
    - Right (bg-tertiary): StatChip (Mode) + StatChip (Page) + description text
  - Search/filter bar (HERO_PANEL, p-5)
    - Grid: Search Input + 3 Select dropdowns (source, remote, experience)
    - Expandable filters section: Sort select + "Clear filters" button
  - Two-column section (grid xl:grid-cols-[1.25fr_0.75fr])
    - Left: Job list (HERO_PANEL)
      - Header bar: Results label + total count
      - Scrollable list (max-h-[72vh]): JobRow cards
      - Pagination footer: page X/Y + Prev/Next buttons
    - Right (xl:sticky xl:top-6): Job detail pane (HERO_PANEL)
      - JobDetail component when selected
      - "Select a role" empty state when none selected

## Components Used
- `Button` (ui): primary/secondary with BUTTON_BASE
- `Input` (ui): with MagnifyingGlass icon
- `Select` (ui): source, remote, experience, sort options
- `JobDetail` (jobs component): full job detail view
- `JobRow` (local): clickable card with title, company, chips, match score
- `StatChip` (local): label + large value + tone background

## Theme & Styling
- HERO_PANEL: border-2 bg-bg-secondary shadow-[4px_4px_0_0_var(--color-text-primary)]
- CHIP: border-2 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]
- Selected job row: bg-accent-primary/8
- Unselected: bg-bg-secondary
- JobRow hover: translate(-1px, -1px) with transition-transform 150ms

## Typography
- Page title: text-4xl sm:text-5xl lg:text-6xl, font-semibold, tracking-[-0.06em]
- Description: text-sm sm:text-base, leading-6, text-text-secondary
- Job title: text-lg, font-semibold, tracking-[-0.05em], truncate
- Source label: text-[10px], font-semibold, uppercase, tracking-[0.18em], text-text-muted
- Company: text-sm, text-text-secondary, truncate
- Pagination: text-xs, font-semibold, uppercase, tracking-[0.18em]

## Interactive States
- JobRow: hover translate(-1px,-1px), selected bg-accent-primary/8
- Search mode buttons: active bg-accent-primary text-white, inactive bg-bg-secondary
- Pagination: disabled state on first/last page
- Loading: 8 skeleton pulse rectangles (h-24)
- Error: danger border panel with red text

## Data/Content Shape
- jobsApi.list(params): {items: Job[], total, total_pages}
- jobsApi.semanticSearch(query, limit): Job[]
- Job: id (SHA-256), title, company_name, source, location, remote_type, job_type, experience_level, match_score, is_starred
- Filters: source (linkedin/indeed/glassdoor/theirstack/career_page), remote_type, experience_level, sort_by, page
- Search modes: "exact" (filters+pagination) or "semantic" (ranked, no pagination)

## Responsive Behavior
- Hero: single column, xl:grid-cols-[1.35fr_0.8fr]
- Filter bar: single column, lg:grid-cols-[1.35fr_repeat(3,1fr)]
- Job list + detail: stacked, xl:grid-cols-[1.25fr_0.75fr]
- Detail pane: xl:sticky xl:top-6
