# Onboarding

## Route
- Path: `/onboarding`
- File: `src/pages/Onboarding.tsx`

## Figma Status: MISSING_FROM_FIGMA

## Layout Structure
- PageHeader (system): eyebrow "First-run setup", title "Onboarding", step badges as meta
- MetricStrip (system): Completion %, Queries count, Locations count, Keys Ready count
- SplitWorkspace (system):
  - Primary:
    - Hero section (PANEL class, grid layout)
      - Left: Step number chip + step label chip, step title (text-3xl/4xl), description
      - Right: Progress bar (h-4, border-2, accent-primary fill), callout text, StateBlocks
    - Step content Surface (conditional per step 0-3):
      - Step 0 (Welcome): 3 StateBlocks explaining what gets configured
      - Step 1 (Profile): 6-field form (name, location, job type, remote type, salary min/max)
      - Step 2 (Search seeds): 3 TagRow components (job titles, locations, watchlist companies)
      - Step 3 (Integrations): OpenRouter + SerpAPI key inputs with Badge status
    - Navigation Surface: Back/Next/Skip/Finish buttons
  - Secondary:
    - Summary StateBlocks (Profile, Search seeds, Watchlist, Connections)
    - "Current move" Surface with guidance and outcome StateBlocks

## Components Used
- `PageHeader`, `MetricStrip`, `SplitWorkspace`, `SectionHeader`, `StateBlock`, `Surface` (system)
- `Badge`, `Button`, `Input`, `Select` (ui)
- `TagRow` (local component) — input + add button + chip list with remove
- Icons: ArrowLeft, ArrowRight, CheckCircle, CurrencyDollar, Key, MagnifyingGlass, MapPin, Plus, RocketLaunch, Sparkle, UserCircle, X

## Theme & Styling
- PANEL: border-2 bg-bg-secondary shadow-[4px_4px_0_0]
- PANEL_SUBTLE: border-2 bg-bg-tertiary shadow-[4px_4px_0_0]
- CHIP: border-2 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]
- Active step chips: bg-accent-primary text-white
- Inactive step chips: bg-bg-secondary text-text-muted

## Typography
- Step title: text-3xl sm:text-4xl, font-semibold, tracking-[-0.06em]
- Step description: text-sm sm:text-base, leading-6, text-secondary
- Tag row label: text-[10px], font-semibold, uppercase, tracking-[0.18em], text-muted
- Chip text: text-[10px], font-semibold, uppercase, tracking-[0.18em]

## Interactive States
- Step badges: active (bg-accent-primary text-white) vs inactive (bg-bg-secondary text-text-muted)
- Tag remove button: hover:text-accent-danger
- Back button: disabled when step === 0
- Empty tag state: border-2 border-dashed, text-sm italic text-text-muted

## Color Tokens Per Theme
| Token | Light | Dark |
|-------|-------|------|
| --bg-secondary | #f5f5f5 | #0a0a0a |
| --bg-tertiary | #ebebeb | #141414 |
| --text-primary | #171717 | #fafafa |
| --text-secondary | #525252 | #d4d4d4 |
| --text-muted | #a3a3a3 | #737373 |
| --accent-primary | #2563eb | #3b82f6 |
| --accent-success | #16a34a | #22c55e |
| --accent-warning | #a16207 | #f59e0b |
| --accent-danger | #dc2626 | #ef4444 |

## Data/Content Shape
- Form state: fullName, location, salaryMin, salaryMax, searchQueries[], searchLocations[], watchlistCompanies[], openrouterKey, serpapiKey, preferredJobTypes[], preferredRemoteTypes[]
- Step labels: ["Welcome", "Profile", "Search", "Integrations"]
- Integration providers: openrouter, serpapi

## Responsive Behavior
- Hero section: stacks vertically on mobile, lg:grid-cols side-by-side
- Form fields: md:grid-cols-2 on Profile step
- SplitWorkspace: stacks on mobile, side-by-side on desktop
- Tag inputs: sm:flex-row on larger screens
