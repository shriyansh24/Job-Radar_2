# Salary Insights

## Route
- Path: `/salary`
- File: `src/pages/SalaryInsights.tsx`

## Figma Status: MISSING_FROM_FIGMA

## Layout Structure
- PageHeader (system, BRUTAL_PANEL): "Prepare" eyebrow + "Salary Insights" h1 + badges "Market percentiles" "Offer coaching"
- MetricStrip (system, BRUTAL override): Saved research count, Median salary, Counter offer amount, Company set count
- SplitWorkspace (xl:grid-cols-[1.25fr_0.95fr]):
  - Primary (space-y-6):
    - ResearchForm (Surface padding="lg"):
      - Input: Job title (searchable, recent suggestions)
      - Input: Company name (optional)
      - Input: Location (city, searchable)
      - Button: "Research Salary"
    - SectionHeader: "Salary Range"
    - RangeView (Surface padding="md"):
      - SalaryRangeBar (horizontal percentile visualization):
        - P25 marker label, P50 label, P75 label, P90 label
        - Competing companies list below
      - YOE brackets expansion (collapsible)
    - OfferEvaluationForm (Surface padding="lg"):
      - Input: Offer amount
      - Input: Company name (auto-fill from research)
      - Button: "Evaluate Offer"
    - VerdictDisplay (if offer evaluated):
      - Assessment badge (strong, competitive, below-market)
      - Counter offer amount
      - Walkaway point
      - Talking points list (bulleted)
      - Negotiation script textarea
  - Secondary (space-y-4):
    - SectionHeader: "Saved Research"
    - SavedResearchCard list (clickable to reload):
      - Company, job title, location, median
    - StateBlock: "Salary negotiation tips"
    - StateBlock: "Market insights"

## Components Used
- System: `PageHeader`, `MetricStrip`, `SplitWorkspace`, `SectionHeader`, `StateBlock`, `Surface`
- UI: `Badge`, `Button`, `EmptyState`, `Input`, `Skeleton`, `Textarea`
- Icons: ChartBar, CurrencyDollar, TrendingUp, Wallet, Warning
- Local: `SalaryRangeBar` (percentile visualization), `VerdictDisplay` (assessment + negotiation guidance)

## Theme & Styling
- BRUTAL_PANEL: !rounded-none !border-2 !shadow-[4px_4px_0_0]
- BRUTAL_BUTTON: !rounded-none !border-2
- SalaryRangeBar: horizontal bar with percentage markers, color-coded regions (below-market red, competitive green, above-market blue)
- VerdictDisplay: colored badge + monospace font for script
- MetricStrip overrides BRUTAL for currency display

## Data/Content Shape
- salaryApi:
  - research(job_title, company_name?, location): Promise<SalaryResearch>
  - evaluateOffer(job_title, offered_salary, company_name, location): Promise<OfferEvaluation>
  - listSavedResearch(): Promise<SalaryResearch[]>
  - saveSalaryResearch(research): Promise<void>
- SalaryResearch: p25, p50, p75, p90, currency, cached_at, competing_companies[], yoe_brackets[]
- OfferEvaluation: assessment (strong|competitive|below_market), counter_offer, walkaway_point, talking_points[], negotiation_script

## Responsive Behavior
- Mobile (< 768px): Stack form and range vertically, single-column cards, SalaryRangeBar scales to viewport
- Tablet (768px–1024px): SplitWorkspace visible, secondary narrower, ResearchForm cols-1
- Desktop (≥ 1024px): Full SplitWorkspace, ResearchForm inline 3-column layout, SalaryRangeBar full width
- Extra Large (≥ 1280px): Enhanced spacing on form elements

---

## Light Theme

### Colors
- Background: #FFFFFF
- Text Primary: #000000
- Text Secondary: #666666
- Border: #000000
- Card Background: #F8F8F8
- Secondary: #F0F0F0
- Accent Primary: #0066FF
- Accent Success: #00AA00
- Accent Warning: #FF9900
- Accent Danger: #FF0000

### Component States
- BRUTAL_PANEL: !rounded-none !border-2 !border-#000000 !bg-#F8F8F8 !shadow-[4px_4px_0_0_#000000]
- BRUTAL_BUTTON: !rounded-none !border-2 !border-#000000 !bg-#F0F0F0 !text-#000000 hover:!bg-#E5E5E5
- BRUTAL_PRIMARY_BUTTON: !rounded-none !border-2 !border-#000000 !bg-#0066FF !text-#FFFFFF hover:!bg-#0052CC
- PageHeader: border-b-2 border-#000000, bg-#FFFFFF
- MetricStrip card: border-2 border-#000000, bg-#F8F8F8
- Badge assessment: bg-#00AA00 (strong), bg-#0066FF (competitive), bg-#FF0000 (below-market)
- SalaryRangeBar: gradient regions, p50 marker bold
- Input: border-2 border-#000000, bg-#FFFFFF
- SavedResearchCard: border-2 border-#E5E5E5, bg-#F8F8F8, hover:bg-#E5E5E5
- StateBlock: border-2 border-#E5E5E5, bg-#F0F0F0, text-#666666

---

## Dark Theme

### Colors
- Background: #0A0A0A
- Text Primary: #FFFFFF
- Text Secondary: #AAAAAA
- Border: #FFFFFF
- Card Background: #1A1A1A
- Secondary: #252525
- Accent Primary: #3399FF
- Accent Success: #00DD00
- Accent Warning: #FFAA33
- Accent Danger: #FF3333

### Component States
- BRUTAL_PANEL: !rounded-none !border-2 !border-#FFFFFF !bg-#1A1A1A !shadow-[4px_4px_0_0_#FFFFFF]
- BRUTAL_BUTTON: !rounded-none !border-2 !border-#FFFFFF !bg-#252525 !text-#FFFFFF hover:!bg-#333333
- BRUTAL_PRIMARY_BUTTON: !rounded-none !border-2 !border-#FFFFFF !bg-#3399FF !text-#000000 hover:!bg-#2680CC
- PageHeader: border-b-2 border-#FFFFFF, bg-#0A0A0A
- MetricStrip card: border-2 border-#FFFFFF, bg-#1A1A1A
- Badge assessment: bg-#00DD00 (strong), bg-#3399FF (competitive), bg-#FF3333 (below-market)
- SalaryRangeBar: dark gradient regions, p50 marker bright
- Input: border-2 border-#FFFFFF, bg-#1A1A1A
- SavedResearchCard: border-2 border-#333333, bg-#1A1A1A, hover:bg-#252525
- StateBlock: border-2 border-#333333, bg-#252525, text-#AAAAAA
