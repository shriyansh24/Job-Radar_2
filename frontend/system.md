# JobRadar Visual System

## Visual Thesis
- Build JobRadar as a reference-first neo-brutalist command center.
- Preserve the current app's routes, auth, and backend behavior, but use the reference repo's typography, color system, shell posture, and interaction language as the live visual authority.
- Light mode stays bright, neutral, and technical. Dark mode stays jet black, high-contrast, and crisp.
- The live type system is `Inter` for interface copy and `JetBrains Mono` for labels, metrics, tabs, and system readouts.

## Theme Tokens
The frontend source of truth is `src/index.css`.

```css
:root {
  --bg-primary: #fafafa;
  --bg-secondary: #f5f5f5;
  --bg-tertiary: #ebebeb;
  --text-primary: #171717;
  --text-secondary: #525252;
  --text-muted: #a3a3a3;
  --border: #09090b;
  --accent-primary: #2563eb;
  --accent-success: #16a34a;
  --accent-warning: #a16207;
  --accent-danger: #dc2626;
}

.dark {
  --bg-primary: #000000;
  --bg-secondary: #0a0a0a;
  --bg-tertiary: #141414;
  --text-primary: #fafafa;
  --text-secondary: #d4d4d4;
  --text-muted: #737373;
  --border: #fafafa;
  --accent-primary: #3b82f6;
  --accent-success: #22c55e;
  --accent-warning: #f59e0b;
  --accent-danger: #ef4444;
}
```

- Semantic colors are theme-specific, not fixed across light and dark.
- `success`, `warning`, `danger`, and `info` all use separate light/dark token values and subtle surface fills.
- Chart grids, axes, legends, tooltips, and series colors must consume chart tokens instead of hardcoded hex values.

## Typography
- Page title: `30px`, semibold, tracking `-0.02em`, normal case.
- Section title: `20px`, bold, uppercase.
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
  - loud wordmark
  - centered command search
  - system status block
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
- Buttons: uppercase mono or bold sans, hard shadow, strong border, press feedback.
- Inputs/selects/textareas: `2px` border, neutral inset surface, blue hard-shadow focus state.
- Surfaces: square corners, strong stroke, hard shadow, optional lift on hover.
- Badges: sharp mono labels with restrained semantic fills.
- Tabs: dense bordered strips instead of soft pills.
- Modals: structural panels, no glass treatment.
- Empty/loading/error states: structural slabs, not airy placeholder cards.

## Responsive Rules
- Phone and tablet layouts keep the same information model as desktop.
- Tablet layouts preserve split-workspace intent where space allows, then stack predictably.
- Mobile routes rely on the drawer and bottom nav instead of hidden alternate flows.
- Do not hide critical state or controls behind mobile-only product logic.

## Implementation Notes
- Shared shell and layout primitives live in `src/components/layout` and `src/components/system`.
- Shared UI primitives live in `src/components/ui`.
- Reference visual authority came from `D:/jobradar-v2-ui-ref`; current app routes and data contracts remain authoritative in this repo.
