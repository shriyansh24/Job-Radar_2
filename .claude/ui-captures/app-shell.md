# AppShell (Layout Wrapper)

## Route
- Path: N/A (wraps all protected routes)
- Files: `src/components/layout/AppShell.tsx`, `src/components/layout/Sidebar.tsx`

## Figma Status: MISSING_FROM_FIGMA (critical — wraps everything)

## Layout Structure
- WorkspaceShell (system component)
  - Fixed Header (h-[var(--header-height)] = 64px, border-b-2)
    - Left cluster
      - Mobile nav toggle (xl:hidden) — 40x40 hard-press button
      - Desktop sidebar collapse toggle (hidden xl:inline-flex) — 40x40
      - Brand mark: "JR" in 40x40 box (hidden sm:flex), bg-primary text
      - Route label: current page name (font-black uppercase tracking-[-0.08em])
      - Group label (hidden lg:inline, mono text-[10px] uppercase)
      - Route description (hidden xl:inline, truncated)
    - Center: Command search bar (hidden lg:flex, min-w-[320px] max-w-[540px])
      - MagnifyingGlass icon + "Command search..." mono label
    - Right cluster
      - System status pill (hidden lg:flex): "System status" + "Optimal" in accent-success
      - NotificationBell component
      - Theme toggle (Sun/Moon icon, 40x40 hard-press button)
      - User info pill (hidden sm:flex): avatar initial + "Active operator" label + display name
      - Logout button: inverted (bg-foreground text-background), "Logout" text hidden sm:inline
  - Sidebar (desktop only, hidden xl:flex)
    - Fixed left, top below header, full height minus header
    - Width: var(--sidebar-width) = 15rem expanded, var(--sidebar-width-collapsed) = 5rem collapsed
    - bg-[var(--sidebar-bg)], border-r-2 border-border
    - Header section: terminal icon (40x40 inverted) + "JobRadar V2" heading + "v2.0.4" version
    - Navigation sections (6 groups): Home, Discover, Execute, Prepare, Intelligence, Operations
      - Section titles: "Core Command", "Discovery", "Execution", "AI Tools", "Intelligence", "System Data"
      - Section label: `.label` class (mono, 10px, uppercase, tracking-[0.18em])
      - Nav items: hard-press buttons, border-2, mono text-[11px] font-bold uppercase tracking-[0.18em]
        - Active: bg-[var(--sidebar-item-active-bg)] text-[var(--sidebar-item-active-text)] shadow-sm
        - Inactive: border-transparent, text-text-secondary, hover shows border + bg
      - Icon springs on hover (x: 2px via framer-motion)
    - Footer: "Add New Job" button (bg-accent-success, text-white, full width)
    - System status: "Optimal" in accent-success
  - Mobile nav drawer (AnimatePresence, xl:hidden)
    - Overlay: fixed inset-0 bg-black/65
    - Slide-in aside: w-[min(22rem,100vw)], spring animation
    - Same workspace sections as desktop sidebar
  - Bottom nav (fixed bottom, lg:hidden)
    - 5-column grid, h-20, border-t-2
    - 5 routes: Radar(/), Jobs, Pipeline, Analytics, Networking
    - Active: bg-primary text-primary-foreground
    - Icon: fill weight when active, bold when inactive
    - Label: mono text-[10px] font-bold uppercase tracking-[0.16em]
  - Content area: <Outlet /> with min-h-0
  - ScraperLog (conditional, shown on Operations group pages)

## Components Used
- `WorkspaceShell` (system component) — main shell layout
- `Sidebar` (layout component) — desktop nav
- `NotificationBell` (layout component) — header bell icon
- `ScraperLog` (scraper component) — bottom log panel
- `NavLink` from react-router-dom
- Icons from @phosphor-icons/react: List, MagnifyingGlass, Moon, Sun, SignOut, X, Plus, TerminalWindow

## Theme & Styling
- Header: bg transparent (inherits from WorkspaceShell), border-b-2 border-border
- Sidebar: bg-[var(--sidebar-bg)]
- All buttons use `hard-press` class for lift/press interaction
- Shadows: var(--shadow-xs) on header buttons, var(--shadow-sm) on active nav items
- No border-radius anywhere (0px)

## Typography
- Brand label: `.command-label` class — mono, 10px, 700, uppercase, tracking-[0.18em], text-muted
- Route title: text-base sm:text-lg, font-black, uppercase, tracking-[-0.08em]
- Command search: mono text-[11px], uppercase, tracking-[0.18em]
- Nav items: mono text-[11px], font-bold, uppercase, tracking-[0.18em]
- Bottom nav labels: mono text-[10px], font-bold, uppercase, tracking-[0.16em]

## Interactive States
- Header buttons (`hard-press`):
  - Default: border-2 border-border bg-background
  - Hover: translate(-2px, -2px), shadow-card-hover
  - Active: translate(2px, 2px), shadow-none
  - Transition: 120ms ease-out-expo
- Sidebar nav items:
  - Default: border-transparent bg-transparent text-text-secondary
  - Hover: border-border bg-[var(--sidebar-item-hover)] text-foreground
  - Active: border-border bg-[var(--sidebar-item-active-bg)] text-[var(--sidebar-item-active-text)]
- Logout button: bg-foreground text-background, hard-press

## Color Tokens Per Theme
| Token | Light | Dark |
|-------|-------|------|
| --sidebar-bg | #f5f5f5 | #0a0a0a |
| --sidebar-item-hover | #ebebeb | #141414 |
| --sidebar-item-active-bg | #2563eb | #3b82f6 |
| --sidebar-item-active-text | #ffffff | #09090b |
| --bg-primary | #fafafa | #000000 |
| --text-primary | #171717 | #fafafa |
| --border-strong | #09090b | #fafafa |
| --accent-primary | #2563eb | #3b82f6 |
| --accent-success | #16a34a | #22c55e |

## Responsive Behavior
- **xl+ (1280px)**: Desktop sidebar visible, bottom nav hidden, command search visible
- **lg (1024px)**: Sidebar hidden, bottom nav hidden, command search visible
- **md-sm**: Mobile layout, mobile nav toggle, bottom nav visible, most header elements hidden
- Sidebar collapse: toggles between 15rem and 5rem width
- Mobile drawer: slides from left with spring animation
