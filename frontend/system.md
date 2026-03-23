# JobRadar Career OS System

## Visual Thesis
- Build JobRadar as a disciplined career operations console, not a generic dashboard.
- Light mode should feel calm, paper-like, and operational.
- Dark mode should be near-black, high-contrast, and dense without becoming noisy.
- Use one assertive action accent and keep the rest of the system neutral and semantic.

## Typography
- Primary family: Geist Sans.
- Monospace family: Geist Mono.
- Use compact, high-clarity type for operational surfaces.
- Reserve oversized type for onboarding, empty states, and top-level page framing.

## Color Rules
- Neutral surfaces first. Color should signal action, status, or hierarchy rather than decorate space.
- Primary accent: electric blue for key actions, selected states, and focus.
- Semantic colors:
  - Success: green
  - Warning: amber
  - Danger: rose/red
  - Info: violet only when meaningfully distinct from the primary accent
- Dense work surfaces should avoid decorative gradients behind content.

## Theme Rules
- Light mode:
  - bright neutral canvas
  - white and soft-zinc surfaces
  - dark ink text
- Dark mode:
  - true-black or near-black canvas
  - stepped charcoal surfaces
  - bright text and crisp borders
- Both themes must keep equivalent information hierarchy and interaction affordances.

## Spacing and Shape
- Base rhythm: 8px.
- Compact operational components can use 4px sub-steps internally.
- Default radius is medium-large and consistent across inputs, cards, and overlays.
- Card treatments are opt-in. Do not nest cards repeatedly.

## Elevation
- Use borders first, shadows second.
- Elevated surfaces should feel deliberate:
  - list/detail panes use border separation
  - floating controls use shadow plus backdrop blur
  - dark mode shadows stay tight to avoid muddy stacks

## Motion
- Motion should clarify focus, entry, or state change.
- Preferred durations:
  - 120ms for hover/press
  - 180-220ms for layout/state transitions
  - 300-450ms for page or section entry
- Prefer opacity, translate, and scale changes over large transforms.

## Layout Grammar
- Command Center: hero metrics, operational feed, and priority actions in a bento-like grid.
- Split Workspace: primary list/table, secondary detail, optional tertiary rail.
- Kanban Workspace: dense columns with persistent summaries and lightweight overlays.
- Guided Setup: progressive, high-trust steps with strong completion signals.
- Settings/Operations: sectioned control center with explicit hierarchy and safe destructive zones.

## Component Rules
- Shared shell and page scaffolding live in `src/components/system`.
- Existing `src/components/ui` remains stable during migration.
- New screens should compose from system primitives before adding page-local wrappers.
- Prefer semantic HTML and utility composition over custom CSS files.

## Shadcn Adoption
- `components.json` and Tailwind compatibility are in place for incremental shadcn adoption.
- Do not replace legacy UI primitives wholesale during foundation work.
- New shadcn-generated pieces should map back to existing design tokens and theme behavior.

## Future Feature Checklist
- Verify the feature works in both light and dark mode.
- Confirm loading, empty, error, and success states exist.
- Use semantic color only for meaning, not decoration.
- Keep keyboard focus visible and consistent.
- Prefer shared system primitives before inventing new layout wrappers.
