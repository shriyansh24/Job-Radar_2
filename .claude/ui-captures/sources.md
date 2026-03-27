# Source Health

## Route
- Path: `/sources`
- File: `src/pages/Sources.tsx`

## Figma Status: MISSING_FROM_FIGMA

## Layout Structure
- PageHeader (system, BRUTAL_PANEL): "Operations" eyebrow + "Source Health" h1 + meta chips "X sources" "Y healthy"
- MetricGrid (md:grid-cols-3):
  - Surface card: "Sources" metric + total count
  - Surface card: "Healthy" metric + healthy count
  - Surface card: "Jobs Found" metric + total jobs found
- SectionHeader: "Source Details"
- SourceCardGrid (md:grid-cols-2 xl:grid-cols-3):
  - SourceCard (Surface padding="md"):
    - Card header: Source name + Health Badge (healthy green, degraded yellow, unhealthy red)
    - Card body:
      - Quality score %
      - Total jobs found count
      - Failure count
      - Last checked timestamp
      - Created timestamp
    - Status icon: Heartbeat (healthy), Pulse (degraded), WarningCircle (unhealthy)
  - EmptyState (if no sources)
- Auto-refetch every 60 seconds (optional indicator: last refreshed at)

## Components Used
- System: `PageHeader`, `Surface`, `SectionHeader`
- UI: `Badge`, `EmptyState`, `Skeleton`
- Icons: Heartbeat, Pulse, ShieldCheck, WarningCircle, Clock
- Local: `SourceCard` (health status display)

## Theme & Styling
- BRUTAL_PANEL: !rounded-none !border-2 !shadow-[4px_4px_0_0]
- PageHeader: border-b-2 border, standard BRUTAL override
- MetricGrid Surface: border-2, centered metric display with large number
- SourceCard: border-2, compact layout with status icon + badge
- Health Badge colors: green (healthy), yellow/orange (degraded), red (unhealthy)
- Card hover: subtle border/shadow change on desktop

## Data/Content Shape
- sourceHealthApi:
  - listSourceHealth(): Promise<SourceHealth[]>
  - (auto-refetch every 60s via useQuery)
- SourceHealth: id, source_name, health_state (healthy|degraded|unhealthy), quality_score (0–100), total_jobs_found (int), failure_count (int), last_check_at (DateTime), created_at (DateTime)

## Responsive Behavior
- Mobile (< 768px): MetricGrid single-column, SourceCardGrid grid-cols-1, no horizontal scroll
- Tablet (768px–1024px): MetricGrid grid-cols-3, SourceCardGrid grid-cols-2, cards adjust width
- Desktop (≥ 1024px): Full layout, MetricGrid 3-column, SourceCardGrid grid-cols-3
- Extra Large (≥ 1280px): Cards may expand with more detail, wider spacing

---

## Light Theme

### Colors
- Background: #FFFFFF
- Text Primary: #000000
- Text Secondary: #666666
- Border: #000000
- Card Background: #F8F8F8
- Secondary: #F0F0F0
- Status Healthy: #00AA00
- Status Degraded: #FF9900
- Status Unhealthy: #FF0000

### Component States
- BRUTAL_PANEL: !rounded-none !border-2 !border-#000000 !bg-#F8F8F8 !shadow-[4px_4px_0_0_#000000]
- PageHeader: border-b-2 border-#000000, bg-#FFFFFF
- MetricGrid Surface: border-2 border-#000000, bg-#F8F8F8
- MetricGrid value: text-#000000, bold, font-size large
- Badge healthy: bg-#00AA00 text-#FFFFFF
- Badge degraded: bg-#FF9900 text-#000000
- Badge unhealthy: bg-#FF0000 text-#FFFFFF
- SourceCard: border-2 border-#E5E5E5, bg-#FFFFFF, hover:border-#000000
- SourceCard status icon healthy: text-#00AA00
- SourceCard status icon degraded: text-#FF9900
- SourceCard status icon unhealthy: text-#FF0000

---

## Dark Theme

### Colors
- Background: #0A0A0A
- Text Primary: #FFFFFF
- Text Secondary: #AAAAAA
- Border: #FFFFFF
- Card Background: #1A1A1A
- Secondary: #252525
- Status Healthy: #00DD00
- Status Degraded: #FFAA33
- Status Unhealthy: #FF3333

### Component States
- BRUTAL_PANEL: !rounded-none !border-2 !border-#FFFFFF !bg-#1A1A1A !shadow-[4px_4px_0_0_#FFFFFF]
- PageHeader: border-b-2 border-#FFFFFF, bg-#0A0A0A
- MetricGrid Surface: border-2 border-#FFFFFF, bg-#1A1A1A
- MetricGrid value: text-#FFFFFF, bold, font-size large
- Badge healthy: bg-#00DD00 text-#000000
- Badge degraded: bg-#FFAA33 text-#000000
- Badge unhealthy: bg-#FF3333 text-#FFFFFF
- SourceCard: border-2 border-#333333, bg-#1A1A1A, hover:border-#FFFFFF
- SourceCard status icon healthy: text-#00DD00
- SourceCard status icon degraded: text-#FFAA33
- SourceCard status icon unhealthy: text-#FF3333
