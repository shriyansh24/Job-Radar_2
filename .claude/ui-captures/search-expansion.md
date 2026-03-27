# Search Expansion

## Route: `/search-expansion` — File: `src/pages/SearchExpansion.tsx`

## Figma Status: MISSING_FROM_FIGMA

## Layout
- **PageHeader**: "Operations" breadcrumb, title "Search Expansion"
- **MetricStrip**: Recent runs count, Expanded terms count, Synonyms count, Engine state badge
- **SplitWorkspace**:
  - **Primary Surface**: SectionHeader + query Input + "Expand query" Button + suggested query chips + results display (expanded terms as Badges, synonyms as Badges, related titles list)
  - **Secondary**: History list (Surface cards with clickable past queries) + guidance StateBlock

## Components
- System: PageHeader, MetricStrip, SplitWorkspace, SectionHeader, StateBlock, Surface
- UI: Badge, Button, EmptyState, Input, Skeleton
- Local: QueryChip (hard-press border-2 mono button)
- Icons: Lightning, MagnifyingGlassPlus, Sparkle, TerminalWindow

## Data
- `searchExpansionApi.expand(query)` — returns:
  ```typescript
  {
    expanded_terms: string[]
    synonyms: string[]
    related_titles: string[]
  }
  ```
- Session history stored in local state (useRef or sessionStorage)

## Behavior
1. User enters search term in Input, clicks "Expand query"
2. API returns expanded terms, synonyms, related job titles
3. Display results as Badge rows + title list
4. Track history in sidebar for quick re-run
5. StateBlock shows guidance: "Expansion uses semantic similarity to find related search terms and job titles"

## Theme Colors

| Element | Light | Dark |
|---------|-------|------|
| PageHeader bg | #FFFFFF | #0A0A0A |
| MetricStrip bg | #F5F5F5 | #1A1A1A |
| Input bg | #FFFFFF | #1A1A1A |
| Input border | #E5E7EB | #404040 |
| Badge (term) | #3B82F6 | #60A5FA |
| Badge (synonym) | #8B5CF6 | #A78BFA |
| Button primary | #000000 | #FFFFFF |
| Icon color | #6366F1 | #818CF8 |
| History card | #F5F5F5 | #1A1A1A |
| StateBlock bg | #EFF6FF | #1E3A8A |
