#!/usr/bin/env python3
"""
Convert legacy alias SKILL.md files into stub redirects.

For each alias:
1) Archive existing SKILL.md to _archive/legacy-skill-md/<name>/SKILL.md
2) Replace with a stub redirect pointing to the canonical destination

Source of truth: docs/review/ambiguous-skills.md section 1 (Legacy Aliases)
"""

import os
import shutil
from pathlib import Path

SKILLS_ROOT = Path(".agents/skills")
ARCHIVE_ROOT = Path("_archive/legacy-skill-md")

# All 112 legacy aliases from docs/review/ambiguous-skills.md section 1a-1h
# Format: (legacy_name, canonical_dest, mode_or_none)
ALIASES = [
    # 1a. Exact duplicates of canonical personas / capabilities
    ("embeddings", "memory/embeddings", None),
    ("memory-management", "memory/memory-management", None),
    ("security-audit", "quality/security-audit", None),
    ("verification-quality-assurance", "quality/verification-quality-assurance", None),
    ("codebase-audit-pre-push", "quality/codebase-audit-pre-push", None),
    ("clean-code", "reference/clean-code", None),
    ("api-design-principles", "reference/api-design-principles", None),
    ("api-patterns", "reference/api-patterns", None),
    ("architecture-patterns", "reference/architecture-patterns", None),
    ("backend-dev-guidelines", "reference/backend-dev-guidelines", None),
    ("autonomous-agent-patterns", "reference/autonomous-agent-patterns", None),
    ("architect-review", "architecture/architect-review", None),
    (
        "architecture-decision-records",
        "architecture/architecture-decision-records",
        None,
    ),
    ("context-fundamentals", "context/context-fundamentals", None),
    ("context-compression", "context/context-compression", None),
    ("context-driven-development", "context/context-driven-development", None),
    ("context-optimizer", "context/context-optimizer", None),
    ("deslop", "utilities/deslop", None),
    ("find-skills", "utilities/find-skills", None),
    ("insights", "utilities/insights", None),
    ("learn-rule", "utilities/learn-rule", None),
    ("pair-programming", "utilities/pair-programming", None),
    ("parallel-worktrees", "utilities/parallel-worktrees", None),
    ("replay-learnings", "utilities/replay-learnings", None),
    ("session-handoff", "utilities/session-handoff", None),
    ("skill-builder", "utilities/skill-builder", None),
    ("smart-commit", "utilities/smart-commit", None),
    ("sparc-methodology", "utilities/sparc-methodology", None),
    ("stream-chain", "utilities/stream-chain", None),
    ("wrap-up", "utilities/wrap-up", None),
    # 1b. Product / domain aliases
    ("agentdb-learning-plugins", "products/agentdb", "learning-plugins"),
    ("agentdb-memory-patterns", "products/agentdb", "memory-patterns"),
    ("agentdb-performance-optimization", "products/agentdb", "perf-optimization"),
    ("agentdb-vector-search", "products/agentdb", "vector-search"),
    ("reasoningbank-with-agentdb", "products/reasoningbank", "agentdb-integration"),
    ("hive-mind-advanced", "products/hive-mind", "advanced"),
    ("flow-nexus-platform", "products/flow-nexus", "platform"),
    ("flow-nexus-swarm", "products/flow-nexus/swarm", None),
    ("performance-analysis", "engineering/performance", None),
    ("api-documenter", "engineering/api", "documenter"),
    ("api-documentation-generator", "engineering/api", "doc-generator"),
    ("api-security-best-practices", "engineering/security", "api-security"),
    ("backend-architect", "engineering/backend", "architect"),
    ("agent-agentic-payments", "domain/payments", None),
    # 1c. GitHub / platform aliases
    ("github-workflow-automation", "platform/github", "workflow-automation"),
    ("github-code-review", "platform/github", "code-review"),
    ("github-multi-repo", "platform/github", "multi-repo"),
    ("github-project-management", "platform/github", "project-management"),
    ("github-release-management", "platform/github", "release-management"),
    # 1d. V3-specific skills
    ("v3-cli-modernization", "products/v3", "cli-modernization"),
    ("v3-core-implementation", "products/v3", "core-implementation"),
    ("v3-ddd-architecture", "products/v3", "ddd-architecture"),
    ("v3-deep-integration", "products/v3", "deep-integration"),
    ("v3-mcp-optimization", "products/v3", "mcp-optimization"),
    ("v3-memory-unification", "products/v3", "memory-unification"),
    ("v3-performance-optimization", "products/v3", "performance-optimization"),
    ("v3-security-overhaul", "products/v3", "security-overhaul"),
    ("v3-swarm-coordination", "products/v3", "swarm-coordination"),
    # 1e. Orchestration / engineering agent-* wrappers
    ("agent-benchmark-suite", "engineering/performance", "benchmarks"),
    ("agent-performance-benchmarker", "engineering/performance", "benchmarker"),
    ("agent-performance-monitor", "engineering/performance", "monitor"),
    ("agent-performance-optimizer", "engineering/performance", "optimizer"),
    ("agent-code-analyzer", "quality/code-review", "analyzer"),
    ("agent-analyze-code-quality", "quality/code-review", "quality-analysis"),
    (
        "agent-production-validator",
        "quality/verification-quality-assurance",
        "prod-validator",
    ),
    ("agent-code-review-swarm", "quality/code-review", "swarm"),
    ("agent-tdd-london-swarm", "engineering/testing", "tdd-london"),
    ("agent-test-long-runner", "engineering/testing", "long-runner"),
    ("agent-dev-backend-api", "engineering/backend", "api"),
    ("agent-docs-api-openapi", "engineering/api", "openapi"),
    ("agent-authentication", "engineering/security", "auth"),
    ("agent-architecture", "architecture/architect-review", None),
    ("agent-arch-system-design", "architecture/", "system-design"),
    ("agent-repo-architect", "architecture/", "repo"),
    ("agent-pseudocode", "core/planning", "pseudocode"),
    ("agent-refinement", "core/", "refinement"),
    ("agent-base-template-generator", "utilities/skill-builder", "template"),
    ("agent-scout-explorer", "research/investigation", "scout"),
    ("agent-memory-coordinator", "memory/memory-management", "coordinator"),
    ("agent-user-tools", "products/flow-nexus", "user-tools"),
    # 1f. Orchestration topology aliases
    ("agent-byzantine-coordinator", "orchestration/consensus", "byzantine"),
    ("agent-gossip-coordinator", "orchestration/coordination", "gossip"),
    ("agent-hierarchical-coordinator", "orchestration/coordination", "hierarchical"),
    (
        "agent-collective-intelligence-coordinator",
        "orchestration/coordination",
        "collective",
    ),
    ("agent-mesh-coordinator", "orchestration/coordination", "mesh"),
    ("agent-raft-manager", "orchestration/consensus", "raft"),
    ("agent-quorum-manager", "orchestration/consensus", "quorum"),
    ("agent-topology-optimizer", "orchestration/swarm", "topology"),
    ("agent-coordinator-swarm-init", "orchestration/swarm", "init"),
    ("agent-multi-repo-swarm", "orchestration/swarm", "multi-repo"),
    ("agent-release-swarm", "orchestration/swarm", "release"),
    ("agent-swarm-issue", "orchestration/swarm", "issue"),
    ("agent-swarm-pr", "orchestration/swarm", "pr"),
    ("agent-swarm-memory-manager", "orchestration/swarm", "memory"),
    ("agent-sync-coordinator", "orchestration/coordination", "sync"),
    ("agent-resource-allocator", "orchestration/core", "resource-alloc"),
    ("agent-load-balancer", "orchestration/core", "load-balance"),
    ("agent-matrix-optimizer", "orchestration/core", "matrix"),
    ("agent-queen-coordinator", "orchestration/swarm", "queen"),
    ("agent-orchestrator-task", "orchestration/core", "task"),
    # 1g. GitHub / platform agent aliases
    ("agent-github-pr-manager", "platform/github", "pr-manager"),
    ("agent-github-modes", "platform/github", "modes"),
    ("agent-pr-manager", "platform/github", "pr-manager"),
    ("agent-project-board-sync", "platform/github", "project-board"),
    ("agent-issue-tracker", "platform/github", "issues"),
    ("agent-ops-cicd-github", "platform/github", "cicd"),
    ("agent-release-manager", "platform/github", "release"),
    # 1h. V3-specific agent aliases
    ("agent-v3-integration-architect", "products/v3", "integration-architect"),
    ("agent-v3-memory-specialist", "products/v3", "memory-specialist"),
    ("agent-v3-performance-engineer", "products/v3", "performance-engineer"),
    ("agent-v3-queen-coordinator", "products/v3", "queen-coordinator"),
    ("agent-v3-security-architect", "products/v3", "security-architect"),
]


def make_stub(legacy_name: str, canonical_dest: str, mode: str | None) -> str:
    """Generate stub SKILL.md content."""
    dest_clean = canonical_dest.rstrip("/")
    headline = f"# DEPRECATED: This skill has moved to {dest_clean}"
    see_line = f"# See {dest_clean}/SKILL.md for the canonical skill"

    lines = [headline, see_line, ""]

    if mode:
        lines.append(f"Legacy alias of **{dest_clean}** (mode: {mode}).")
    else:
        lines.append(f"Legacy alias of **{dest_clean}**.")

    lines.append(f"Please use: {dest_clean}")
    lines.append("")
    lines.append("> Policy: docs/architecture/skill-system-design.md")
    lines.append("")
    return "\n".join(lines)


def main():
    stubbed = 0
    skipped_already_stub = 0
    skipped_missing_dir = 0
    skipped_missing_file = 0
    failures = []

    for legacy_name, canonical_dest, mode in ALIASES:
        skill_dir = SKILLS_ROOT / legacy_name
        skill_md = skill_dir / "SKILL.md"

        # Check directory exists
        if not skill_dir.is_dir():
            failures.append((legacy_name, "directory not found"))
            skipped_missing_dir += 1
            continue

        # Check SKILL.md exists
        if not skill_md.is_file():
            failures.append((legacy_name, "SKILL.md not found"))
            skipped_missing_file += 1
            continue

        # Check if already a stub (starts with # DEPRECATED)
        with open(skill_md, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
        if first_line.startswith("# DEPRECATED"):
            skipped_already_stub += 1
            continue

        # Archive the existing SKILL.md
        archive_dir = ARCHIVE_ROOT / legacy_name
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_dest = archive_dir / "SKILL.md"
        shutil.copy2(skill_md, archive_dest)

        # Write stub
        stub_content = make_stub(legacy_name, canonical_dest, mode)
        with open(skill_md, "w", encoding="utf-8") as f:
            f.write(stub_content)

        stubbed += 1

    # Report
    print("=" * 60)
    print("LEGACY ALIAS STUB CONVERSION REPORT")
    print("=" * 60)
    print(f"Total aliases in manifest:     {len(ALIASES)}")
    print(f"Successfully stubbed:          {stubbed}")
    print(f"Skipped (already stubbed):     {skipped_already_stub}")
    print(f"Skipped (missing directory):   {skipped_missing_dir}")
    print(f"Skipped (missing SKILL.md):    {skipped_missing_file}")
    print()

    if failures:
        print(f"FAILURES ({len(failures)}):")
        for name, reason in failures:
            print(f"  - {name}: {reason}")
    else:
        print("No failures.")
    print()
    print(f"Archives written to: {ARCHIVE_ROOT}/")


if __name__ == "__main__":
    main()
