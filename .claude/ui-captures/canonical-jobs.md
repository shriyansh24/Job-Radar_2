# Canonical Jobs

## Route: `/canonical-jobs` — File: `src/pages/CanonicalJobs.tsx`

## Figma Status: MISSING_FROM_FIGMA

## Layout
- **PageHeader**: "Operations" breadcrumb, title "Canonical Jobs", "Show stale only" toggle button, meta chips (loaded/open/stale counts)
- **Surface** (padding="none"): SectionHeader + rows showing title, company, location, status Badge, source count, stale indicator, close/reactivate action buttons

## Components
- System: PageHeader, SectionHeader, Surface
- UI: Badge, Button, EmptyState, Skeleton
- Icons: GitMerge, WarningCircle

## Data
- `canonicalJobsApi`:
  - `list({stale_only})` — fetch all canonical jobs, optionally filtered
  - `close(id)` — close a canonical job
  - `reactivate(id)` — reactivate a closed canonical job

## Model: CanonicalJob
```typescript
{
  id: string
  title: string
  company: string
  location: string
  status: "open" | "closed"
  source_count: number
  is_stale: boolean
  first_seen_at: DateTime
  last_seen_at: DateTime
}
```

## Behavior
1. On load, fetch canonical jobs list (default all, toggle to stale-only)
2. Display table with row-level actions: close or reactivate
3. Badge shows status color (green/open, gray/closed)
4. Stale indicator icon appears if `is_stale === true`
5. Source count links to detailed source breakdown (future)

## Theme Colors

| Element | Light | Dark |
|---------|-------|------|
| PageHeader bg | #FFFFFF | #0A0A0A |
| Surface bg | #F5F5F5 | #1A1A1A |
| Text primary | #000000 | #FFFFFF |
| Badge (open) | #10B981 | #10B981 |
| Badge (closed) | #9CA3AF | #6B7280 |
| Stale icon | #F59E0B | #FBBF24 |
| Border | #E5E7EB | #404040 |
