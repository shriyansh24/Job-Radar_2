## Learned User Preferences
- Prefers a complete, high-agency frontend UI/UX overhaul guided by the taste-skill plan rather than incremental, generic changes.
- Wants both light mode and a jet-black, high-contrast dark mode as first-class themes across the entire frontend.
- Expects premium visual polish: Geist typography, Phosphor icons, Framer Motion micro-interactions, and a Bento-style dashboard layout.

## Agent Read Order
- Current operational state lives in `docs/current-state/00-index.md`.
- Audit and bug-history state lives in `docs/audit/00-index.md`.
- Repo working conventions and command surface live in `CLAUDE.md`.

## Learned Workspace Facts
- The `jobradar-v2` frontend uses Tailwind CSS v4 with design tokens defined via CSS variables in `frontend/src/index.css` instead of the `@theme` at-rule.
- The frontend is on `@phosphor-icons/react` for all icons and uses Geist Sans / Geist Mono as the type system.
- The theme system is wired through a Zustand `useUIStore` that toggles a `.dark` class on the HTML root and persists the choice in `localStorage`.
- The current UI surface is a Career OS workspace with `Home`, `Discover`, `Execute`, `Prepare`, `Intelligence`, and `Operations` route groupings, plus first-class `/copilot`, `/networking`, `/email`, and `/outcomes` pages.
- `frontend/system.md` is the design-system source of truth for tokens, layout grammar, and component rules.
- Verified local validation is currently green for frontend lint, frontend tests, frontend build, and the targeted backend settings/auth/admin integration tests.
