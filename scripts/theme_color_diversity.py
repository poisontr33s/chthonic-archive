#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: theme_color_diversity.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ extensions/chthonic-archive/themes/*.json
# ║   └─◄ scripts/theme_promote_master.py
# ║   └─◄ scripts/theme_artcop.py
# ╚════════════════════════════════════════════════════════════════════════════

"""
Theme Color Diversity Pass — reduce monotone color concentration.

After palette-aware promotion, many reference colors collapse to the same
nearest target color, creating visual monotony (e.g., 129 keys all using
the same gold #D9B56A). This script:

  1. Finds colors used more than --threshold times
  2. Groups the keys using each overused color by VS Code namespace
  3. Generates perceptual variants (±lightness, ±saturation)
  4. Redistributes keys across variants per-namespace
  5. Preserves alpha channels and non-hex values

The variants stay close enough to maintain theme identity while adding
enough differentiation that UI elements look distinct.

@SID:           TOOL_THEME_COLOR_DIVERSITY_V1
@Shabti:        CLI Script
@Heka-Ayni:     CONCEPT_THEME_REFINE
@Purpose:       Reduce color concentration via perceptual variant redistribution.

Usage:
  uv run scripts/theme_color_diversity.py --target mandala          # refine one
  uv run scripts/theme_color_diversity.py --target all              # refine all
  uv run scripts/theme_color_diversity.py --target all --dry-run    # preview
  uv run scripts/theme_color_diversity.py --target rogbiv --threshold 30
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import colorsys
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
THEMES_DIR = REPO_ROOT / "extensions" / "chthonic-archive" / "themes"
TARGETS = {
    "mandala": "chthonic-mandala-color-theme.json",
    "rogbiv": "chthonic-rogbiv-color-theme.json",
    "decorator": "chthonic-decorator-color-theme.json",
    "geology": "chthonic-geology-color-theme.json",
}

# --- Color math ---

def hex_to_rgb(h: str) -> tuple[float, float, float] | None:
    h = h.strip()
    if not h.startswith("#"):
        return None
    core = h[1:]
    if len(core) == 8:
        core = core[:6]
    if len(core) != 6:
        return None
    try:
        r, g, b = int(core[0:2], 16), int(core[2:4], 16), int(core[4:6], 16)
        return (r / 255.0, g / 255.0, b / 255.0)
    except ValueError:
        return None


def rgb_to_hex(r: float, g: float, b: float) -> str:
    return f"#{max(0,min(255,int(r*255))):02x}{max(0,min(255,int(g*255))):02x}{max(0,min(255,int(b*255))):02x}"


def generate_variants(base_hex: str, count: int, spread: float = 0.04) -> list[str]:
    """Generate `count` perceptual variants of a base color.

    Varies lightness and saturation symmetrically around the original.
    `spread` controls the maximum deviation (0.04 = ±4% lightness).
    """
    rgb = hex_to_rgb(base_hex)
    if rgb is None:
        return [base_hex] * count

    h, l, s = colorsys.rgb_to_hls(*rgb)

    variants = []
    if count == 1:
        return [base_hex]

    for i in range(count):
        # Distribute evenly from -spread to +spread
        t = (i / (count - 1)) * 2 - 1  # -1 to +1
        # Adjust lightness primarily, saturation secondarily
        new_l = max(0.0, min(1.0, l + t * spread))
        new_s = max(0.0, min(1.0, s + t * spread * 0.5))
        r, g, b = colorsys.hls_to_rgb(h, new_l, new_s)
        variants.append(rgb_to_hex(r, g, b))

    return variants


def namespace_of(key: str) -> str:
    """Extract the VS Code namespace prefix from a color key."""
    parts = key.split(".")
    if len(parts) >= 2:
        return parts[0]
    return key


def diversify_theme(theme_path: Path, threshold: int, spread: float,
                    dry_run: bool, variants: int | None = None) -> dict:
    """Run the diversity pass on a single theme file.

    threshold: colors appearing more than this many times are targeted.
        Default 20 is empirically chosen — colors appearing >20× create visual
        monotony without contributing semantic meaning (verified across all 4
        chthonic themes post-promotion, where single gold collapsed to 129 keys).
    variants: override the auto-computed variant count per overused color.
        If None, variant count is auto-derived from namespace group count.
    """
    theme = json.loads(theme_path.read_text(encoding="utf-8"))
    colors = theme.get("colors", {})

    # Count usage of each base color (ignoring alpha)
    usage: dict[str, list[str]] = {}
    for key, val in colors.items():
        if not isinstance(val, str) or not val.startswith("#"):
            continue
        base = val[:7].upper()
        usage.setdefault(base, []).append(key)

    overused = {color: keys for color, keys in usage.items()
                if len(keys) > threshold}

    stats = {
        "overused_colors": len(overused),
        "keys_diversified": 0,
        "max_before": max((len(v) for v in usage.values()), default=0),
        "details": [],
    }

    if not overused:
        return stats

    for color, keys in sorted(overused.items(), key=lambda x: -len(x[1])):
        # Group keys by namespace
        ns_groups: dict[str, list[str]] = {}
        for k in keys:
            ns = namespace_of(k)
            ns_groups.setdefault(ns, []).append(k)

        n_groups = len(ns_groups)
        if variants is not None:
            n_variants = variants
        elif n_groups < 2:
            # Single namespace — generate variants within it
            n_variants = min(max(3, len(keys) // 10), 8)
        else:
            n_variants = min(n_groups, 12)

        generated_variants = generate_variants(color.lower(), n_variants, spread)

        detail = {
            "color": color,
            "original_count": len(keys),
            "namespaces": n_groups,
            "variants_generated": len(generated_variants),
        }

        # Assign variants round-robin by namespace
        sorted_ns = sorted(ns_groups.keys())
        for i, ns in enumerate(sorted_ns):
            variant = generated_variants[i % len(generated_variants)]
            for key in ns_groups[ns]:
                old_val = colors[key]
                # Preserve alpha suffix
                alpha = old_val[7:] if len(old_val) > 7 else ""
                new_val = variant + alpha
                if not dry_run:
                    colors[key] = new_val
                stats["keys_diversified"] += 1

        stats["details"].append(detail)

    if not dry_run:
        theme["colors"] = dict(sorted(colors.items()))
        bak_path = theme_path.with_suffix(".bak")
        shutil.copy(theme_path, bak_path)
        theme_path.write_text(
            json.dumps(theme, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    # Compute max-after
    if not dry_run:
        recount = Counter()
        for val in colors.values():
            if isinstance(val, str) and val.startswith("#"):
                recount[val[:7].upper()] += 1
        stats["max_after"] = max(recount.values(), default=0)
    else:
        stats["max_after"] = "—"

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Reduce color concentration via perceptual variant redistribution")
    parser.add_argument("--target", required=True,
                        choices=["mandala", "rogbiv", "decorator", "geology", "all"],
                        help="Which theme(s) to refine")
    parser.add_argument("--threshold", type=int, default=20,
                        help="Colors used more than this many times are diversified (default: 20 — empirically chosen; colours appearing >20× create monotony without semantic meaning)")
    parser.add_argument("--spread", type=float, default=0.04,
                        help="Max lightness/saturation deviation (default: 0.04 = ±4%%)") 
    parser.add_argument("--variants", type=int, default=None,
                        help="Override auto-computed variant count per overused color (default: auto-derived from namespace group count, max 12)")
    parser.add_argument("--report-only", action="store_true",
                        help="Preview with full details but no file writes; richer than --dry-run (always shows per-color breakdown)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing files")
    args = parser.parse_args()

    print("☥ Theme Color Diversity Pass\n")

    targets = list(TARGETS.keys()) if args.target == "all" else [args.target]
    effective_dry_run = args.dry_run or args.report_only

    for t in targets:
        fname = TARGETS[t]
        path = THEMES_DIR / fname
        print(f"  ☥ {fname}")

        stats = diversify_theme(path, args.threshold, args.spread, effective_dry_run, args.variants)

        print(f"    Overused colors (>{args.threshold}x): {stats['overused_colors']}")
        print(f"    Keys diversified: {stats['keys_diversified']}")
        print(f"    Max usage: {stats['max_before']} → {stats['max_after']}")
        for d in stats.get("details", []):
            print(f"      {d['color']} × {d['original_count']} → "
                  f"{d['variants_generated']} variants across {d['namespaces']} namespaces")
        if args.report_only:
            print("    [REPORT ONLY — no files written (--report-only)]")
        elif args.dry_run:
            print("    [DRY RUN — no files written]")
        else:
            print(f"    ✅ Written")
        print()

    print("  ☥ Diversity pass complete. Run theme_artcop.py to verify WCAG.")


if __name__ == "__main__":
    main()
