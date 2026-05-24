#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: fix_headers.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Enforce correct shebang/encoding headers on scripts by file extension.
Prepends the canonical header if missing or wrong, shifts existing content down.

Usage: uv run scripts/fix_headers.py [--dry-run] [--validate] [paths...]
       Defaults to scanning the whole repo if no paths given.

@SID:           TOOL_FIX_HEADERS_V1
@Shabti:        CLI Script
@Purpose:       Enforce correct shebang/encoding headers on scripts by file extension.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


import argparse
import sys
from pathlib import Path

# Canonical headers per extension (list of lines, no trailing newline)
HEADERS: dict[str, list[str]] = {
    ".py":  ["#!/usr/bin/env python3", "#-*- coding: utf-8 -*-"],
    ".ps1": ["#!/usr/bin/env pwsh"],
    ".sh":  ["#!/usr/bin/env bash"],
}

# Default: scan from repo root
SCAN_DIRS = ["."]

# Skip these directories entirely (vendored, generated, agent infra)
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__",
    ".codex", ".claude", ".temple", ".vscode",
    "meta-ide", "build",
}
# Directories matching these prefixes are also skipped (venvs, etc.)
SKIP_PREFIXES = (".venv", "venv")


def needs_fix(lines: list[str], header: list[str]) -> bool:
    """Return True if the file's top lines don't match the expected header."""
    for i, expected in enumerate(header):
        if i >= len(lines) or lines[i].rstrip("\r\n") != expected:
            return True
    return False


def strip_wrong_header(lines: list[str], ext: str) -> list[str]:
    """Remove any existing shebang/encoding lines that don't belong."""
    cleaned = []
    skip_zone = True
    for line in lines:
        stripped = line.rstrip("\r\n")
        if skip_zone:
            # Skip lines that look like shebangs or encoding declarations
            if stripped.startswith("#!") or stripped.startswith("# -*-") or stripped.startswith("#-*-"):
                continue
            # Also skip blank lines between removed headers and content
            if stripped == "" and not cleaned:
                continue
            skip_zone = False
        cleaned.append(line)
    return cleaned


def fix_file(path: Path, dry_run: bool) -> bool:
    """Fix one file. Returns True if changed."""
    ext = path.suffix.lower()
    header = HEADERS.get(ext)
    if header is None:
        return False

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)

    if not needs_fix(lines, header):
        return False

    # Strip any wrong shebang/encoding lines first
    content_lines = strip_wrong_header(lines, ext)

    # Build new file: header + blank line + content
    newline = "\n"
    new_lines = [h + newline for h in header]
    # Add separator blank line if content doesn't start with one
    if content_lines and content_lines[0].strip():
        new_lines.append(newline)
    new_lines.extend(content_lines)

    new_text = "".join(new_lines)

    if dry_run:
        print(f"  WOULD FIX: {path}")
        return True

    path.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"  FIXED: {path}")
    return True


def validate_file(path: Path) -> str | None:
    """Check one file's header. Returns status string or None if correct."""
    ext = path.suffix.lower()
    header = HEADERS.get(ext)
    if header is None:
        return None

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    for i, expected in enumerate(header):
        actual = lines[i].rstrip("\r\n") if i < len(lines) else "<missing>"
        if actual != expected:
            return f"FAIL  line {i+1}: got {actual!r}, want {expected!r}"
    return None


def main():
    parser = argparse.ArgumentParser(description="Fix script headers by extension")
    parser.add_argument("paths", nargs="*", help="Files or dirs to scan (default: scripts/)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    parser.add_argument("--validate", action="store_true", help="Check headers and report pass/fail (no writes)")
    args = parser.parse_args()

    targets = [Path(p) for p in args.paths] if args.paths else [Path(d) for d in SCAN_DIRS]

    files: list[Path] = []
    for t in targets:
        if t.is_file():
            files.append(t)
        elif t.is_dir():
            for ext in HEADERS:
                for f in sorted(t.rglob(f"*{ext}")):
                    if not any(
                        part in SKIP_DIRS or part.startswith(SKIP_PREFIXES)
                        for part in f.parts
                    ):
                        files.append(f)

    if not files:
        print("No matching files found.")
        return

    if args.validate:
        passed = 0
        failed = 0
        for f in files:
            result = validate_file(f)
            if result:
                print(f"  FAIL: {f}  ({result})")
                failed += 1
            else:
                print(f"  OK:   {f}")
                passed += 1
        print(f"\n{passed} passed, {failed} failed out of {len(files)} files.")
        sys.exit(1 if failed else 0)

    fixed = 0
    for f in files:
        if fix_file(f, args.dry_run):
            fixed += 1

    label = "would fix" if args.dry_run else "fixed"
    print(f"\n{fixed}/{len(files)} files {label}.")


if __name__ == "__main__":
    main()
