# Ambiguous Skills Review

> Updated: 2026-03-09
> Scope: All 147 UNRESOLVED legacy root-level skill directories (excludes 33 already-stubbed
> and 14 canonical roots). Documentation only -- no moves, merges, or deletions.

---

## 1. Legacy Aliases (already consolidated)

These legacy root-level directories have an **identical canonical skill already living
inside a taxonomy root**. The legacy copy still has original content (not yet stubbed),
but the canonical destination already exists and is authoritative.

When stubs are eventually created, each of these should redirect to its canonical path.

### 1a. Exact duplicates of canonical personas / capabilities

| # | Legacy root skill | Canonical destination | Notes |
|---|---|---|---|
| 1 | `embeddings` | `memory/embeddings` | capability |
| 2 | `memory-management` | `memory/memory-management` | capability |
| 3 | `security-audit` | `quality/security-audit` | capability |
| 4 | `verification-quality-assurance` | `quality/verification-quality-assurance` | capability |
| 5 | `codebase-audit-pre-push` | `quality/codebase-audit-pre-push` | capability |
| 6 | `clean-code` | `reference/clean-code` | reference |
| 7 | `api-design-principles` | `reference/api-design-principles` | reference |
| 8 | `api-patterns` | `reference/api-patterns` | reference |
| 9 | `architecture-patterns` | `reference/architecture-patterns` | reference |
| 10 | `backend-dev-guidelines` | `reference/backend-dev-guidelines` | reference |
| 11 | `autonomous-agent-patterns` | `reference/autonomous-agent-patterns` | reference |
| 12 | `architect-review` | `architecture/architect-review` | architecture |
| 13 | `architecture-decision-records` | `architecture/architecture-decision-records` | architecture |
| 14 | `context-fundamentals` | `context/context-fundamentals` | context |
| 15 | `context-compression` | `context/context-compression` | context |
| 16 | `context-driven-development` | `context/context-driven-development` | context |
| 17 | `context-optimizer` | `context/` (no exact match yet) | close -- see note [A] |
| 18 | `deslop` | `utilities/deslop` | utility |
| 19 | `find-skills` | `utilities/find-skills` | utility |
| 20 | `insights` | `utilities/insights` | utility |
| 21 | `learn-rule` | `utilities/learn-rule` | utility |
| 22 | `pair-programming` | `utilities/pair-programming` | utility |
| 23 | `parallel-worktrees` | `utilities/parallel-worktrees` | utility |
| 24 | `replay-learnings` | `utilities/replay-learnings` | utility |
| 25 | `session-handoff` | `utilities/session-handoff` | utility |
| 26 | `skill-builder` | `utilities/skill-builder` | utility |
| 27 | `smart-commit` | `utilities/smart-commit` | utility |
| 28 | `sparc-methodology` | `utilities/sparc-methodology` | utility |
| 29 | `stream-chain` | `utilities/stream-chain` | utility |
| 30 | `wrap-up` | `utilities/wrap-up` | utility |

> **[A]** `context-optimizer` has no exact canonical child yet, but `context/` is the
> obvious home. Listing it here because the mapping is unambiguous even if the child
> doesn't exist yet.

### 1b. Product / domain aliases

| # | Legacy root skill | Canonical destination | Notes |
|---|---|---|---|
| 31 | `agentdb-learning-plugins` | `products/agentdb` (mode: learning-plugins) | product family |
| 32 | `agentdb-memory-patterns` | `products/agentdb` (mode: memory-patterns) | product family |
| 33 | `agentdb-performance-optimization` | `products/agentdb` (mode: perf-optimization) | product family |
| 34 | `agentdb-vector-search` | `products/agentdb` (mode: vector-search) | product family |
| 35 | `reasoningbank-with-agentdb` | `products/reasoningbank` (mode: agentdb-integration) | product family |
| 36 | `hive-mind-advanced` | `products/hive-mind` (mode: advanced) | product family |
| 37 | `flow-nexus-platform` | `products/flow-nexus` (mode: platform) | product family |
| 38 | `flow-nexus-swarm` | `products/flow-nexus/swarm` | product family |
| 39 | `performance-analysis` | `engineering/performance` | capability overlap |
| 40 | `api-documenter` | `engineering/api` (mode: documenter) | engineering overlap |
| 41 | `api-documentation-generator` | `engineering/api` (mode: doc-generator) | engineering overlap |
| 42 | `api-security-best-practices` | `engineering/security` (mode: api-security) | engineering overlap |
| 43 | `backend-architect` | `engineering/backend` (mode: architect) | engineering overlap |
| 44 | `agent-agentic-payments` | `domain/payments` | domain family (2nd alias after agent-payments stub) |

### 1c. GitHub / platform aliases

| # | Legacy root skill | Canonical destination | Notes |
|---|---|---|---|
| 45 | `github-workflow-automation` | `platform/github` (mode: workflow-automation) | platform family |
| 46 | `github-code-review` | `platform/github` (mode: code-review) | platform family |
| 47 | `github-multi-repo` | `platform/github` (mode: multi-repo) | platform family |
| 48 | `github-project-management` | `platform/github` (mode: project-management) | platform family |
| 49 | `github-release-management` | `platform/github` (mode: release-management) | platform family |

### 1d. V3-specific skills (deferred archive, clear product family)

| # | Legacy root skill | Canonical destination | Notes |
|---|---|---|---|
| 50 | `v3-cli-modernization` | products/v3 (deferred) | v3 product ecosystem |
| 51 | `v3-core-implementation` | products/v3 (deferred) | v3 product ecosystem |
| 52 | `v3-ddd-architecture` | products/v3 (deferred) | v3 product ecosystem |
| 53 | `v3-deep-integration` | products/v3 (deferred) | v3 product ecosystem |
| 54 | `v3-mcp-optimization` | products/v3 (deferred) | v3 product ecosystem |
| 55 | `v3-memory-unification` | products/v3 (deferred) | v3 product ecosystem |
| 56 | `v3-performance-optimization` | products/v3 (deferred) | v3 product ecosystem |
| 57 | `v3-security-overhaul` | products/v3 (deferred) | v3 product ecosystem |
| 58 | `v3-swarm-coordination` | products/v3 (deferred) | v3 product ecosystem |

### 1e. Orchestration / coordination aliases (boilerplate agent-* wrappers)

These are auto-generated agent-* wrappers whose function maps directly to an existing
canonical orchestration or engineering skill.

| # | Legacy root skill | Canonical destination | Notes |
|---|---|---|---|
| 59 | `agent-benchmark-suite` | `engineering/performance` (mode: benchmarks) | perf family |
| 60 | `agent-performance-benchmarker` | `engineering/performance` (mode: benchmarker) | perf family |
| 61 | `agent-performance-monitor` | `engineering/performance` (mode: monitor) | perf family |
| 62 | `agent-performance-optimizer` | `engineering/performance` (mode: optimizer) | perf family |
| 63 | `agent-code-analyzer` | `quality/code-review` (mode: analyzer) | quality family |
| 64 | `agent-analyze-code-quality` | `quality/code-review` (mode: quality-analysis) | quality family |
| 65 | `agent-production-validator` | `quality/verification-quality-assurance` (mode: prod-validator) | quality family |
| 66 | `agent-code-review-swarm` | `quality/code-review` (mode: swarm) | quality family |
| 67 | `agent-tdd-london-swarm` | `engineering/testing` (mode: tdd-london) | testing family |
| 68 | `agent-test-long-runner` | `engineering/testing` (mode: long-runner) | testing family |
| 69 | `agent-dev-backend-api` | `engineering/backend` (mode: api) | backend family |
| 70 | `agent-docs-api-openapi` | `engineering/api` (mode: openapi) | api family |
| 71 | `agent-authentication` | `engineering/security` (mode: auth) | security family |
| 72 | `agent-architecture` | `architecture/architect-review` | architecture family |
| 73 | `agent-arch-system-design` | `architecture/` (mode: system-design) | architecture family |
| 74 | `agent-repo-architect` | `architecture/` (mode: repo) | architecture family |
| 75 | `agent-pseudocode` | `core/planning` (mode: pseudocode) | core family |
| 76 | `agent-refinement` | `core/` (mode: refinement) | core family |
| 77 | `agent-base-template-generator` | `utilities/skill-builder` (mode: template) | utilities family |
| 78 | `agent-scout-explorer` | `research/investigation` (mode: scout) | research family |
| 79 | `agent-memory-coordinator` | `memory/memory-management` (mode: coordinator) | memory family |
| 80 | `agent-user-tools` | `products/flow-nexus` (mode: user-tools) | product family |

### 1f. Orchestration topology aliases

These are specializations of the `orchestration/` canonical family -- different
consensus/coordination algorithms or swarm topologies.

| # | Legacy root skill | Canonical destination | Notes |
|---|---|---|---|
| 81 | `agent-byzantine-coordinator` | `orchestration/consensus` (mode: byzantine) | consensus variant |
| 82 | `agent-gossip-coordinator` | `orchestration/coordination` (mode: gossip) | coordination variant |
| 83 | `agent-hierarchical-coordinator` | `orchestration/coordination` (mode: hierarchical) | coordination variant |
| 84 | `agent-collective-intelligence-coordinator` | `orchestration/coordination` (mode: collective) | coordination variant |
| 85 | `agent-mesh-coordinator` | `orchestration/coordination` (mode: mesh) | coordination variant |
| 86 | `agent-raft-manager` | `orchestration/consensus` (mode: raft) | consensus variant |
| 87 | `agent-quorum-manager` | `orchestration/consensus` (mode: quorum) | consensus variant |
| 88 | `agent-topology-optimizer` | `orchestration/swarm` (mode: topology) | swarm variant |
| 89 | `agent-coordinator-swarm-init` | `orchestration/swarm` (mode: init) | swarm variant |
| 90 | `agent-multi-repo-swarm` | `orchestration/swarm` (mode: multi-repo) | swarm variant |
| 91 | `agent-release-swarm` | `orchestration/swarm` (mode: release) | swarm variant |
| 92 | `agent-swarm-issue` | `orchestration/swarm` (mode: issue) | swarm variant |
| 93 | `agent-swarm-pr` | `orchestration/swarm` (mode: pr) | swarm variant |
| 94 | `agent-swarm-memory-manager` | `orchestration/swarm` (mode: memory) | swarm variant |
| 95 | `agent-sync-coordinator` | `orchestration/coordination` (mode: sync) | coordination variant |
| 96 | `agent-resource-allocator` | `orchestration/core` (mode: resource-alloc) | core variant |
| 97 | `agent-load-balancer` | `orchestration/core` (mode: load-balance) | core variant |
| 98 | `agent-matrix-optimizer` | `orchestration/core` (mode: matrix) | core variant |
| 99 | `agent-queen-coordinator` | `orchestration/swarm` (mode: queen) | swarm variant |
| 100 | `agent-orchestrator-task` | `orchestration/core` (mode: task) | core variant |

### 1g. GitHub / platform agent aliases

| # | Legacy root skill | Canonical destination | Notes |
|---|---|---|---|
| 101 | `agent-github-pr-manager` | `platform/github` (mode: pr-manager) | github family |
| 102 | `agent-github-modes` | `platform/github` (mode: modes) | github family |
| 103 | `agent-pr-manager` | `platform/github` (mode: pr-manager) | github family (duplicate of #101) |
| 104 | `agent-project-board-sync` | `platform/github` (mode: project-board) | github family |
| 105 | `agent-issue-tracker` | `platform/github` (mode: issues) | github family |
| 106 | `agent-ops-cicd-github` | `platform/github` (mode: cicd) | github family |
| 107 | `agent-release-manager` | `platform/github` (mode: release) | github family |

### 1h. V3-specific agent aliases

| # | Legacy root skill | Canonical destination | Notes |
|---|---|---|---|
| 108 | `agent-v3-integration-architect` | products/v3 (deferred) | v3 agent |
| 109 | `agent-v3-memory-specialist` | products/v3 (deferred) | v3 agent |
| 110 | `agent-v3-performance-engineer` | products/v3 (deferred) | v3 agent |
| 111 | `agent-v3-queen-coordinator` | products/v3 (deferred) | v3 agent |
| 112 | `agent-v3-security-architect` | products/v3 (deferred) | v3 agent |

**Legacy alias total: 112**

---

## 2. Genuinely Ambiguous (needs decision)

These skills do NOT clearly map to a single existing canonical family. They require
a human decision about where they belong, whether they should remain standalone, or
whether they should be archived.

### 2a. ~~KEEP_STANDALONE~~ RESOLVED

All 9 skills have been canonicalized and their legacy roots stubbed.

| # | Legacy skill | Canonical destination | Status |
|---|---|---|---|
| 1 | `agent-manager-skill` | `ops/agent-manager` | done |
| 2 | `orchestrate` | `orchestration/orchestrate` | done |
| 3 | `hooks-automation` | `ops/hooks-automation` | done |
| 4 | `workflow-automation` | `ops/workflow-automation` | done |
| 5 | `worker-integration` | `ops/worker-integration` | done |
| 6 | `worker-benchmarks` | `ops/worker-benchmarks` | done |
| 7 | `claims` | `ops/claims-authorization` | done |
| 8 | `ab-test-setup` | `ops/ab-test-setup` | done |
| 9 | `claude-speed-reader` | `utilities/claude-speed-reader` | done |

### 2b. ARCHIVE_LATER

Highly specialized, niche, or experimental skills unlikely to be used in the current
project context. Should be archived (not deleted) after migration stabilizes.

| # | Skill | Summary | Reason | Confidence |
|---|---|---|---|---|
| 1 | `agentic-jujutsu` | Quantum-resistant, self-learning version control for AI agents with ReasoningBank intelligence. | Experimental; no production use case evident | high |
| 2 | `20-andruia-niche-intelligence` | Spanish-language domain intelligence strategist for Andru.ia projects. | Project-specific; not generalizable | high |
| 3 | `agent-trading-predictor` | Trading prediction agent. | Domain-specific; no relation to core project | high |
| 4 | `agent-pagerank-analyzer` | PageRank analysis agent. | Niche algorithm; no active use case | high |
| 5 | `agent-sona-learning-optimizer` | SONA learning optimization agent. | Experimental neural subsystem | high |
| 6 | `agent-safla-neural` | SAFLA neural agent. | Experimental neural subsystem | high |
| 7 | `agent-app-store` | App store agent. | Product concept; no active implementation | med |
| 8 | `agent-challenges` | Challenges agent. | Gamification concept; no active use | med |
| 9 | `agent-sandbox` | Sandbox agent. | Generic sandbox; overlaps with products/ | med |

### 2c. DEPRECATE_LATER

Skills that overlap significantly with canonical families but are NOT exact duplicates.
They add marginal value and should be folded in when time permits.

| # | Skill | Summary | Proposed merge target | Confidence |
|---|---|---|---|---|
| 1 | `codebase-cleanup-refactor-clean` | Code refactoring expert with SOLID patterns. | `reference/clean-code` (merge content) | high |
| 2 | `agent-automation-smart-agent` | Generic "smart agent" automation wrapper. | `orchestration/core` (redundant abstraction) | med |
| 3 | `agent-workflow` | Generic workflow agent. | `workflow-automation` (superset) | med |
| 4 | `agent-workflow-automation` | Workflow automation agent wrapper. | `workflow-automation` (superset) | med |
| 5 | `agent-worker-specialist` | Worker specialist agent. | `worker-integration` (superset) | med |
| 6 | `agent-migration-plan` | Migration planning agent. | `core/planning` (mode: migration) | med |

### 2d. ~~NEEDS_HUMAN_DECISION~~ RESOLVED

All 11 skills have been canonicalized (0 remaining).

| # | Legacy skill | Canonical destination | Status |
|---|---|---|---|
| 1 | `ai-engineer` | `core/personas/ai-engineer` | done |
| 2 | `ai-agents-architect` | `core/personas/ai-agents-architect` | done |
| 3 | `pro-workflow` | `ops/pro-workflow` | done |
| 4 | `agent-orchestration-improve-agent` | `quality/agent-improvement` | done |
| 5 | `agent-orchestration-multi-agent-optimize` | `orchestration/optimization` | done |
| 6 | `agent-orchestrator-task` | `orchestration/task-routing` | done |
| 7 | `agent-memory-mcp` | `memory/mcp` | done |
| 8 | `agent-memory-systems` | `memory/systems` | done |
| 9 | `agent-memory-coordinator` | `memory/coordination` | done |
| 10 | `agent-evaluation` | `quality/agent-evaluation` | done |
| 11 | `agents-v2-py` | `platform/azure-agents` | done |

> `agent-tool-builder` and `agentfolio` were originally listed here but were
> canonicalized as part of the final cleanup. Their canonical homes are
> `engineering/tooling/agent-tool-builder` and `utilities/agent-discovery`
> respectively. They count toward the section 1 alias total (stubs redirect
> to canonical) rather than inflating this section's count.

---

## 3. Final Counts

| Category | Section | Count | Status |
|---|---|---|---|
| Legacy aliases | 1 | 112 | resolved -- stubbed, canonical exists |
| Keep standalone | 2a | 9 | resolved -- stubbed, new canonical created |
| Needs human decision | 2d | 11 | resolved -- stubbed, new canonical created |
| Archive later | 2b | 9 | **unresolved** -- original content intact |
| Deprecate later | 2c | 6 | **unresolved** -- original content intact |
| | | | |
| **Resolved** | | **132** | 89.8% of 147 |
| **Unresolved** | | **15** | 10.2% of 147 |
| **Total** | | **147** | |

---

## 4. Notes

- **33 additional skills** (Phase 1) already have `# DEPRECATED` stub redirects and
  are excluded from this document entirely.
- **Total canonical skills: 87** (run `python scripts/validate_skills.py` for
  the authoritative count).
- Deprecated stub count is not tracked manually; run the validator or
  `grep -rl "^# DEPRECATED" .agents/skills/*/SKILL.md | wc -l` for a live count.
- V3 skills (9 root + 5 agent-v3-*) are mapped to `products/v3` but actual migration
  is deferred per existing policy.
- `context-optimizer` is listed as an alias even though `context/context-optimizer`
  doesn't exist yet -- the mapping is unambiguous.
- `ops/` hosts 8 canonical skills: agent-manager, hooks-automation, workflow-automation,
  worker-integration, worker-benchmarks, claims-authorization, ab-test-setup, pro-workflow.
