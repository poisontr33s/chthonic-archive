#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: patch_harani_game_refs.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
patch_harani_game_refs.py — Script logic for patch_harani_game_refs.py.

@SID:           PATCH_HARANI_GAME_REFS_V1
@Shabti:        CLI Script
@Purpose:       Script logic for patch_harani_game_refs.py.
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# @SID: PATCH_HARANI_GAME_REFS_V1
# Remove all 'game world' / 'game-world' compound phrases from §10.3.21 in SSOT.
# The SSOT describes a world, not a game; self-referential 'game' breaks canon immersion.

import sys

SSOT_PATH = ".github/copilot-instructions.archive.md"

REPLACEMENTS = [
    ("the game world\u2019s continent", "the world\u2019s continent"),
    ("the game world's continent", "the world's continent"),
    ("occupy game-world positions from NPC-neutral", "occupy world positions from NPC-neutral"),
    ("in current game-world timeline", "in the current timeline"),
    ("any civilization in the game world\u2019s documented history", "any civilization in documented history"),
    ("any civilization in the game world's documented history", "any civilization in documented history"),
    ("Game-side directive:** the correct rendered state for Hara\u2019ni in the ASC-NATIVE-CHAIN-RPG is no lingerie layer",
     "Rendering directive:** the correct rendered state for Hara\u2019ni is no lingerie layer"),
    ("Game-side directive:** the correct rendered state for Hara'ni in the ASC-NATIVE-CHAIN-RPG is no lingerie layer",
     "Rendering directive:** the correct rendered state for Hara'ni is no lingerie layer"),
    ("40,000 years prior to game-world present", "40,000 years prior to the world\u2019s present"),
    ("not extinct, not mythic in the game world", "not extinct, not mythic in the world"),
    ("current game-world status: sovereign", "current status: sovereign"),
    # catch any remaining generic compounds
    ("game-world", "world"),
    ("game world", "world"),
]

def main():
    dry_run = "--dry-run" in sys.argv

    with open(SSOT_PATH, encoding="utf-8") as f:
        content = f.read()

    original = content
    applied = []
    for old, new in REPLACEMENTS:
        if old in content:
            count = content.count(old)
            content = content.replace(old, new)
            applied.append((old, new, count))

    if not applied:
        print("No replacements needed — content already clean.")
        return

    for old, new, count in applied:
        print(f"  [{count}x] '{old}' -> '{new}'")

    if dry_run:
        print("\nDry-run: no file written.")
        return

    with open(SSOT_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\nWritten: {SSOT_PATH}")
    print(f"Total replacements: {sum(c for _, _, c in applied)}")

if __name__ == "__main__":
    main()
