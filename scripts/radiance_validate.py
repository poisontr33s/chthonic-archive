#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: radiance_validate.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ \s+(.+)")
# ╚════════════════════════════════════════════════════════════════════════════


@SID:           TOOL_RADIANCE_VALIDATE_V1
@Shabti:        CLI Script
@Purpose:       Validate Ogdoad-Ceque Radiance cross-references in all Python envelopes.
"""Validate Ogdoad-Ceque Radiance cross-references in all Python envelopes."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RADIANCE_PAT = re.compile(r"║\s+└─◄\s+(.+)")
SKIP_DIRS = {".venv", "__pycache__", "site-packages", "node_modules", "target"}


def main() -> int:
    broken: list[tuple[str, int, str]] = []
    standalone = 0
    valid = 0
    glob_refs = 0

    for pyfile in sorted(ROOT.rglob("*.py")):
        if any(p in SKIP_DIRS for p in pyfile.parts):
            continue
        try:
            text = pyfile.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if i > 20:  # Envelopes live in the first ~15 lines
                break
            m = RADIANCE_PAT.search(line)
            if not m:
                continue
            target = m.group(1).strip()
            # Skip template / code / standalone lines
            if target.startswith("<") or target.startswith("{") or target.startswith("("):
                standalone += 1
                continue
            # Glob refs (e.g. themes/*.json)
            if "*" in target:
                glob_refs += 1
                continue
            # Strip trailing annotations like (imports: process_data)
            target_clean = re.sub(r"\s*\(.*\)\s*$", "", target).strip()
            # Normalize backslashes
            target_clean = target_clean.replace("\\", "/")
            resolved = ROOT / target_clean
            if resolved.exists():
                valid += 1
            else:
                rel = pyfile.relative_to(ROOT)
                broken.append((str(rel), i, target_clean))

    print(f"Valid:      {valid}")
    print(f"Standalone: {standalone}")
    print(f"Glob refs:  {glob_refs}")
    print(f"Broken:     {len(broken)}")
    if broken:
        print()
        for src, line, tgt in broken:
            print(f"  {src}:{line} -> {tgt}")
    return 1 if broken else 0


if __name__ == "__main__":
    raise SystemExit(main())
