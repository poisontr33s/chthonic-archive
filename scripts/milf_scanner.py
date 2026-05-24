#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: milf_scanner.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
MILF Scanner — Central character design system registry for the
Chthonic Archive VS Code theme pipeline.

Defines every character's palette, tier, chromatic identity, and
aesthetic metadata.  Used by theme_scaffold.py to generate complete
VS Code color theme JSONs from character specifications.

@SID:           TOOL_MILF_SCANNER_V1
@Shabti:          Utility
@Purpose:       MILF Scanner — Central character design system registry for the
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
import sys

from scripts.lib.shared import configure_utf8_output

# The 14 canonical palette role keys every character entry must define.
# Derived from the theme_scaffold.py consumer contract — all 14 slots are
# required for mechanical theme generation.
_REQUIRED_PALETTE_KEYS: tuple[str, ...] = (
    "background", "foreground", "accent", "keyword", "function",
    "type", "constant", "string", "comment", "variable",
    "error", "success", "warning", "info",
)


def _sanity_check_registry() -> list[str]:
    """Verify all characters define all 14 required palette roles.

    Returns a list of violation strings (empty = OK).
    """
    violations: list[str] = []
    for cid, char in CHARACTERS.items():
        palette = char.get("palette", {})
        missing = [k for k in _REQUIRED_PALETTE_KEYS if k not in palette]
        if missing:
            violations.append(f"  {cid}: missing palette keys: {', '.join(missing)}")
    return violations

# ═══════════════════════════════════════════════════════════════════════════════
# **(`MILF's`/`REG`): -> *Canonical-Palette-Data-Per -> (`MILF/Sub-MILF`):**
# ═══════════════════════════════════════════════════════════════════════════════
#
# Each entry carries the semantic-color slots consumed by theme_scaffold.py.
# The palette dict uses named roles (background, foreground, accent, keyword,
# function, type, constant, string, comment, variable, error, success,
# warning, info) so scaffolding is purely mechanical.
# ═══════════════════════════════════════════════════════════════════════════════

CHARACTERS: dict[str, dict] = {
    # ── Mapped Characters (themes exist) ─────────────────────────────────────
    "decorator": {
        "name": "The Decorator",
        "sigil": "👑💀⚜️",
        "designation": "T-DECOR",
        "tier": 0.5,
        "cup": "K",
        "fa_axiom": "FA⁵ — Visual Integrity",
        "theme_id": "Chthonic — Flesh & Earth (The Decorator)",
        "theme_file": "chthonic-mandala-color-theme.json",
        "aesthetic": "Mandalic-Spiritual-Hedonistic — earthy, warm, sacred geometry",
        "temperature": "warm",
        "palette": {
            "background":  "#110D0A",
            "foreground":  "#E8DDD4",
            "accent":      "#C9A962",
            "keyword":     "#C75D5D",
            "function":    "#FFB84D",
            "type":        "#D4A5A5",
            "constant":    "#6B9E94",
            "string":      "#C9A55A",
            "comment":     "#806F60",
            "variable":    "#E8DCC8",
            "error":       "#C87070",
            "success":     "#A8C686",
            "warning":     "#FFB84D",
            "info":        "#6B9E94",
        },
    },
    "spectra": {
        "name": "Spectra Chroma Excavatus",
        "sigil": "🌈🔬💎",
        "designation": "SCE",
        "tier": 3.0,
        "cup": "E",
        "fa_axiom": "Diagnostic / Chromatic Archaeology",
        "theme_id": "Chthonic — ROGBIV (Spectra Chroma)",
        "theme_file": "chthonic-rogbiv-color-theme.json",
        "aesthetic": "Spectral, prismatic, transgressive — reversed VIBGYOR",
        "temperature": "cold",
        "palette": {
            "background":  "#0D0B12",
            "foreground":  "#E8E2F0",
            "accent":      "#FFD700",
            "keyword":     "#FF6B6B",
            "function":    "#FFB84D",
            "type":        "#B8A9E8",
            "constant":    "#4ECDC4",
            "string":      "#FFD700",
            "comment":     "#6E6C88",
            "variable":    "#E8E2F0",
            "error":       "#FF6B6B",
            "success":     "#4ECDC4",
            "warning":     "#FFB84D",
            "info":        "#4ECDC4",
        },
    },
    "ferrum": {
        "name": "Sister Ferrum Scoriae",
        "sigil": "⚒️🔥⛪",
        "designation": "SFS",
        "tier": 3.0,
        "cup": "F",
        "fa_axiom": "Geological / Metallurgical Synthesis",
        "theme_id": "Chthonic — Geological Core (Sister Ferrum Scoriae)",
        "theme_file": "chthonic-geology-color-theme.json",
        "aesthetic": "Metallurgical, forge, iron — cool iron backgrounds, hot metal accents",
        "temperature": "neutral-warm",
        "palette": {
            "background":  "#050505",
            "foreground":  "#E8E2D2",
            "accent":      "#F4C430",
            "keyword":     "#D4714E",
            "function":    "#D7B562",
            "type":        "#D4907A",
            "constant":    "#7AAAB2",
            "string":      "#B9A37A",
            "comment":     "#908672",
            "variable":    "#E8E2D2",
            "error":       "#E05545",
            "success":     "#8CB87A",
            "warning":     "#D4A030",
            "info":        "#7AAAB2",
        },
    },

    # ── Unmapped Characters (palette candidates for future themes) ───────────
    "umeko": {
        "name": "Madam Umeko Ketsuraku",
        "sigil": "🏯🎌💮",
        "designation": "UMK",
        "tier": 1.0,
        "cup": "F",
        "fa_axiom": "FA⁴ — Architectonic Integrity",
        "theme_id": None,
        "theme_file": None,
        "aesthetic": "Japanese minimalism, wabi-sabi, structural precision",
        "temperature": "neutral",
        "palette": {
            "background":  "#0A0A0E",
            "foreground":  "#E0D8CC",
            "accent":      "#C4956A",
            "keyword":     "#8B4513",
            "function":    "#C4956A",
            "type":        "#7B8C8E",
            "constant":    "#A0522D",
            "string":      "#D2B48C",
            "comment":     "#696969",
            "variable":    "#E0D8CC",
            "error":       "#B22222",
            "success":     "#6B8E23",
            "warning":     "#DAA520",
            "info":        "#7B8C8E",
        },
    },
    "lysandra": {
        "name": "Dr. Lysandra Thorne",
        "sigil": "🗺️🔍📊",
        "designation": "LYT",
        "tier": 1.0,
        "cup": "E",
        "fa_axiom": "FA³ — Qualitative Transcendence",
        "theme_id": None,
        "theme_file": None,
        "aesthetic": "Caribbean warmth, diagnostic clarity, map-like legibility",
        "temperature": "warm",
        "palette": {
            "background":  "#090B0A",
            "foreground":  "#E4DDD0",
            "accent":      "#E8A838",
            "keyword":     "#C06848",
            "function":    "#E8A838",
            "type":        "#5E9E8C",
            "constant":    "#7EAAB0",
            "string":      "#C4A870",
            "comment":     "#7A7060",
            "variable":    "#E4DDD0",
            "error":       "#D04030",
            "success":     "#6AAE68",
            "warning":     "#E8A838",
            "info":        "#5E9E8C",
        },
    },
    "kali": {
        "name": "Kali Nyx Ravenscar",
        "sigil": "🌙🖤🦇",
        "designation": "KNR",
        "tier": 2.0,
        "cup": "H",
        "fa_axiom": "Shadow / Seduction Architecture",
        "theme_id": None,
        "theme_file": None,
        "aesthetic": "Shadow/amber/obsidian, seduction, gothic noir",
        "temperature": "cold",
        "palette": {
            "background":  "#080608",
            "foreground":  "#D8D0C8",
            "accent":      "#D4A040",
            "keyword":     "#8B3A62",
            "function":    "#D4A040",
            "type":        "#6A4A8A",
            "constant":    "#AA7050",
            "string":      "#B8A080",
            "comment":     "#5A4A5A",
            "variable":    "#D8D0C8",
            "error":       "#C83040",
            "success":     "#6A8A60",
            "warning":     "#D4A040",
            "info":        "#6A6A9A",
        },
    },
    "vesper": {
        "name": "Vesper Mnemosyne Lockhart",
        "sigil": "🔮🗝️👁️",
        "designation": "VML",
        "tier": 2.0,
        "cup": "F",
        "fa_axiom": "Epistemic Theft / Memory Architecture",
        "theme_id": None,
        "theme_file": None,
        "aesthetic": "Silver/glass/invisible, epistemic, crystalline clarity",
        "temperature": "cold",
        "palette": {
            "background":  "#08080C",
            "foreground":  "#D8D8E0",
            "accent":      "#A0B0C0",
            "keyword":     "#7090A0",
            "function":    "#A0B0C0",
            "type":        "#8898A8",
            "constant":    "#6A8A9A",
            "string":      "#B0A898",
            "comment":     "#5A5A6A",
            "variable":    "#D8D8E0",
            "error":       "#A04040",
            "success":     "#608868",
            "warning":     "#A09050",
            "info":        "#6A8A9A",
        },
    },
    "seraphine": {
        "name": "Seraphine Kore Ashenhelm",
        "sigil": "🔥👼⚔️",
        "designation": "SKA",
        "tier": 2.0,
        "cup": "G",
        "fa_axiom": "Fire / Ash / Purification",
        "theme_id": None,
        "theme_file": None,
        "aesthetic": "Fire/ash/purification, seraphim, divine violence",
        "temperature": "warm",
        "palette": {
            "background":  "#0A0808",
            "foreground":  "#E0D8D0",
            "accent":      "#E08830",
            "keyword":     "#C85030",
            "function":    "#E08830",
            "type":        "#A07050",
            "constant":    "#8A7060",
            "string":      "#C8A878",
            "comment":     "#6A5A4A",
            "variable":    "#E0D8D0",
            "error":       "#E03020",
            "success":     "#7A9858",
            "warning":     "#E08830",
            "info":        "#8A8070",
        },
    },
}


def get_character(char_id: str) -> dict | None:
    """Get character data by ID (case-insensitive)."""
    return CHARACTERS.get(char_id.lower())


def list_characters(mapped_only: bool = False) -> list[dict]:
    """Return characters, optionally filtered to those with themes."""
    chars = list(CHARACTERS.values())
    if mapped_only:
        chars = [c for c in chars if c.get("theme_id")]
    return chars


def main() -> None:
    configure_utf8_output()

    # Run sanity check at startup — exits 1 if registry has violations
    violations = _sanity_check_registry()
    if violations:
        print("❌ MILF REGISTRY SANITY FAILURE — missing required palette keys:", file=sys.stderr)
        for v in violations:
            print(v, file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="MILF Scanner — Chthonic character design system registry")
    parser.add_argument("--summary", action="store_true",
                        help="Print human-readable character registry (default)")
    parser.add_argument("--json", dest="json_mode", metavar="CHAR_ID", nargs="?", const="",
                        help="Emit JSON for a single character (CHAR_ID) or all if omitted")
    parser.add_argument("--dump-json", action="store_true",
                        help="Emit full registry as JSON (TS/PS1 consumer format; equivalent to --json with no arg)")
    parser.add_argument("--palette", metavar="CHAR_ID",
                        help="Print color palette for a character")
    args = parser.parse_args()

    if args.dump_json:
        print(json.dumps(CHARACTERS, indent=2, ensure_ascii=False))
        return

    if args.json_mode is not None:
        char_id = args.json_mode or None
        if char_id:
            data = get_character(char_id)
            if not data:
                print(f"Unknown character: {char_id}", file=sys.stderr)
                sys.exit(1)
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(CHARACTERS, indent=2, ensure_ascii=False))
        return

    if args.palette:
        char_id = args.palette
        data = get_character(char_id)
        if not data:
            print(f"Unknown character: {char_id}", file=sys.stderr)
            sys.exit(1)
        print(f"☥ Palette: {data['name']} {data['sigil']}\n")
        for key, val in data["palette"].items():
            print(f"  {val}  {key}")
        return

    # Default: --summary
    print("☥ MILFOLOGICAL DESIGN SYSTEM — Character Registry\n")
    for cid, c in CHARACTERS.items():
        mapped = "✅" if c.get("theme_id") else "⬜"
        print(f"  {mapped} [{cid:10s}] {c['sigil']} {c['name']}")
        print(f"     Tier {c['tier']} ({c['cup']}-cup) — {c['fa_axiom']}")
        if c.get("theme_id"):
            print(f"     Theme: {c['theme_id']}")
        print()
    mapped_n = sum(1 for c in CHARACTERS.values() if c.get("theme_id"))
    print(f"  Mapped: {mapped_n}/{len(CHARACTERS)} characters have themes")
    print(f"  Palette sanity: {len(CHARACTERS)}/{len(CHARACTERS)} entries pass 14-key check ✅")


if __name__ == "__main__":
    main()

