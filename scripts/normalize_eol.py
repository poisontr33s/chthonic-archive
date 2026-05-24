#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: normalize_eol.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Normalize line endings to LF for selected repo files.

This repo uses `.gitattributes` to enforce LF, but that only takes effect on
checkout/renormalize. This script lets us normalize surgically without doing a
repo-wide renormalization pass.

Invocation:
- uv run scripts/normalize_eol.py <path> [<path> ...]

@SID:           TOOL_NORMALIZE_EOL_V1
@Shabti:        CLI Script
@Purpose:       Normalize line endings to LF for selected repo files.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import sys
from pathlib import Path


def normalize_one(p: Path) -> bool:
    raw = p.read_bytes()
    # Fast path: already LF-only (or binary with no CRLF).
    if b"\r\n" not in raw:
        return False
    text = raw.decode("utf-8", errors="strict")
    text = text.replace("\r\n", "\n")
    p.write_text(text, encoding="utf-8", newline="\n")
    return True


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: normalize_eol.py <path> [<path> ...]")
        return 2

    changed = 0
    for a in argv[1:]:
        p = Path(a)
        if not p.exists() or not p.is_file():
            print(f"skip: {a}")
            continue
        if normalize_one(p):
            changed += 1
    print(f"normalized: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
