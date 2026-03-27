#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: check_python_policy.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
@SID: TOOL_CHECK_PYTHON_POLICY
@Shabti: Validation Script
@Context: Repository Hygiene / Python Execution Policy Enforcement
@Implements: CONCEPT_CHECK_PYTHON_POLICY
@Purpose:       Script logic for check_python_policy.py.
This script scans specified files in the repository to enforce Python execution and dependency policies. It checks for:
- Prohibited patterns such as "cmd /c", "pip install", and raw "python *.py" usage outside of "uv run".
- Optional proto-SSOT style signals in markdown files when --proto-ssot-style is enabled.
Usage: uv run scripts/check_python_policy.py [--repo-root <path>] [--paths <glob1> <glob2> ...] [--include-docs] [--proto-ssot-style]
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from lib.ssot_paths import SSOT_PROTO

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".next", "dist", "build"}
DEFAULT_GLOBS = [
    "scripts/*.py",
    "scripts/*.ps1",
    ".codex/skills/**/scripts/*.py",
    ".claude/skills/**/scripts/*.py",
]
DOC_GLOBS = [
    "AGENT_COMMON.md",
    "AGENTS.md",
    ".codex/skills/**/SKILL.md",
    ".claude/skills/**/SKILL.md",
]
PROTO_GLOBS = [
    SSOT_PROTO,
    "codex/mailbox/*.md",
    "claude/mailbox/*.md",
]

RULES = {
    "no_cmd_c": re.compile(r"\bcmd\s*/c\b", re.IGNORECASE),
    "no_pip_install": re.compile(r"\bpip(?:3)?\s+install\b", re.IGNORECASE),
    "no_raw_python_py": re.compile(r"(?<!uv run )\bpython(?:3)?\s+[^\n`]*\.py\b", re.IGNORECASE),
}
PROTO_STYLE_RULES = {
    "symbolic_tuple_notation": re.compile(r"\*\*\(`[^`]+`\)\*\*"),
    "semantic_arrow_connector": re.compile(r"(→|<->|↔)"),
    "backtick_presence": re.compile(r"`[^`]+`"),
    "section_separator": re.compile(r"(?m)^---\s*$"),
}


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def collect_targets(repo_root: Path, globs: list[str]) -> list[Path]:
    found: set[Path] = set()
    for pattern in globs:
        for path in repo_root.glob(pattern):
            if not path.is_file() or should_skip(path):
                continue
            found.add(path)
    return sorted(found)


def find_violations(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    issues: list[str] = []

    if path.suffix == ".py" and re.search(r"(?m)^#\s*///\s*script\b", text):
        issues.append("inline_script_deps: found '# /// script' block")
        return issues

    # Command-policy checks are enforced on shell/docs surfaces, not Python source bodies.
    if path.suffix in {".ps1", ".md"}:
        for rule_name, pattern in RULES.items():
            if pattern.search(text):
                issues.append(f"{rule_name}: pattern matched")
    return issues


def find_proto_style_violations(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    issues: list[str] = []
    if path.suffix.lower() != ".md":
        return issues

    # Require all four signals in proto mode.
    for rule_name, pattern in PROTO_STYLE_RULES.items():
        if not pattern.search(text):
            issues.append(f"proto_{rule_name}: missing")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Repository Python execution/dependency policy checker.")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--paths", nargs="*", help="Override target globs")
    parser.add_argument("--include-docs", action="store_true", help="Also scan docs and SKILL.md files")
    parser.add_argument(
        "--proto-ssot-style",
        action="store_true",
        help="Check markdown files for proto-SSOT symbolic/backtick style signals.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if args.proto_ssot_style:
        globs = args.paths if args.paths else list(PROTO_GLOBS)
    else:
        globs = args.paths if args.paths else list(DEFAULT_GLOBS)
        if args.include_docs and not args.paths:
            globs.extend(DOC_GLOBS)
    targets = collect_targets(repo_root, globs)

    violations = []
    for path in targets:
        issues = find_proto_style_violations(path) if args.proto_ssot_style else find_violations(path)
        if issues:
            rel = path.relative_to(repo_root).as_posix()
            violations.append((rel, issues))

    print(f"Checked files: {len(targets)}")
    print(f"Files with violations: {len(violations)}")
    for rel, issues in violations:
        print(rel)
        for issue in issues:
            print(f"  - {issue}")

    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
