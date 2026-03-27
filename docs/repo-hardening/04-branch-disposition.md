# Branch Disposition

## Purpose
Record the evidence-based disposition for retained branches before feature recovery or deletion decisions.

## Source-Of-Truth Status
- Status: `DOCUMENTED`
- Scope: branch forensics
- Last validation basis: `git` history plus GitHub PR metadata on `2026-03-27`

| Branch | Current Status | Unique Value | Disposition | Rationale |
|---|---|---|---|---|
| `main` | stable backend/P2 landing line, local branch behind `origin/main` by one commit | canonical baseline for merged backend and repo-hardening work before UI overhaul | `KEEP` | this is the repository baseline and default branch |
| `codex/ui-changes` | active branch | unique frontend overhaul, theme-family runtime, page decomposition, current UI docs/captures | `KEEP` | this is the live UI line |
| `feat/p1-core-value` | retained feature spike | unique P0/P1 capability work: deeper auto-apply wiring beyond the recovered extractor/adapter/safety slice, interview prep, resume tailoring/renderer/validator, hybrid search, worker slices, pipeline ergonomics | `PORT_SELECTIVELY` | high-value capability source, but stale and not safe to merge blindly |
| `origin/feat/p2-polish-advanced` | historical remote branch | strong provenance for P2 feature intent | `DEFER_AS_HISTORY` | current tip appears converged into `main`; use for traceability, not as a direct port source |
| `ui-overhaul-design` | local historical UI spike | early UI/docs experiments, grouped sidebar work, FilterChip, skeletons | `KEEP_AS_HISTORY` | not the chosen live UI line, but still useful as historical context until explicitly archived |
| `codex/career-os-overhaul` | earlier UI/UX milestone | pre-reference-first UI milestone and doc refresh | `KEEP_AS_MILESTONE` | useful as a waypoint, but not the main forward branch |

## P0 / P1 / P2 Evidence Leads

### P0
Evidence branch: `feat/p1-core-value` via PR #12
- ATS IDs and composite keys
- normalization
- resume IR/parser
- SQL pattern detector
- hybrid/local-first router foundations
- freshness scoring

### P1
Evidence branch: `feat/p1-core-value` via PR #13
- deeper auto-apply wiring beyond the recovered extractor, adapters, and safety slice
- interview prep
- resume tailoring, rendering, validation
- outcomes
- hybrid search
- digest and embedding backfill workers
- pipeline ergonomics

### P2
Evidence branch: `main` with historical provenance in `origin/feat/p2-polish-advanced` via PR #17
- analytics predictor / RAG
- email
- networking
- salary
- form learning
- resume archetypes / extra templates
- dedup feedback
- GPU acceleration

## Next Step
- Continue matrix-driven P1 recovery decisions without treating `feat/p1-core-value` as a merge candidate.
