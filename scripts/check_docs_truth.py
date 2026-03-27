from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DOC_FILES = [
    ROOT / "README.md",
    ROOT / "AGENTS.md",
    ROOT / "CLAUDE.md",
    ROOT / "PROJECT_STATUS.md",
    ROOT / "DECISIONS.md",
    ROOT / "SECURITY.md",
]
DOC_FILES.extend(sorted((ROOT / "docs" / "current-state").glob("*.md")))

LINK_RE = re.compile(r"\[[^\]]+]\(([^)]+)\)")
CODE_RE = re.compile(r"`([^`\n]+)`")
ROOT_SEGMENTS = {
    ".claude",
    ".env.example",
    ".github",
    "AGENTS.md",
    "CLAUDE.md",
    "DECISIONS.md",
    "PROJECT_STATUS.md",
    "README.md",
    "SECURITY.md",
    "THIRD_PARTY_CODE.md",
    "backend",
    "docker-compose.dev.yml",
    "docker-compose.yml",
    "docs",
    "frontend",
    "infra",
    "scripts",
}
PATH_PREFIXES = (
    ".claude/",
    ".env.example",
    ".github/",
    "AGENTS.md",
    "CLAUDE.md",
    "DECISIONS.md",
    "PROJECT_STATUS.md",
    "README.md",
    "SECURITY.md",
    "THIRD_PARTY_CODE.md",
    "backend/",
    "docker-compose.dev.yml",
    "docker-compose.yml",
    "docs/",
    "frontend/",
    "infra/",
    "scripts/",
)
OPTIONAL_PATHS = {
    ".claude/launch.json",
    ".claude/worktrees/",
}
VALID_SUFFIXES = (
    "/",
    ".md",
    ".txt",
    ".py",
    ".ts",
    ".tsx",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".env",
    ".lock",
)


def looks_like_repo_path(candidate: str) -> bool:
    if not candidate or "://" in candidate or candidate.startswith("#"):
        return False
    if candidate.startswith(("mailto:", "http:", "https:")):
        return False
    if "*" in candidate or "{" in candidate or "}" in candidate:
        return False
    if any(candidate.startswith(prefix) for prefix in PATH_PREFIXES):
        return True
    if "/" not in candidate or not candidate.endswith(VALID_SUFFIXES):
        return False
    first_segment = candidate.split("/", 1)[0]
    return first_segment in ROOT_SEGMENTS


def normalize_code_candidate(candidate: str) -> str:
    trimmed = candidate.strip().rstrip(".,:;)")
    if " " in trimmed:
        return ""
    return trimmed.replace("\\", "/")


def resolve_reference(doc_file: Path, reference: str) -> Path:
    normalized = reference.replace("\\", "/")
    if normalized.startswith("/") or normalized in ROOT_SEGMENTS or any(
        normalized.startswith(prefix) for prefix in PATH_PREFIXES
    ):
        return ROOT / normalized.lstrip("/")
    return (doc_file.parent / normalized).resolve()


def iter_references(doc_file: Path) -> list[tuple[str, str]]:
    content = doc_file.read_text(encoding="utf-8")
    references: list[tuple[str, str]] = []
    for match in LINK_RE.finditer(content):
        target = match.group(1).strip()
        if looks_like_repo_path(target):
            references.append(("link", target))
    for match in CODE_RE.finditer(content):
        target = normalize_code_candidate(match.group(1))
        if target and looks_like_repo_path(target):
            references.append(("code", target))
    return references


def main() -> int:
    missing: list[str] = []
    for doc_file in DOC_FILES:
        for ref_kind, reference in iter_references(doc_file):
            resolved = resolve_reference(doc_file, reference)
            if reference in OPTIONAL_PATHS:
                continue
            if not resolved.exists():
                missing.append(
                    f"{doc_file.relative_to(ROOT)} [{ref_kind}] -> {reference} -> {resolved.relative_to(ROOT)}"
                )

    if missing:
        print("Missing documentation references detected:")
        for item in missing:
            print(f"- {item}")
        return 1

    print("Documentation references validated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
