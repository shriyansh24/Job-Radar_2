# Interview Prep

## Route
- Path: `/interview`
- File: `src/pages/InterviewPrep.tsx`

## Figma Status: MISSING_FROM_FIGMA

## Layout Structure
- PageHeader (system, BRUTAL_PANEL): "Prepare" eyebrow + "Interview Prep" h1 + badge "Ace your interviews"
- MetricStrip (system, BRUTAL override): Sessions count, Active session, Latest score %, Mode
- Tabs: "Practice" / "History"
- SplitWorkspace (xl:grid-cols-[1.25fr_0.95fr]):
  - Primary (space-y-6):
    - Practice Tab:
      - GenerateForm (Surface padding="lg"):
        - Select: Job title (searchable, multi-job tracking)
        - CheckboxGroup: Question types (behavioral, technical, system_design, culture_fit)
        - Select: Count (5, 10, 15, 20)
        - Button: "Generate Session"
      - SectionHeader: "Questions"
      - QuestionCard accordion list:
        - Question text + category Badge + difficulty Badge
        - (expanded) Answer textarea + Evaluate button
    - History Tab:
      - SectionHeader: "Session History"
      - SessionHistoryCard grid (md:grid-cols-2):
        - Card: Session date, questions answered, overall_score %
        - Status Badge (completed, in_progress)
        - Click to replay
  - Secondary (space-y-4):
    - StateBlock: "Practice guidance"
    - StateBlock: "Interview tips by difficulty"
    - StateBlock: "Your progress tracking"

## Components Used
- System: `PageHeader`, `MetricStrip`, `SplitWorkspace`, `SectionHeader`, `StateBlock`, `Surface`
- UI: `Badge`, `Button`, `Checkbox`, `EmptyState`, `Select`, `Skeleton`, `Tabs`, `Textarea`
- Icons: Brain, CheckCircle, Clock, Lightning, TrendingUp
- Local: `GenerateForm`, `QuestionCard` (expandable), `SessionHistoryCard`

## Theme & Styling
- BRUTAL_PANEL: !rounded-none !border-2 !shadow-[4px_4px_0_0]
- BRUTAL_BUTTON: !rounded-none !border-2 !shadow-none
- GenerateForm: Surface with form grid (space-y-4)
- QuestionCard: border-2, expandable with smooth height transition
- MetricStrip overrides BRUTAL for high contrast

## Data/Content Shape
- interviewApi:
  - generate(job_id, question_types[], count): Promise<InterviewSession>
  - listSessions(limit): Promise<InterviewSession[]>
  - getSession(sessionId): Promise<InterviewSession>
  - evaluate(session_id, question_id, answer): Promise<QuestionScore>
- InterviewSession: id, job_id, created_at, questions[], scores[], overall_score (0–100), mode (timed|untimed), status (in_progress|completed)
- InterviewQuestion: id, question, category, type (behavioral|technical|system_design|culture_fit), difficulty (easy|medium|hard), suggested_answer
- QuestionScore: question_id, score (0–100), feedback, timestamp

## Responsive Behavior
- Mobile (< 768px): Stack tabs vertically, single-column card layout, GenerateForm full-width
- Tablet (768px–1024px): SplitWorkspace visible but secondary narrower, SessionHistoryCard grid-cols-1
- Desktop (≥ 1024px): Full SplitWorkspace, MetricStrip 4-column horizontal, SessionHistoryCard grid-cols-2
- Extra Large (≥ 1280px): MetricStrip may expand if additional metrics added

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

### Component States
- BRUTAL_PANEL: !rounded-none !border-2 !border-#000000 !bg-#F8F8F8 !shadow-[4px_4px_0_0_#000000]
- BRUTAL_BUTTON: !rounded-none !border-2 !border-#000000 !bg-#F0F0F0 !text-#000000 hover:!bg-#E5E5E5
- BRUTAL_PRIMARY_BUTTON: !rounded-none !border-2 !border-#000000 !bg-#0066FF !text-#FFFFFF hover:!bg-#0052CC
- PageHeader: border-b-2 border-#000000, bg-#FFFFFF
- MetricStrip card: border-2 border-#000000, bg-#F8F8F8
- Badge: bg-#0066FF text-#FFFFFF (primary), bg-#F0F0F0 text-#000000 (secondary)
- QuestionCard: border-2 border-#000000, bg-#FFFFFF, hover:bg-#F8F8F8
- SessionHistoryCard: border-2 border-#E5E5E5, bg-#F8F8F8
- StateBlock: border-2 border-#E5E5E5, bg-#F0F0F0, text-#666666
- Textarea: border-2 border-#000000, bg-#FFFFFF

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

### Component States
- BRUTAL_PANEL: !rounded-none !border-2 !border-#FFFFFF !bg-#1A1A1A !shadow-[4px_4px_0_0_#FFFFFF]
- BRUTAL_BUTTON: !rounded-none !border-2 !border-#FFFFFF !bg-#252525 !text-#FFFFFF hover:!bg-#333333
- BRUTAL_PRIMARY_BUTTON: !rounded-none !border-2 !border-#FFFFFF !bg-#3399FF !text-#000000 hover:!bg-#2680CC
- PageHeader: border-b-2 border-#FFFFFF, bg-#0A0A0A
- MetricStrip card: border-2 border-#FFFFFF, bg-#1A1A1A
- Badge: bg-#3399FF text-#000000 (primary), bg-#252525 text-#FFFFFF (secondary)
- QuestionCard: border-2 border-#FFFFFF, bg-#1A1A1A, hover:bg-#252525
- SessionHistoryCard: border-2 border-#333333, bg-#1A1A1A
- StateBlock: border-2 border-#333333, bg-#252525, text-#AAAAAA
- Textarea: border-2 border-#FFFFFF, bg-#1A1A1A
