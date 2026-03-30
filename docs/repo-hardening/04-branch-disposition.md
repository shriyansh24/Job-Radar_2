# Branch Disposition

## Purpose
Record the evidence-based disposition for retained branches before feature recovery or deletion decisions.

## Source-Of-Truth Status
- Status: `DOCUMENTED`
- Scope: branch forensics
- Last validation basis: `git` history plus GitHub PR metadata on `2026-03-30`

| Branch | Current Status | Unique Value | Disposition | Rationale |
|---|---|---|---|---|
| `main` | canonical active branch | merged backend, frontend, runtime, test, CI, and repo-hardening line | `KEEP` | this is the repository baseline and default branch after PR #26 |
| `codex/ui-changes` | merged historical integration branch | unique frontend overhaul, theme-family runtime, page decomposition, current UI docs/captures | `KEEP_AS_MERGED_PROVENANCE` | this branch was merged into `main` and is now retained only through history and traceability docs |
| `feat/p1-core-value` | retained feature spike | provenance for the recovered ATS identity, auto-apply, interview/search, analytics-pattern, resume preview/export, and runtime slices, plus a few branch-era variants that are now explicitly archived as historical alternatives | `KEEP_AS_SELECTIVE_PROVENANCE` | high-value traceability source, but stale and not safe to merge blindly; remaining non-promoted variants are tracked as archive decisions rather than open live-scope work |
| `origin/feat/p2-polish-advanced` | historical remote branch | strong provenance for P2 feature intent | `DEFER_AS_HISTORY` | current tip appears converged into `main`; use for traceability, not as a direct port source |
| `ui-overhaul-design` | local historical UI spike | early UI/docs experiments, grouped sidebar work, FilterChip, skeletons | `KEEP_AS_HISTORY` | not the chosen live UI line, but still useful as historical context until explicitly archived |
| `codex/career-os-overhaul` | earlier UI/UX milestone | pre-reference-first UI milestone and doc refresh | `KEEP_AS_MILESTONE` | useful as a waypoint, but not the main forward branch |

## P0 / P1 / P2 Evidence Leads

### P0
Evidence branch: `feat/p1-core-value` via PR #12
- ATS IDs and composite keys (partially recovered via `codex/ui-changes`, now live on `main`)
- normalization
- resume IR/parser
- SQL pattern detector
- branch-era local-first router foundations now archived as historical research, not live committed scope
- freshness scoring

### P1
Evidence branch: `feat/p1-core-value` via PR #13
- remaining auto-apply/operator depth beyond the recovered execution slice
- interview prep follow-through beyond the now-live stage-aware prep bundle
- resume tailoring, rendering, validation
- outcomes
- hybrid search follow-through beyond the now-live bounded ranking slice
- digest and embedding backfill workers
- pipeline ergonomics not yet promoted beyond the now-live rejected/withdrawn stages and bounded drag/drop transitions

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
- Use `feat/p1-core-value` as provenance only: already-adopted slices now live on `main`, and non-promoted variants stay archived in `docs/research/` plus the traceability matrix.
