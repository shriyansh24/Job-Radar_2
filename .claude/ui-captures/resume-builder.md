# Resume Builder

## Route
- Path: `/resume`
- File: `src/pages/ResumeBuilder.tsx`

## Figma Status
MISSING_FROM_FIGMA

## Layout Structure
- PageHeader (system): eyebrow "Prepare", title "Resume Builder"
- MetricStrip: Versions, Default set, Jobs loaded, Selection status
- Tabs: Upload | Versions | Tailor | AI Council
- Tab content (SplitWorkspace per tab):
  - **Upload**: Dropzone (border-2 border-dashed, drag active state) + StateBlocks
  - **Versions**: VersionCard grid (md:grid-cols-2) with preview modal
  - **Tailor**: Resume Select + Job Select + "Tailor Resume" button + TailorResultPanel (scores, bullets, experience, skills)
  - **Council**: Resume Select + "Get AI Evaluation" button + score display (text-5xl) + evaluation cards per model

## Components Used
- System: `PageHeader`, `MetricStrip`, `SplitWorkspace`, `SectionHeader`, `StateBlock`, `Surface`
- UI: `Badge`, `Button`, `EmptyState`, `Modal`, `Select`, `SkeletonCard`, `Tabs`
- react-dropzone for file upload
- Local: VersionCard, TailorResultPanel

## Data/Content Shape
- resumeApi: listVersions, upload(File), tailor(resumeId, jobId), council(resumeId)
- ResumeVersion: id, filename, is_default, parsed_text, created_at
- ResumeTailorResponse: summary, ats_score_before, ats_score_after, enhanced_bullets[], reordered_experience[], skills_section[], stage2_output
- Council: overall_score, evaluations[]{model, score, feedback}

## Theme Variants
### Light Theme
- Background: surface-primary (white/near-white)
- Text: text-primary (dark gray/charcoal)
- Dropzone: border-2 border-dashed border-secondary, hover: bg-tertiary
- Dropzone active: border-accent-primary bg-accent-primary-subtle
- Cards: bg-secondary with subtle shadow
- Select: bg-primary border-primary focus:border-accent-primary
- Buttons: Primary (accent-primary bg), Secondary (border-2)
- Score display: text-accent-primary text-5xl
- Evaluation cards: bg-secondary with border-l-4 accent-primary
- StateBlock: bg-tertiary text-secondary

### Dark Theme
- Background: surface-primary (near-black)
- Text: text-primary (light gray/white)
- Dropzone: border-2 border-dashed border-secondary (darker), hover: bg-tertiary
- Dropzone active: border-accent-primary bg-accent-primary-subtle (adjusted)
- Cards: bg-secondary (darker) with subtle shadow
- Select: bg-primary (darker) border-primary focus:border-accent-primary
- Buttons: Primary (accent-primary bg), Secondary (border-2 lighter)
- Score display: text-accent-primary text-5xl
- Evaluation cards: bg-secondary (darker) with border-l-4 accent-primary
- StateBlock: bg-tertiary (darker) text-secondary (lighter)
