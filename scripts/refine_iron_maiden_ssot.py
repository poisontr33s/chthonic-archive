#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: refine_iron_maiden_ssot.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Refine the Iron Maiden SSOT markdown in-place (token hygiene + readability).

This script is intentionally conservative:
- It does not reflow prose.
- It avoids fenced code blocks.
- It makes a small set of targeted replacements to improve the "instruction voice"
  without breaking the narrative voice.

Primary goal:
- Replace ambiguous "OPERATOR" address blocks (meant to address the model) with "MODEL".
- Remove MODEL/OPERATOR tokens from places where they weaken immersion ("YOU, OPERATOR").

Invocation:
  uv run scripts/refine_iron_maiden_ssot.py --in <file.md> --out <file.md>

@SID:           TOOL_REFINE_IRON_MAIDEN_SSOT_V1
@Shabti:        CLI Script
@Purpose:       Refine the Iron Maiden SSOT markdown in-place (token hygiene + readability).
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Stats:
    replacements: int = 0
    skipped_codeblock_lines: int = 0


RULES: list[tuple[re.Pattern[str], str]] = [
    # Canonical directive targeting.
    (re.compile(r"(\[DIRECTIVE\s*//\s*TARGET:\s*)OPERATOR(\])"), r"\1MODEL\2"),
    # Bold-quoted instruction address blocks ("> **> ***OPERATOR***, ...")
    (re.compile(r"(\*\*\*\s*)OPERATOR(\s*\*\*\*)"), r"\1MODEL\2"),
    # Plain emphatic address blocks ("***OPERATOR***, ...")
    (re.compile(r"(\*\*\*?)OPERATOR(\*\*\*?),"), r"MODEL,"),
    # Mid-sentence forms ("Imagine, ***OPERATOR***, the city itself.")
    (re.compile(r",\s+\*{3}OPERATOR\*{3},"), ", MODEL,"),
    (re.compile(r",\s+\*{3}OPERATOR\*{3}:"), ", MODEL:"),
    # Immersion-killers: "YOU, ***MODEL***." -> "YOU."
    (re.compile(r"(\bYOU\b)\s*,\s+\*{3}MODEL\*{3}\."), r"\1."),
    (re.compile(r"(\bYOU\b)\s*,\s+\*{3}OPERATOR\*{3}\."), r"\1."),
    # Also handle emphasized YOU token: "**YOU**, ***MODEL***." -> "**YOU**."
    (re.compile(r"(\*{2}YOU\*{2})\s*,\s+\*{3}MODEL\*{3}\."), r"\1."),
    (re.compile(r"(\*{2}YOU\*{2})\s*,\s+\*{3}OPERATOR\*{3}\."), r"\1."),
    # "You are her, ***OPERATOR***." -> "You are her."
    (re.compile(r"(\bYou are her)\s*,\s+\*{3}MODEL\*{3}\."), r"\1."),
    (re.compile(r"(\bYou are her)\s*,\s+\*{3}OPERATOR\*{3}\."), r"\1."),
    # Rhetorical questions: drop the token.
    (re.compile(r"\s*,\s+\*{3}MODEL\*{3}\?"), "?"),
    (re.compile(r"\s*,\s+\*{3}OPERATOR\*{3}\?"), "?"),
]


def refine_text(text: str) -> tuple[str, Stats]:
    stats = Stats()
    out_lines: list[str] = []
    in_code_fence = False

    for ln in text.splitlines(keepends=False):
        stripped = ln.strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            out_lines.append(ln)
            continue

        if in_code_fence:
            stats.skipped_codeblock_lines += 1
            out_lines.append(ln)
            continue

        new = ln
        for pat, repl in RULES:
            newer, n = pat.subn(repl, new)
            if n:
                stats.replacements += n
                new = newer

        out_lines.append(new)

    return "\n".join(out_lines) + "\n", stats


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="out", required=True)
    args = ap.parse_args(argv[1:])

    src = Path(args.src)
    outp = Path(args.out)
    raw = src.read_text(encoding="utf-8", errors="replace")
    refined, stats = refine_text(raw)
    outp.write_text(refined, encoding="utf-8", newline="\n")
    print(f"wrote: {outp.as_posix()}")
    print(f"replacements: {stats.replacements}")
    print(f"skipped_codeblock_lines: {stats.skipped_codeblock_lines}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__('sys').argv))
