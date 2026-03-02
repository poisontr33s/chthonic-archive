#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: deact_ref_iron_maiden_ssot.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Replace bracketed ACT cross-references in the Iron Maiden SSOT with
self-contained section labels.

The SSOT is intentionally ACT-structured, but bracket refs like:
  [REF: ACT SEVEN]
  [REF: ACT SEVEN // KEYSTONE ECHO: COACH]
create an internal inconsistency with the top-level directive that forbids
referring to ACTs "from elsewhere in the prompt" when addressing the user.

This script only rewrites the bracketed [REF: ACT ...] tokens. It does not
rename ACT headings.

@SID:           TOOL_DEACT_REF_IRON_MAIDEN_SSOT_V1
@Shabti:        CLI Script
@Purpose:       Replace bracketed ACT cross-references in the Iron Maiden SSOT with
"""

from __future__ import annotations

import re
from pathlib import Path


TARGET = Path("codex/codex-session-logs/The-Iron-Maiden-(SSOT)-Copyright-Savant.md")


ACT_TO_LABEL: dict[str, str] = {
    "ZERO": "The Weight of the Belt",
    "ONE": "Fadeout - Champion's Ballad",
    "TWO": "Reflection - In the Mirror's Glare",
    "THREE": "The Inner Voices",
    "FOUR": "Creeds of the Damned",
    "FIVE": "Chemical Currents / Substances",
    "SIX": "World / Locations",
    "SEVEN": "Echoes / Hauntings",
    "EIGHT": "The Ring",
    "NINE": "The Art of the Fight / Weapons & Key Items",
    "TEN": "The Show Must Go On",
    "ELEVEN": "The Inner Circle",
    "TWELVE": "Beyond the Ropes",
}


REF_RE = re.compile(
    r"\[REF:\s*ACT\s+([A-Z]+)"  # ACT token
    r"(?:\s+([A-Z0-9 _-]+?))?"  # optional qualifier like "DIVE BAR"
    r"\s*(?:(//)\s*([^\]]+))?\]"  # optional suffix after //
)


def _clean_suffix(s: str) -> str:
    s = s.strip()
    # Reduce visual noise: `KEYSTONE ECHO: COACH` is the useful part.
    return re.sub(r"\s+", " ", s)


def rewrite_refs(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        act = m.group(1)
        qualifier = m.group(2)
        suffix = m.group(4)
        label = ACT_TO_LABEL.get(act, f"ACT {act}")
        parts: list[str] = []
        if qualifier:
            parts.append(_clean_suffix(qualifier))
        if suffix:
            parts.append(_clean_suffix(suffix))
        if parts:
            return f"(see {label}: {'; '.join(parts)})"
        return f"(see {label})"

    return REF_RE.sub(repl, text)


def main() -> None:
    s = TARGET.read_text(encoding="utf-8")
    out = rewrite_refs(s)
    if out != s:
        TARGET.write_text(out, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
