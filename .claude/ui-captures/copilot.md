# Copilot

## Route
- Path: `/copilot`
- File: `src/pages/Copilot.tsx`

## Figma Status: IN_FIGMA

## Layout Structure
- Container (space-y-6, no outer padding — uses system components)
  - PageHeader (system): eyebrow "Prepare", title "Copilot", badges (Context-aware chat, Ask history, Cover letters)
  - MetricStrip (system): Recent Context, Transcript, Mode, Letter status
  - Tabs Surface: 3 tabs (Assistant, History, Letters)
  - Tab content (SplitWorkspace per tab):
    - **Assistant tab**:
      - Primary: Job context Select + transcript (message bubbles) + prompt starters + Textarea + Send button
      - Secondary: Active job context StateBlock + Job snapshot Surface
    - **History tab**:
      - Primary: Textarea for question + "Analyze history" button + answer display area
      - Secondary: Prompt starters (3 buttons) + use case StateBlock
    - **Letters tab**:
      - Primary: Job Select + Style Select + Template Textarea + "Generate draft" button + draft display
      - Secondary: Draft status StateBlock + Selected job StateBlock

## Components Used
- System: `PageHeader`, `MetricStrip`, `SplitWorkspace`, `SectionHeader`, `StateBlock`, `Surface`
- UI: `Badge`, `Button`, `EmptyState`, `Select`, `Skeleton`, `Tabs`, `Textarea`
- `ReactMarkdown` with `remark-gfm` for assistant responses
- `MarkdownBlock` (local): prose styling for markdown content
- Icons: Brain, Briefcase, ClockCounterClockwise, FileText, Lightbulb, MagicWand, Sparkle

## Theme & Styling
- Uses system components (Surface, StateBlock) with default theming
- Chat bubbles: assistant = border-border bg-tertiary, user = ml-auto border-border bg-accent-primary/10
- Prompt starters: border-2 bg-tertiary px-3 py-2 mono text-[10px] uppercase, hover:bg-card
- Markdown prose: prose-sm, prose-p:text-text-secondary, prose-headings:text-text-primary

## Data/Content Shape
- copilotApi.chat(message, jobContext, jobId): {response: string}
- copilotApi.askHistory(question): {answer: string}
- copilotApi.generateCoverLetter(jobId, style, template): CoverLetterResult
- TranscriptEntry: {id, role: user|assistant, content, label}
- Letter styles: professional, startup, technical, career-change

## Responsive Behavior
- SplitWorkspace handles responsive stacking
- Tab content fills available space
- Prompt starters wrap with flex-wrap

---

## Light Theme

### Colors
- Background: #FFFFFF
- Text Primary: #000000
- Text Secondary: #666666
- Border: #E5E5E5
- Card Background: #F8F8F8
- Tertiary: #F0F0F0
- Accent Primary: #0066FF
- Accent Secondary: #E8F0FF

### Component States
- PageHeader: border-2 border-#000000, bg-#F8F8F8
- Surface: border-2 border-#E5E5E5, bg-#FFFFFF
- StateBlock: border-border, bg-tertiary, text-text-secondary
- Chat bubble (Assistant): border-2 border-#E5E5E5, bg-#F0F0F0
- Chat bubble (User): border-2 border-#0066FF, bg-#E8F0FF, ml-auto
- Prompt starter: border-2 border-#000000, bg-#F0F0F0, hover:bg-#E5E5E5
- Tab active: border-b-2 border-#0066FF
- Select: border-2 border-#000000, bg-#FFFFFF
- Textarea: border-2 border-#000000, bg-#FFFFFF, focus:border-#0066FF

---

## Dark Theme

### Colors
- Background: #0A0A0A
- Text Primary: #FFFFFF
- Text Secondary: #AAAAAA
- Border: #333333
- Card Background: #1A1A1A
- Tertiary: #252525
- Accent Primary: #3399FF
- Accent Secondary: #1A4D80

### Component States
- PageHeader: border-2 border-#FFFFFF, bg-#1A1A1A
- Surface: border-2 border-#333333, bg-#1A1A1A
- StateBlock: border-border, bg-tertiary, text-text-secondary
- Chat bubble (Assistant): border-2 border-#333333, bg-#252525
- Chat bubble (User): border-2 border-#3399FF, bg-#1A4D80, ml-auto
- Prompt starter: border-2 border-#AAAAAA, bg-#252525, hover:bg-#333333
- Tab active: border-b-2 border-#3399FF
- Select: border-2 border-#FFFFFF, bg-#1A1A1A
- Textarea: border-2 border-#FFFFFF, bg-#1A1A1A, focus:border-#3399FF
