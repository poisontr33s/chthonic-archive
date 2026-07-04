#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: repair_markdown_artifacts.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
@SID:           TOOL_REPAIR_MARKDOWN_ARTIFACTS_V1
@Shabti:        CLI Script
@Context:       Documentation Hygiene / Markdown Rendering Repair
@Purpose:       Repair markdown artifacts without rewriting content.

This tool is intentionally conservative. It does not reflow prose or invent
new content. It only applies formatting-level repairs that make deep-research
markdown render as intended:

- remove invisible glyph artifacts;
- fix malformed heading spacing;
- optionally fence obvious ASCII/box-drawing layout blocks so they render
  consistently in Markdown viewers.

Usage:
    uv run scripts/repair_markdown_artifacts.py --dry-run
    uv run scripts/repair_markdown_artifacts.py CLAUDEBASE/sub-surface-skinny-dipping
    uv run scripts/repair_markdown_artifacts.py file.md --verbose
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

INVISIBLE_TRANSLATION = str.maketrans(
    {
        "\ufeff": "",
        "\u200b": "",
        "\u200c": "",
        "\u200d": "",
        "\u2060": "",
    }
)

HEADING_FIX_RE = re.compile(r"^(#{1,6})(\S)")
FENCE_RE = re.compile(r"^\s*(```|~~~)")

LAYOUT_GLYPHS = set("│└┘┌┐├┤┬┴─═╔╗╚╝╟╢╤╧╪╫▼▲▶◀")
BRACKET_LABEL_RE = re.compile(r"^\s*[\[(].+[\])]\s*$")

DEFAULT_TARGETS = [Path("CLAUDEBASE/sub-surface-skinny-dipping")]
SKIP_DIRS = {".git", ".claude", ".codex", ".vscode", "__pycache__", "node_modules", "dist", "build", ".venv", "venv"}


@dataclass
class FileResult:
    path: Path
    changed: bool
    notes: list[str]


def normalize_line(line: str) -> str:
    line = line.translate(INVISIBLE_TRANSLATION)
    line = HEADING_FIX_RE.sub(r"\1 \2", line)
    return line


def is_markdown_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".md"


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def gather_targets(targets: list[Path]) -> list[Path]:
    files: list[Path] = []
    for target in targets:
        if target.is_file():
            if is_markdown_file(target) and not should_skip(target):
                files.append(target)
            continue
        if target.is_dir():
            for path in sorted(target.rglob("*.md")):
                if not should_skip(path):
                    files.append(path)
    return files


def looks_like_layout_block(lines: list[str]) -> bool:
    if len(lines) < 3:
        return False

    nonblank = [line for line in lines if line.strip()]
    if len(nonblank) < 3:
        return False

    layout_lines = 0
    layout_chars = 0
    total_chars = 0
    for line in nonblank:
        total_chars += len(line.replace(" ", ""))
        layout_chars += sum(1 for ch in line if ch in LAYOUT_GLYPHS)
        if any(ch in LAYOUT_GLYPHS for ch in line):
            layout_lines += 1
        elif BRACKET_LABEL_RE.match(line) and len(line.strip()) <= 120:
            layout_lines += 1

    if total_chars == 0:
        return False

    density = layout_chars / total_chars
    return layout_lines >= 3 and density >= 0.08


def fence_block(lines: list[str], newline: str) -> list[str]:
    fenced = ["```"]
    fenced.extend(line.rstrip() for line in lines)
    fenced.append("```")
    return [line + newline for line in fenced]


def process_text(text: str, fence_layout_blocks: bool) -> tuple[str, list[str]]:
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()
    had_final_newline = text.endswith(("\n", "\r"))

    output: list[str] = []
    notes: list[str] = []
    buffer: list[str] = []
    in_fence = False

    def flush_buffer() -> None:
        nonlocal buffer
        if not buffer:
            return
        cleaned = [normalize_line(line) for line in buffer]
        if fence_layout_blocks and looks_like_layout_block(cleaned):
            output.extend(fence_block(cleaned, newline))
            notes.append(f"fenced layout block ({cleaned[0][:48]!r})")
        else:
            output.extend(line + newline for line in cleaned)
        buffer = []

    for line in lines:
        if FENCE_RE.match(line):
            flush_buffer()
            output.append(normalize_line(line) + newline)
            in_fence = not in_fence
            continue

        if in_fence:
            output.append(normalize_line(line) + newline)
            continue

        if line.strip() == "":
            flush_buffer()
            output.append(line + newline)
            continue

        buffer.append(line)

    flush_buffer()

    result = "".join(output)
    if not had_final_newline and result.endswith(newline):
        result = result[: -len(newline)]
    return result, notes


def repair_file(path: Path, dry_run: bool, fence_layout_blocks: bool) -> FileResult:
    original = path.read_text(encoding="utf-8", errors="replace")
    repaired, notes = process_text(original, fence_layout_blocks=fence_layout_blocks)
    changed = repaired != original
    if changed and not dry_run:
        path.write_text(repaired, encoding="utf-8", newline="")
    return FileResult(path=path, changed=changed, notes=notes)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Repair markdown rendering artifacts without rewriting content."
    )
    parser.add_argument(
        "targets",
        nargs="*",
        default=[str(p) for p in DEFAULT_TARGETS],
        help="Files or directories to repair (default: CLAUDEBASE/sub-surface-skinny-dipping)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report planned changes without writing files",
    )
    parser.add_argument(
        "--no-fence-layout",
        action="store_true",
        help="Disable automatic fencing of obvious ASCII/box-drawing layout blocks",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-file repair details",
    )
    args = parser.parse_args()

    targets = [Path(target) for target in args.targets]
    files = gather_targets(targets)

    changed = 0
    touched = 0
    for file_path in files:
        result = repair_file(file_path, dry_run=args.dry_run, fence_layout_blocks=not args.no_fence_layout)
        if result.changed:
            changed += 1
            if args.verbose:
                action = "WOULD FIX" if args.dry_run else "FIXED"
                print(f"{action}: {result.path}")
                for note in result.notes:
                    print(f"  - {note}")
        touched += 1

    label = "would change" if args.dry_run else "changed"
    print(f"\n[repair_markdown_artifacts] {touched} markdown file(s) scanned, {changed} {label}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
