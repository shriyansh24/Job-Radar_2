# Ambiguous Skills Review

This document tracks legacy skills that haven't been consolidated into canonical families.
They are NOT blocking validation - they are informational for future cleanup.

## Categories

---

## Needs Merge Target

These skills have substantial content and could merge into existing canonical families.

| Skill | Description | Proposed Destination | Confidence |
|-------|-------------|----------------------|------------|
| ai-agents-architect | Expert in designing autonomous AI agents, tool use, memory, planning, orchestration | domain/ (new ai-agents folder) | high |
| ai-engineer | Production LLM apps, RAG systems, vector search, multimodal AI | domain/ai-engineering | high |
| ai-agent-development | CrewAI, LangGraph, custom agent orchestration | domain/ai-engineering | high |
| autonomous-agents | Autonomous agent patterns and best practices | reference/autonomous-agent-patterns (merge) | med |
| neural-training | SONA, MoE, EWC++ for neural pattern training | domain/ml/neural-training | high |

---

## Likely Keep Standalone

These skills have unique value or are product-specific and should stay as-is.

| Skill | Description | Reason | Confidence |
|-------|-------------|--------|------------|
| v3-* (9 skills) | claude-flow v3 specific implementations | Product ecosystem - deferred per migration policy | high |
| ab-test-setup | A/B test setup guidelines | Utility for experimentation | med |
| 20-andruia-niche-intelligence | Domain-specific intelligence for Andruia | Specialized domain knowledge | low |
| hooks-automation | Claude Code hooks automation | Unique CLI integration | med |

---

## Likely Deprecate Later

These skills are superseded by canonical skills and can be deprecated after audit.

| Skill | Description | Replaced By | Confidence |
|-------|-------------|-------------|-------------|
| agent-agent | → core/agent | persona type | high |
| agent-coder | → engineering/coding | capability type | high |
| agent-planner | → core/planning | persona type | high |
| agent-researcher | → research/investigation | capability type | high |
| agent-reviewer | → quality/code-review | capability type | high |
| agent-tester | → engineering/testing | capability type | high |
| agent-swarm | → products/flow-nexus/swarm | product type | high |
| agent-coordination | → orchestration/core | capability type | high |
| agent-consensus-coordinator | → orchestration/consensus | capability type | high |
| agent-adaptive-coordinator | → orchestration/coordination | capability type | high |
| agent-security-manager | → engineering/security | capability type | high |
| agent-performance-analyzer | → engineering/performance | capability type | high |
| agentdb-advanced-features | → products/agentdb | product type | high |
| reasoningbank-intelligence | → products/reasoningbank | product type | high |
| hive-mind | → products/hive-mind | product type | high |
| flow-nexus-neural | → products/flow-nexus | product type | high |
| embeddings | → memory/embeddings | capability type | high |
| memory-management | → memory/memory-management | capability type | high |
| security-audit | → quality/security-audit | capability type | high |
| verification-quality-assurance | → quality/verification-quality-assurance | capability type | high |
| clean-code | → reference/clean-code | reference type | high |
| api-design-principles | → reference/api-design-principles | reference type | high |
| api-patterns | → reference/api-patterns | reference type | high |
| architecture-patterns | → reference/architecture-patterns | reference type | high |
| backend-dev-guidelines | → reference/backend-dev-guidelines | reference type | high |
| architect-review | → architecture/architect-review | reference type | high |
| context-fundamentals | → context/context-fundamentals | reference type | high |
| context-compression | → context/context-compression | reference type | high |
| context-driven-development | → context/context-driven-development | reference type | high |
| deslop | → utilities/deslop | utility type | high |
| find-skills | → utilities/find-skills | utility type | high |
| insights | → utilities/insights | utility type | high |
| learn-rule | → utilities/learn-rule | utility type | high |
| pair-programming | → utilities/pair-programming | utility type | high |
| parallel-worktrees | → utilities/parallel-worktrees | utility type | high |
| replay-learnings | → utilities/replay-learnings | utility type | high |
| session-handoff | → utilities/session-handoff | utility type | high |
| skill-builder | → utilities/skill-builder | utility type | high |
| smart-commit | → utilities/smart-commit | utility type | high |
| sparc-methodology | → utilities/sparc-methodology | utility type | high |
| stream-chain | → utilities/stream-chain | utility type | high |
| wrap-up | → utilities/wrap-up | utility type | high |
| github-automation | → platform/github | integration type | high |

---

## Likely Archive Later (NOT NOW)

These are v3-specific or highly specialized. Do NOT delete during active migration.

| Skill | Description | Reason |
|-------|-------------|--------|
| v3-swarm-coordination | 15-agent hierarchical mesh for v3 | v3 product-specific |
| v3-security-overhaul | CVE remediation for v3 | v3 product-specific |
| v3-performance-optimization | 2.49x-7.47x performance targets | v3 product-specific |
| v3-memory-unification | AgentDB unification | v3 product-specific |
| v3-mcp-optimization | MCP server optimization | v3 product-specific |
| v3-deep-integration | Deep agentic-flow integration | v3 product-specific |
| v3-ddd-architecture | DDD for v3 | v3 product-specific |
| v3-core-implementation | Core v3 implementation | v3 product-specific |
| v3-cli-modernization | CLI modernization for v3 | v3 product-specific |

---

## Notes

- This is a checkpoint document created after Phase 1 consolidation
- V3 skills are explicitly deferred per migration policy (high-risk product ecosystem)
- All "Needs Merge" skills have working canonical destinations already (see above)
- The "Likely Deprecate" list shows 40+ stubs that point to canonical - they already work correctly
- Archive decision should be made AFTER migration stabilizes (per design doc)
