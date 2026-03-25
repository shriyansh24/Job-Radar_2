## Learned User Preferences
- Prefers a complete, high-agency reference-first frontend overhaul rather than incremental, generic changes.
- Wants both light mode and a jet-black, high-contrast dark mode as first-class themes across the entire frontend.
- Expects premium visual polish: Inter + JetBrains Mono, Phosphor icons, Framer Motion micro-interactions, hard 2px borders, sharp corners, and a command-center shell.

## Agent Read Order
- Current operational state lives in `docs/current-state/00-index.md`.
- Audit and bug-history state lives in `docs/audit/00-index.md`.
- Repo working conventions and command surface live in `CLAUDE.md`.

## Learned Workspace Facts
- The `jobradar-v2` frontend uses Tailwind CSS v4 with design tokens defined via CSS variables in `frontend/src/index.css`.
- The frontend uses `@phosphor-icons/react` and `Inter` / `JetBrains Mono` as the live type system.
- The theme system is wired through a Zustand `useUIStore` that toggles a `.dark` class on the HTML root and persists the choice in `localStorage`.
- The current UI surface is a reference-first neo-brutalist command center: fixed top bar, desktop rail, mobile drawer, mobile bottom nav, and routed page families under `Home`, `Discover`, `Execute`, `Prepare`, `Intelligence`, and `Operations`.
- `frontend/system.md` is the design-system source of truth for tokens, layout grammar, shell posture, and component rules.
- Verified local validation is currently green for frontend lint, frontend tests, frontend build, targeted backend auth/settings/admin/vault integration tests, and browser-level desktop/tablet/phone route sweeps with artifacts in `output/playwright/`.
