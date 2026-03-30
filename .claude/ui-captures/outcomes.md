# Outcomes

## Route
- Path: `/outcomes`
- File: `src/pages/Outcomes.tsx`

## Figma Status: MISSING_FROM_FIGMA

## Layout Structure
- Hero section (space-y-4, pb-6):
  - Custom hero panel (HERO_PANEL style):
    - Left: "Intelligence / Outcomes" eyebrow + "Track outcomes" h1 + description
    - Right: 3 chips (Intelligence, Application outcomes, Company patterns)
  - 3 SummaryTiles grid (sm:grid-cols-3):
    - Response Rate %, Ghost Rate %, Avg Offer amount
- TwoColumn layout (xl:grid-cols-[1.25fr_0.95fr], space-y-6):
  - Primary (space-y-6):
    - OutcomeCaptureForm (Surface padding="lg"):
      - Select: Application (job title, company, recent suggestions)
      - Select: Stage reached (applied, phone_screen, technical, onsite, offer, rejected)
      - ConditionalFields (based on stage):
        - If offer: Input offer_amount, Input equity%, Input total_comp
        - If rejected: Select rejection_reason, Input days_to_response
      - Input: Days to response
      - Toggle: Was ghosted?
      - Toggle: Referral used?
      - Toggle: Cover letter used?
      - Select: Application method (website, recruiter, referral, other)
      - Textarea: Feedback notes
      - Button: "Save Outcome"
    - SectionHeader: "Outcome Intelligence"
    - IntelligencePanel (Surface padding="md"):
      - "Stage distribution" chart (horizontal bar, color-coded per stage)
      - "Top rejection reasons" list (sorted by frequency)
    - CompanyInsightLookup (Surface padding="lg"):
      - Input: Company search (autocomplete)
      - Button: "Look up company"
    - CompanyMetricGrid (if lookup result):
      - Total applications count
      - Callback rate %
      - Ghost rate %
      - Offer rate %
      - Avg response days
      - Culture notes textarea (editable)
  - Secondary (space-y-4):
    - StateBlock: "Outcome tracking guide"
    - StateBlock: "Company insights explained"
    - StateBlock: "Negotiation best practices"

## Components Used
- System: `Surface`, `SectionHeader`, `StateBlock`, `HERO_PANEL`, `INSET_PANEL`, `CHIP`, `BUTTON_BASE`
- UI: `Badge`, `Button`, `EmptyState`, `Input`, `Select`, `Skeleton`, `Textarea`, `Toggle`
- Icons: BookmarkedSimple, CheckCircle, TrendingUp, WarningCircle, User, Building
- Local: `SummaryTile` (metric card), `ToggleChip` (toggle state display), `CompanyMetric` (stat card)

## Theme & Styling
- HERO_PANEL: !rounded-none !border-2 !shadow-[4px_4px_0_0], lg:grid-cols side-by-side
- SummaryTile: border-2, centered metric + label, color-coded by type
- ToggleChip: button-like toggle with active state highlight
- CompanyMetricGrid: 3-column grid on desktop, 2-column on tablet, 1-column on mobile
- Stage distribution chart: stacked horizontal bars, legend below
- OutcomeCaptureForm: form-grid with space-y-4

## Data/Content Shape
- outcomesApi:
  - getOutcome(id): Promise<OutcomeRecord>
  - createOutcome(payload): Promise<OutcomeRecord>
  - updateOutcome(id, payload): Promise<OutcomeRecord>
  - listOutcomes(limit, offset): Promise<OutcomeRecord[]>
  - getStats(): Promise<OutcomeStats>
  - getCompanyInsights(company_name): Promise<CompanyInsight>
  - updateCompanyNotes(company_name, notes): Promise<void>
- OutcomeRecord: application_id, stage_reached (applied|phone_screen|technical|onsite|offer|rejected), rejection_reason?, rejection_stage?, days_to_response, offer_amount?, equity_percent?, total_comp?, negotiated_amount?, final_decision, was_ghosted, referral_used, cover_letter_used, application_method, feedback_notes, created_at, updated_at
- OutcomeStats: response_rate (0–1), ghosting_rate (0–1), avg_offer_amount, stage_distribution{}, top_rejection_reasons[]
- CompanyInsight: company_name, total_applications, callback_count, ghost_rate (0–1), offer_rate (0–1), avg_response_days, culture_notes

## Responsive Behavior
- Mobile (< 768px): Hero stacked, SummaryTiles single-column, form full-width, CompanyMetricGrid grid-cols-1
- Tablet (768px–1024px): Hero side-by-side, SummaryTiles grid-cols-3, form cols-1, CompanyMetricGrid grid-cols-2
- Desktop (≥ 1024px): Full TwoColumn with primary/secondary, form inline elements, CompanyMetricGrid grid-cols-3
- Extra Large (≥ 1280px): Enhanced form spacing, wider metrics display

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
- HERO_PANEL: !rounded-none !border-2 !border-#000000 !bg-#F8F8F8 !shadow-[4px_4px_0_0_#000000]
- CHIP: !rounded-none !border-2 !border-#000000 !bg-#F0F0F0 !text-#000000
- BUTTON_BASE: !rounded-none !border-2 !border-#000000 !bg-#F0F0F0 hover:!bg-#E5E5E5
- SummaryTile: border-2 border-#000000, bg-#FFFFFF
- SummaryTile value (Response Rate): text-#00AA00, bold
- SummaryTile value (Ghost Rate): text-#FF0000, bold
- SummaryTile value (Avg Offer): text-#0066FF, bold
- Toggle active: !bg-#0066FF !text-#FFFFFF
- Toggle inactive: !bg-#F0F0F0 !text-#000000
- OutcomeCaptureForm Surface: bg-#FFFFFF, border-2 border-#000000
- Select: border-2 border-#000000, bg-#FFFFFF
- IntelligencePanel chart: stage colors (applied #0066FF, phone_screen #3399FF, technical #00AA00, onsite #FF9900, offer #00AA00, rejected #FF0000)
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
- Accent Primary: #3399FF
- Accent Success: #00DD00
- Accent Warning: #FFAA33
- Accent Danger: #FF3333

### Component States
- HERO_PANEL: !rounded-none !border-2 !border-#FFFFFF !bg-#1A1A1A !shadow-[4px_4px_0_0_#FFFFFF]
- CHIP: !rounded-none !border-2 !border-#FFFFFF !bg-#252525 !text-#FFFFFF
- BUTTON_BASE: !rounded-none !border-2 !border-#FFFFFF !bg-#252525 hover:!bg-#333333
- SummaryTile: border-2 border-#FFFFFF, bg-#1A1A1A
- SummaryTile value (Response Rate): text-#00DD00, bold
- SummaryTile value (Ghost Rate): text-#FF3333, bold
- SummaryTile value (Avg Offer): text-#3399FF, bold
- Toggle active: !bg-#3399FF !text-#000000
- Toggle inactive: !bg-#252525 !text-#FFFFFF
- OutcomeCaptureForm Surface: bg-#1A1A1A, border-2 border-#FFFFFF
- Select: border-2 border-#FFFFFF, bg-#1A1A1A
- IntelligencePanel chart: stage colors (applied #3399FF, phone_screen #5DADE2, technical #00DD00, onsite #FFAA33, offer #00DD00, rejected #FF3333)
- StateBlock: border-2 border-#333333, bg-#252525
