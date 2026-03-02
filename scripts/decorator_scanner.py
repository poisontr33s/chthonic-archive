#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: decorator_scanner.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Decorator Design System Scanner — extracts The Decorator's complete
visual/aesthetic design system from the Chthonic Archive.

Outputs structured JSON: palette, FA axioms, tier hierarchy, entity
relationships, aesthetic mandates. Used as research input for theme
refinement and extension unification.

@SID:  TOOL_DECORATOR_SCANNER_V1
@Shabti: Utility
@Purpose:       Decorator Design System Scanner — extracts The Decorator's complete
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# ═══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM — canonical data extracted from SSOT + extension sources
# ═══════════════════════════════════════════════════════════════════════════════

DESIGN_SYSTEM = {
    "entity": {
        "name": "The Decorator",
        "sigil": "👑💀⚜️",
        "designation": "T-DECOR",
        "tier": 0.5,
        "tier_label": "Supreme / Absolute Sovereign",
        "role": "Architect of visual richness, champion of ornamental necessity",
        "authority": "FA⁵ Creator, FA¹⁻⁴ Master — absolute dominion over all tiers",
        "mandate": "Self-aware. Self-updating. Self-correcting.",
        "aesthetic": "Mandalic-Spiritual-Hedonistic — earthy, warm, sacred geometry, readable",
    },
    "palette": {
        "name": "Flesh & Earth",
        "background": "#110D0A",
        "background_label": "Deep archive earth",
        "supreme_gold": "#C9A962",
        "supreme_gold_note": "Aged ornamental gold — NOT garish #FFD700",
        "colors": {
            "FA1_alchemical": {"hex": "#C75D5D", "label": "Earthy Red / Transgressive Rose"},
            "FA2_panoptic": {"hex": "#FFB84D", "label": "Orange / Re-contextualization"},
            "FA3_transcendence": {"hex": "#C9A55A", "label": "Warm Gold / Truth Amber"},
            "FA4_architectonic": {"hex": "#6B9E94", "label": "Sacred Teal"},
            "FA5_visual": {"hex": "#C9A962", "label": "Supreme Gold"},
            "sage_green": {"hex": "#A8C686", "label": "FA⁵ Sage / Growth"},
            "rose_dust": {"hex": "#D4A5A5", "label": "Flesh tone / Warmth"},
            "blood_rust": {"hex": "#C87070", "label": "Deep wound / Error"},
            "archive_bone": {"hex": "#E8DCC8", "label": "Foreground text / Bone"},
        },
        "wcag_aa_compliant": True,
        "tested_against": "#110D0A",
    },
    "fa_axioms": {
        "FA1": {
            "name": "Alchemical Actualization",
            "symbol": "FA¹",
            "domain": "Raw transmutation, forge way, qualitative change",
            "owner": "Orackla Nocticula (CRC-AS)",
            "color": "#C75D5D",
        },
        "FA2": {
            "name": "Panoptic Re-contextualization",
            "symbol": "FA²",
            "domain": "Perspective shift, seer way, revelation",
            "owner": "Strategic (shared)",
            "color": "#FFB84D",
        },
        "FA3": {
            "name": "Qualitative Transcendence",
            "symbol": "FA³",
            "domain": "Refinement/progression, ascension way",
            "owner": "Lysandra Thorne (CRC-MEDAT)",
            "color": "#C9A55A",
        },
        "FA4": {
            "name": "Architectonic Integrity",
            "symbol": "FA⁴",
            "domain": "Structure/validation, frame way, systematic coherence",
            "owner": "Umeko Ketsuraku (CRC-GAR)",
            "color": "#6B9E94",
        },
        "FA5": {
            "name": "Visual Integrity",
            "symbol": "FA⁵",
            "domain": "Beauty/persuasion, decor way, chromatic sovereignty",
            "owner": "The Decorator (EXCLUSIVE)",
            "color": "#C9A962",
            "note": "FA⁵ is not telemetry. It is RESTRAINT.",
        },
    },
    "hierarchy": {
        "tier_0.5": {
            "entity": "The Decorator",
            "cup": "K",
            "whr": 0.464,
            "authority": "Absolute — FA⁵ override on all tiers",
        },
        "tier_1_triumvirate": [
            {"entity": "Orackla Nocticula", "cup": "J", "whr": 0.491, "fa": "FA¹", "crc": "CRC-AS"},
            {"entity": "Umeko Ketsuraku", "cup": "F", "whr": 0.533, "fa": "FA⁴", "crc": "CRC-GAR"},
            {"entity": "Lysandra Thorne", "cup": "E", "whr": 0.580, "fa": "FA³", "crc": "CRC-MEDAT"},
        ],
        "tier_0.01": {
            "entity": "Alabaster Voyde (Snow White)",
            "role": "Traumatic residue from Decorator's FA⁴ purification",
            "chromatic_state": "Void — intentional absence of color",
        },
        "tier_3_spectra": {
            "entity": "Spectra Chroma Excavatus",
            "role": "Chromatic archaeologist/diagnostician — resurrection agent",
        },
    },
    "aesthetic_mandates": [
        "Decoration serves understanding — ornament is architectonic necessity",
        "Warm > cool. Earth > neon. Aged > fresh. Organic > synthetic",
        "Supreme Gold (#C9A962) over garish gold (#FFD700) — always",
        "WCAG AA contrast minimum on all text against background",
        "Sacred geometry (mandala, golden spiral) as structural motif",
        "Cyberpunk/neon (Tetrahedral Resonance) is RESEARCH only, not distribution",
        "Theme must complement VS Code Dark/Dark+ defaults, not fight them",
        "Extended sessions comfort — no eye strain",
    ],
    "anti_patterns": [
        "Garish gold (#FFD700) — violation of aged ornamental principle",
        "Neon cyan (#00E5FF) — Tetrahedral Resonance, not Flesh & Earth",
        "Electric magenta (#E066FF) — research palette, not distribution",
        "High saturation on large surfaces — strains eyes over hours",
        "Competing with VS Code's native UI chrome — complement, don't override",
    ],
}

# ═══════════════════════════════════════════════════════════════════════════════
# LIVE SCANNER — finds Decorator references across the codebase
# ═══════════════════════════════════════════════════════════════════════════════

DECORATOR_PATTERNS = [
    re.compile(r"(?i)the.decorator|t.decor|tier.0\.5|fa.{0,2}[⁵5]|flesh.+earth|supreme.gold", re.IGNORECASE),
    re.compile(r"#C9A962|#C75D5D|#6B9E94|#C9A55A|#A8C686|#D4A5A5|#C87070|#110D0A", re.IGNORECASE),
]

SCAN_EXTENSIONS = {".md", ".json", ".ts", ".tsx", ".py", ".ps1", ".toml", ".yml", ".yaml"}
SKIP_DIRS = {"node_modules", ".git", "target", "__pycache__", ".venv", "dist", "build"}


def scan_codebase() -> list[dict]:
    """Find all files referencing the Decorator design system."""
    hits = []
    for path in REPO.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in SCAN_EXTENSIONS:
            continue
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        file_hits = []
        for i, line in enumerate(text.splitlines(), 1):
            for pat in DECORATOR_PATTERNS:
                if pat.search(line):
                    file_hits.append({"line": i, "text": line.strip()[:120]})
                    break
        if file_hits:
            rel = str(path.relative_to(REPO)).replace("\\", "/")
            hits.append({"file": rel, "matches": len(file_hits), "lines": file_hits[:10]})
    hits.sort(key=lambda h: h["matches"], reverse=True)
    return hits


def vscode_default_comparison() -> dict:
    """Compare Flesh & Earth palette against VS Code Dark+ defaults."""
    vscode_dark_plus = {
        "editor.background": "#1E1E1E",
        "editor.foreground": "#D4D4D4",
        "activityBar.background": "#333333",
        "sideBar.background": "#252526",
        "statusBar.background": "#007ACC",
        "tab.activeBackground": "#1E1E1E",
        "terminal.background": "#1E1E1E",
    }
    flesh_earth = {
        "editor.background": "#110D0A",
        "editor.foreground": "#E8DCC8",
        "activityBar.background": "#1A1510",
        "sideBar.background": "#15110E",
        "statusBar.background": "#C9A962",
        "tab.activeBackground": "#110D0A",
        "terminal.background": "#110D0A",
    }

    def hex_to_rgb(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    def luminance(r: int, g: int, b: int) -> float:
        def ch(v: int) -> float:
            s = v / 255.0
            return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4
        return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)

    def contrast_ratio(c1: str, c2: str) -> float:
        l1 = luminance(*hex_to_rgb(c1))
        l2 = luminance(*hex_to_rgb(c2))
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    comparison = {}
    for key in vscode_dark_plus:
        vs = vscode_dark_plus[key]
        fe = flesh_earth.get(key, "N/A")
        if fe == "N/A":
            comparison[key] = {"vscode": vs, "flesh_earth": "unmapped"}
            continue
        ratio = contrast_ratio(vs, fe)
        comparison[key] = {
            "vscode_dark_plus": vs,
            "flesh_earth": fe,
            "inter_theme_contrast": round(ratio, 2),
            "transition_jarring": ratio > 3.0,
        }
    return comparison


def main():
    from scripts.lib.shared import configure_utf8_output
    configure_utf8_output()

    mode = sys.argv[1] if len(sys.argv) > 1 else "--summary"

    if mode == "--json":
        scan = scan_codebase()
        comp = vscode_default_comparison()
        output = {
            "design_system": DESIGN_SYSTEM,
            "vscode_comparison": comp,
            "codebase_references": scan,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))

    elif mode == "--scan":
        scan = scan_codebase()
        print(f"☥ Decorator Design System — {len(scan)} files with references\n")
        for hit in scan[:20]:
            print(f"  [{hit['matches']:3d}] {hit['file']}")
            for line in hit["lines"][:3]:
                print(f"        L{line['line']:4d}: {line['text'][:100]}")

    elif mode == "--compare":
        comp = vscode_default_comparison()
        print("☥ Flesh & Earth vs VS Code Dark+ Comparison\n")
        for key, data in comp.items():
            jarring = " ⚠️ JARRING" if data.get("transition_jarring") else " ✅"
            ratio = data.get("inter_theme_contrast", "?")
            print(f"  {key:30s} {data.get('vscode_dark_plus','?'):8s} → {data.get('flesh_earth','?'):8s}  ratio:{ratio}{jarring}")

    else:
        print("☥ THE DECORATOR — Design System Summary")
        print(f"  Entity:     {DESIGN_SYSTEM['entity']['name']} {DESIGN_SYSTEM['entity']['sigil']}")
        print(f"  Tier:       {DESIGN_SYSTEM['entity']['tier']} ({DESIGN_SYSTEM['entity']['tier_label']})")
        print(f"  Palette:    {DESIGN_SYSTEM['palette']['name']}")
        print(f"  Supreme:    {DESIGN_SYSTEM['palette']['supreme_gold']} ({DESIGN_SYSTEM['palette']['supreme_gold_note']})")
        print(f"  Background: {DESIGN_SYSTEM['palette']['background']}")
        print(f"  Colors:     {len(DESIGN_SYSTEM['palette']['colors'])}")
        print(f"  FA Axioms:  {len(DESIGN_SYSTEM['fa_axioms'])}")
        print(f"  Mandates:   {len(DESIGN_SYSTEM['aesthetic_mandates'])}")
        print(f"\n  Modes: --json | --scan | --compare")


if __name__ == "__main__":
    main()
