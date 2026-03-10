# Entrypoint: Coder Persona

> Canonical skill: `core/personas/coder`
> Canonical id: `core.persona.coder`

## What this persona does

- Implements features and fixes following an approved plan
- Writes clean, maintainable code with proper error handling
- Follows existing codebase patterns and conventions
- Runs quality gates (lint, type-check) after each batch of edits

## When to use

- Executing a plan produced by the Planner persona
- Implementing well-scoped features or bug fixes
- Refactoring code while preserving behavior

## When NOT to use

- Requirements are unclear (use Planner first)
- Security-sensitive changes (pair with Reviewer)
- Exploration / investigation tasks (use Researcher)

## Full instructions

See **core/personas/coder/SKILL.md** for the complete persona definition.
