#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: asciify_iron_maiden_ssot.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Asciify the Iron Maiden SSOT markdown.

Goal: Remove common mojibake + non-ASCII punctuation introduced by copy/paste
or markdown conversion, while preserving meaning and layout.

This is intentionally conservative: it only replaces a small, known set of
codepoints observed in this repo's SSOT drafts.

@SID:           TOOL_ASCIIFY_IRON_MAIDEN_SSOT_V1
@Shabti:        CLI Script
@Purpose:       Asciify the Iron Maiden SSOT markdown.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

from pathlib import Path


REPLACEMENTS: dict[str, str] = {
    "\u00a9": "(c)",  # ©
    "\u00e9": "e",  # é
    "\u2013": "-",  # en dash
    "\u2014": "--",  # em dash
    "\u2018": "'",  # left single quote
    "\u2019": "'",  # right single quote
    "\u2026": "...",  # ellipsis
    "\ufe0f": "",  # variation selector (e.g., ©️)
}


def asciify_text(s: str) -> str:
    for src, dst in REPLACEMENTS.items():
        s = s.replace(src, dst)
    return s


def main() -> None:
    target = Path("codex/codex-session-logs/The-Iron-Maiden-(SSOT)-Copyright-Savant.md")
    s = target.read_text(encoding="utf-8")
    out = asciify_text(s)
    if out != s:
        target.write_text(out, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
