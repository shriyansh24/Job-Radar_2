# Targets

## Route
- Path: `/targets`
- File: `src/pages/Targets.tsx`

## Figma Status: MISSING_FROM_FIGMA

## Layout Structure
- PageHeader (system, BRUTAL_PANEL): "Operations" eyebrow + "Targets" h1 + action buttons "Import CSV" "Export CSV"
- MetricStrip (optional, system BRUTAL override): Total targets, Enabled targets, Last scraped, Success rate
- TargetTable (Surface padding="none"):
  - Table columns (sortable headers):
    - URL (truncated with copy button)
    - Company
    - ATS Vendor
    - Priority class (watchlist, hot, warm, default) - Badge
    - Enabled - Toggle
    - Last scraped - Timestamp
    - Attempts count
    - Action button: "View details"
  - Rows: TargetRowSkeleton during load
  - EmptyState (if no targets)
  - Pagination controls (previous, page number input, next, rows-per-page select)
- TargetDetailModal (if "View details" clicked):
  - Modal header: Company + URL
  - Modal body:
    - Basic fields: url, company, ats_vendor, priority_class
    - Toggle: enabled
    - AttemptTimeline (chronological list):
      - Each attempt: status Badge, timestamp, error message (if applicable)
    - Action button: "Clear history"
  - Modal footer: Close button

## Components Used
- System: `PageHeader`, `Surface`, `StateBlock`
- UI: `Badge`, `Button`, `EmptyState`, `Modal`, `Select`, `Skeleton`, `Textarea`, `Toggle`
- Icons: ArrowUpDown, Copy, Download, Eye, Info, Trash, Upload, WarningCircle
- Local: `TargetRowSkeleton` (table row skeleton), `AttemptTimeline` (chronological attempt display)

## Theme & Styling
- BRUTAL_PANEL: !rounded-none !border-2 !shadow-[4px_4px_0_0]
- BRUTAL_TABLE: !rounded-none, border-collapse, header bg darker than body
- Table header: border-2 on bottom, cursor pointer on sortable columns
- Table row: border-b-2, hover:bg-secondary
- Badge priority: watchlist red, hot orange, warm yellow, default gray
- Badge status: success green, pending gray, error red
- Modal: BRUTAL_PANEL style, full-height on mobile
- AttemptTimeline: vertical line with dots + text entries

## Data/Content Shape
- scraperApi:
  - listTargets(params: TargetListParams): Promise<{items: ScrapeTarget[], total: int}>
  - getTarget(id): Promise<ScrapeTarget>
  - updateTarget(id, payload): Promise<ScrapeTarget>
  - deleteTarget(id): Promise<void>
  - importTargets(csvFile): Promise<{imported: int, errors: string[]}>
  - exportTargets(): Promise<Blob> // CSV file
- TargetListParams: page, limit, sort_by, sort_order, enabled_only?, search?
- ScrapeTarget: id, url, company, priority_class (watchlist|hot|warm|default), ats_vendor, enabled, last_scraped_at, created_at, attempts: ScrapeAttempt[]
- ScrapeAttempt: id, target_id, status (pending|success|failed|partial), timestamp, error_message?, parsed_data_count?

## Responsive Behavior
- Mobile (< 768px): Table horizontal scroll, modal full-screen, pagination stacked
- Tablet (768px–1024px): Table visible, columns may hide less-critical ones, modal 80vw width
- Desktop (≥ 1024px): Full table, modal 60vw width, compact pagination
- Extra Large (≥ 1280px): Table with all columns visible, more spacing

---

## Light Theme

### Colors
- Background: #FFFFFF
- Text Primary: #000000
- Text Secondary: #666666
- Border: #000000
- Card Background: #F8F8F8
- Secondary: #F0F0F0
- Status Success: #00AA00
- Status Pending: #FF9900
- Status Error: #FF0000
- Priority Watchlist: #FF0000
- Priority Hot: #FF9900
- Priority Warm: #FFDD00
- Priority Default: #999999

### Component States
- BRUTAL_PANEL: !rounded-none !border-2 !border-#000000 !bg-#F8F8F8 !shadow-[4px_4px_0_0_#000000]
- Table container: border-2 border-#000000, bg-#FFFFFF
- Table header: border-b-2 border-#000000, bg-#F0F0F0, font-weight bold
- Table row: border-b-1 border-#E5E5E5, bg-#FFFFFF, hover:bg-#F8F8F8
- Badge priority watchlist: bg-#FF0000 text-#FFFFFF
- Badge priority hot: bg-#FF9900 text-#FFFFFF
- Badge priority warm: bg-#FFDD00 text-#000000
- Badge priority default: bg-#999999 text-#FFFFFF
- Badge status success: bg-#00AA00 text-#FFFFFF
- Badge status pending: bg-#FF9900 text-#FFFFFF
- Badge status error: bg-#FF0000 text-#FFFFFF
- Toggle enabled: !bg-#00AA00
- Toggle disabled: !bg-#E5E5E5
- Modal: border-2 border-#000000, bg-#FFFFFF, shadow-[4px_4px_0_0_#000000]
- AttemptTimeline dot: border-2 circle, color per status

---

## Dark Theme

### Colors
- Background: #0A0A0A
- Text Primary: #FFFFFF
- Text Secondary: #AAAAAA
- Border: #FFFFFF
- Card Background: #1A1A1A
- Secondary: #252525
- Status Success: #00DD00
- Status Pending: #FFAA33
- Status Error: #FF3333
- Priority Watchlist: #FF3333
- Priority Hot: #FFAA33
- Priority Warm: #FFDD77
- Priority Default: #666666

### Component States
- BRUTAL_PANEL: !rounded-none !border-2 !border-#FFFFFF !bg-#1A1A1A !shadow-[4px_4px_0_0_#FFFFFF]
- Table container: border-2 border-#FFFFFF, bg-#0A0A0A
- Table header: border-b-2 border-#FFFFFF, bg-#252525, font-weight bold
- Table row: border-b-1 border-#333333, bg-#1A1A1A, hover:bg-#252525
- Badge priority watchlist: bg-#FF3333 text-#FFFFFF
- Badge priority hot: bg-#FFAA33 text-#000000
- Badge priority warm: bg-#FFDD77 text-#000000
- Badge priority default: bg-#666666 text-#FFFFFF
- Badge status success: bg-#00DD00 text-#000000
- Badge status pending: bg-#FFAA33 text-#000000
- Badge status error: bg-#FF3333 text-#FFFFFF
- Toggle enabled: !bg-#00DD00
- Toggle disabled: !bg-#333333
- Modal: border-2 border-#FFFFFF, bg-#1A1A1A, shadow-[4px_4px_0_0_#FFFFFF]
- AttemptTimeline dot: border-2 circle, color per status
