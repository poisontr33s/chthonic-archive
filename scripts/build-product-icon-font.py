#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: build-product-icon-font.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Add new glyphs to chthonic-product-icons.woff by direct T2CharString injection.
Does NOT rebuild from scratch — preserves all existing glyphs.

Usage:
    uv run scripts/build-product-icon-font.py [--dry-run] [--verify] [--list]

    --dry-run   Show what would be added, don't write.
    --verify    After writing, verify all new codepoints are in output font.
    --list      List all current glyphs in the font and exit.

Current task: add E02D (folder) to separate it from E00A (extensions).

Requires: fonttools (installed automatically by uv run)

@SID:           BUILD_PRODUCT_ICON_FONT_V2
@Shabti:        CLI Script
@Purpose:       Add new glyphs to chthonic-product-icons.woff by direct T2CharString injection.
"""

#@SID: BUILD_PRODUCT_ICON_FONT_V2


import json
import sys
from pathlib import Path

REPO     = Path(__file__).resolve().parent.parent
WOFF_IN  = REPO / "extensions/chthonic-archive/themes/fonts/chthonic-product-icons.woff"
WOFF_OUT = WOFF_IN  # overwrite in place
MAP_FILE = REPO / "extensions/chthonic-archive/themes/fonts/chthonic-product-icons.json"

DRY_RUN = "--dry-run" in sys.argv
VERIFY  = "--verify"  in sys.argv
LIST    = "--list"    in sys.argv

# ─── New glyphs to add ───────────────────────────────────────────────────────
# Each entry: (glyph_name, codepoint, T2CharString program)
# T2 program uses string operator names (rmoveto, rlineto, endchar).
# Coordinates are relative. Y-up, em=1000.
#
# Folder shape: body rect + raised tab at top-left
_FOLDER_PROGRAM = [
    80, 100, "rmoveto",     # move to bottom-left of body
    840,   0, "rlineto",    # → bottom-right  (920, 100)
      0, 720, "rlineto",    # ↑ top-right      (920, 820)
   -470,   0, "rlineto",    # ← top-mid        (450, 820)
      0,  40, "rlineto",    # ↑ tab-inner-left  (450, 860)
   -370,   0, "rlineto",    # ← tab-top-left    (80,  860)
      0,-760, "rlineto",    # ↓ back to start   (80,  100)
    "endchar",
]

NEW_GLYPHS: list[tuple[str, int, list]] = [
    ("folder", 0xE02D, _FOLDER_PROGRAM),
]


def main() -> None:
    from fontTools.ttLib import TTFont
    from fontTools.misc.psCharStrings import T2CharString

    if not WOFF_IN.exists():
        sys.exit(f"ERROR: font not found at {WOFF_IN}")

    font = TTFont(WOFF_IN)
    cmap = font.getBestCmap()

    if LIST:
        glyph_map = json.loads(MAP_FILE.read_text())
        cp_to_name = {int(v.replace("U+", ""), 16): k for k, v in glyph_map.items()}
        print(f"{'Codepoint':<12} {'Canonical':<40} {'Glyph name'}")
        print("-" * 65)
        for cp in sorted(cmap.keys()):
            canonical = cp_to_name.get(cp, "—")
            print(f"U+{cp:04X}       {canonical:<40} {cmap[cp]}")
        return

    if "CFF " not in font and "glyf" not in font:
        sys.exit("ERROR: unrecognized font format (expected CFF or glyf)")

    is_cff = "CFF " in font

    for glyph_name, codepoint, program in NEW_GLYPHS:
        if codepoint in cmap:
            print(f"[build-font] SKIP U+{codepoint:04X} ({glyph_name}) — already in font")
            continue

        print(f"[build-font] {'DRY-RUN: ' if DRY_RUN else ''}adding U+{codepoint:04X} → {glyph_name}")

        if DRY_RUN:
            continue

        font.glyphOrder = font.glyphOrder + [glyph_name]

        for table in font["cmap"].tables:
            if hasattr(table, "cmap") and table.isUnicode():
                table.cmap[codepoint] = glyph_name

        font["hmtx"].metrics[glyph_name] = (1000, 80)

        if is_cff:
            cs = T2CharString()
            cs.program = list(program)
            font["CFF "].cff.topDictIndex[0].CharStrings[glyph_name] = cs
        else:
            # TrueType: convert the relative-move program to absolute pen calls
            from fontTools.pens.ttGlyphPen import TTGlyphPen
            tt_pen = TTGlyphPen(None)
            # Build absolute coordinates from the relative program
            x, y = 0, 0
            started = False
            i = 0
            while i < len(program):
                tok = program[i]
                if isinstance(tok, str):
                    if tok == "rmoveto":
                        x += int(program[i - 2])
                        y += int(program[i - 1])
                        if started:
                            tt_pen.closePath()
                        tt_pen.moveTo((x, y))
                        started = True
                    elif tok == "rlineto":
                        x += int(program[i - 2])
                        y += int(program[i - 1])
                        tt_pen.lineTo((x, y))
                    elif tok == "endchar":
                        if started:
                            tt_pen.closePath()
                        break
                i += 1
            glyph = tt_pen.glyph()
            font["glyf"][glyph_name] = glyph
            # Recalculate bounds
            font["glyf"][glyph_name].recalcBounds(font["glyf"])

    if DRY_RUN:
        print("[build-font] --dry-run: no output written")
        return

    font.flavor = "woff"
    font.save(str(WOFF_OUT))
    print(f"[build-font] ✓ wrote {WOFF_OUT}")

    glyph_map = json.loads(MAP_FILE.read_text())
    changed = False
    for glyph_name, codepoint, _ in NEW_GLYPHS:
        cp_str = f"U+{codepoint:04X}"
        if glyph_name not in glyph_map:
            glyph_map[glyph_name] = cp_str
            changed = True
    if changed:
        MAP_FILE.write_text(json.dumps(glyph_map, indent=2) + "\n", encoding="utf-8")
        print(f"[build-font] ✓ updated {MAP_FILE.name}")

    if VERIFY:
        verify_font = TTFont(WOFF_OUT)
        verify_cmap = verify_font.getBestCmap()
        fail = 0
        for glyph_name, codepoint, _ in NEW_GLYPHS:
            if verify_cmap.get(codepoint) == glyph_name:
                print(f"[build-font] verify ✓ U+{codepoint:04X} → {glyph_name}")
            else:
                print(f"[build-font] verify ✗ U+{codepoint:04X} expected {glyph_name}, got {verify_cmap.get(codepoint)}")
                fail += 1
        if fail:
            sys.exit(1)


if __name__ == "__main__":
    main()
