# Dashboard (Command Center)

## Route
- Path: `/`
- File: `src/pages/Dashboard.tsx`

## Figma Status: IN_FIGMA

## Layout Structure
- Outer container (space-y-6, px-4 py-4 sm:px-6 sm:py-6)
  - Hero section (motion.section, HERO_PANEL, grid xl:grid-cols-[1.45fr_0.8fr])
    - Left: chips (Home, jobs scraped today) + "Command Center" h1 (text-4xl/5xl/6xl) + 3 action buttons
    - Right (bg-tertiary border-l-2 on xl): 2 HeroMetric cards (success rate, avg response time)
  - Metric tiles row (grid sm:grid-cols-2 lg:grid-cols-4): Total jobs, Applications, Interviews, Offers
  - Two-column section (grid lg:grid-cols-[1.2fr_0.8fr])
    - Left column (space-y-4):
      - Pipeline distribution "Pressure map" (INSET_PANEL)
        - Stacked progress bar (h-12, animated with framer-motion spring)
        - 3 volume tiles (leads/active/final)
      - "Transmission feed" / Recent movement (HERO_PANEL)
        - Header with "Live" chip
        - FeedRow list (divide-y-2) showing recent jobs
        - Each FeedRow: 48x48 icon box + title + meta + optional match badge
    - Right column (space-y-4):
      - "Priority queue" section (HERO_PANEL)
        - Late-stage applications FeedRow
        - Newest posting FeedRow
        - Dashed empty placeholder

## Components Used
- `Button` (ui): primary and secondary variants with BUTTON_BASE overrides
- `HeroMetric` (local): label, value, icon, tone tinted backgrounds
- `FeedRow` (local): icon box + title + meta + badge
- `MetricTile` (local): large number display with icon
- Icons: ArrowRight, Briefcase, Buildings, Clock, PaperPlaneTilt, Plus, Sparkle, TrendUp, UsersThree
- `motion.section`, `motion.div` from framer-motion for animations
- `cn` utility, `formatDistanceToNow` from date-fns

## Theme & Styling
- HERO_PANEL: border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]
- INSET_PANEL: border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)]
- CHIP: border-2 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]
- BUTTON_BASE: !rounded-none !border-2 !uppercase !tracking-[0.18em]
- All borders: 2px solid var(--color-text-primary)
- Icon containers: 40x40 or 44x44 boxes with border-2 bg-tertiary
- Tone backgrounds: bg-accent-*/10 or bg-accent-*/8 for subtle tints

## Typography
- Page title: text-4xl sm:text-5xl lg:text-6xl, font-semibold, tracking-[-0.06em]
- Section title: text-xl sm:text-2xl, font-semibold, uppercase, tracking-[-0.04em]
- Metric value: text-3xl or text-4xl, font-semibold, tracking-[-0.05em] or [-0.06em]
- Labels: text-[10px], font-semibold, uppercase, tracking-[0.18em], text-text-muted
- Feed title: text-sm sm:text-base, font-semibold, uppercase, tracking-[-0.03em]
- Body: text-sm, leading-6, text-text-secondary

## Interactive States
- Hero section entrance: opacity 0→1, y 12→0, duration 0.35s, ease [0.16, 1, 0.3, 1]
- Buttons: BUTTON_BASE with hard-press behavior
- FeedRow hover: bg-black/5 dark:bg-white/5 transition-colors
- Progress bars: spring animation (stiffness 180, damping 24)

## Color Tokens Per Theme
| Token | Light | Dark |
|-------|-------|------|
| --bg-primary | #fafafa | #000000 |
| --bg-secondary | #f5f5f5 | #0a0a0a |
| --bg-tertiary | #ebebeb | #141414 |
| --text-primary | #171717 | #fafafa |
| --text-secondary | #525252 | #d4d4d4 |
| --text-muted | #a3a3a3 | #737373 |
| --accent-primary | #2563eb | #3b82f6 |
| --accent-success | #16a34a | #22c55e |
| --accent-warning | #a16207 | #f59e0b |

## Data/Content Shape
- analyticsApi.overview(): total_jobs, total_applications, total_interviews, total_offers, response_rate, avg_days_to_response, jobs_scraped_today
- jobsApi.list(5 most recent): items[] with title, company_name, location, remote_type, posted_at, match_score
- pipelineApi.pipeline(): object keyed by stage (saved/applied/screening/interviewing/offer/accepted) → application arrays
- Pipeline stages: saved, applied, screening, interviewing, offer, accepted

## Responsive Behavior
- Hero: single column on mobile, xl:grid-cols-[1.45fr_0.8fr] on desktop
- Metrics: sm:grid-cols-2, lg:grid-cols-4
- Main content: single column on mobile, lg:grid-cols-[1.2fr_0.8fr]
- Feed dividers: divide-y-2 border color matches text-primary
- Padding: px-4 py-4 sm:px-6 sm:py-6
