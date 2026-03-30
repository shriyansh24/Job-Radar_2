# Companies

## Route
- Path: `/companies`
- File: `src/pages/Companies.tsx`

## Figma Status
MISSING_FROM_FIGMA

## Layout Structure
- PageHeader (system): eyebrow "Operations", title "Companies", filter buttons as actions, record/verified count meta chips
- 3 Surface metric cards (grid md:grid-cols-3): Registry Size, Verified, Visible Now
- Company registry table (Surface padding="none"):
  - Header bar with SectionHeader
  - Column headers (hidden md:grid, bg-tertiary): Company, Domain, ATS, Status, Jobs, Confidence
  - Data rows (divide-y-2): company name, domain, ATS provider, status Badge, job count, confidence %
  - Mobile: stacks with visible labels

## Components Used
- System: `PageHeader`, `SectionHeader`, `Surface`
- UI: `Badge`, `EmptyState`, `Skeleton`
- Icons: Buildings, CheckCircle, Globe, TrendUp

## Data/Content Shape
- companiesApi.list(): Company[] with canonical_name, domain, ats_provider, validation_state (verified/unverified/invalid), job_count, confidence_score
- Filter: validation_state or "All"

## Theme Variants
### Light Theme
- Background: surface-primary (white/near-white)
- Text: text-primary (dark gray/charcoal)
- Metric cards: bg-secondary with accent border
- Table header: bg-tertiary with text-secondary
- Status badges: color-coded (verified=green, unverified=yellow, invalid=red)
- Hover states: subtle bg lift on rows

### Dark Theme
- Background: surface-primary (near-black)
- Text: text-primary (light gray/white)
- Metric cards: bg-secondary with accent border (lighter)
- Table header: bg-tertiary (darker) with text-secondary
- Status badges: color-coded dark variants
- Hover states: subtle bg lift on rows (lighter shade)
