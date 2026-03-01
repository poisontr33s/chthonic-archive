#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
Path Naming Audit - dry-run naming governance for files and folders.

Scans the repository, classifies current file/folder naming styles, and emits
an actionable dry-run rename plan only where the naming policy is mature enough
to be applied mechanically. Ambiguous lanes are inventoried but not renamed.

@SID:           TOOL_PATH_NAMING_AUDIT_V1
@Type:          Utility
@Context:       Repo structure / naming governance / dry-run prerequisite

Usage:
  uv run scripts/path_naming_audit.py
  uv run scripts/path_naming_audit.py --json
  uv run scripts/path_naming_audit.py --strict
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.lib.shared import configure_utf8_output, find_repo_root

REPO_ROOT = find_repo_root(Path(__file__).resolve())

SKIP_DIRS: set[str] = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "target",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".next",
    "book",
}

DOC_LIKE_ROOTS: set[str] = {
    "docs",
    ".github",
    ".temple",
    "claude",
    "codex",
    "dumpster-dive",
    "chthonic-golden",
}

SCRIPT_TEXT_EXTENSIONS: set[str] = {
    ".py",
    ".ps1",
    ".sh",
    ".rb",
}

SCRIPT_SLUG_EXTENSIONS: set[str] = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
}

RESERVED_EXACT_NAMES: set[str] = {
    "AGENTS.md",
    "AGENT_COMMON.md",
    "README.md",
    "GEMINI.md",
    "NEXT.md",
    "LICENSE",
    "package.json",
    "bun.lock",
    "bunfig.toml",
    "book.toml",
    "Cargo.toml",
    "Cargo.lock",
    "tsconfig.json",
    "settings.json",
    ".gitignore",
    ".gitattributes",
    ".vscodeignore",
    ".copilotignore",
    ".python-version",
    "SKILL.md",
    # GitHub Copilot canonical paths — loaded by exact name
    "copilot-instructions.md",
    "copilot-instructions.archive.md",
}

# Paths under these .github/ subdirectories are wired into VS Code
# instruction/prompt configs by absolute path. Renaming them requires
# synchronized config updates, not mechanical dry-run renames.
COORDINATED_RENAME_DIRS: set[str] = {
    "instructions",
    "prompts",
}


@dataclass(slots=True)
class PathRecord:
    rel_path: str
    kind: str
    name: str
    style: str
    policy_family: str
    target_style: str | None
    proposed_name: str | None
    proposed_rel_path: str | None
    reason: str


def split_tokens(raw: str) -> list[str]:
    normalized = raw
    normalized = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", normalized)
    normalized = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", normalized)
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"[_\-.]+", " ", normalized)
    tokens = re.findall(r"[A-Za-z0-9]+", normalized)
    return [token for token in tokens if token]


def detect_style(name: str, kind: str) -> str:
    stem = name if kind == "dir" else Path(name).stem
    hidden = stem.startswith(".")
    if hidden:
        stem = stem[1:]
    if not stem:
        return "hidden"
    if re.fullmatch(r"[A-Z0-9]+(?:_[A-Z0-9]+)+", stem):
        return "hidden-screaming-snake" if hidden else "screaming-snake"
    if re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)+", stem):
        return "hidden-snake" if hidden else "snake"
    if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)+", stem):
        return "hidden-kebab" if hidden else "kebab"
    if re.fullmatch(r"[A-Z0-9]+(?:-[A-Z0-9]+)+", stem):
        return "hidden-screaming-kebab" if hidden else "screaming-kebab"
    if re.fullmatch(r"[A-Z][A-Za-z0-9]+(?:[A-Z][A-Za-z0-9]+)*", stem):
        return "hidden-pascal" if hidden else "pascal"
    if re.fullmatch(r"[a-z]+(?:[A-Z][A-Za-z0-9]+)+", stem):
        return "hidden-camel" if hidden else "camel"
    if re.fullmatch(r"[a-z0-9]+", stem):
        return "hidden-lower" if hidden else "lower"
    if re.fullmatch(r"[A-Z0-9]+", stem):
        return "hidden-upper" if hidden else "upper"
    return "hidden-mixed" if hidden else "mixed"


def to_style(name: str, kind: str, target_style: str) -> str:
    path = Path(name)
    stem = name if kind == "dir" else path.stem
    suffix = "" if kind == "dir" else path.suffix
    hidden_prefix = "." if stem.startswith(".") else ""
    if hidden_prefix:
        stem = stem[1:]
    tokens = split_tokens(stem)
    if not tokens:
        return name
    if target_style == "screaming-snake":
        rendered = "_".join(token.upper() for token in tokens)
    elif target_style == "snake":
        rendered = "_".join(token.lower() for token in tokens)
    elif target_style == "kebab":
        rendered = "-".join(token.lower() for token in tokens)
    else:
        return name
    return f"{hidden_prefix}{rendered}{suffix}"


def determine_policy(rel_path: Path, kind: str) -> tuple[str, str | None, str]:
    name = rel_path.name
    parts = rel_path.parts
    suffix = "" if kind == "dir" else rel_path.suffix.lower()

    if name in RESERVED_EXACT_NAMES:
        return ("reserved", None, "reserved exact filename")

    if kind == "dir":
        if name.startswith(".") and len(name) > 1:
            return ("directory", "kebab", "directories normalize to kebab-case; preserve dot prefix")
        return ("directory", "kebab", "directories normalize to kebab-case")

    if suffix == ".md" and parts and parts[0] in DOC_LIKE_ROOTS:
        stem_upper = rel_path.stem.upper()
        if stem_upper in {"README", "AGENTS", "GEMINI", "NEXT", "INDEX", "SKILL"}:
            return ("reserved-doc", None, "reserved documentation basename")
        if len(parts) >= 2 and parts[0] == ".github" and parts[1] in COORDINATED_RENAME_DIRS:
            return (
                "coordinated-rename",
                "screaming-snake",
                "VS Code instruction/prompt wiring requires synchronized config update",
            )
        return ("docs-markdown", "screaming-snake", "doc/protocol slabstones normalize to SCREAMING_SNAKE_CASE")

    if "scripts" in parts:
        if suffix in SCRIPT_TEXT_EXTENSIONS:
            return ("script-text", "snake", "textual scripts normalize to snake_case")
        if suffix in SCRIPT_SLUG_EXTENSIONS:
            return ("script-slug", "kebab", "CLI/runtime scripts normalize to kebab-case slugs")

    return ("inventory-only", None, "lane not canonized for automatic renames yet")


def build_record(path: Path) -> PathRecord:
    rel_path = path.relative_to(REPO_ROOT)
    kind = "dir" if path.is_dir() else "file"
    style = detect_style(path.name, kind)
    policy_family, target_style, reason = determine_policy(rel_path, kind)
    proposed_name: str | None = None
    proposed_rel_path: str | None = None
    if target_style:
        candidate = to_style(path.name, kind, target_style)
        if candidate != path.name:
            proposed_name = candidate
            proposed_rel_path = rel_path.with_name(candidate).as_posix()
    return PathRecord(
        rel_path=rel_path.as_posix(),
        kind=kind,
        name=path.name,
        style=style,
        policy_family=policy_family,
        target_style=target_style,
        proposed_name=proposed_name,
        proposed_rel_path=proposed_rel_path,
        reason=reason,
    )


def walk_records() -> list[PathRecord]:
    records: list[PathRecord] = []
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [dirname for dirname in dirs if dirname not in SKIP_DIRS]
        root_path = Path(root)
        if root_path != REPO_ROOT:
            records.append(build_record(root_path))
        for filename in sorted(files):
            records.append(build_record(root_path / filename))
    return records


def build_payload(records: list[PathRecord]) -> dict[str, Any]:
    style_counts = Counter(record.style for record in records)
    kind_counts = Counter(record.kind for record in records)
    policy_counts = Counter(record.policy_family for record in records)

    rename_candidates = [record for record in records if record.proposed_rel_path]
    by_target_style = Counter(record.target_style for record in rename_candidates if record.target_style)
    by_kind = Counter(record.kind for record in rename_candidates)

    ext_style_counts: dict[str, Counter[str]] = defaultdict(Counter)
    top_level_dir_counts: dict[str, Counter[str]] = defaultdict(Counter)
    ambiguous_samples: list[dict[str, str]] = []

    for record in records:
        rel = Path(record.rel_path)
        if record.kind == "file":
            suffix = rel.suffix.lower() or "<no-ext>"
            ext_style_counts[suffix][record.style] += 1
        if rel.parts:
            top_level = rel.parts[0]
            top_level_dir_counts[top_level][record.style] += 1
        if record.policy_family == "inventory-only" and len(ambiguous_samples) < 40:
            ambiguous_samples.append(
                {
                    "path": record.rel_path,
                    "style": record.style,
                    "reason": record.reason,
                }
            )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "repo_root": str(REPO_ROOT),
        "totals": {
            "paths": len(records),
            "files": kind_counts.get("file", 0),
            "directories": kind_counts.get("dir", 0),
            "rename_candidates": len(rename_candidates),
            "inventory_only": policy_counts.get("inventory-only", 0),
        },
        "style_counts": dict(style_counts.most_common()),
        "policy_counts": dict(policy_counts.most_common()),
        "rename_candidates_by_target_style": dict(by_target_style.most_common()),
        "rename_candidates_by_kind": dict(by_kind.most_common()),
        "rename_candidates": [asdict(record) for record in rename_candidates],
        "ambiguous_samples": ambiguous_samples,
        "extension_style_census": {
            suffix: dict(counter.most_common())
            for suffix, counter in sorted(ext_style_counts.items())
        },
        "top_level_style_census": {
            root: dict(counter.most_common())
            for root, counter in sorted(top_level_dir_counts.items())
        },
    }


def render_report(payload: dict[str, Any], limit: int) -> str:
    lines: list[str] = []
    append = lines.append

    totals = payload["totals"]
    append("Path Naming Audit")
    append(f"repo root: {payload['repo_root']}")
    append(f"generated: {payload['generated_at']}")
    append("")
    append("Totals")
    append(f"- paths scanned: {totals['paths']}")
    append(f"- files: {totals['files']}")
    append(f"- directories: {totals['directories']}")
    append(f"- rename candidates: {totals['rename_candidates']}")
    append(f"- inventory-only paths: {totals['inventory_only']}")
    append("")

    append("Policy Families")
    for key, count in payload["policy_counts"].items():
        append(f"- {key}: {count}")
    append("")

    append("Current Naming Styles")
    for key, count in payload["style_counts"].items():
        append(f"- {key}: {count}")
    append("")

    append("Rename Candidates By Target Style")
    for key, count in payload["rename_candidates_by_target_style"].items():
        append(f"- {key}: {count}")
    append("")

    append("Top-Level Style Census")
    for root, styles in payload["top_level_style_census"].items():
        dominant = next(iter(styles.items())) if styles else ("-", 0)
        append(f"- {root}: dominant {dominant[0]} ({dominant[1]})")
    append("")

    append(f"Rename Candidates (first {limit})")
    for row in payload["rename_candidates"][:limit]:
        append(
            f"- {row['rel_path']} -> {row['proposed_rel_path']} "
            f"[{row['policy_family']} / {row['target_style']}]"
        )
    if not payload["rename_candidates"]:
        append("- none")
    append("")

    append("Ambiguous Inventory Samples")
    for row in payload["ambiguous_samples"][:limit]:
        append(f"- {row['path']} [{row['style']}] ({row['reason']})")
    if not payload["ambiguous_samples"]:
        append("- none")
    append("")

    append("Interpretation")
    append("- This tool is dry-run only. It does not rename anything.")
    append("- Paths in 'inventory-only' lanes were scanned and classified, but not given mechanical rename targets.")
    append("- The next rename phase should consume this report, not guess at conventions ad hoc.")
    append("")
    return "\n".join(lines)


def main() -> int:
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        description="Dry-run audit for file/folder naming governance."
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of the text report.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if rename candidates exist.")
    parser.add_argument(
        "--limit",
        type=int,
        default=80,
        help="Maximum rename/ambiguous rows to print in text mode.",
    )
    args = parser.parse_args()

    payload = build_payload(walk_records())

    if args.json:
        json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_report(payload, args.limit))

    if args.strict and payload["totals"]["rename_candidates"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
