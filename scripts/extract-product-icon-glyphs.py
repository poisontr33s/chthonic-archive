#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: extract-product-icon-glyphs.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Extract glyphs from chthonic-product-icons.woff → SVG files in themes/fonts/src/
Each glyph becomes one SVG file named by its canonical glyph name (from fonts/*.json).

Usage:
    uv run scripts/extract-product-icon-glyphs.py [--list]
    --list  Print glyph names and codepoints only, don't write files.

Requires: fonttools (installed automatically by uv run)

@SID:           EXTRACT_PRODUCT_ICON_GLYPHS_V1
@Shabti:        CLI Script
@Purpose:       Extract glyphs from chthonic-product-icons.woff → SVG files in themes/fonts/src/
"""

# @SID: EXTRACT_PRODUCT_ICON_GLYPHS_V1


import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WOFF = REPO / "extensions/chthonic-archive/themes/fonts/chthonic-product-icons.woff"
MAP_FILE = REPO / "extensions/chthonic-archive/themes/fonts/chthonic-product-icons.json"
OUT_DIR = REPO / "extensions/chthonic-archive/themes/fonts/src"

LIST_ONLY = "--list" in sys.argv


def cp_to_int(cp_str: str) -> int:
    """Convert 'U+E001' → 0xE001"""
    return int(cp_str.replace("U+", ""), 16)


def main() -> None:
    from fontTools.ttLib import TTFont
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.misc.transform import Identity

    if not WOFF.exists():
        sys.exit(f"ERROR: font not found at {WOFF}")

    glyph_map: dict[str, str] = json.loads(MAP_FILE.read_text())

    font = TTFont(WOFF)
    cmap = font.getBestCmap()
    glyph_set = font.getGlyphSet()

    # Build reverse map: glyph_name → canonical_id
    reverse: dict[str, str] = {}
    for canonical_id, cp_str in glyph_map.items():
        cp = cp_to_int(cp_str)
        glyph_name = cmap.get(cp)
        if glyph_name:
            reverse[glyph_name] = canonical_id

    if LIST_ONLY:
        print(f"{'Canonical ID':<40} {'Codepoint':<10} {'Glyph Name'}")
        print("-" * 70)
        for canonical_id, cp_str in sorted(glyph_map.items(), key=lambda x: x[1]):
            cp = cp_to_int(cp_str)
            glyph_name = cmap.get(cp, "NOT IN FONT")
            print(f"{canonical_id:<40} {cp_str:<10} {glyph_name}")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    units_per_em = font["head"].unitsPerEm
    ascender = font["hhea"].ascender
    descender = font["hhea"].descender

    extracted = 0
    missing = 0

    for canonical_id, cp_str in glyph_map.items():
        cp = cp_to_int(cp_str)
        glyph_name = cmap.get(cp)
        if not glyph_name:
            print(f"WARN: no glyph for {canonical_id} ({cp_str})")
            missing += 1
            continue

        pen = SVGPathPen(glyph_set)
        glyph_set[glyph_name].draw(pen)
        path_data = pen.getCommands()

        # Build minimal SVG (viewBox matches font em square)
        # Y axis is flipped for SVG (font coords: up = positive, SVG: down = positive)
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 {-ascender} {units_per_em} {units_per_em}">\n'
            f'  <g transform="scale(1,-1) translate(0,{-ascender})">\n'
            f'    <path d="{path_data}"/>\n'
            f'  </g>\n'
            f'</svg>\n'
        )

        out_file = OUT_DIR / f"{canonical_id}.svg"
        out_file.write_text(svg, encoding="utf-8")
        extracted += 1

    print(f"[extract-product-icon-glyphs] ✓ extracted {extracted} glyphs → {OUT_DIR}")
    if missing:
        print(f"[extract-product-icon-glyphs] WARN: {missing} codepoints not found in font")


if __name__ == "__main__":
    main()
