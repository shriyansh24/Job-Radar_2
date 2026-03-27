# Repository Evidence Ledger

## Purpose
Capture verified contradictions, stale references, runtime conflicts, branch leads, and quality-gate gaps before structural edits.

## Source-Of-Truth Status
- Status: `DOCUMENTED`
- Scope: evidence only, not policy
- Last validation basis: direct file inspection, `git` history, and GitHub PR metadata on `2026-03-27`

## Commands Used
- `git branch -a -vv`
- `git log --oneline --decorate --graph --all --max-count 80`
- `gh pr list --limit 20 --state all`
- `gh pr view 12 --json number,title,body,headRefName,baseRefName,mergeCommit,commits,files`
- `gh pr view 13 --json number,title,body,headRefName,baseRefName,mergeCommit,commits,files`
- `gh pr view 17 --json number,title,body,headRefName,baseRefName,mergeCommit,commits,files`
- direct reads of `README.md`, `CLAUDE.md`, `AGENTS.md`, `.env.example`, `docker-compose.yml`, `docker-compose.dev.yml`, `backend/app/config.py`, `backend/app/database.py`, `backend/app/main.py`, `backend/app/auth/service.py`, `frontend/vite.config.ts`, `frontend/system.md`, `docs/current-state/*`, `docs/system-inventory/*`, `.github/workflows/*`, `.github/dependabot.yml`, and test trees under `frontend/src` and `backend/tests`

## Verified Repo Surfaces

### Documentation Layers
- Live state: `docs/current-state/`
- Bug ledger: `docs/audit/`
- Exploratory roadmap: `docs/research/`
- Working conventions: `README.md`, `AGENTS.md`, `CLAUDE.md`, `PROJECT_STATUS.md`, `DECISIONS.md`
- Historical/system inventory: `docs/system-inventory/`

### Branches Worth Mining
- `main`
- `codex/ui-changes`
- `feat/p1-core-value`
- `ui-overhaul-design`
- remote history/provenance:
  - `origin/feat/p2-polish-advanced`
  - `origin/feature/ui/figma/neo-brutalist-themes`
  - `origin/codex/career-os-overhaul`

### Runtime Surfaces
- Backend config: `backend/app/config.py`
- Backend startup: `backend/app/main.py`
- Database engine/session: `backend/app/database.py`
- Auth cookie behavior: `backend/app/auth/service.py`
- Security headers / request IDs / timing / rate limits: `backend/app/shared/middleware.py`
- Compose runtime: `docker-compose.yml`
- Dev overlay: `docker-compose.dev.yml`
- Frontend proxy/runtime: `frontend/vite.config.ts`

### Quality-Gate Surfaces
- CI: `.github/workflows/ci.yml`
- Code scanning: `.github/workflows/codeql.yml`
- Dependency review: `.github/workflows/dependency-review.yml`
- Dependency update automation: `.github/dependabot.yml`
- Security reporting guidance: `SECURITY.md`

## Verified Contradictions

| Status | Area | Evidence | Reality |
|---|---|---|---|
| `DOCUMENTED` | Local DB truth is split | `CLAUDE.md` says `5433`, `jobradar-postgres`, password `jobradar220568`; `.env.example`, `docker-compose.yml`, and `backend/app/config.py` say `5432` and `jobradar` | Code defaults and compose both point to `5432`; `CLAUDE.md` reflects a separate manual-local setup and currently conflicts with the code/compose baseline |
| `DOCUMENTED` | Redis truth is split | `.env.example` shows no Redis password; `backend/app/config.py` expects a password by default; `docker-compose.yml` requires `jobradar-redis` and may enable TLS | The compose/runtime truth is passworded Redis with optional TLS; `.env.example` is stale/incomplete |
| `DOCUMENTED` | Startup model is split | `README.md` says `docker start jobradar-postgres`; `docs/current-state/05-ops-and-ci.md` says `docker compose up -d postgres redis`; `docker-compose.dev.yml` is only an overlay | There are at least two different local boot models documented without an explicit decision hierarchy |
| `DOCUMENTED` | Backend validation counts drift | `docs/current-state/00-index.md` says targeted backend slice is `26 passed`; `docs/current-state/02-backend.md` still says `24 passed` | The newer `26 passed` claim is the fresher state; backend docs still need reconciliation |
| `DOCUMENTED` | Current-state references a missing historical doc set | `docs/current-state/04-data-and-scraping.md` says a legacy superpowers doc set contains historical plans | That legacy superpowers doc set does not exist on the current branch |
| `DOCUMENTED` | Current-state and system-inventory conflict | `docs/system-inventory/13-open-questions.txt` still treats search expansion, resume tailor, salary typing, scraper responses, admin typing, and vault updates as open | `docs/current-state/03-frontend.md` says those surfaces are aligned; inventory docs are stale unless code disproves current-state |
| `DOCUMENTED` | Theme wording drifts from tokens | `frontend/system.md` says dark mode is “jet black” | Default dark tokens in `frontend/src/index.css` are near-black (`#0A0A0A` / `#2A2A2C` / `#353437`), not literal `#000000` |
| `DOCUMENTED` | Dev proxy does not match containerized dev | `frontend/vite.config.ts` proxies `/api` to `http://localhost:8000`; `docker-compose.dev.yml` runs the frontend inside a container | In containerized dev, `localhost:8000` points at the frontend container, not backend; proxy truth is only correct for host-local frontend dev |

## Verified Test And Workflow Findings

| Status | Area | Evidence | Finding |
|---|---|---|---|
| `FIXED` | Frontend ops-page tests | `frontend/src/tests/pages/Admin.page.test.tsx`, `frontend/src/tests/pages/Companies.page.test.tsx`, `frontend/src/tests/pages/SearchExpansion.page.test.tsx`, `frontend/src/tests/pages/Sources.page.test.tsx`, `frontend/src/tests/pages/Targets.page.test.tsx` | The misleading phase-based ops suite has been replaced with route-owned page tests inside the new taxonomy. |
| `DOCUMENTED` | Frontend test topology | `frontend/src/tests/`, `frontend/e2e/` | The frontend now has role-based unit and browser lanes, but several page and component suites still cover multiple behaviors inside one file. |
| `DOCUMENTED` | Backend test topology | `backend/tests/{contracts,infra,integration,migrations,security,unit,workers}` | The backend layout is now role-based, but `unit/` and `edge_cases/` still contain mixed ownership and should continue to be drained deliberately. |
| `FIXED_IN_WORKTREE` | Committed browser/e2e lane exists but is still shallow | `frontend/playwright.config.ts`, `frontend/e2e/README.md`, and the first `smoke/`, `flows/`, and `theme-matrix/` specs are now checked in | Browser QA is no longer manual-only, but the committed lane still covers only a narrow authenticated shell/theme slice |
| `DOCUMENTED` | CI job naming is too coarse | `.github/workflows/ci.yml` has only `backend` and `frontend` jobs | Failures are hard to localize from GitHub UI because security, lint, type, and test steps are collapsed into generic jobs |
| `DOCUMENTED` | Coverage expectations are uneven | backend gate uses `--cov-fail-under=60`; frontend gate uses `40` statement coverage | The repo has no explicit rationale for why frontend quality policy is materially lower |
| `DOCUMENTED` | CODEOWNERS / templates absent | no `CODEOWNERS`, no issue or PR templates under `.github/` | There is no repo-level guidance for review ownership or PR hygiene beyond workflow checks |

## Verified Branch And Phase Leads

| Status | Branch | Evidence | Finding |
|---|---|---|---|
| `DOCUMENTED` | `feat/p1-core-value` | local tip `cc907ec`; PR #13 metadata | Still contains unique P0/P1 capability work not in `main` or `codex/ui-changes`, especially auto-apply adapters, interview prep, resume tailoring, outcomes, hybrid search, and worker slices |
| `DOCUMENTED` | `origin/feat/p2-polish-advanced` | PR #17 metadata and current branch topology | Useful as provenance for P2 capability history, but current tip appears converged into `main`; not a unique live-code branch anymore |
| `DOCUMENTED` | `codex/ui-changes` | live branch history from `3ae5eac` through `863241e` | This is the unique UI overhaul line with theme-family runtime, shell/page decomposition, and doc/capture refresh |
| `DOCUMENTED` | `ui-overhaul-design` | branch-only commits visible in local history | Historical UI spike with unique docs/components, but not the selected live UI line |

## Source-Of-Truth Matrix

| Domain | Source Of Truth | Notes |
|---|---|---|
| Live shipped repo state | `docs/current-state/` | Must win over system-inventory unless code disproves it |
| Historical bug status | `docs/audit/` | Bug ledger only, not current runtime instructions |
| Exploratory roadmap | `docs/research/` | Do not treat as shipped scope without promotion |
| Executable runtime defaults | `backend/app/config.py`, `backend/app/main.py`, `backend/app/database.py`, `docker-compose.yml`, `docker-compose.dev.yml`, `frontend/vite.config.ts` | These files overrule ambiguous prose |
| Frontend visual system | `frontend/src/index.css`, `frontend/system.md` | Wording still needs reconciliation with actual tokens |
| Branch/phase truth | `git` history + GitHub PR metadata | Must be proven file-by-file before integration decisions |

## Immediate Risks
- Runtime instructions can still boot the wrong DB or Redis configuration depending on which doc is followed.
- `feat/p1-core-value` contains meaningful capability work that can be lost by neglect, but it is too stale to merge blindly.
- The repo now has a committed Playwright/browser lane, but route-family and outcome-level coverage are still thin.
- The frontend/backend contract claims in `docs/system-inventory/13-open-questions.txt` are no longer trustworthy as live truth.

## What This Ledger Does Not Yet Prove
- Whether all current-state claims about frontend/backend contract alignment hold under fresh backend validation
- Whether Alembic replay from clean state is fully safe
- Whether non-default theme families are route-complete across the full frontend
- Which exact P1 slices should be ported first and which should be rejected
