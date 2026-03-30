# UI Captures Index

> Generated 2026-03-27. Current browser capture index for the integrated frontend sweep.
> Use this directory as the current screenshot reference set for browser QA on `codex/ui-changes`.

## Theme Note
The current frontend runtime supports `default`, `terminal`, `blueprint`, and `phosphor`, each with `light` and `dark` modes. This directory contains both current representative captures and older historical route notes.

## Pages

### Layout
| Page | Route | File | Figma Status | Notes |
|------|-------|------|--------------|-------|
| [AppShell](app-shell.md) | N/A (wrapper) | `layout/AppShell.tsx` + `layout/Sidebar.tsx` | MISSING_FROM_FIGMA | Critical - wraps all protected routes. Sidebar, header, bottom nav, mobile drawer. |

### Public Routes
| Page | Route | File | Figma Status | Notes |
|------|-------|------|--------------|-------|
| [Login](login.md) | `/login` | `pages/Login.tsx` | IN_FIGMA | Standalone full-viewport page, no AppShell. |
| [Onboarding](onboarding.md) | `/onboarding` | `pages/Onboarding.tsx` | MISSING_FROM_FIGMA | 4-step wizard using system components. |

### Home
| Page | Route | File | Figma Status | Notes |
|------|-------|------|--------------|-------|
| [Dashboard](dashboard.md) | `/` | `pages/Dashboard.tsx` | IN_FIGMA | Command center with hero, metrics, pipeline map, feed. |

### Discover
| Page | Route | File | Figma Status | Notes |
|------|-------|------|--------------|-------|
| [Job Board](job-board.md) | `/jobs` | `pages/JobBoard.tsx` | IN_FIGMA | Split list/detail with exact + semantic search. |
| [Companies](companies.md) | `/companies` | `pages/Companies.tsx` | MISSING_FROM_FIGMA | Tabular company registry with validation filter. |

### Execute
| Page | Route | File | Figma Status | Notes |
|------|-------|------|--------------|-------|
| [Pipeline](pipeline.md) | `/pipeline` | `pages/Pipeline.tsx` | IN_FIGMA | Kanban-style stage columns with advance actions. |
| [Auto Apply](auto-apply.md) | `/auto-apply` | `pages/AutoApply.tsx` | MISSING_FROM_FIGMA | Profiles, rules, run history, stats tabs. |
| [Networking](networking.md) | `/networking` | `pages/Networking.tsx` | MISSING_FROM_FIGMA | Contact CRM + referral desk + outreach generation. |
| [Email](email.md) | `/email` | `pages/Email.tsx` | MISSING_FROM_FIGMA | Signal log + detail + replay surface. |

### Prepare
| Page | Route | File | Figma Status | Notes |
|------|-------|------|--------------|-------|
| [Resume Builder](resume-builder.md) | `/resume` | `pages/ResumeBuilder.tsx` | MISSING_FROM_FIGMA | Upload, versions, tailor, AI council tabs. |
| [Interview Prep](interview-prep.md) | `/interview` | `pages/InterviewPrep.tsx` | MISSING_FROM_FIGMA | Generate questions + practice + history. |
| [Salary Insights](salary-insights.md) | `/salary` | `pages/SalaryInsights.tsx` | MISSING_FROM_FIGMA | Research + range viz + offer evaluation. |
| [Document Vault](document-vault.md) | `/vault` | `pages/DocumentVault.tsx` | MISSING_FROM_FIGMA | Resume + cover letter shelf with CRUD. |
| [Copilot](copilot.md) | `/copilot` | `pages/Copilot.tsx` | IN_FIGMA | Chat, history analysis, cover letter generation. |

### Intelligence
| Page | Route | File | Figma Status | Notes |
|------|-------|------|--------------|-------|
| [Analytics](analytics.md) | `/analytics` | `pages/Analytics.tsx` | IN_FIGMA | Charts, source quality table, skills pulse. |
| [Outcomes](outcomes.md) | `/outcomes` | `pages/Outcomes.tsx` | MISSING_FROM_FIGMA | Outcome capture + company insight lookup. |

### Operations
| Page | Route | File | Figma Status | Notes |
|------|-------|------|--------------|-------|
| [Profile](profile.md) | `/profile` | `pages/Profile.tsx` | MISSING_FROM_FIGMA | Full profile editor with BRUTAL overrides. |
| [Settings](settings.md) | `/settings` | `pages/Settings.tsx` | IN_FIGMA | Workspace config, integrations, searches, security. |
| [Sources](sources.md) | `/sources` | `pages/Sources.tsx` | MISSING_FROM_FIGMA | Source health cards with telemetry. |
| [Targets](targets.md) | `/targets` | `pages/Targets.tsx` | MISSING_FROM_FIGMA | Scrape target management with attempt timeline. |
| [Canonical Jobs](canonical-jobs.md) | `/canonical-jobs` | `pages/CanonicalJobs.tsx` | MISSING_FROM_FIGMA | Merged job entities, stale cleanup. |
| [Search Expansion](search-expansion.md) | `/search-expansion` | `pages/SearchExpansion.tsx` | MISSING_FROM_FIGMA | Query expansion with term/synonym generation. |
| [Admin](admin.md) | `/admin` | `pages/Admin.tsx` | MISSING_FROM_FIGMA | System health, diagnostics, source table, actions. |

## Current Capture Packs

### Integrated sweep
- `integrated-dashboard-default-dark-desktop.png`
- `integrated-jobs-default-dark-desktop.png`
- `integrated-pipeline-default-dark-desktop.png`
- `integrated-analytics-default-dark-desktop.png`
- `integrated-settings-default-dark-desktop.png`
- `integrated-admin-default-dark-desktop.png`
- `integrated-resume-default-dark-desktop.png`
- `integrated-dashboard-default-dark-mobile.png`

### Theme-family spot checks
- `dashboard-default-dark-desktop.png`
- `dashboard-blueprint-light-desktop.png`
- `dashboard-phosphor-dark-phone.png`
- `analytics-terminal-dark-desktop.png`
- `settings-default-dark-desktop.png`
- `settings-blueprint-light-tablet.png`
- `admin-default-dark-desktop.png`
- `jobs-default-dark-desktop.png`
- `pipeline-default-dark-desktop.png`

## Summary
- Total routes in the authenticated sweep: 22
- Representative captures reflect the current decomposed frontend, simplified shell, and cleaned page copy
- Historical route notes below are still useful for file-to-screen mapping, but the current PNG set above is the live browser QA reference

## Screenshots

Representative screenshots in this folder were captured programmatically via Playwright against the live local app.

- Desktop captures use 1440x900 or 1536x960 class viewports
- Mobile captures use 390x844 class viewports
- Tablet captures use 1024x1366 class viewports
- Authenticated sweeps log in through the real `/login` surface
- This directory is the canonical browser QA artifact location for the current branch

## Design System Reference
- Theme CSS: `src/index.css`
- Design doc: `frontend/system.md`
- System components: `src/components/system/`
- UI primitives: `src/components/ui/`
- Icon set: `@phosphor-icons/react` (bold weight default)
- Fonts: Inter (sans/display) + JetBrains Mono (labels/metrics)
- Border radius: 0px everywhere
- Shadows: hard offset (no blur)
