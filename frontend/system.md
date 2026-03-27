# JobRadar Visual System

## Visual Thesis
- Build JobRadar as a reference-first command center.
- Preserve the current app's routes, auth, and backend behavior, but use Figma Make as the live authority for theme families, typography, shell posture, and interaction language.
- Light mode stays bright, neutral, and technical. Dark mode stays jet black, high-contrast, and crisp.
- The live type system is `Inter` for interface copy, `Space Grotesk` for display and section headlines, and `JetBrains Mono` for labels, metrics, tabs, and system readouts.
- The current sweep is stripping generated copy from login, settings, dashboard, jobs, pipeline, and copilot while preserving behavior.

## Theme Tokens
The frontend source of truth is `src/index.css`.

```css
:root {
  --bg-primary: #F4F4F0;
  --bg-secondary: #E5E1E4;
  --bg-tertiary: #E1E2EC;
  --text-primary: #09090B;
  --text-secondary: #44474E;
  --text-muted: #44474E;
  --border: #09090B;
  --accent-primary: #2563EB;
  --accent-success: #16a34a;
  --accent-warning: #a16207;
  --accent-danger: #BA1A1A;
}

.dark {
  --bg-primary: #0A0A0A;
  --bg-secondary: #2A2A2C;
  --bg-tertiary: #353437;
  --text-primary: #E5E1E4;
  --text-secondary: #C3C6D7;
  --text-muted: #C3C6D7;
  --border: #8D90A0;
  --accent-primary: #3B82F6;
  --accent-success: #22c55e;
  --accent-warning: #f59e0b;
  --accent-danger: #FFB4AB;
}
```

- Runtime theme state is now `theme family + mode`, not only `light/dark`.
- Supported families at the token level:
  - `default`
  - `terminal`
  - `blueprint`
  - `phosphor`
- Full-route validation currently uses `default` as the baseline family, with representative browser spot checks for `terminal`, `blueprint`, and `phosphor`.
- The non-default families are live in runtime and settings, but deeper route-by-route visual QA remains iterative work.
- Semantic colors are theme-specific, not fixed across light and dark.
- `success`, `warning`, `danger`, and `info` all use separate light/dark token values and subtle surface fills.
- Chart grids, axes, legends, tooltips, and series colors must consume chart tokens instead of hardcoded hex values.

## Typography
- Page title: `30px`, semibold, tracking `-0.02em`, normal case.
- Section title: `20px`, bold, uppercase.
- Display/headline face: `Space Grotesk`.
- Eyebrow label: `11px`, medium, uppercase, tracking `0.18em`.
- Body copy: `14px`, regular, dense but readable.
- Metrics and operational values: `JetBrains Mono`.
- Numeric counters stay loud. Long string values in shared metric slabs fall back to smaller wrapped text so emails and status strings do not break layout.

## Structural Rules
- Default radius is `0px`.
- Primary surfaces use `2px` borders and hard offset shadows.
- Elevation comes from border + offset shadow, not blur.
- Active and pressed states flatten or reduce the hard shadow instead of animating with soft motion.
- Labels, tabs, metadata, and system status read in uppercase mono.

## Shell Grammar
- Fixed header height: `64px`.
- Desktop left rail: `240px` expanded, `80px` collapsed.
- Mobile shell: drawer from the left plus fixed bottom navigation.
- Header pattern:
  - compact wordmark
  - current route label
  - theme toggle
  - operator identity
  - logout
- Main layout families:
  - command dashboard
  - split list/detail workspaces
  - dense operator consoles
  - AI workspaces
  - auth/setup forms

## Component Rules
- Buttons: uppercase mono labels, `2px` border, no drop shadow, and hard-press translation. Primary CTAs use fill and border contrast instead of shadow. Shared button variants must not reintroduce elevation.
- Cards and surfaces: square corners, `2px` structural borders, hard offset shadows, and optional hover lift. Card subcomponents should use structural header/content/footer sections instead of nested ad hoc wrappers.
- Page headers: hero panels, not simple title rows. Use a mono eyebrow, optional meta-chip rail, loud `Space Grotesk` title, and an action cluster on the right.
- Metric strips: one shared slab with internal dividers, not separate card mosaics.
- Inputs/selects/textareas: label-aware wrappers, `2px` borders, neutral inset surfaces, and blue hard-shadow focus states. Error states stay red without adding soft glow.
- Badges: sharp mono labels with restrained semantic fills. Semantic badges are `success`, `warning`, `danger`, and `info`; avoid decorative pill treatments.
- Tabs: bordered segmented strips instead of soft pills.
- Modals: structural overlays with bordered headers, loud titles, and no glass styling.
- Empty/loading/error states: structural slabs and inset panels, not airy placeholder cards.
- State blocks: inset alert panels with mono titles and optional action affordances.

## Responsive Rules
- Phone and tablet layouts keep the same information model as desktop.
- Tablet layouts preserve split-workspace intent where space allows, then stack predictably.
- Mobile routes rely on the drawer and bottom nav instead of hidden alternate flows.
- Do not hide critical state or controls behind mobile-only product logic.

## Implementation Notes
- Shared shell and layout primitives live in `src/components/layout` and `src/components/system`.
- Shared UI primitives live in `src/components/ui`.
- Figma Make is the primary visual authority for theme families and shell/page composition.
- `origin/feature/ui/figma/neo-brutalist-themes` is a secondary code donor only, not a merge target.
- Current app routes, auth, stores, and data contracts remain authoritative in this repo.
- Shared buttons should stay shadowless even when surrounding surfaces retain structural offsets.
