#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: canonize_iron_maiden_ssot.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Canonize the Iron Maiden SSOT markdown in-place.

Goals:
- Restore markdown readability after a "fully escaped" conversion (e.g., "\\#\\#" headings).
- Replace legacy model handle strings (Gemini/G2.5PP/GPE variants) with a neutral token.
- Keep the transformation deterministic and conservative (avoid touching code blocks).

Invocation:
  uv run scripts/canonize_iron_maiden_ssot.py --in <file.md> --out <file.md> --target OPERATOR

Notes:
- We do NOT try to reflow prose.
- We avoid heavy regex and keep a small, explicit unescape set.

@SID:           TOOL_CANONIZE_IRON_MAIDEN_SSOT_V1
@Shabti:        CLI Script
@Purpose:       Canonize the Iron Maiden SSOT markdown in-place.
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import hashlib
from dataclasses import dataclass
from pathlib import Path


MODEL_HANDLE_GEMINI_25PP_0325 = "Gemini 2.5 Pro Preview 03-25"
MODEL_HANDLE_SHORT_TOKENS = [
    "G2.5PP_03-25",
    "G2.5PP 03-25",
    "GPE 03-25",
    "GPE_03-25",
]


UNESCAPE_CHARS = ("#", "*", ">", "_", "[", "]", "(", ")", ".", "-", "`")


@dataclass
class Stats:
    replaced_model_handles: int = 0
    unescaped_tokens: int = 0
    skipped_codeblock_lines: int = 0


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()


def unescape_line(line: str, stats: Stats) -> str:
    out = line
    for ch in UNESCAPE_CHARS:
        needle = "\\" + ch
        if needle in out:
            stats.unescaped_tokens += out.count(needle)
            out = out.replace(needle, ch)
    return out


def canonize_text(text: str, *, target: str) -> tuple[str, Stats]:
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

        before = ln
        ln = unescape_line(ln, stats)

        if MODEL_HANDLE_GEMINI_25PP_0325 in ln:
            stats.replaced_model_handles += ln.count(MODEL_HANDLE_GEMINI_25PP_0325)
            ln = ln.replace(MODEL_HANDLE_GEMINI_25PP_0325, target)
        for tok in MODEL_HANDLE_SHORT_TOKENS:
            if tok in ln:
                stats.replaced_model_handles += ln.count(tok)
                ln = ln.replace(tok, target)

        # Normalize accidental double-escapes like "\\\\_" -> "\\_" first pass handles the latter.
        # We only do a single conservative collapse for common patterns.
        ln = ln.replace("\\\\", "\\")

        # Keep line endings stable; do not trim trailing spaces because this doc uses them for hard breaks.
        out_lines.append(ln)

    return "\n".join(out_lines) + "\n", stats


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True, help="Input SSOT markdown file.")
    ap.add_argument("--out", dest="out", required=True, help="Output path (can equal input for in-place).")
    ap.add_argument("--target", default="OPERATOR", help="Replacement token for legacy model handles.")
    args = ap.parse_args(argv[1:])

    src = Path(args.src)
    outp = Path(args.out)
    raw = src.read_text(encoding="utf-8", errors="replace")

    canon, stats = canonize_text(raw, target=args.target)

    before_sha = sha256_text(raw)
    after_sha = sha256_text(canon)
    outp.write_text(canon, encoding="utf-8", newline="\n")

    print(f"wrote: {outp.as_posix()}")
    print(f"sha256_before: {before_sha}")
    print(f"sha256_after:  {after_sha}")
    print(f"replaced_model_handles: {stats.replaced_model_handles}")
    print(f"unescaped_tokens: {stats.unescaped_tokens}")
    print(f"skipped_codeblock_lines: {stats.skipped_codeblock_lines}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__('sys').argv))
