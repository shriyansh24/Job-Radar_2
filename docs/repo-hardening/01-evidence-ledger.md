# Repository Evidence Ledger

## Purpose
Capture verified contradictions, stale references, runtime conflicts, branch leads, and quality-gate gaps before and during structural edits.

## Source-Of-Truth Status
- Status: `DOCUMENTED`
- Scope: evidence only, not policy
- Last validation basis: direct file inspection, `git` history, GitHub PR metadata, local validation, and compose/runtime reads on `2026-03-27`

## Commands Used
- `git branch -a -vv`
- `git log --oneline --decorate --graph --all --max-count 80`
- `gh pr list --limit 20 --state all`
- `gh pr view 12 --json number,title,body,headRefName,baseRefName,mergeCommit,commits,files`
- `gh pr view 13 --json number,title,body,headRefName,baseRefName,mergeCommit,commits,files`
- `gh pr view 17 --json number,title,body,headRefName,baseRefName,mergeCommit,commits,files`
- `docker compose -f docker-compose.yml -f docker-compose.dev.yml config`
- direct reads of `README.md`, `CLAUDE.md`, `AGENTS.md`, `.env.example`, `docker-compose.yml`, `docker-compose.dev.yml`, `backend/app/config.py`, `backend/app/database.py`, `backend/app/main.py`, `backend/app/runtime/scheduler.py`, `backend/app/workers/scheduler.py`, `frontend/vite.config.ts`, `frontend/system.md`, `docs/current-state/*`, `docs/system-inventory/*`, `.github/workflows/*`, `.github/dependabot.yml`, and test trees under `frontend/src`, `frontend/e2e`, and `backend/tests`

## Verified Repo Surfaces

### Documentation Layers
- Live state: `docs/current-state/`
- Bug ledger: `docs/audit/`
- Exploratory roadmap: `docs/research/`
- Working conventions: `README.md`, `AGENTS.md`, `CLAUDE.md`, `PROJECT_STATUS.md`, `DECISIONS.md`
- Hardening/control layer: `docs/repo-hardening/`
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
- Dedicated scheduler runtime: `backend/app/runtime/scheduler.py`
- Scheduler registration: `backend/app/workers/scheduler.py`
- Database engine/session: `backend/app/database.py`
- Auth cookie behavior: `backend/app/auth/service.py`
- Security headers / request IDs / timing / rate limits: `backend/app/shared/middleware.py`
- Compose runtime: `docker-compose.yml`
- Dev overlay: `docker-compose.dev.yml`
- Frontend proxy/runtime: `frontend/vite.config.ts`

### Quality-Gate Surfaces
- CI: `.github/workflows/ci.yml`
- Browser lane: `.github/workflows/frontend-e2e.yml`
- Docs validation: `.github/workflows/docs-validation.yml`
- Migration replay: `.github/workflows/migration-safety.yml`
- Code scanning: `.github/workflows/codeql.yml`
- Dependency review: `.github/workflows/dependency-review.yml`
- Dependency update automation: `.github/dependabot.yml`
- Security reporting guidance: `SECURITY.md`

## Verified Contradictions

| Status | Area | Evidence | Reality |
|---|---|---|---|
| `FIXED` | Local DB truth was split | `CLAUDE.md` previously said `5433`, `jobradar-postgres`, password `jobradar220568`; `.env.example`, `docker-compose.yml`, and `backend/app/config.py` said `5432` and `jobradar` | The compose-first runtime is now the explicit baseline across `README.md`, `CLAUDE.md`, `.env.example`, and current-state docs |
| `FIXED` | Startup model was split | `README.md` previously said `docker start jobradar-postgres`; current-state already used compose | Compose-first runtime plus bind-mounted overlay are now documented with an explicit hierarchy |
| `FIXED` | Backend validation counts drifted | `docs/current-state/00-index.md` said `26 passed`; `docs/current-state/02-backend.md` still said `24 passed` | Current-state docs now consistently use the `26 passed` targeted backend slice |
| `FIXED` | Current-state referenced a missing historical doc set | `docs/current-state/04-data-and-scraping.md` referenced a missing legacy superpowers doc set | The missing-path reference was removed from live docs |
| `FIXED` | Current-state and system-inventory conflicted | `docs/system-inventory/13-open-questions.txt` treated resolved contract drift as open | Current-state remains authoritative and the inventory file now carries historical framing |
| `FIXED` | Dev proxy previously did not match containerized dev | `frontend/vite.config.ts` proxies `/api` to `http://localhost:8000`; `docker-compose.dev.yml` runs the frontend inside a container | The dev overlay now sets `VITE_API_PROXY_TARGET=http://backend:8000`, publishes only `5173:5173`, and health-checks the actual Vite port |
| `FIXED` | Browser lane did not exist in-repo | Browser QA was manual-only in `.claude/ui-captures/` | Playwright config and committed `frontend/e2e/{smoke,flows,theme-matrix,support}` suites now exist and are wired into GitHub Actions |
| `FIXED` | CI job naming was too coarse | Generic frontend/backend jobs made failures hard to localize | Required checks now emit stable, specific job names for backend quality, backend tests, frontend quality, frontend build/tests, docs validation, migration safety, and browser smoke |
| `FIXED` | CODEOWNERS / templates were absent | No `CODEOWNERS`, no issue or PR templates under `.github/` | CODEOWNERS plus PR and issue templates are now checked in as repo guardrails |
| `DOCUMENTED` | Dark-mode wording still drifts from tokens | Some docs still describe default dark mode as literal jet black | The live default dark tokens remain near-black unless a theme family overrides them; docs must keep that distinction explicit |
| `DOCUMENTED` | Redis critical-path wording drifts from runtime | Redis is provisioned in compose and still has a config default, but there is no active backend Redis client usage | Redis is available for queued/future async surfaces today, but it is not on the API/scheduler critical path and docs must say so explicitly |
| `DOCUMENTED` | Scheduler readiness is better but still file-based | `backend/app/runtime/scheduler.py` now gates readiness on DB reachability, but compose still checks a sentinel file | Scheduler readiness now proves startup + DB reachability, but job-level dependency health remains a separate observability concern |

## Verified Test And Workflow Findings

| Status | Area | Evidence | Finding |
|---|---|---|---|
| `FIXED` | Frontend ops-page tests | `frontend/src/tests/pages/Admin.page.test.tsx`, `Companies.page.test.tsx`, `SearchExpansion.page.test.tsx`, `Sources.page.test.tsx`, `Targets.page.test.tsx` | The misleading phase-based ops suite has been replaced with route-owned page tests inside the new taxonomy |
| `DOCUMENTED` | Frontend test topology | `frontend/src/tests/`, `frontend/e2e/` | The frontend now has role-based unit and browser lanes, but several page and component suites still cover multiple behaviors inside one file |
| `DOCUMENTED` | Backend test topology | `backend/tests/{contracts,infra,integration,migrations,security,unit,workers}` | The backend layout is role-based, but `unit/` and `edge_cases/` still contain mixed ownership and should continue to be drained deliberately |
| `FIXED` | Committed browser/e2e lane exists | `frontend/playwright.config.ts`, `frontend/e2e/README.md`, and checked-in specs under `smoke/`, `flows/`, and `theme-matrix/` | Browser QA is no longer manual-only; the remaining gap is route breadth, not lane absence |
| `DOCUMENTED` | Coverage expectations are uneven | backend gate uses `--cov-fail-under=60`; frontend gate uses `40` statement coverage | The repo still needs an explicit rationale for why frontend quality policy is materially lower |

## Verified Branch And Phase Leads

| Status | Branch | Evidence | Finding |
|---|---|---|---|
| `DOCUMENTED` | `feat/p1-core-value` | local tip `cc907ec`; PR #13 metadata | Still contains unique P0/P1 capability work not in `main` or `codex/ui-changes`, especially auto-apply adapters, interview prep, resume tailoring, outcomes, hybrid search, and worker slices |
| `DOCUMENTED` | `origin/feat/p2-polish-advanced` | PR #17 metadata and current branch topology | Useful as provenance for P2 capability history, but current tip appears converged into `main`; not a unique live-code branch anymore |
| `DOCUMENTED` | `codex/ui-changes` | live branch history from `3ae5eac` through `5ef1c0a` | This is the unique UI overhaul and hardening line with theme-family runtime, shell/page decomposition, runtime split, CSRF hardening, and committed browser coverage |
| `DOCUMENTED` | `ui-overhaul-design` | branch-only commits visible in local history | Historical UI spike with unique docs/components, but not the selected live UI line |

## Source-Of-Truth Matrix

| Domain | Source Of Truth | Notes |
|---|---|---|
| Live shipped repo state | `docs/current-state/` | Must win over system-inventory unless code disproves it |
| Historical bug status | `docs/audit/` | Bug ledger only, not current runtime instructions |
| Exploratory roadmap | `docs/research/` | Do not treat as shipped scope without promotion |
| Executable runtime defaults | `backend/app/config.py`, `backend/app/main.py`, `backend/app/runtime/scheduler.py`, `backend/app/database.py`, `docker-compose.yml`, `docker-compose.dev.yml`, `frontend/vite.config.ts` | These files overrule ambiguous prose |
| Frontend visual system | `frontend/src/index.css`, `frontend/system.md` | Wording must match actual tokens and theme families |
| Branch/phase truth | `git` history + GitHub PR metadata | Must be proven file-by-file before integration decisions |

## Immediate Risks
- `feat/p1-core-value` contains meaningful capability work that can be lost by neglect, but it is too stale to merge blindly.
- The committed Playwright/browser lane now exists, but route-family and eight-mode coverage are still thin.
- Several historical/system-inventory documents still read like live status unless explicitly archived or demoted.
- Scheduler readiness is now less false-green than before, but worker/job failure semantics still need more explicit observability.

## What This Ledger Does Not Yet Prove
- Whether all current-state claims about frontend/backend contract alignment hold under a fresh full backend validation run
- Whether Alembic replay from clean state is fully safe beyond the current upgrade check
- Which exact P1 slices should be ported first and which should be rejected
- Whether all non-default theme families are route-complete across the full frontend
