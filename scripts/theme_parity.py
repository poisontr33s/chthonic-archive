#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: theme_parity.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Theme Parity Checker — ensures all Chthonic VS Code color themes share
the same structural coverage: identical workbench color keys, matching
tokenColors scope count, and consistent semantic token modifier sets.

Reports missing/extra keys per theme relative to the canonical master
(Flesh & Earth / The Decorator).

@SID:           TOOL_THEME_PARITY_V1
@Shabti:          Utility
@Purpose:       Theme Parity Checker — ensures all Chthonic VS Code color themes share
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


import argparse
import json
import sys
from pathlib import Path

from scripts.lib.shared import configure_utf8_output

REPO = Path(__file__).resolve().parent.parent
THEME_DIR = REPO / "extensions" / "chthonic-archive" / "themes"
# The Decorator theme has the most comprehensive key coverage and is the
# T0.5 authority in the chthonic palette hierarchy. Mandala is a subset.
MASTER_NAME = "chthonic-decorator-color-theme.json"


def _load_theme(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_parity(master_path: Path, target_path: Path) -> dict:
    """Compare a target theme against the master for structural parity."""
    master = _load_theme(master_path)
    target = _load_theme(target_path)

    master_colors = set(master.get("colors", {}).keys())
    target_colors = set(target.get("colors", {}).keys())

    master_stc = set(master.get("semanticTokenColors", {}).keys())
    target_stc = set(target.get("semanticTokenColors", {}).keys())

    master_tc_count = len(master.get("tokenColors", []))
    target_tc_count = len(target.get("tokenColors", []))

    return {
        "name": target.get("name", target_path.name),
        "file": target_path.name,
        "colors_missing": sorted(master_colors - target_colors),
        "colors_extra": sorted(target_colors - master_colors),
        "semantic_missing": sorted(master_stc - target_stc),
        "semantic_extra": sorted(target_stc - master_stc),
        "token_count_master": master_tc_count,
        "token_count_target": target_tc_count,
    }


def main() -> None:
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        description="Check structural parity of all Chthonic VS Code themes against a master")
    parser.add_argument("--master", default=MASTER_NAME,
                        help=f"Master theme filename (default: {MASTER_NAME})")
    parser.add_argument("--json", dest="json_mode", action="store_true",
                        help="Emit results as JSON")
    args = parser.parse_args()

    master_path = THEME_DIR / args.master
    if not master_path.exists():
        print(f"Master theme not found: {master_path}", file=sys.stderr)
        sys.exit(1)

    # Discover all color theme JSONs except the master and icon themes
    targets = sorted(
        p for p in THEME_DIR.glob("*-color-theme.json")
        if p.name != args.master
    )

    if not targets:
        print("No target themes found alongside master.", file=sys.stderr)
        sys.exit(1)

    json_mode = args.json_mode

    all_results = []
    all_pass = True

    print(f"☥ THEME PARITY CHECK — Master: {args.master}\n")

    for t in targets:
        result = check_parity(master_path, t)
        all_results.append(result)

        cm = result["colors_missing"]
        ce = result["colors_extra"]
        sm = result["semantic_missing"]
        se = result["semantic_extra"]
        tc_ok = result["token_count_master"] == result["token_count_target"]
        perfect = not cm and not ce and not sm and not se and tc_ok

        if not perfect:
            all_pass = False

        if json_mode:
            continue

        icon = "✅" if perfect else "❌"
        print(f"  {icon} {result['name']}")
        print(f"     File: {result['file']}")
        print(f"     Colors: {len(cm)} missing, {len(ce)} extra")
        print(f"     Semantic tokens: {len(sm)} missing, {len(se)} extra")
        print(f"     Token rules: {result['token_count_target']}/{result['token_count_master']}")

        if cm:
            print(f"     ↳ Missing colors: {', '.join(cm[:8])}")
            if len(cm) > 8:
                print(f"       ... and {len(cm) - 8} more")
        if ce:
            print(f"     ↳ Extra colors: {', '.join(ce[:8])}")
            if len(ce) > 8:
                print(f"       ... and {len(ce) - 8} more")
        if sm:
            print(f"     ↳ Missing semantic: {', '.join(sm)}")
        if se:
            print(f"     ↳ Extra semantic: {', '.join(se)}")
        if not tc_ok:
            print(f"     ↳ Token count mismatch: {result['token_count_target']} vs master {result['token_count_master']}")
        print()

    if json_mode:
        print(json.dumps(all_results, indent=2, ensure_ascii=False))
        return

    # Summary — per-theme missing key count
    total = len(targets)
    passed = sum(1 for r in all_results
                 if not r["colors_missing"] and not r["colors_extra"]
                 and not r["semantic_missing"] and not r["semantic_extra"]
                 and r["token_count_master"] == r["token_count_target"])
    grade = "🟢 ALL PASS" if all_pass else f"🔴 {total - passed}/{total} DIVERGENT"
    print(f"  Parity: {passed}/{total} themes match master — {grade}")
    print()
    print("  Missing key counts (colors | semantic | token rules):")
    for r in all_results:
        cm = len(r["colors_missing"])
        sm = len(r["semantic_missing"])
        tc_delta = r["token_count_master"] - r["token_count_target"]
        icon = "✅" if cm == 0 and sm == 0 and tc_delta == 0 else "❌"
        print(f"  {icon} {r['file']}: {cm} colors | {sm} semantic | {tc_delta:+d} token rules")

    if not all_pass:
        sys.exit(1)


if __name__ == "__main__":
    main()
