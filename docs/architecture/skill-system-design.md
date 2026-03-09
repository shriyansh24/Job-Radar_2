# Skill System Design

## Purpose

This repository contains a large library of LLM "skills" used by multiple agent runtimes (Cursor, Claude Code, etc.). Over time, skills accumulated from multiple packs and began to sprawl.

This document defines:
- what a "skill" is
- the allowed skill types
- the canonical directory layout
- how compatibility is preserved
- how new skills are added without reintroducing chaos

## Definitions

### Skill
A **skill** is a self-contained instruction bundle that can be loaded by an LLM agent runtime. A skill typically contains:
- `SKILL.md`: primary instructions
- optional `resources/`, `scripts/`, `assets/`, `references/`
- `skill.yaml`: machine-readable metadata used for indexing, taxonomy, and compatibility

### Canonical Skill
A **canonical skill** is the single source of truth for a capability/persona/workflow/etc. Canonical skills live in the taxonomy folders under `.agents/skills/`.

### Compatibility Stub
A **compatibility stub** is a minimal `SKILL.md` left at an old location to preserve existing references. Stubs redirect users/agents to the canonical path.

On Windows, stubs are preferred over symlinks due to filesystem/link fragility.

## Skill Types

Every skill MUST be categorized into exactly one of the following types.

### 1) Persona
A **persona** defines *how an agent thinks*.
Personas optimize for a viewpoint and output style. Personas typically call multiple capabilities.
Examples: coder, planner, reviewer, researcher, tester, architect

### 2) Capability
A **capability** defines *what an agent can do*.
Examples: engineering/api, engineering/performance, orchestration/consensus, memory/management, quality/code-review

### 3) Workflow Pattern
A **workflow** defines *how work is executed* (sequence, handoffs, parallelism).
Examples: swarm workflows, plan→implement→review loops, workflow automation patterns

### 4) Integration (Platform)
An **integration** defines *where the agent operates* (GitHub, a specific CLI, a runtime framework).
Examples: platform/github, platform/azure-agents

### 5) Product Integration
A **product integration** is a specialized ecosystem tied to a particular tool or framework.
Examples: products/flow-nexus, products/agentdb, products/v3

### 6) Reference Knowledge
Reference skills are standards/guides/patterns used for grounding and consistency.
Examples: clean code, API patterns, architecture patterns, backend guidelines, context fundamentals

### 7) Utility
Utilities are helpers that assist development or usage, but are not core reasoning modules.
Examples: wrap-up, session-handoff, sandbox, templates, worktrees helpers

### 8) Ambiguous (Temporary Only)
"Ambiguous" is a quarantine state. Any ambiguous skill must be resolved into one of the above types or archived later.

## Directory Layout

Canonical layout lives under `.agents/skills/` with taxonomy folders:
core, engineering, orchestration, architecture, research, quality, memory, context,
platform, ops, domain, products, reference, utilities

Rule: Canonical skills must live under exactly one taxonomy folder.

## Manifest Format (skill.yaml)

Every canonical skill directory MUST include a `skill.yaml`.
Minimum fields:
- id, name, type, category, legacy_paths, aliases, status, notes

Optional:
- modes, tools, inputs, outputs

## Modes vs New Skills

Use a MODE when:
- same goal, different strategy
- small instruction differences
Create a NEW SKILL when:
- different goal or IO contract
- merging reduces clarity

## Compatibility Policy

Preserve compatibility via stub SKILL.md files at old locations.
Stubs must be minimal, clearly point to canonical location, and not diverge.

## Platform Surfaces

Platform surfaces are views (e.g., .claude/skills, .agent/skills).
Rules:
- canonical skills live only in .agents/skills
- platform surfaces reference canonical skills
- platform overrides belong in platform config, not duplicated skills

## Governance Rules (Preventing Sprawl)

1) Every skill has an owner area (engineering/orchestration/products/etc.)
2) New skills require classification (type/category + reason not a mode)
3) Avoid micro-skills; prefer fewer skills + clearer modes
4) Deprecation is explicit (status: deprecated + redirect stub)

## Review Checklist

1) What type is it?
2) Correct category?
3) Mode vs new skill?
4) Overlap with existing canonical?
5) Needs platform/product isolation?
6) Has skill.yaml?
7) Legacy paths/aliases updated?
8) Discovery validated?

## Current Migration Status

Active migration:
- no deletion
- stubs preserve compatibility
- consolidations happen family-by-family
- high-risk product ecosystems (e.g., v3) remain deferred until stability is proven
