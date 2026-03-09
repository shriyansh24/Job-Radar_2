# Adding a Skill

## Quick rule
Before adding a skill, decide whether it should be a **new skill** or a **mode** of an existing canonical skill. Prefer a mode when possible.

## Step 1: Classify the skill type
Every skill must have exactly one type:
persona, capability, workflow, integration, product, reference, utility
If you cannot classify it, do not add it yet.

## Step 2: Choose the canonical location
Canonical skills live in `.agents/skills/` under one taxonomy folder:
core, engineering, orchestration, architecture, research, quality, memory, context,
platform, ops, domain, products, reference, utilities

## Step 3: Decide "mode vs new skill"
Prefer a MODE when:
- same goal, different strategy
- small instruction differences
Prefer a NEW SKILL when:
- meaningfully different goal
- different inputs/outputs
- would confuse users if collapsed

## Step 4: Create the skill folder
Create a folder in the canonical taxonomy and include at minimum:
- SKILL.md
- skill.yaml
Optionally add: resources/, scripts/, assets/, references/

## Step 5: Write skill.yaml
Minimum required fields:
- id, name, type, category, legacy_paths, aliases, status, notes
Optional: modes, tools, inputs, outputs

## Step 6: Write SKILL.md
Include:
- purpose
- expected inputs
- expected outputs
- constraints (do/don't)
- examples

## Step 7: If renaming/relocating, add compatibility stubs
If replacing an old name/path:
- keep the old folder
- replace old SKILL.md with a short redirect stub
- record legacy path in skill.yaml
Prefer stubs over symlinks on Windows.

## Step 8: Validate discovery
Confirm:
- new canonical path is discoverable
- old names (if any) are still discoverable
- canonical IDs are unique

## Checklist
- [ ] Type classified
- [ ] Correct taxonomy chosen
- [ ] Mode vs new decided
- [ ] skill.yaml created
- [ ] SKILL.md written
- [ ] Stubs added (if needed)
- [ ] Discovery validated
