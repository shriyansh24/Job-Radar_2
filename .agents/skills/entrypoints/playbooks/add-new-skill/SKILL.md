# Playbook: Add New Skill

Chain of personas and capabilities for creating a new canonical skill.

## Steps

| # | Phase | Persona / Capability | Canonical path | What to do |
|---|-------|---------------------|----------------|------------|
| 1 | Specify | Specification | `core/personas/specification` | Define what the skill does, when to use it, its category and type |
| 2 | Implement | Coder | `core/personas/coder` | Create the canonical folder with `skill.yaml` and `SKILL.md` |
| 3 | Review | Reviewer | `core/personas/reviewer` | Verify YAML fields, check for ID collisions, validate content quality |
| 4 | Build | Skill Builder | `utilities/skill-builder` | Ensure proper frontmatter structure and directory conventions |
| 5 | Wrap-up | Wrap-up | `utilities/wrap-up` | Run `validate_skills.py`, summarize, commit |

## When to use

- Adding a brand-new skill to the taxonomy
- Promoting a legacy skill to canonical status
- Creating entrypoints or playbooks

## When NOT to use

- Modifying an existing skill (just edit it directly)
- Deprecating a skill (use the stub redirect pattern)

## Handoff

Provide to Step 1: skill purpose, proposed category, any existing legacy content.
