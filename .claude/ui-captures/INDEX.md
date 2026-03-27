# UI Captures Index

> Generated 2026-03-26. Covers all 23 routed pages + the AppShell layout wrapper.
> Cross-referenced against Figma Make file pages: Dashboard, Jobs, Pipeline, Analytics, Copilot, Settings, Login, GenericPage.

## Theme Note
The app has **2 themes**: Light and Dark (toggled via `.dark` class on root element). There are NOT 4 themes — the color token table in each capture shows Light and Dark columns.

## Pages

### Layout
| Page | Route | File | Figma Status | Notes |
|------|-------|------|-------------|-------|
| [AppShell](app-shell.md) | N/A (wrapper) | `layout/AppShell.tsx` + `layout/Sidebar.tsx` | MISSING_FROM_FIGMA | Critical — wraps all protected routes. Sidebar, header, bottom nav, mobile drawer. |

### Public Routes
| Page | Route | File | Figma Status | Notes |
|------|-------|------|-------------|-------|
| [Login](login.md) | `/login` | `pages/Login.tsx` | IN_FIGMA | Standalone full-viewport page, no AppShell. |
| [Onboarding](onboarding.md) | `/onboarding` | `pages/Onboarding.tsx` | MISSING_FROM_FIGMA | 4-step wizard using system components. |

### Home
| Page | Route | File | Figma Status | Notes |
|------|-------|------|-------------|-------|
| [Dashboard](dashboard.md) | `/` | `pages/Dashboard.tsx` | IN_FIGMA | Command center with hero, metrics, pipeline map, feed. |

### Discover
| Page | Route | File | Figma Status | Notes |
|------|-------|------|-------------|-------|
| [Job Board](job-board.md) | `/jobs` | `pages/JobBoard.tsx` | IN_FIGMA | Split list/detail with exact + semantic search. |
| [Companies](companies.md) | `/companies` | `pages/Companies.tsx` | MISSING_FROM_FIGMA | Tabular company registry with validation filter. |

### Execute
| Page | Route | File | Figma Status | Notes |
|------|-------|------|-------------|-------|
| [Pipeline](pipeline.md) | `/pipeline` | `pages/Pipeline.tsx` | IN_FIGMA | Kanban-style stage columns with advance actions. |
| [Auto Apply](auto-apply.md) | `/auto-apply` | `pages/AutoApply.tsx` | MISSING_FROM_FIGMA | Profiles, rules, run history, stats tabs. |
| [Networking](networking.md) | `/networking` | `pages/Networking.tsx` | MISSING_FROM_FIGMA | Contact CRM + referral desk + outreach generation. |
| [Email](email.md) | `/email` | `pages/Email.tsx` | MISSING_FROM_FIGMA | Signal log + detail + replay surface. |

### Prepare
| Page | Route | File | Figma Status | Notes |
|------|-------|------|-------------|-------|
| [Resume Builder](resume-builder.md) | `/resume` | `pages/ResumeBuilder.tsx` | MISSING_FROM_FIGMA | Upload, versions, tailor, AI council tabs. |
| [Interview Prep](interview-prep.md) | `/interview` | `pages/InterviewPrep.tsx` | MISSING_FROM_FIGMA | Generate questions + practice + history. |
| [Salary Insights](salary-insights.md) | `/salary` | `pages/SalaryInsights.tsx` | MISSING_FROM_FIGMA | Research + range viz + offer evaluation. |
| [Document Vault](document-vault.md) | `/vault` | `pages/DocumentVault.tsx` | MISSING_FROM_FIGMA | Resume + cover letter shelf with CRUD. |
| [Copilot](copilot.md) | `/copilot` | `pages/Copilot.tsx` | IN_FIGMA | Chat, history analysis, cover letter generation. |

### Intelligence
| Page | Route | File | Figma Status | Notes |
|------|-------|------|-------------|-------|
| [Analytics](analytics.md) | `/analytics` | `pages/Analytics.tsx` | IN_FIGMA | Charts, source quality table, skills pulse. |
| [Outcomes](outcomes.md) | `/outcomes` | `pages/Outcomes.tsx` | MISSING_FROM_FIGMA | Outcome capture + company insight lookup. |

### Operations
| Page | Route | File | Figma Status | Notes |
|------|-------|------|-------------|-------|
| [Profile](profile.md) | `/profile` | `pages/Profile.tsx` | MISSING_FROM_FIGMA | Full profile editor with BRUTAL overrides. |
| [Settings](settings.md) | `/settings` | `pages/Settings.tsx` | IN_FIGMA | Workspace config, integrations, searches, security. |
| [Sources](sources.md) | `/sources` | `pages/Sources.tsx` | MISSING_FROM_FIGMA | Source health cards with telemetry. |
| [Targets](targets.md) | `/targets` | `pages/Targets.tsx` | MISSING_FROM_FIGMA | Scrape target management with attempt timeline. |
| [Canonical Jobs](canonical-jobs.md) | `/canonical-jobs` | `pages/CanonicalJobs.tsx` | MISSING_FROM_FIGMA | Merged job entities, stale cleanup. |
| [Search Expansion](search-expansion.md) | `/search-expansion` | `pages/SearchExpansion.tsx` | MISSING_FROM_FIGMA | Query expansion with term/synonym generation. |
| [Admin](admin.md) | `/admin` | `pages/Admin.tsx` | MISSING_FROM_FIGMA | System health, diagnostics, source table, actions. |

## Summary
- **Total pages**: 23 (+ AppShell wrapper)
- **IN_FIGMA**: 7 (Dashboard, Jobs, Pipeline, Analytics, Copilot, Settings, Login)
- **MISSING_FROM_FIGMA**: 16 + AppShell = 17
- **GenericPage** in Figma appears to be a template/placeholder, not a specific route

## Screenshots

All 92 screenshots captured programmatically via Playwright (headless Chromium, @2x retina):

**Per page**: `<name>-light.png`, `<name>-dark.png`, `<name>-mobile-light.png`, `<name>-mobile-dark.png`

- **Desktop**: 1440×900 viewport @2x (2880×1800 actual pixels)
- **Mobile**: 390×844 viewport @2x (780×1688 actual pixels, iPhone 14 Pro equivalent)
- **Location**: `screenshots/` directory (92 files, ~1.3 MB total)
- **Auth**: API calls mocked (empty data state) — shows page chrome/layout, not populated data

## Design System Reference
- Theme CSS: `src/index.css` — single source of truth for all tokens
- Design doc: `frontend/system.md` — visual authority
- System components: `src/components/system/` — 13 shared primitives
- UI primitives: `src/components/ui/` — 16 base components
- Icon set: `@phosphor-icons/react` (bold weight default)
- Fonts: Inter (sans/display) + JetBrains Mono (labels/metrics)
- Border radius: 0px everywhere (neo-brutalist)
- Shadows: hard offset (no blur)
