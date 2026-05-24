#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: theme_sfs_transmute.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
SFS (Sister Ferrum Scoriae) Geological Core Transmutation — WPTG Stage 04.

Applies atomic, contextual changesets to the Geology theme to establish
geological identity through warm iron-dark backgrounds, differentiated
surface hierarchy, and reduced color concentration. Each changeset is
independently reversible (Atomic Reversibility directive).

@SID:           TOOL_THEME_SFS_TRANSMUTE_V1
@Shabti:          Utility
@Purpose:       SFS (Sister Ferrum Scoriae) Geological Core Transmutation — WPTG Stage 04.
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import hashlib
import json
import sys
import colorsys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
THEME_PATH = _REPO_ROOT / "extensions" / "chthonic-archive" / "themes" / "chthonic-geology-color-theme.json"

# --- SFS Geological Background Hierarchy ---
# Ferrum Scoriae = iron slag. Backgrounds evoke deep iron with warm undertones.
# Progressive lightening from editor (deepest) → widget (shallowest).
GEOLOGICAL_BACKGROUNDS = {
    # Deep iron: warm black with iron-brown undertone (H=25°, S=30%, L=3%)
    "editor.background":                "#0C0A08",
    "outputView.background":            "#0C0A08",
    "breadcrumb.background":            "#0C0A08",
    "tab.inactiveBackground":           "#0C0A08",
    "tab.unfocusedInactiveBackground":  "#0C0A08",
    # Forged iron: slightly lighter (H=25°, S=25%, L=4%)
    "sideBar.background":               "#100D0A",
    "activityBar.background":            "#100D0A",
    # Slag surface: differentiated panels (H=25°, S=20%, L=5%)
    "panel.background":                  "#130F0C",
    "terminal.background":               "#130F0C",
    # Crucible: elevated surfaces (H=25°, S=18%, L=7%)
    "editorWidget.background":           "#181310",
    "editorHoverWidget.background":      "#181310",
    "editorSuggestWidget.background":    "#181310",
    "peekViewEditor.background":         "#181310",
    "dropdown.background":               "#181310",
    "input.background":                  "#181310",
    "quickInput.background":             "#181310",
    "editorHoverWidget.statusBarBackground": "#100D0A",
}

# --- WCAG Foreground Fixes ---
# Where foreground was #000000 on a colored background, replace with a warm
# dark that reads well. #0C0A08 on #f3c32e = ~15:1. #0C0A08 on #79a9b1 = 7.2:1.
WCAG_FOREGROUND_FIXES = {
    "button.foreground":                "#0C0A08",
    "statusBar.noFolderForeground":     "#0C0A08",
    "statusBarItem.remoteForeground":   "#0C0A08",
    "statusBarItem.warningForeground":  "#0C0A08",
    "editorCursor.background":          "#0C0A08",
}

# Stable content hash of all changeset constants — used for idempotency check.
# Recomputed each import so it always reflects the current state of the consts.
_CHANGESET_HASH: str = hashlib.sha256(
    json.dumps(
        {"backgrounds": GEOLOGICAL_BACKGROUNDS, "wcag_fg": WCAG_FOREGROUND_FIXES},
        sort_keys=True,
    ).encode()
).hexdigest()[:16]


def hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    """Convert hex color to HSL (0-360, 0-100, 0-100)."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) > 6:
        hex_color = hex_color[:6]
    r, g, b = int(hex_color[0:2], 16) / 255, int(hex_color[2:4], 16) / 255, int(hex_color[4:6], 16) / 255
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s * 100, l * 100


def hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert HSL (0-360, 0-100, 0-100) to hex."""
    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


def warm_variant(hex_color: str, target_hue: float = 25.0, warmth: float = 0.15) -> str:
    """Shift a color's hue toward a warm target while preserving lightness."""
    if hex_color.lower().startswith('#000000') and len(hex_color) > 7:
        return hex_color  # Preserve alpha-channel transparent values
    h, s, l = hex_to_hsl(hex_color)
    if s < 2 and l < 8:  # Near-black neutrals: inject warm undertone
        new_h = target_hue
        new_s = max(s, 15.0 * warmth / 0.15)
        return hsl_to_hex(new_h, new_s, max(l, 2.5))
    return hex_color


def diversify_gold_ore(colors: dict, threshold: int = 35) -> dict:
    """Reduce #D7B562 concentration by generating geological variants.

    Gold ore in geology isn't uniform — it has pyrite (brassy), chalcopyrite
    (copper-gold), and electrum (pale gold) variations.
    """
    target = "#d7b562"
    matching_keys = [k for k, v in colors.items() if v.lower() == target]

    if len(matching_keys) <= threshold:
        return colors

    # Geological gold ore variants
    variants = [
        "#D7B562",  # Pure gold ore (original)
        "#D4B06A",  # Electrum (pale, silver-alloyed)
        "#DAB55A",  # Pyrite flash (brassy)
        "#D2B870",  # Chalcopyrite (copper undertone)
        "#D9B25E",  # Native gold (deep)
        "#D0B466",  # Alluvial gold (muted)
    ]

    # Group by VS Code namespace for consistent assignment
    namespaces: dict[str, list[str]] = {}
    for key in matching_keys:
        ns = key.split('.')[0] if '.' in key else '_root'
        namespaces.setdefault(ns, []).append(key)

    result = dict(colors)
    variant_idx = 0
    for ns in sorted(namespaces.keys()):
        for key in sorted(namespaces[ns]):
            result[key] = variants[variant_idx % len(variants)]
            variant_idx += 1

    return result


def apply_transmutation(theme: dict, dry_run: bool = False) -> dict:
    """Apply all SFS transmutation changesets."""
    colors = dict(theme.get("colors", {}))
    changes = []

    # Pass 1: Geological backgrounds
    for key, new_val in GEOLOGICAL_BACKGROUNDS.items():
        if key in colors:
            old_val = colors[key]
            if old_val.lower() != new_val.lower():
                changes.append(("BG-WARMTH", key, old_val, new_val))
                if not dry_run:
                    colors[key] = new_val

    # Pass 2: WCAG foreground fixes
    for key, new_val in WCAG_FOREGROUND_FIXES.items():
        if key in colors:
            old_val = colors[key]
            if old_val.lower() != new_val.lower():
                changes.append(("WCAG-FG", key, old_val, new_val))
                if not dry_run:
                    colors[key] = new_val

    # Pass 3: Gold ore diversification
    pre_gold = len([v for v in colors.values() if v.lower() == "#d7b562"])
    if pre_gold > 35:
        colors = diversify_gold_ore(colors)
        post_gold = len([v for v in colors.values() if v.lower() == "#d7b562"])
        changes.append(("GOLD-DIVERSIFY", f"#D7B562 usage", str(pre_gold), str(post_gold)))

    # Pass 4: Remaining #000000 backgrounds that should be warm
    remaining_black_bgs = [
        k for k, v in colors.items()
        if v.lower() == "#000000"
        and k not in GEOLOGICAL_BACKGROUNDS
        and k not in WCAG_FOREGROUND_FIXES
        and not k.endswith("Border")
        and not k.endswith("Opacity")
    ]
    for key in remaining_black_bgs:
        old_val = colors[key]
        # Only warm non-transparent, non-border #000000 values
        new_val = "#0C0A08"
        changes.append(("WARM-BLACK", key, old_val, new_val))
        if not dry_run:
            colors[key] = new_val

    if not dry_run:
        theme["colors"] = colors

    return changes


def _verify_idempotent(theme_path: Path) -> bool:
    """Check whether the theme already reflects all changeset values (idempotent state)."""
    with open(theme_path, "r", encoding="utf-8") as f:
        theme = json.load(f)
    colors = theme.get("colors", {})
    pending = []
    for key, expected in {**GEOLOGICAL_BACKGROUNDS, **WCAG_FOREGROUND_FIXES}.items():
        if key in colors and colors[key].lower() != expected.lower():
            pending.append((key, colors[key], expected))
    if pending:
        print(f"  VERIFY: PENDING — {len(pending)} changeset value(s) not yet applied")
        for key, current, expected in pending[:10]:
            print(f"    {key}: {current} → {expected}")
        if len(pending) > 10:
            print(f"    ... and {len(pending) - 10} more")
        return False
    print(f"  VERIFY: IDEMPOTENT — all changeset values already present in theme")
    print(f"  Changeset hash: {_CHANGESET_HASH}")
    return True


def main():
    parser = argparse.ArgumentParser(description="SFS Geological Core Transmutation — WPTG Stage 04")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing files")
    parser.add_argument("--verify", action="store_true",
                        help="Check if theme is already in idempotent (fully-applied) state; exit 0 if yes, 1 if not")
    args = parser.parse_args()

    if not THEME_PATH.exists():
        print(f"ERROR: Theme not found at {THEME_PATH}")
        sys.exit(1)

    if args.verify:
        ok = _verify_idempotent(THEME_PATH)
        sys.exit(0 if ok else 1)

    with open(THEME_PATH, 'r', encoding='utf-8') as f:
        theme = json.load(f)

    print(f"☥ SFS TRANSMUTATION — WPTG Stage 04")
    print(f"  Theme: {theme.get('name', 'Unknown')}")
    print(f"  Changeset hash: {_CHANGESET_HASH}")
    print(f"  Mode:  {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()

    changes = apply_transmutation(theme, dry_run=args.dry_run)

    # Report
    categories = {}
    for cat, key, old, new in changes:
        categories.setdefault(cat, []).append((key, old, new))

    for cat in ["BG-WARMTH", "WCAG-FG", "GOLD-DIVERSIFY", "WARM-BLACK"]:
        items = categories.get(cat, [])
        if items:
            print(f"  [{cat}] {len(items)} changes:")
            for key, old, new in items:
                print(f"    {key}: {old} → {new}")
            print()

    total = len(changes)
    print(f"  Total changesets: {total}")

    if not args.dry_run and total > 0:
        with open(THEME_PATH, 'w', encoding='utf-8') as f:
            json.dump(theme, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print(f"\n  ✅ Written to {THEME_PATH}")
    elif args.dry_run:
        print(f"\n  (dry run — no files modified)")


if __name__ == "__main__":
    main()

