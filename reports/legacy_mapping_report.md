# Legacy Skill Mapping Report
# Generated: 2026-03-09
# Phase A + B1 - Skill Migration

## Summary
- Total skills moved (Phase A): 30
- Total families consolidated (Phase B1): 5
- Compatibility symlinks/stubs created: 35+

## B1 Consolidation Summary

### 1. HIVE-MIND Family
- **Canonical:** products/hive-mind
- **Old skills:** hive-mind, hive-mind-advanced
- **Modes:** 1 (advanced)
- **Compatibility:** Stub SKILL.md at old locations

### 2. REASONINGBANK Family  
- **Canonical:** products/reasoningbank
- **Old skills:** reasoningbank-intelligence, reasoningbank-with-agentdb
- **Modes:** 1 (with-agentdb)
- **Compatibility:** Stub SKILL.md at old locations

### 3. TESTING Family
- **Canonical:** engineering/testing
- **Old skills:** agent-tester, agent-test-long-runner, agent-benchmark-suite
- **Modes:** 2 (long-running, benchmark)
- **Standalone:** worker-benchmarks
- **Compatibility:** Stub SKILL.md at old locations

### 4. PERFORMANCE Family
- **Canonical:** engineering/performance
- **Old skills:** agent-performance-analyzer, -benchmarker, -monitor, -optimizer
- **Modes:** 4 (analyze, benchmark, monitor, optimize)
- **Standalone:** agent-matrix-optimizer, performance-analysis
- **Compatibility:** Stub SKILL.md at old locations

### 5. GITHUB Family
- **Canonical:** platform/github
- **Old skills:** github-automation, -code-review, -multi-repo, -project-management, -release-management, -workflow-automation
- **Modes:** 6 (automation, code-review, multi-repo, projects, release, workflows)
- **Standalone:** agent-github-modes, agent-pr-manager, agent-issue-tracker, etc.
- **Compatibility:** Stub SKILL.md at old locations

## Moved Skills

| Old Path | New Path | Manifest ID | Category |
|----------|----------|-------------|----------|
| .agents/skills/clean-code | .agents/skills/reference/clean-code | reference.clean-code | reference |
| .agents/skills/api-design-principles | .agents/skills/reference/api-design-principles | reference.api-design-principles | reference |
| .agents/skills/api-patterns | .agents/skills/reference/api-patterns | reference.api-patterns | reference |
| .agents/skills/architecture-patterns | .agents/skills/reference/architecture-patterns | reference.architecture-patterns | reference |
| .agents/skills/backend-dev-guidelines | .agents/skills/reference/backend-dev-guidelines | reference.backend-guidelines | reference |
| .agents/skills/autonomous-agent-patterns | .agents/skills/reference/autonomous-agent-patterns | reference.autonomous-agent-patterns | reference |
| .agents/skills/context-compression | .agents/skills/context/context-compression | context.compression | context |
| .agents/skills/context-driven-development | .agents/skills/context/context-driven-development | context.cd-development | context |
| .agents/skills/context-fundamentals | .agents/skills/context/context-fundamentals | context.fundamentals | context |
| .agents/skills/wrap-up | .agents/skills/utilities/wrap-up | utilities.wrap-up | utilities |
| .agents/skills/session-handoff | .agents/skills/utilities/session-handoff | utilities.handoff | utilities |
| .agents/skills/pair-programming | .agents/skills/utilities/pair-programming | utilities.pair-programming | utilities |
| .agents/skills/parallel-worktrees | .agents/skills/utilities/parallel-worktrees | utilities.worktrees | utilities |
| .agents/skills/smart-commit | .agents/skills/utilities/smart-commit | utilities.commit | utilities |
| .agents/skills/skill-builder | .agents/skills/utilities/skill-builder | utilities.skill-builder | utilities |
| .agents/skills/sparc-methodology | .agents/skills/utilities/sparc-methodology | utilities.sparc | utilities |
| .agents/skills/find-skills | .agents/skills/utilities/find-skills | utilities.skill-discovery | utilities |
| .agents/skills/deslop | .agents/skills/utilities/deslop | utilities.deslop | utilities |
| .agents/skills/insights | .agents/skills/utilities/insights | utilities.analytics | utilities |
| .agents/skills/learn-rule | .agents/skills/utilities/learn-rule | utilities.learning | utilities |
| .agents/skills/replay-learnings | .agents/skills/utilities/replay-learnings | utilities.replay | utilities |
| .agents/skills/stream-chain | .agents/skills/utilities/stream-chain | utilities.streaming | utilities |
| .agents/skills/architect-review | .agents/skills/architecture/architect-review | architecture.review | architecture |
| .agents/skills/architecture-decision-records | .agents/skills/architecture/architecture-decision-records | architecture.adrs | architecture |
| .agents/skills/codebase-audit-pre-push | .agents/skills/quality/codebase-audit-pre-push | quality.pre-push-audit | quality |
| .agents/skills/security-audit | .agents/skills/quality/security-audit | quality.security-audit | quality |
| .agents/skills/verification-quality-assurance | .agents/skills/quality/verification-quality-assurance | quality.qa | quality |
| .agents/skills/memory-management | .agents/skills/memory/memory-management | memory.management | memory |
| .agents/skills/embeddings | .agents/skills/memory/embeddings | memory.embeddings | memory |
| .agents/skills/claude-scientific-skills | .agents/skills/domain/claude-scientific-skills | domain.scientific | domain |

## Taxonomy Structure Created

```
.agents/skills/
├── core/                    (empty - for future core skills)
├── engineering/             (empty - for future engineering skills)
├── orchestration/          (empty - for future orchestration skills)
├── architecture/           (2 skills moved here)
├── research/               (empty - for future research skills)
├── memory/                 (2 skills moved here)
├── quality/                (3 skills moved here)
├── context/                (3 skills moved here)
├── platform/               (empty - for future platform skills)
├── ops/                    (empty - for future ops skills)
├── domain/                 (1 skill moved here)
├── products/               (empty - for future product skills)
├── utilities/              (13 skills moved here)
└── reference/              (6 skills moved here)
```

## Compatibility Notes

- All moved skills have compatibility symlinks at original locations
- Original paths now point to new taxonomy locations via symlinks
- Existing references to old paths will continue to work
- Manifest files (skill.yaml) added to each moved skill

## Changes Deferred

The following merge families were NOT consolidated in Phase A:

1. **coordination** (13+ coordinator skills) - needs mode design
2. **swarm** (9+ swarm skills) - needs mode design
3. **github** (6+ github skills) - needs mode design
4. **v3** (9 v3-* skills) - project-specific, needs review
5. **agentdb** (5 agentdb-* skills) - product-specific
6. **flow-nexus** (3 flow-nexus-* skills) - product-specific
7. **hive-mind** (2 hive-* skills) - product-specific
8. **reasoningbank** (2 reasoningbank-* skills) - product-specific
9. **performance** (5+ performance skills) - needs consolidation
10. **api** (6 api-* skills) - needs consolidation
11. **testing** (3 testing skills) - needs consolidation

## Platform Symlinks Status

| Platform | Status |
|----------|--------|
| .claude/skills/ | Still pointing to old locations - needs update for moved skills |
| .agent/skills/ | Still pointing to old locations - needs update |
| .augment/skills/ | Still pointing to old locations - needs update |
| skills/ (root) | Still pointing to old locations - needs update |

Note: Compatibility symlinks created within .agents/skills/ should maintain functionality,
but platform-level symlinks in .claude/, .agent/, etc. may need separate updates.
