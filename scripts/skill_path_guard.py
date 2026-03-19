#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Skill Path Guard

Audit skill and agent settings surfaces for broken/stale repo-local path
references and optionally rewrite resolvable drift.

Primary scope:
- .codex/skills/**/SKILL.md
- .claude/skills/**/SKILL.md
- .gemini/extensions/**/SKILL.md
- .claude/settings*.json
- .gemini/settings.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from scripts.lib.shared import configure_utf8_output, find_repo_root, setup_logging


PATH_TOKEN_RE = re.compile(
    r"(?P<path>"
    r"(?:[A-Za-z]:[\\/][^`\r\n\"'\s]+)"
    r"|(?:\.\.?[\\/][^`\r\n\"'\s]+)"
    r"|(?:(?:\.codex|\.claude|\.gemini|codex|claude|gemini|scripts|docs|\.temple)[\\/][^`\r\n\"'\s]+)"
    r")"
)

EXT_HINT_RE = re.compile(r"\.(md|json|toml|yaml|yml|py|ps1|txt|schema)$", re.IGNORECASE)
OLD_ROOT_RE = re.compile(r"^[A-Za-z]:[\\/]Users[\\/]erdno[\\/]chthonic-archive", re.IGNORECASE)
SKIP_PARTS = {"node_modules", ".git", "target", "__pycache__", ".venv", "build", "dist"}


@dataclass
class Finding:
    file: str
    raw: str
    status: str
    replacement: str | None = None
    reason: str | None = None


def build_index(repo_root: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for path in repo_root.rglob("*"):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if not path.is_file():
            continue
        index.setdefault(path.name, []).append(path)
    return index


def looks_like_path(token: str) -> bool:
    if token.startswith(("http://", "https://", "mailto:")):
        return False
    if "://" in token:
        return False
    if any(ch in token for ch in ("/", "\\")):
        return True
    return bool(EXT_HINT_RE.search(token))


def normalize_candidate(raw: str, source_file: Path, repo_root: Path) -> Path | None:
    cleaned = raw.strip().strip("`'\"")
    if not looks_like_path(cleaned):
        return None
    if "<" in cleaned or ">" in cleaned:
        return None

    if OLD_ROOT_RE.match(cleaned):
        suffix = re.sub(OLD_ROOT_RE, "", cleaned).lstrip("\\/")
        return repo_root / Path(suffix)

    if re.match(r"^[A-Za-z]:[\\/]", cleaned):
        return Path(cleaned)

    if cleaned.startswith((".codex/", ".claude/", ".gemini/", "codex/", "claude/", "gemini/", "scripts/", "docs/", ".temple/")):
        return repo_root / Path(cleaned.replace("\\", "/"))

    return (source_file.parent / cleaned).resolve()


def replacement_style(raw: str, target: Path, source_file: Path, repo_root: Path) -> str:
    cleaned = raw.strip().strip("`'\"")
    if OLD_ROOT_RE.match(cleaned):
        return str(target)
    if re.match(r"^[A-Za-z]:[\\/]", cleaned):
        return str(target)
    if cleaned.startswith((".codex/", ".claude/", ".gemini/", "codex/", "claude/", "gemini/", "scripts/", "docs/", ".temple/")):
        return target.relative_to(repo_root).as_posix()
    return os.path.relpath(target, source_file.parent).replace("\\", "/")


def resolve_token(raw: str, source_file: Path, repo_root: Path, index: dict[str, list[Path]]) -> tuple[str, str | None, str | None]:
    candidate = normalize_candidate(raw, source_file, repo_root)
    if candidate is None:
        return "skip", None, None

    if candidate.exists():
        if OLD_ROOT_RE.match(raw):
            replacement = replacement_style(raw, candidate, source_file, repo_root)
            return "stale_root", replacement, "stale username/root path"
        return "ok", None, None

    basename = Path(str(candidate)).name
    matches = index.get(basename, [])
    if len(matches) == 1:
        replacement = replacement_style(raw, matches[0], source_file, repo_root)
        return "fixable", replacement, f"unique basename match: {matches[0].relative_to(repo_root).as_posix()}"
    if len(matches) > 1:
        return "ambiguous", None, f"multiple basename matches for {basename}"
    return "broken", None, "target does not exist"


def scan_file(path: Path, repo_root: Path, index: dict[str, list[Path]], apply: bool) -> list[Finding]:
    text = path.read_text(encoding="utf-8", errors="replace")
    findings: list[Finding] = []
    replacements: list[tuple[str, str]] = []

    seen: set[str] = set()
    for match in PATH_TOKEN_RE.finditer(text):
        raw = match.group("path")
        if raw in seen:
            continue
        seen.add(raw)
        status, replacement, reason = resolve_token(raw, path, repo_root, index)
        if status == "skip" or status == "ok":
            continue
        findings.append(Finding(str(path.relative_to(repo_root)), raw, status, replacement, reason))
        if apply and replacement and status in {"fixable", "stale_root"}:
            replacements.append((raw, replacement))

    if apply and replacements:
        updated = text
        for old, new in replacements:
            updated = updated.replace(old, new)
        if updated != text:
            path.write_text(updated, encoding="utf-8")

    return findings


def default_targets(repo_root: Path) -> list[Path]:
    targets: list[Path] = []
    for pattern in (
        ".codex/skills/**/SKILL.md",
        ".claude/skills/**/SKILL.md",
        ".gemini/extensions/**/SKILL.md",
        ".claude/settings.json",
        ".claude/settings.local.json",
        ".gemini/settings.json",
    ):
        targets.extend(repo_root.glob(pattern))
    return sorted({p.resolve() for p in targets if p.exists()})


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Audit/fix stale skill path references")
    parser.add_argument("--fix", action="store_true", help="Rewrite resolvable path drift in place")
    parser.add_argument("--json", action="store_true", help="Emit JSON findings")
    parser.add_argument("paths", nargs="*", help="Optional files/directories to scan")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    setup_logging(log_file=repo_root / "logs" / "skill_path_guard.log")
    index = build_index(repo_root)

    targets: list[Path] = []
    if args.paths:
        for raw in args.paths:
            p = (Path(raw) if Path(raw).is_absolute() else (repo_root / raw)).resolve()
            if p.is_dir():
                targets.extend(sorted(x for x in p.rglob("*") if x.is_file() and x.name in {"SKILL.md", "settings.json", "settings.local.json"}))
            elif p.exists():
                targets.append(p)
    else:
        targets = default_targets(repo_root)

    findings: list[Finding] = []
    for target in targets:
        findings.extend(scan_file(target, repo_root, index, args.fix))

    if args.json:
        print(json.dumps([f.__dict__ for f in findings], indent=2))
    else:
        if not findings:
            print("OK: no stale or broken skill path references found")
        else:
            for f in findings:
                print(f"[{f.status}] {f.file}: {f.raw}")
                if f.replacement:
                    print(f"  -> {f.replacement}")
                if f.reason:
                    print(f"  :: {f.reason}")

    return 0 if not any(f.status in {"broken", "ambiguous"} for f in findings) else 1


if __name__ == "__main__":
    raise SystemExit(main())
