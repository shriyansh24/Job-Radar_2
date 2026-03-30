# Admin

## Route
- Path: `/admin`
- File: `src/pages/Admin.tsx`

## Figma Status: MISSING_FROM_FIGMA

## Layout Structure
- PageHeader (system, BRUTAL_PANEL): "Operations" eyebrow + "Admin" h1 + meta chips "API status" "DB online/offline" "X/Y sources healthy"
- SplitWorkspace (xl:grid-cols-[1.25fr_0.95fr]):
  - Primary (space-y-6):
    - SectionHeader: "System Health"
    - HealthMetricGrid (md:grid-cols-3):
      - Surface card: "Database" status + Badge (online green, offline red)
      - Surface card: "Redis" status + Badge (online green, offline red)
      - Surface card: "API" status + Badge (healthy green, degraded yellow, down red)
    - SectionHeader: "Diagnostics"
    - DiagnosticGrid (md:grid-cols-2 xl:grid-cols-4):
      - DiagnosticItem card:
        - Icon + label + value (Python version, Platform, Applications, Total jobs)
    - SectionHeader: "Source Health"
    - SourceHealthTable (Surface padding="none"):
      - Table columns (sortable):
        - Source name
        - Status Badge (healthy, degraded, unhealthy)
        - Last check timestamp
        - Jobs found count
        - Failures count
      - Rows: source health items
      - EmptyState (if no sources)
    - SectionHeader: "Actions"
    - ActionsGrid (grid-cols-2 md:grid-cols-4):
      - Button: "Reindex FTS" (icon ArrowClockwise)
      - Button: "Reindex Search" (icon MagnifyingGlass)
      - Button: "Export data" (icon DownloadSimple)
      - Button: "Import data" (icon UploadSimple, triggers file input)
  - Secondary (space-y-4):
    - StateBlock: "System status overview"
    - StateBlock: "Recent errors or warnings"
    - StateBlock: "Data management guide"

## Components Used
- System: `PageHeader`, `SectionHeader`, `SplitWorkspace`, `Surface`, `StateBlock`
- UI: `Badge`, `Button`, `EmptyState`, `Skeleton`
- Icons: ArrowClockwise, Briefcase, Cloud, Clock, Database, DownloadSimple, UploadSimple, Warning, WarningCircle
- Local: `DiagnosticItem` (icon + label + value card)

## Theme & Styling
- BRUTAL_PANEL: !rounded-none !border-2 !shadow-[4px_4px_0_0]
- BRUTAL_BUTTON: !rounded-none !border-2
- PageHeader: border-b-2, standard BRUTAL override
- HealthMetricGrid Surface: border-2, centered metric display
- DiagnosticItem: border-2, icon + value layout, compact
- SourceHealthTable: border-2 container, header border-b-2, row borders
- ActionsGrid buttons: equal spacing, icon + label

## Data/Content Shape
- adminApi:
  - health(): Promise<HealthStatus>
  - diagnostics(): Promise<SystemDiagnostics>
  - sourceHealth(): Promise<SourceHealth[]>
  - reindexFTS(): Promise<{reindexed: int}>
  - reindexSearch(): Promise<{reindexed: int}>
  - exportData(): Promise<Blob> // JSON/CSV file
  - importData(file): Promise<{imported: int, errors: string[]}>
- HealthStatus: database (online|offline), redis (online|offline), api (healthy|degraded|down)
- SystemDiagnostics: python_version (string), platform (string), job_count (int), application_count (int)
- SourceHealth: id, source_name, health_state (healthy|degraded|unhealthy), last_check_at (DateTime), total_jobs_found (int), failure_count (int)

## Responsive Behavior
- Mobile (< 768px): HealthMetricGrid single-column, DiagnosticGrid grid-cols-2, ActionsGrid grid-cols-2, table horizontal scroll
- Tablet (768px–1024px): HealthMetricGrid grid-cols-3, DiagnosticGrid grid-cols-2, ActionsGrid grid-cols-2
- Desktop (≥ 1024px): Full SplitWorkspace, HealthMetricGrid grid-cols-3, DiagnosticGrid grid-cols-4, ActionsGrid grid-cols-4
- Extra Large (≥ 1280px): Enhanced spacing, wider cards

---

## Light Theme

### Colors
- Background: #FFFFFF
- Text Primary: #000000
- Text Secondary: #666666
- Border: #000000
- Card Background: #F8F8F8
- Secondary: #F0F0F0
- Status Online: #00AA00
- Status Offline: #FF0000
- Status Healthy: #00AA00
- Status Degraded: #FF9900
- Status Down: #FF0000

### Component States
- BRUTAL_PANEL: !rounded-none !border-2 !border-#000000 !bg-#F8F8F8 !shadow-[4px_4px_0_0_#000000]
- BRUTAL_BUTTON: !rounded-none !border-2 !border-#000000 !bg-#F0F0F0 !text-#000000 hover:!bg-#E5E5E5
- PageHeader: border-b-2 border-#000000, bg-#FFFFFF
- HealthMetricGrid Surface: border-2 border-#000000, bg-#F8F8F8
- Badge online: bg-#00AA00 text-#FFFFFF
- Badge offline: bg-#FF0000 text-#FFFFFF
- Badge healthy: bg-#00AA00 text-#FFFFFF
- Badge degraded: bg-#FF9900 text-#FFFFFF
- Badge down: bg-#FF0000 text-#FFFFFF
- DiagnosticItem: border-2 border-#E5E5E5, bg-#FFFFFF, icon color matches status
- SourceHealthTable: border-2 border-#000000, header border-b-2 border-#000000
- Table row: border-b-1 border-#E5E5E5, hover:bg-#F8F8F8
- ActionsGrid button: border-2 border-#000000
- StateBlock: border-2 border-#E5E5E5, bg-#F0F0F0

---

## Dark Theme

### Colors
- Background: #0A0A0A
- Text Primary: #FFFFFF
- Text Secondary: #AAAAAA
- Border: #FFFFFF
- Card Background: #1A1A1A
- Secondary: #252525
- Status Online: #00DD00
- Status Offline: #FF3333
- Status Healthy: #00DD00
- Status Degraded: #FFAA33
- Status Down: #FF3333

### Component States
- BRUTAL_PANEL: !rounded-none !border-2 !border-#FFFFFF !bg-#1A1A1A !shadow-[4px_4px_0_0_#FFFFFF]
- BRUTAL_BUTTON: !rounded-none !border-2 !border-#FFFFFF !bg-#252525 !text-#FFFFFF hover:!bg-#333333
- PageHeader: border-b-2 border-#FFFFFF, bg-#0A0A0A
- HealthMetricGrid Surface: border-2 border-#FFFFFF, bg-#1A1A1A
- Badge online: bg-#00DD00 text-#000000
- Badge offline: bg-#FF3333 text-#FFFFFF
- Badge healthy: bg-#00DD00 text-#000000
- Badge degraded: bg-#FFAA33 text-#000000
- Badge down: bg-#FF3333 text-#FFFFFF
- DiagnosticItem: border-2 border-#333333, bg-#1A1A1A, icon color matches status
- SourceHealthTable: border-2 border-#FFFFFF, header border-b-2 border-#FFFFFF
- Table row: border-b-1 border-#333333, hover:bg-#252525
- ActionsGrid button: border-2 border-#FFFFFF
- StateBlock: border-2 border-#333333, bg-#252525
