# Login

## Route
- Path: `/login`
- File: `src/pages/Login.tsx`

## Figma Status: IN_FIGMA

## Layout Structure
- Full viewport container (min-h-[100dvh], no AppShell)
  - Background gradient overlay (pointer-events-none)
    - Light: radial gradients with blue (top-left) and amber (bottom-right) at 10% opacity
    - Dark: no gradient (bg-none)
  - Theme toggle button (absolute right-6 top-6, z-10)
  - Centered card (max-w-md, vertically centered with flex)
    - motion.section (fade-in + scale animation)
      - Main panel (PANEL class: border-2 bg-secondary)
        - Header section (border-b-2 px-5 py-4)
          - Eyebrow: "Authentication Gateway V2.0.4" (10px, bold, uppercase, tracking-[0.25em])
          - Title: "Sign in" (text-2xl, font-black, uppercase, tracking-tighter)
          - Subtitle: "Welcome back" (text-sm, font-bold, uppercase, tracking-[0.18em])
          - Description text
        - Form section (px-5 py-5, space-y-4)
          - Error banner (border-2 accent-danger, bg-danger-subtle)
          - Email Input (FIELD class overrides)
          - Password Input (FIELD class overrides)
          - "Keep session active" checkbox (border-2, custom styled)
          - "Sign in" primary button (full width, PRIMARY_BUTTON class)
        - Footer section (border-t-2 px-5 py-5)
          - Divider with "Security protocol" label
          - OAuth buttons grid (sm:grid-cols-2): GitHub, Google
          - Security note: "AES-256 encrypted session handling..." with ShieldCheck icon

## Components Used
- `Button` (ui) — primary and secondary variants
- `Input` (ui) — email and password fields
- Icons: ArrowRight, GithubLogo, GoogleLogo, ShieldCheck, SpinnerGap, Sun, Moon
- `motion.section` from framer-motion for entrance animation

## Theme & Styling
- Page background: bg-background (light: #fafafa, dark: #000000 via dark:bg-black)
- Panel: border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-secondary)]
- Field overrides: !rounded-none !border-2 !bg-secondary !text-primary, focus:!border-accent-primary
- Primary button: !bg-accent-primary !text-white, dark:!bg-blue-700 dark:hover:!bg-blue-800
- Secondary button: !bg-secondary hover:bg-black/5 dark:hover:bg-white/5

## Typography
- Eyebrow: 10px, bold, uppercase, tracking-[0.25em], text-muted
- Title: text-2xl, font-black, uppercase, tracking-tighter
- Subtitle: text-sm, font-bold, uppercase, tracking-[0.18em], text-primary
- Body: text-sm, leading-6, text-secondary
- Checkbox label: font-medium, uppercase, tracking-[0.08em]

## Interactive States
- Theme toggle: 40x40, border-2, hover:bg-black/5 dark:hover:bg-white/5, active:scale-95
- Primary button: loading state shows SpinnerGap icon
- Checkbox: custom accent-[var(--color-accent-primary)]
- OAuth buttons: SECONDARY_BUTTON hover effects

## Color Tokens Per Theme
| Token | Light | Dark |
|-------|-------|------|
| --bg-primary (page bg) | #fafafa | #000000 |
| --bg-secondary (panel bg) | #f5f5f5 | #0a0a0a |
| --text-primary (borders, text) | #171717 | #fafafa |
| --text-muted (eyebrow) | #a3a3a3 | #737373 |
| --text-secondary (description) | #525252 | #d4d4d4 |
| --accent-primary (CTA) | #2563eb | #3b82f6 |
| --accent-danger (error) | #dc2626 | #ef4444 |
| --accent-danger-subtle | rgba(220,38,38,0.16) | rgba(239,68,68,0.2) |

## Data/Content Shape
- Form fields: email (text), password (password), keepSession (checkbox)
- Error state: string message displayed in banner

## Responsive Behavior
- Single column, max-w-md centered
- OAuth buttons: single column on xs, sm:grid-cols-2
- Padding adjusts: px-5 sm:px-6
- Full viewport height on all sizes

## Animation
- Card entrance: opacity 0→1, y 20→0, scale 0.985→1
- Duration: 0.45s, ease: [0.16, 1, 0.3, 1], delay: 0.03s
