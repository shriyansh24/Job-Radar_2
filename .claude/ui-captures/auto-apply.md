# Auto Apply

## Route
- Path: `/auto-apply`
- File: `src/pages/AutoApply.tsx`

## Figma Status
MISSING_FROM_FIGMA

## Layout Structure
- PageHeader (system): eyebrow "Execute", title "Auto Apply", profile/rule/pending meta chips, dynamic action button
- MetricStrip: Profiles, Active Rules, Runs, Success Rate
- Tabs: Profiles | Rules | Run History | Statistics
- Tab content (SplitWorkspace per tab):
  - **Profiles**: ProfileCard grid (lg:grid-cols-2) + active/coverage StateBlocks
  - **Rules**: RuleCard list with toggle + rule explanation StateBlocks
  - **History**: RunRow list (tabular) + success/failure StateBlocks
  - **Stats**: 4 stat tiles (sm:grid-cols-2) + queue health/conversion StateBlocks
- Modals: CreateProfileModal (6 fields + template), CreateRuleModal (name, score, keywords)

## Components Used
- System: `PageHeader`, `MetricStrip`, `SplitWorkspace`, `SectionHeader`, `StateBlock`, `Surface`
- UI: `Badge`, `Button`, `EmptyState`, `Input`, `Modal`, `SkeletonCard`, `Tabs`, `Textarea`
- Local: ProfileCard, RuleCard, RunRow, KeywordInput, CreateProfileModal, CreateRuleModal

## Data/Content Shape
- autoApplyApi: listProfiles, createProfile, listRules, createRule, updateRule, getStats, runs
- Profile: name, email, phone, linkedin_url, github_url, portfolio_url, cover_letter_template, is_active
- Rule: name, min_match_score, required_keywords[], excluded_keywords[], is_active
- Run: job_id, status, ats_provider, fields_filled, fields_missed, started_at, completed_at
- Stats: total_runs, successful, failed, pending

## Theme Variants
### Light Theme
- Background: surface-primary (white/near-white)
- Text: text-primary (dark gray/charcoal)
- Cards: bg-secondary with subtle shadow
- Active profile/rule: accent-primary-subtle highlight
- Modal: bg-secondary with border-2
- Buttons: Primary (accent-primary bg), Secondary (border-2)
- Hover states: slight elevation, opacity shift

### Dark Theme
- Background: surface-primary (near-black)
- Text: text-primary (light gray/white)
- Cards: bg-secondary (darker) with subtle shadow
- Active profile/rule: accent-primary-subtle highlight (adjusted)
- Modal: bg-secondary (darker) with border-2
- Buttons: Primary (accent-primary bg), Secondary (border-2 lighter)
- Hover states: slight elevation, opacity shift (lighter)
