#!/usr/bin/env python3
"""
Skill validation script.
Validates canonical skills strictly; legacy stubs are warned but not failed.

Type inference (for contributors):
- canonical skills under core/ with folders: agent, planning, specification -> persona
- canonical skills under products/ -> product
- canonical skills under platform/ -> integration
- canonical skills under reference/, context/, architecture/ -> reference
- canonical skills under utilities/ -> utility
- canonical skills under all other canonical roots -> capability

If adding a new canonical skill, add the appropriate type: field to its skill.yaml.
"""

import os
import sys
from pathlib import Path

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

SKILLS_ROOT = Path(".agents/skills")
REQUIRED_FIELDS = ["id", "name", "type", "category", "status", "notes"]

CANONICAL_ROOTS = {
    "core",
    "engineering",
    "orchestration",
    "architecture",
    "research",
    "quality",
    "memory",
    "context",
    "platform",
    "ops",
    "domain",
    "products",
    "reference",
    "utilities",
    "entrypoints",
    "workflows",
}


def is_canonical(skill_dir: Path) -> bool:
    """Check if skill is under a canonical taxonomy root."""
    parts = skill_dir.relative_to(SKILLS_ROOT).parts
    return len(parts) > 0 and parts[0] in CANONICAL_ROOTS


def find_skill_dirs(root: Path) -> list[Path]:
    """Find all directories containing SKILL.md."""
    skill_dirs = []
    for dirpath, dirnames, filenames in os.walk(root):
        if "SKILL.md" in filenames:
            skill_dirs.append(Path(dirpath))
    return skill_dirs


def check_yaml(root: Path) -> tuple[bool, str | None, dict | None]:
    """Check if skill.yaml exists and is valid. Returns (exists, error, data)."""
    yaml_path = root / "skill.yaml"
    if not yaml_path.exists():
        return False, "missing skill.yaml", None

    if not HAS_YAML:
        return False, "PyYAML not available", None

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            return True, "empty skill.yaml", None
        return True, None, data
    except yaml.YAMLError as e:
        return True, f"invalid YAML: {e}", None
    except Exception as e:
        return True, f"read error: {e}", None


def validate_fields(data: dict) -> list[str]:
    """Check for required fields."""
    missing = []
    for field in REQUIRED_FIELDS:
        if field not in data:
            missing.append(field)
    return missing


def main():
    if not HAS_YAML:
        print("ERROR: PyYAML is not installed.")
        print("Install it with: pip install pyyaml")
        sys.exit(1)

    if not SKILLS_ROOT.exists():
        print(f"ERROR: Skills root not found: {SKILLS_ROOT}")
        sys.exit(1)

    skill_dirs = find_skill_dirs(SKILLS_ROOT)
    total = len(skill_dirs)

    canonical_errors = []
    legacy_warnings = []
    canonical_ids: dict[str, Path] = {}
    canonical_validated = 0

    for skill_dir in skill_dirs:
        canonical = is_canonical(skill_dir)
        has_yaml, yaml_error, data = check_yaml(skill_dir)

        if canonical:
            if not has_yaml:
                canonical_errors.append(
                    (skill_dir, f"missing skill.yaml: {yaml_error}")
                )
                continue

            if yaml_error:
                canonical_errors.append((skill_dir, yaml_error))
                continue

            if data is None:
                canonical_errors.append((skill_dir, "empty skill.yaml"))
                continue

            missing = validate_fields(data)
            if missing:
                canonical_errors.append(
                    (skill_dir, f"missing fields: {', '.join(missing)}")
                )
                continue

            if "id" in data:
                skill_id = data["id"]
                if skill_id in canonical_ids:
                    canonical_errors.append(
                        (
                            skill_dir,
                            f"duplicate id '{skill_id}' (first seen in {canonical_ids[skill_id]})",
                        )
                    )
                else:
                    canonical_ids[skill_id] = skill_dir
                    canonical_validated += 1

        else:
            if not has_yaml:
                legacy_warnings.append(
                    (skill_dir, "legacy stub without skill.yaml (OK)")
                )
            elif yaml_error:
                legacy_warnings.append(
                    (skill_dir, f"legacy skill.yaml issue: {yaml_error}")
                )
            elif data and "id" in data:
                if data["id"] in canonical_ids:
                    legacy_warnings.append(
                        (skill_dir, f"duplicate id '{data['id']}' vs canonical")
                    )

    print("=" * 60)
    print("SKILL VALIDATION REPORT")
    print("=" * 60)
    print(f"Total skills scanned: {total}")
    print(f"Canonical skills validated: {canonical_validated}")
    print()

    print(f"CANONICAL ERRORS (fail): {len(canonical_errors)}")
    if canonical_errors:
        for path, err in canonical_errors:
            print(f"  - {path}: {err}")
    else:
        print("  (none)")
    print()

    print(f"LEGACY WARNINGS ( informational): {len(legacy_warnings)}")
    if legacy_warnings:
        for path, err in legacy_warnings[:10]:
            print(f"  - {path}: {err}")
        if len(legacy_warnings) > 10:
            print(f"  ... and {len(legacy_warnings) - 10} more")
    else:
        print("  (none)")
    print()

    if canonical_errors:
        print("VALIDATION FAILED (canonical errors found)")
        sys.exit(1)
    else:
        print("VALIDATION PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
