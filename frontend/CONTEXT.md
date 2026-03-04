# Frontend Module Context

## Purpose
Dark-themed React dashboard for browsing, filtering, and tracking job applications with real-time scraper events, AI copilot tools, and analytics.

## Current Status
- Design system: Implemented (Geist dark theme, CSS variables, noise overlay)
- Layout shell: Implemented (240px sidebar, 56px topbar, scrollable main)
- Dashboard page: Implemented (4 stat cards, top matches, charts)
- Job Board page: Implemented (filters, virtualized list, detail panel)
- Pipeline page: Implemented (8-column drag-drop kanban)
- Analytics page: Implemented (5 chart types via Recharts)
- Settings page: Implemented (3 tabs: API Keys, Scraper Config, Resume)
- Scraper log drawer: Implemented (floating terminal, SSE-connected)

## Design System
```css
--bg-base:        #000000    /* Page background */
--bg-surface:     #0a0a0a    /* Card backgrounds */
--bg-elevated:    #111111    /* Hover states, active items */
--border:         #333333    /* Borders, dividers */
--text-primary:   #EDEDED    /* Main text */
--text-secondary: #888888    /* Secondary text */
--accent:         #0070F3    /* Primary accent (Vercel blue) */
--accent-green:   #10B981    /* Success, new items */
--accent-amber:   #F5A623    /* Warning, saved items */
--accent-red:     #E00000    /* Error, rejected */
--accent-cyan:    #3291FF    /* Applied status */
--font-ui:        'Geist'    /* UI text */
--font-mono:      'Geist Mono' /* Numbers, code, timestamps */
```

## Key Components

### State Management (Zustand)
```typescript
interface JobStore {
  currentPage: string        // "dashboard" | "jobboard" | "pipeline" | "analytics" | "settings"
  selectedJobId: string | null
  filters: JobFilters
  viewMode: "list" | "grid"
  scraperLogs: ScraperLogEntry[]
  isLogDrawerOpen: boolean
  isFilterPanelOpen: boolean
  totalJobCount: number
  isScraperRunning: boolean
  isResumeActive: boolean
}
```

### API Client (axios)
- Base URL: `/api` (proxied by Vite to :8000)
- Functions: fetchJobs, fetchJob, updateJob, fetchStats, triggerScraper,
  fetchScraperStatus, semanticSearch, fetchSettings, updateSettings,
  uploadResume, streamCopilot, connectSSE, fetchSavedSearches,
  createSavedSearch, deleteSavedSearch

### Data Fetching (TanStack React Query v5)
- Query keys: `['stats']`, `['jobs', filters]`, `['jobs', 'pipeline']`,
  `['jobs', 'top-matches']`, `['settings']`, `['saved-searches']`
- Stale time: 30 seconds
- Retry: 1 attempt

## Dependencies
- react 19, react-dom 19
- @tanstack/react-query 5 (server state)
- @tanstack/react-virtual 3 (virtualized lists, 50K+ items)
- @dnd-kit/core 6, @dnd-kit/sortable 8 (drag-drop kanban)
- zustand 5 (client state)
- recharts 2 (charts: Area, Bar, Pie)
- axios 1.7 (HTTP client)
- lucide-react 0.460 (icons)
- date-fns 4 (time formatting)
- react-hot-toast 2 (notifications)

## Build
- Vite 6 + @vitejs/plugin-react
- TypeScript 5.6 (strict mode)
- TailwindCSS 3.4 with custom .cjs config
- Production bundle: ~835KB (gzipped ~250KB)
