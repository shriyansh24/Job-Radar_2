# Deprecating a Skill

Deprecation means a skill remains discoverable, but is no longer the recommended entrypoint.

Do NOT hard-delete skills during active migration.

## Step 1: Decide deprecation type
A) Replaced by another skill
B) Rolled into a mode
C) Obsolete / no replacement (deprecate first; archive later)

## Step 2: Update the canonical replacement
Ensure the replacement skill exists, documents how to achieve the old outcomes, and has skill.yaml.

## Step 3: Mark the old skill deprecated
In old skill.yaml:
- status: deprecated
- notes: replacement canonical path/ID (+ mode if relevant)
If no manifest exists, add a minimal one.

## Step 4: Replace old SKILL.md with a compatibility stub
Stub must:
- state it is deprecated
- point to canonical replacement path/ID
- specify replacement mode if relevant
Keep stubs minimal.

## Step 5: Record the mapping
Update/append to reports/legacy_mapping_report.md with:
- old path
- new canonical path/ID
- mode (if applicable)
- date
- reason

## Step 6: Validate
Confirm:
- old name still discoverable
- new canonical still discoverable
- stubs don't contradict canonical instructions

## Archival policy (later)
Only after a waiting period + audit confirming no reliance:
- move deprecated skills to _archive/
During active migration:
- do not delete
- deprecate + stub
- keep compatibility intact
