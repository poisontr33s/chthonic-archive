#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: python_header_canon.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
python_header_canon.py — Script logic for python_header_canon.py.

@SID:           TOOL_PYTHON_HEADER_CANON_V1
@Shabti:        CLI Script
@Purpose:       Script logic for python_header_canon.py.
"""

from __future__ import annotations

import argparse
from pathlib import Path

CANON = ["#!/usr/bin/env python3", "#-*- coding: utf-8 -*-"]
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules"}


def iter_py_files(root: Path) -> list[Path]:
    files: list[Path] = []
    if root.is_file() and root.suffix == ".py":
        return [root]
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def normalize(path: Path) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines()

    idx = 0
    if idx < len(lines) and lines[idx].startswith("#!"):
        idx += 1
    if idx < len(lines) and lines[idx].strip() in {"# -*- coding: utf-8 -*-", "#-*- coding: utf-8 -*-"}:
        idx += 1

    new_lines = CANON + lines[idx:]
    if new_lines == lines:
        return False
    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize Python headers to repo canon.")
    parser.add_argument("targets", nargs="+", help="Files/directories to normalize.")
    args = parser.parse_args()

    changed: list[Path] = []
    scanned = 0
    for target in args.targets:
        root = Path(target)
        if not root.exists():
            continue
        for py_file in iter_py_files(root):
            scanned += 1
            if normalize(py_file):
                changed.append(py_file)

    print(f"Scanned: {scanned}")
    print(f"Changed: {len(changed)}")
    for path in changed[:25]:
        print(path.as_posix())


if __name__ == "__main__":
    main()
