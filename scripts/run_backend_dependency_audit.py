from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_policy(policy_path: Path) -> list[str]:
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    reviewed = payload.get("reviewed_exceptions", [])
    if not isinstance(reviewed, list):
        raise ValueError("pip-audit policy must contain a list of reviewed_exceptions.")
    ignore_ids: list[str] = []
    for entry in reviewed:
        if not isinstance(entry, dict) or "id" not in entry:
            raise ValueError("Each reviewed pip-audit exception must contain an 'id'.")
        ignore_ids.append(str(entry["id"]))
    return ignore_ids


def main() -> int:
    repo_root = _repo_root()
    parser = argparse.ArgumentParser(
        description="Run backend pip-audit using the checked-in reviewed exception policy."
    )
    parser.add_argument(
        "--requirements",
        default=".ci-requirements.txt",
        help="Requirements file to audit, relative to the backend directory.",
    )
    parser.add_argument(
        "--policy",
        default="backend/pip-audit-policy.json",
        help="Policy file with reviewed pip-audit exceptions, relative to the repo root.",
    )
    args = parser.parse_args()

    backend_dir = repo_root / "backend"
    policy_path = repo_root / args.policy
    ignore_ids = _load_policy(policy_path)

    command = [
        "uv",
        "tool",
        "run",
        "pip-audit",
        "-r",
        args.requirements,
    ]
    for ignore_id in ignore_ids:
        command.extend(["--ignore-vuln", ignore_id])

    completed = subprocess.run(command, cwd=backend_dir, check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    sys.exit(main())
