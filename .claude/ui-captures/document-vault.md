# Document Vault

## Route
- Path: `/vault`
- File: `src/pages/DocumentVault.tsx`

## Figma Status: MISSING_FROM_FIGMA

## Layout Structure
- PageHeader (system, BRUTAL_PANEL): "Prepare" eyebrow + "Document Vault" h1 + badge "Organize your materials"
- MetricStrip (system, BRUTAL override): Resumes count, Cover letters count, Editor active, Upload status
- Tabs: "Resumes" / "Cover Letters"
- SplitWorkspace (xl:grid-cols-[1.25fr_0.95fr]):
  - Primary (space-y-6):
    - Resumes Tab:
      - FileDropzone (Surface padding="lg"):
        - Drag/drop zone with icon, "Drop resumes here or click to select"
        - Accept: .pdf, .docx, .doc, .txt
        - Upload progress overlay
      - SectionHeader: "Your Resumes"
      - ResumeCard grid (md:grid-cols-2 xl:grid-cols-3):
        - Card: filename, upload date, file size, is_default indicator
        - Actions: Preview button, Edit button, Delete button with confirm modal
      - EmptyState (if no resumes)
    - Cover Letters Tab:
      - FileDropzone (similar to Resumes)
      - SectionHeader: "Your Cover Letters"
      - CoverLetterCard grid (md:grid-cols-2 xl:grid-cols-3):
        - Card: filename, job context, created date
        - Actions: Preview button, Edit button, Delete button with confirm modal
      - EmptyState (if no cover letters)
  - Secondary (space-y-4):
    - StateBlock: "Resume best practices"
    - StateBlock: "Cover letter tips"
    - StateBlock: "Document management guide"

## Components Used
- System: `PageHeader`, `MetricStrip`, `SplitWorkspace`, `SectionHeader`, `StateBlock`, `Surface`
- UI: `Badge`, `Button`, `EmptyState`, `Input`, `Modal`, `Skeleton`, `Tabs`, `Textarea`
- Icons: Document, Eye, Pencil, Trash, UploadSimple, CheckCircle
- Local: `FileDropzone` (react-dropzone), `ResumeCard` (with preview/edit/delete), `CoverLetterCard` (with preview/edit/delete)
- Modal: Preview modal with PDF viewer, Edit modal with filename + content textarea

## Theme & Styling
- BRUTAL_PANEL: !rounded-none !border-2 !shadow-[4px_4px_0_0]
- BRUTAL_BUTTON: !rounded-none !border-2
- FileDropzone: dashed border-2 when idle, solid border-2 on hover/drag-over, success green on valid drop
- ResumeCard/CoverLetterCard: border-2, compact layout with action buttons
- Modal: BRUTAL_PANEL style, full-height for preview, textarea for edit
- Upload progress: indeterminate linear progress bar over dropzone

## Data/Content Shape
- vaultApi:
  - listResumes(): Promise<ResumeVersion[]>
  - uploadResume(file): Promise<ResumeVersion>
  - updateResume(id, parsed_text): Promise<ResumeVersion>
  - deleteResume(id): Promise<void>
  - setDefaultResume(id): Promise<void>
  - listCoverLetters(): Promise<CoverLetterResult[]>
  - uploadCoverLetter(file): Promise<CoverLetterResult>
  - updateCoverLetter(id, content): Promise<CoverLetterResult>
  - deleteCoverLetter(id): Promise<void>
- ResumeVersion: id, filename, parsed_text, file_size_bytes, is_default, created_at, updated_at
- CoverLetterResult: id, job_id, filename, content, created_at, updated_at

## Responsive Behavior
- Mobile (< 768px): Dropzone full-width, single-column card grid, modal full-screen
- Tablet (768px–1024px): SplitWorkspace visible, secondary narrower, grid-cols-2
- Desktop (≥ 1024px): Full SplitWorkspace, ResumeCard grid-cols-2, CoverLetterCard grid-cols-3
- Extra Large (≥ 1280px): Grid may expand to 4 columns with more spacing

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
- Accent Danger: #FF0000

### Component States
- BRUTAL_PANEL: !rounded-none !border-2 !border-#000000 !bg-#F8F8F8 !shadow-[4px_4px_0_0_#000000]
- BRUTAL_BUTTON: !rounded-none !border-2 !border-#000000 !bg-#F0F0F0 !text-#000000 hover:!bg-#E5E5E5
- BRUTAL_PRIMARY_BUTTON: !rounded-none !border-2 !border-#000000 !bg-#0066FF !text-#FFFFFF hover:!bg-#0052CC
- PageHeader: border-b-2 border-#000000, bg-#FFFFFF
- MetricStrip card: border-2 border-#000000, bg-#F8F8F8
- FileDropzone idle: border-2 dashed border-#E5E5E5, bg-#FFFFFF
- FileDropzone hover: border-2 dashed border-#000000, bg-#F8F8F8
- FileDropzone drop-valid: border-2 solid border-#00AA00, bg-#F0FFF0
- ResumeCard: border-2 border-#E5E5E5, bg-#FFFFFF, hover:border-#000000
- Badge is_default: bg-#0066FF text-#FFFFFF
- Danger button: border-#FF0000 bg-#FF0000 text-#FFFFFF
- Modal backdrop: bg-#000000/50

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
- Accent Danger: #FF3333

### Component States
- BRUTAL_PANEL: !rounded-none !border-2 !border-#FFFFFF !bg-#1A1A1A !shadow-[4px_4px_0_0_#FFFFFF]
- BRUTAL_BUTTON: !rounded-none !border-2 !border-#FFFFFF !bg-#252525 !text-#FFFFFF hover:!bg-#333333
- BRUTAL_PRIMARY_BUTTON: !rounded-none !border-2 !border-#FFFFFF !bg-#3399FF !text-#000000 hover:!bg-#2680CC
- PageHeader: border-b-2 border-#FFFFFF, bg-#0A0A0A
- MetricStrip card: border-2 border-#FFFFFF, bg-#1A1A1A
- FileDropzone idle: border-2 dashed border-#333333, bg-#0A0A0A
- FileDropzone hover: border-2 dashed border-#FFFFFF, bg-#1A1A1A
- FileDropzone drop-valid: border-2 solid border-#00DD00, bg-#0A2A0A
- ResumeCard: border-2 border-#333333, bg-#1A1A1A, hover:border-#FFFFFF
- Badge is_default: bg-#3399FF text-#000000
- Danger button: border-#FF3333 bg-#FF3333 text-#FFFFFF
- Modal backdrop: bg-#FFFFFF/10
