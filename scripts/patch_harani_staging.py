#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: patch_harani_staging.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
patch_harani_staging.py — Script logic for patch_harani_staging.py.

@SID:           PATCH_HARANI_STAGING_V1
@Shabti:        CLI Script
@Purpose:       Script logic for patch_harani_staging.py.
"""

# @SID: PATCH_HARANI_STAGING_V1
# Apply same game-world removals to the harani_ssot_block.md staging file.

import sys

TARGET = "game/lore/species/harani_ssot_block.md"

REPLACEMENTS = [
    ("The geological record of that anomaly is absent from the current game world.",
     "The geological record of that anomaly is absent from the current world record."),
    ("the current game world", "the current world"),
    ("occupy game-world positions from NPC-neutral", "occupy world positions from NPC-neutral"),
    ("in current game-world timeline", "in the current timeline"),
    ("any civilization in the game world\u2019s documented history", "any civilization in documented history"),
    ("any civilization in the game world's documented history", "any civilization in documented history"),
    ("**Game-side directive:** the correct rendered state for Hara\u2019ni in the ASC-NATIVE-CHAIN-RPG is no lingerie layer",
     "**Rendering directive:** the correct rendered state for Hara\u2019ni is no lingerie layer"),
    ("**Game-side directive:** the correct rendered state for Hara'ni in the ASC-NATIVE-CHAIN-RPG is no lingerie layer",
     "**Rendering directive:** the correct rendered state for Hara'ni is no lingerie layer"),
    ("current game-world status: sovereign", "current status: sovereign"),
    ("population extant in game world", "population extant in the world"),
    ("game-world", "world"),
    ("game world", "world"),
]

def main():
    dry_run = "--dry-run" in sys.argv

    with open(TARGET, encoding="utf-8") as f:
        content = f.read()

    applied = []
    for old, new in REPLACEMENTS:
        if old in content:
            count = content.count(old)
            content = content.replace(old, new)
            applied.append((old, new, count))

    if not applied:
        print("No replacements needed.")
        return

    for old, new, count in applied:
        print(f"  [{count}x] '{old[:60]}' -> '{new[:60]}'")

    if dry_run:
        print("\nDry-run: no file written.")
        return

    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\nWritten: {TARGET}")

if __name__ == "__main__":
    main()
