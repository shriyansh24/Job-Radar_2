# Profile

## Route
- Path: `/profile`
- File: `src/pages/Profile.tsx`

## Figma Status: MISSING_FROM_FIGMA

## Layout Structure
- Custom hero section (BRUTAL_PANEL_ALT):
  - Left: "Prepare / Profile" eyebrow + "Profile ledger" h1 + description
  - Right: Signed in panel (user email, sign-out button)
  - Right: Source panels (LinkedIn connected, GitHub connected)
- PageHeader (system, BRUTAL_PANEL): "Profile" title + "Generate answers" button + "Save profile" button
- MetricStrip (system, BRUTAL override): Search seeds count, Watchlist companies, Education count, Experience count
- SplitWorkspace (xl:grid-cols-[1.25fr_0.95fr]):
  - Primary (space-y-6):
    - 6 SettingsSection panels:
      1. Identity (8 fields):
         - Input: Full name
         - Input: Phone number
         - Input: Location (city, searchable)
         - Input: LinkedIn URL
         - Input: GitHub URL
         - Input: Portfolio URL
         - Select: Work authorization (eligible, sponsorship_required, not_authorized)
         - Input: Additional identity field
      2. Preferences:
         - ToggleGroup: Preferred job types (full_time, part_time, contract, freelance)
         - ToggleGroup: Preferred remote types (on_site, hybrid, remote)
         - Range slider: Salary min–max
      3. Search seeds (TagEditor):
         - TagEditor (input + add button + chip list):
           - Pre-populated search terms
           - Add/remove functionality
      4. Education (EntryCard list):
         - SectionHeader: "Education"
         - Button: "Add education"
         - EntryCard list (removable):
           - School name, degree, field, graduation year
      5. Experience (EntryCard list):
         - SectionHeader: "Experience"
         - Button: "Add experience"
         - EntryCard list (removable):
           - Company, position, duration, description
      6. Answer bank:
         - SectionHeader: "Answer bank"
         - Button: "Generate answers"
         - Q&A cards (editable textarea, save per answer)
  - Secondary (space-y-4):
    - StateBlock: "Profile usage: applied X times with this profile"
    - StateBlock: "Workspace summary: Y applications, Z outcomes"
    - StateBlock: "Readiness check: X/10 profile completeness"

## Components Used
- System: `PageHeader`, `MetricStrip`, `SettingsSection`, `SplitWorkspace`, `StateBlock`, `Surface`
- UI: `Badge`, `Button`, `Input`, `Select`, `Skeleton`, `Textarea`, `Toggle`
- Icons: CheckCircle, Copy, LinkedinLogo, GithubLogo, Globe, Briefcase, School, X
- Local: `ToggleGroup` (multi-select button group), `TagEditor` (input + add + chip list), `EntryCard` (removable nested form)

## Theme & Styling
- BRUTAL_PANEL_ALT: custom hero with inverted colors
- BRUTAL_PANEL: PageHeader override with neo-brutalist border/shadow
- BRUTAL_FIELD: !rounded-none !border-2 inputs throughout
- SettingsSection: bordered panel with section header + toggle/input fields
- TagEditor chip: inline badge-style, X icon to remove
- EntryCard: collapsible/expandable form section with nested inputs
- ToggleGroup: button-style toggle set with active state

## Data/Content Shape
- profileApi:
  - getProfile(): Promise<UserProfile>
  - updateProfile(payload): Promise<UserProfile>
  - generateAnswers(): Promise<AnswerBank>
- UserProfile: full_name, phone, location, linkedin_url, github_url, portfolio_url, work_authorization, preferred_job_types[], preferred_remote_types[], salary_min, salary_max, education[], work_experience[], search_queries[], search_locations[], watchlist_companies[], answer_bank{}, created_at, updated_at
- EducationEntry: school_name, degree, field_of_study, graduation_year
- WorkExperienceEntry: company_name, position, start_date, end_date, description
- AnswerBank: {[question_id]: answer_text}

## Responsive Behavior
- Mobile (< 768px): Hero stacked, MetricStrip single-column, SettingsSection full-width, EntryCard collapsed
- Tablet (768px–1024px): Hero side-by-side, MetricStrip 2-column, SettingsSection expandable
- Desktop (≥ 1024px): Full SplitWorkspace, all SettingsSection visible, TwoColumn metrics
- Extra Large (≥ 1280px): Enhanced form spacing, wider input fields

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
- BRUTAL_PANEL_ALT: !rounded-none !border-2 !border-#000000 !bg-#F0F0F0 !shadow-[4px_4px_0_0_#000000]
- BRUTAL_PANEL: !rounded-none !border-2 !border-#000000 !bg-#F8F8F8 !shadow-[4px_4px_0_0_#000000]
- BRUTAL_FIELD: !rounded-none !border-2 !border-#000000 !bg-#FFFFFF !text-#000000 focus:!border-#0066FF
- PageHeader: border-b-2 border-#000000, bg-#FFFFFF
- MetricStrip card: border-2 border-#000000, bg-#F8F8F8
- SettingsSection: border-2 border-#E5E5E5, bg-#FFFFFF, header border-b-2 border-#000000
- ToggleGroup button active: !bg-#0066FF !text-#FFFFFF
- ToggleGroup button inactive: !bg-#F0F0F0 !text-#000000
- TagEditor chip: bg-#0066FF text-#FFFFFF, hover:bg-#0052CC
- EntryCard: border-2 border-#E5E5E5, bg-#F8F8F8
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

### Component States
- BRUTAL_PANEL_ALT: !rounded-none !border-2 !border-#FFFFFF !bg-#252525 !shadow-[4px_4px_0_0_#FFFFFF]
- BRUTAL_PANEL: !rounded-none !border-2 !border-#FFFFFF !bg-#1A1A1A !shadow-[4px_4px_0_0_#FFFFFF]
- BRUTAL_FIELD: !rounded-none !border-2 !border-#FFFFFF !bg-#1A1A1A !text-#FFFFFF focus:!border-#3399FF
- PageHeader: border-b-2 border-#FFFFFF, bg-#0A0A0A
- MetricStrip card: border-2 border-#FFFFFF, bg-#1A1A1A
- SettingsSection: border-2 border-#333333, bg-#1A1A1A, header border-b-2 border-#FFFFFF
- ToggleGroup button active: !bg-#3399FF !text-#000000
- ToggleGroup button inactive: !bg-#252525 !text-#FFFFFF
- TagEditor chip: bg-#3399FF text-#000000, hover:bg-#2680CC
- EntryCard: border-2 border-#333333, bg-#252525
- StateBlock: border-2 border-#333333, bg-#252525
