#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: patch_utf8.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
patch_utf8.py — Apply in-script UTF-8 stdio wrapper to CLI scripts.

Inserts a `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')`
block into Python CLI scripts so they render Unicode correctly on Windows
without requiring the caller to set $env:PYTHONUTF8='1' or PYTHONIOENCODING.

CLI detection mirrors ci/checks/python-headers.ts:isCliScript:
    Library (skip):  __init__.py OR path under */src/*
    CLI (patch):     under scripts/ or probes/, OR has `if __name__ == "__main__":`,
                     OR has `def main(`

Idempotent: a file already containing the wrapper is skipped.

@SID:           TOOL_PATCH_UTF8_V2
@Shabti:        CLI Script
@Purpose:       UTF-8 stdio defense-in-depth across CLI scripts.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

UTF8_FIX = """import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
"""

WRAPPER_MARKER = "sys.stdout = io.TextIOWrapper"

UTF8_FIX_BLOCK_RE = re.compile(
    r"\n?import sys\nimport io\nif sys\.platform == 'win32':\n"
    r"    sys\.stdout = io\.TextIOWrapper\(sys\.stdout\.buffer, encoding='utf-8'\)\n"
    r"    sys\.stderr = io\.TextIOWrapper\(sys\.stderr\.buffer, encoding='utf-8'\)\n+"
)


def is_cli_script(path: Path, content: str) -> bool:
    """Mirror of ci/checks/python-headers.ts isCliScript(), with one
    Python-side refinement: scripts/lib/* helpers are library modules
    unless they carry an entry point. Side-effecting wrapper code at
    import time is an anti-pattern for helpers consumed by other scripts.

    Returns False for library modules (skip patching).
    Returns True for CLI scripts (apply patching).
    """
    name = path.name
    parts_posix = path.as_posix()

    if name == "__init__.py":
        return False
    if "/src/" in parts_posix:
        return False

    has_main_block = bool(
        re.search(r"^if\s+__name__\s*==\s*['\"]__main__['\"]", content, re.MULTILINE)
    )

    # scripts/lib/* — helper library, skip unless explicit entry point
    if re.search(r"(?:^|/)scripts/lib/", parts_posix):
        return has_main_block

    if re.search(r"(?:^|/)(scripts|probes)/", parts_posix):
        return True
    if has_main_block:
        return True
    if re.search(r"^def\s+main\s*\(", content, re.MULTILINE):
        return True

    return True


def find_insertion_point(content: str) -> int:
    """Locate the byte offset where the UTF-8 wrapper should be inserted.

    Walks past shebang, encoding declaration, decorative # comment header,
    and module docstring. Inserts before the first real code statement.
    """
    lines = content.split("\n")
    insert_idx = 0
    cursor = 0

    if lines and lines[0].startswith("#!"):
        cursor = len(lines[0]) + 1
        insert_idx = cursor

    if len(lines) > 1 and re.match(r"^#.*coding[:=]", lines[1]):
        cursor += len(lines[1]) + 1
        insert_idx = cursor

    while cursor < len(content):
        nl = content.find("\n", cursor)
        if nl == -1:
            break
        line = content[cursor:nl]
        if line == "" or line.startswith("#"):
            cursor = nl + 1
            insert_idx = cursor
            continue
        break

    docstring_match = re.search(r'^"""', content[cursor:], re.MULTILINE)
    if docstring_match and docstring_match.start() < 50:
        ds_start = cursor + docstring_match.start()
        ds_end = content.find('"""', ds_start + 3)
        if ds_end != -1:
            after = ds_end + 3
            nl = content.find("\n", after)
            insert_idx = (nl + 1) if nl != -1 else after

    return insert_idx


def patch_python_file(path: Path, dry_run: bool = False) -> str:
    """Patch one file. Returns outcome label."""
    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return "skipped-binary"

    if WRAPPER_MARKER in content:
        return "skipped-already"

    if not is_cli_script(path, content):
        return "skipped-library"

    insert_idx = find_insertion_point(content)
    new_content = content[:insert_idx] + "\n" + UTF8_FIX + "\n" + content[insert_idx:]

    if not dry_run:
        path.write_text(new_content, encoding="utf-8")

    return "patched"


def revert_python_file(path: Path, dry_run: bool = False) -> str:
    """Strip the UTF-8 wrapper block from a previously-patched file."""
    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return "skipped-binary"

    if WRAPPER_MARKER not in content:
        return "skipped-not-patched"

    new_content = UTF8_FIX_BLOCK_RE.sub("\n", content, count=1)
    if new_content == content:
        return "skipped-no-match"

    if not dry_run:
        path.write_text(new_content, encoding="utf-8")

    return "reverted"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply or revert UTF-8 stdio wrapper on Python CLI scripts."
    )
    parser.add_argument(
        "targets",
        nargs="*",
        default=["scripts"],
        help="Directories or files to operate on (default: scripts/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing files",
    )
    parser.add_argument(
        "--revert",
        action="store_true",
        help="Strip the UTF-8 wrapper from previously-patched files",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show per-file outcome (default: summary only)",
    )
    args = parser.parse_args()

    paths: list[Path] = []
    for target in args.targets:
        p = Path(target)
        if p.is_dir():
            paths.extend(sorted(p.rglob("*.py")))
        elif p.is_file() and p.suffix == ".py":
            paths.append(p)

    op = revert_python_file if args.revert else patch_python_file
    op_label = "revert" if args.revert else "patch"

    counts: dict[str, int] = {}
    for path in paths:
        try:
            outcome = op(path, dry_run=args.dry_run)
        except Exception as exc:
            outcome = f"error: {exc}"
        counts[outcome] = counts.get(outcome, 0) + 1
        if args.verbose:
            print(f"  {outcome:25s} {path}")

    suffix = " (dry-run)" if args.dry_run else ""
    print(f"\n[patch_utf8] {op_label}{suffix} - {len(paths)} files scanned:")
    for outcome, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {n:5d}  {outcome}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
