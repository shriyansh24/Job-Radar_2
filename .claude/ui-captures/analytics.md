# Analytics

## Route
- Path: `/analytics`
- File: `src/pages/Analytics.tsx`

## Figma Status: IN_FIGMA

## Layout Structure
- Container (space-y-6, px-4 py-4 sm:px-6 sm:py-6)
  - Hero section (HERO_PANEL with shadow, grid xl:grid-cols-[1.4fr_0.8fr])
    - Left: "Intelligence" + "Last 30 days" chips, "Analytics" h1, description, "Last 30 Days" + "Export PDF" button chips
    - Right (bg-tertiary): Interviews MetricTile + Offers MetricTile
  - Metric row (grid md:grid-cols-2 xl:grid-cols-4): Jobs, Applications, Response rate, Avg days
  - Two-column section (grid xl:grid-cols-[1.45fr_0.8fr])
    - Left (space-y-4):
      - Chart slab (HERO_PANEL): header + lazy-loaded Charts component (4 charts in 2x2 grid)
      - Skills pulse (INSET_PANEL): top skills as chip badges
    - Right: Source quality table (HERO_PANEL)
      - Table: Source | Jobs | Quality | Match columns
      - Color-coded quality scores (≥80 success, ≥50 warning, <50 danger)

## Components Used
- `Skeleton` (ui): loading states
- `Charts` (analytics) — lazy-loaded via React.lazy with Suspense
- `MetricTile` (local): label + value + hint + icon + tone
- Icons: Briefcase, Clock, DownloadSimple, PaperPlaneTilt, TrendUp

## Theme & Styling
- Same HERO_PANEL/INSET_PANEL/CHIP pattern as Dashboard
- Table: min-w-full border-separate, header text-[10px] uppercase mono
- Quality color coding: ≥80% text-accent-success, ≥50% text-accent-warning, <50% text-accent-danger
- Skill chips: border-2 bg-secondary px-3 py-1 text-[10px] uppercase tracking-[0.18em]

## Data/Content Shape
- analyticsApi.overview(): total_jobs, total_applications, response_rate, avg_days_to_response, total_interviews, total_offers
- analyticsApi.daily(30): daily data points for charts
- analyticsApi.sources(): source name, total_jobs, quality_score, avg_match_score
- analyticsApi.skills(10): skill name + count
- analyticsApi.funnel(): funnel stage data

## Responsive Behavior
- Metrics: md:grid-cols-2, xl:grid-cols-4
- Charts: lg:grid-cols-2
- Content: stacked, xl side-by-side

---

## Light Theme

### Colors
- Background: #FFFFFF
- Text Primary: #000000
- Text Secondary: #666666
- Border: #E5E5E5
- Card Background: #F8F8F8
- Tertiary: #F0F0F0
- Accent Primary: #0066FF
- Accent Success: #00AA00
- Accent Warning: #FF9900
- Accent Danger: #FF0000

### Component States
- HERO_PANEL: border-2 border-#000000, bg-#F8F8F8, shadow-[4px_4px_0_0_#000000]
- INSET_PANEL: border-2 border-#E5E5E5, bg-#F0F0F0
- CHIP: border-2 border-#000000, bg-#FFFFFF, text-#000000
- MetricTile: text-#000000, label: text-#666666, icon: text-#0066FF
- Table Header: text-#000000, uppercase, mono, letter-spacing 0.18em
- Quality Scores:
  - ≥80%: text-#00AA00
  - ≥50%: text-#FF9900
  - <50%: text-#FF0000

---

## Dark Theme

### Colors
- Background: #0A0A0A
- Text Primary: #FFFFFF
- Text Secondary: #AAAAAA
- Border: #333333
- Card Background: #1A1A1A
- Tertiary: #252525
- Accent Primary: #3399FF
- Accent Success: #00DD00
- Accent Warning: #FFBB33
- Accent Danger: #FF3333

### Component States
- HERO_PANEL: border-2 border-#FFFFFF, bg-#1A1A1A, shadow-[4px_4px_0_0_#FFFFFF]
- INSET_PANEL: border-2 border-#333333, bg-#252525
- CHIP: border-2 border-#AAAAAA, bg-#1A1A1A, text-#FFFFFF
- MetricTile: text-#FFFFFF, label: text-#AAAAAA, icon: text-#3399FF
- Table Header: text-#FFFFFF, uppercase, mono, letter-spacing 0.18em
- Quality Scores:
  - ≥80%: text-#00DD00
  - ≥50%: text-#FFBB33
  - <50%: text-#FF3333
