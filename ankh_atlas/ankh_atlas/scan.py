#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: scan.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
File scanner - deterministic traversal,
no filtering beyond build artifacts.

@SID:           TOOL_SCAN_V1
@Shabti:        CLI Script
@Purpose:       File scanner - deterministic traversal,
"""

from pathlib import Path
from typing import Iterator


def iter_md(root: Path) -> Iterator[Path]:
    """Recursively find all .md files in deterministic order.

    Excludes:
    - .venv/ (Python virtual environments)
    - node_modules/ (JavaScript dependencies)
    - .git/ (version control internals)

    Yields paths in sorted order for deterministic output.
    """
    excluded_dirs = {".venv", "node_modules", ".git"}

    for md_path in sorted(root.rglob("*.md")):
        # Check if any parent directory is excluded
        if any(parent.name in excluded_dirs for parent in md_path.parents):
            continue
        yield md_path


def scan_file(path: Path) -> Iterator[tuple[int, str]]:
    """Read file line-by-line with 1-indexed line numbers.

    Yields: (line_number, line_content)
    """
    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        # Skip binary files, encoding issues, or permission denied
        return

    for i, line in enumerate(content.splitlines(), start=1):
        yield i, line
