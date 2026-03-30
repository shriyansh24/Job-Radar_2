# Email Signals

## Route
- Path: `/email`
- File: `src/pages/Email.tsx`

## Figma Status
MISSING_FROM_FIGMA

## Layout Structure
- Custom hero section (PANEL):
  - Left: "Execute / Signals" eyebrow + "Email Signals" h1 + description + 3 HeroPill (Status/Window/Desk)
  - Right: 3 MetricCard tiles (Processed, Actionable, Avg confidence)
- Two-column grid (xl:grid-cols-[0.95fr_1.05fr]):
  - Left: Signal log (PANEL, scrollable max-h-[72vh])
    - Header: search Input + action filter Select
    - Log entries (selectable buttons): subject, sender, action Badge, company, timestamp, confidence
  - Right (space-y-6):
    - Selected log detail (PANEL): subject, sender, detected action, confidence, matched application, company, job title
    - Replay a signal (PANEL): sender, from, subject inputs + body Textarea + "Process signal" button + result display
    - Operating notes (PANEL_ALT): 3 guidance paragraphs

## Components Used
- UI: `Badge`, `Button`, `EmptyState`, `Input`, `Select`, `Skeleton`, `Textarea`
- Local: MetricCard, HeroPill
- Icons: ArrowClockwise, Buildings, CheckCircle, EnvelopeSimple, Funnel, MagnifyingGlass, Sparkle

## Data/Content Shape
- emailApi: listLogs(limit), processWebhook(payload)
- EmailLog: id, sender, subject, parsed_action, confidence, company_extracted, job_title_extracted, matched_application_id, processed_at
- EmailWebhookPayload: sender, from_, to, subject, text, html
- Filter options: all, interview, rejection, offer, follow_up, unknown

## Theme Variants
### Light Theme
- Hero: bg-secondary with text-primary
- Metric cards: bg-secondary border-2
- Panels (PANEL): border-2 bg-secondary shadow-[4px_4px_0_0]
- Selected log entry: bg-accent-primary-subtle with accent-primary border
- Log list: divide-y-2 divide-secondary
- Action badges: color-coded (interview=blue, rejection=red, offer=green, follow_up=yellow, unknown=gray)
- Inputs/selects: bg-primary border-primary focus:border-accent-primary
- HeroPill: bg-tertiary text-secondary

### Dark Theme
- Hero: bg-secondary (darker) with text-primary (lighter)
- Metric cards: bg-secondary (darker) border-2
- Panels (PANEL): border-2 bg-secondary (darker) shadow-[4px_4px_0_0]
- Selected log entry: bg-accent-primary-subtle (adjusted) with accent-primary border
- Log list: divide-y-2 divide-secondary (darker)
- Action badges: color-coded dark variants
- Inputs/selects: bg-primary (darker) border-primary focus:border-accent-primary
- HeroPill: bg-tertiary (darker) text-secondary (lighter)
