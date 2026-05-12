#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @SID: PATCH-HARANI-R2-001
# Round 2 targeted patch for §10.3.21 Hara'ni.
#
# SSOT fixes:
#   [A] Silence section: "The correct game asset is no lingerie layer"
#       -> "The correct rendered state is no lingerie layer"
#       (vocabulary sync with "Rendering directive" in Lingerie protocol note)
#     2. Substrate paragraph: "population extant in world"
#        -> "population extant in the world"
#     3. Substrate Traceability footer: "population extant in world"
#        -> "population extant in the world"
#
#   Staging (game/lore/species/harani_ssot_block.md):
#     4. Origin paragraph: "absent from the current world record"
#        -> "absent from the current world"
#        (patch_harani_staging.py introduced "world record" — wrong; geology
#         IS the world record; the intended meaning is the anomaly is absent
#         from the observable world today)
#     5. Same "game asset" -> "rendered state" fix as SSOT
#     6. Substrate "population extant in world" -> "in the world" (if present)

import sys
from pathlib import Path

SSOT = Path(".github/copilot-instructions.archive.md")
STAGING = Path("game/lore/species/harani_ssot_block.md")

SSOT_REPLACEMENTS = [
    # Silence section — missed in round 1
    (
        "The correct game asset is no lingerie layer — the architecture supports itself, as it has for forty millennia.",
        "The correct rendered state is no lingerie layer — the architecture supports itself, as it has for forty millennia.",
    ),
    # Substrate paragraph — add "the"
    (
        "not extinct, not mythic in the world — they are present, visible, assessed regularly). Unlike VLN-CNST, the substrate descends from evolutionary selection — it exists across a population, not as a single instance. Every Hara\u2019ni adult female carries this architecture as species baseline. Individual variation exists (range B160\u2013175, W38\u201344, H154\u2013162) but no member falls below O-cup volume at adult maturity.",
        "not extinct, not mythic in the world — they are present, visible, assessed regularly). Unlike VLN-CNST, the substrate descends from evolutionary selection — it exists across a population, not as a single instance. Every Hara\u2019ni adult female carries this architecture as species baseline. Individual variation exists (range B160\u2013175, W38\u201344, H154\u2013162) but no member falls below O-cup volume at adult maturity.",
    ),
    # Substrate paragraph — canonical form  (ASCII apostrophe variant)
    (
        "not extinct, not mythic in the world \u2014 they are present, visible, assessed regularly). Unlike VLN-CNST, the substrate descends from evolutionary selection \u2014 it exists across a population, not as a single instance. Every Hara'ni adult female carries this architecture as species baseline. Individual variation exists (range B160\u2013175, W38\u201344, H154\u2013162) but no member falls below O-cup volume at adult maturity.",
        "not extinct, not mythic in the world \u2014 they are present, visible, assessed regularly). Unlike VLN-CNST, the substrate descends from evolutionary selection \u2014 it exists across a population, not as a single instance. Every Hara'ni adult female carries this architecture as species baseline. Individual variation exists (range B160\u2013175, W38\u201344, H154\u2013162) but no member falls below O-cup volume at adult maturity.",
    ),
    # Substrate Traceability footer
    (
        "population extant in world)",
        "population extant in the world)",
    ),
]

STAGING_REPLACEMENTS = [
    # Fix "world record" bug introduced by patch_harani_staging.py
    (
        "The geological record of that anomaly is absent from the current world record.",
        "The geological record of that anomaly is absent from the current world.",
    ),
    # Same Silence section fix
    (
        "The correct game asset is no lingerie layer — the architecture supports itself, as it has for forty millennia.",
        "The correct rendered state is no lingerie layer — the architecture supports itself, as it has for forty millennia.",
    ),
    # Substrate Traceability footer (staging variant)
    (
        "population extant in the world)",
        "population extant in the world)",
    ),
]


def patch(path: Path, replacements: list, dry_run: bool) -> int:
    text = path.read_text(encoding="utf-8")
    total = 0
    for old, new in replacements:
        if old == new:
            continue
        count = text.count(old)
        if count:
            text = text.replace(old, new)
            total += count
            print(f"  [{count}x] '{old[:70]}...' -> '{new[:70]}...'")
    if total and not dry_run:
        path.write_text(text, encoding="utf-8")
        print(f"  Written: {path}")
    elif not total:
        print(f"  (nothing to change in {path.name})")
    return total


def main():
    dry_run = "--dry-run" in sys.argv
    mode = "DRY-RUN" if dry_run else "LIVE"
    print(f"=== Hara'ni §10.3.21 Round-2 Patch [{mode}] ===\n")

    print(f"SSOT: {SSOT}")
    ssot_total = patch(SSOT, SSOT_REPLACEMENTS, dry_run)

    print(f"\nStaging: {STAGING}")
    staging_total = patch(STAGING, STAGING_REPLACEMENTS, dry_run)

    print(f"\nTotal replacements: {ssot_total + staging_total}")
    if dry_run:
        print("Dry-run: no files written.")


if __name__ == "__main__":
    main()
