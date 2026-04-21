#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: theme_promote_master.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ extensions/chthonic-archive/themes/*.json
# ║   └─◄ scripts/milf_scanner.py
# ║   └─◄ scripts/theme_parity.py
# ╚════════════════════════════════════════════════════════════════════════════

"""
Theme Promote Master — bring thin themes up to full key coverage.

The Decorator (669 keys) and Geology (669 keys) have comprehensive VS Code
color coverage. Mandala (master, 209 keys) and ROGBIV (209 keys) are missing
~460 color keys, ~53 token rules, and ~44 semantic tokens.

This script:
  1. Reads the "reference" theme (Geology = most comprehensive)
  2. Reads a "target" theme (Mandala or ROGBIV)
  3. For every key in reference that target lacks, generates a value
     by mapping the reference palette onto the target palette using
     color-space proximity (closest hue/luminance match)
  4. Writes the expanded target back

The palette mapping preserves each theme's character identity while
ensuring all VS Code UI surfaces are covered.

@SID:           TOOL_THEME_PROMOTE_MASTER_V1
@Shabti:        CLI Script
@Heka-Ayni:     CONCEPT_THEME_PROMOTE
@Purpose:       Expand thin themes to full coverage via palette-aware key promotion.

Usage:
  uv run scripts/theme_promote_master.py --target mandala      # expand mandala
  uv run scripts/theme_promote_master.py --target rogbiv        # expand rogbiv
  uv run scripts/theme_promote_master.py --target all           # expand both
  uv run scripts/theme_promote_master.py --dry-run --target all # preview only
"""

import argparse
import colorsys
import json
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
THEMES_DIR = REPO_ROOT / "extensions" / "chthonic-archive" / "themes"

REFERENCE = "chthonic-geology-color-theme.json"
TARGETS = {
    "mandala": "chthonic-mandala-color-theme.json",
    "rogbiv": "chthonic-rogbiv-color-theme.json",
    "decorator": "chthonic-decorator-color-theme.json",
    "geology": "chthonic-geology-color-theme.json",
}


def hex_to_rgb(h: str) -> tuple[float, float, float] | None:
    """Parse #RRGGBB or #RRGGBBAA to (r,g,b) floats 0-1."""
    h = h.strip()
    if not h.startswith("#"):
        return None
    h = h[1:]
    if len(h) == 8:
        h = h[:6]  # strip alpha
    if len(h) != 6:
        return None
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (r / 255.0, g / 255.0, b / 255.0)
    except ValueError:
        return None


def rgb_to_hex(r: float, g: float, b: float) -> str:
    return f"#{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"


def hex_to_hsl(h: str) -> tuple[float, float, float] | None:
    rgb = hex_to_rgb(h)
    if rgb is None:
        return None
    return colorsys.rgb_to_hls(*rgb)  # note: hls not hsl


def color_distance(c1: str, c2: str, metric: str = "hsl") -> float:
    """Distance between two hex colors.

    metric='hsl'  (default): perceptual HSL delta — weight hue×3 + light + sat
    metric='euclidean': sRGB Euclidean distance (0..1 normalised per channel)
    """
    if metric == "euclidean":
        def _parse_rgb(h: str) -> tuple[float, float, float] | None:
            h = h.lstrip("#")
            if len(h) < 6:
                return None
            try:
                r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
                return r / 255.0, g / 255.0, b / 255.0
            except ValueError:
                return None
        rgb1 = _parse_rgb(c1)
        rgb2 = _parse_rgb(c2)
        if rgb1 is None or rgb2 is None:
            return 999.0
        import math
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))

    hsl1 = hex_to_hsl(c1)
    hsl2 = hex_to_hsl(c2)
    if hsl1 is None or hsl2 is None:
        return 999.0
    # Weight hue more than lightness and saturation
    dh = min(abs(hsl1[0] - hsl2[0]), 1.0 - abs(hsl1[0] - hsl2[0]))
    dl = abs(hsl1[1] - hsl2[1])
    ds = abs(hsl1[2] - hsl2[2])
    return (dh * 3.0) + dl + ds


def extract_hex_from_value(val) -> str | None:
    """Extract the primary hex color from a theme value (string or dict)."""
    if isinstance(val, str):
        m = re.match(r"^(#[0-9A-Fa-f]{6,8})", val)
        return m.group(1)[:7] if m else None
    if isinstance(val, dict) and "foreground" in val:
        return extract_hex_from_value(val["foreground"])
    return None


def build_palette_map(ref_colors: dict, target_colors: dict) -> dict[str, str]:
    """Build a mapping from reference hex values to nearest target hex values."""
    # Collect unique colors from each palette
    ref_hexes = set()
    for v in ref_colors.values():
        h = extract_hex_from_value(v)
        if h:
            ref_hexes.add(h[:7].upper())

    target_hexes = set()
    for v in target_colors.values():
        h = extract_hex_from_value(v)
        if h:
            target_hexes.add(h[:7].upper())

    if not target_hexes:
        return {}

    target_list = sorted(target_hexes)
    mapping = {}
    for rh in ref_hexes:
        best = min(target_list, key=lambda th: color_distance(rh, th))
        mapping[rh] = best

    return mapping


def map_color(ref_value: str, palette_map: dict[str, str]) -> str:
    """Map a reference color value to the target palette."""
    if not isinstance(ref_value, str):
        return ref_value

    m = re.match(r"^(#[0-9A-Fa-f]{6})([0-9A-Fa-f]{0,2})$", ref_value)
    if not m:
        return ref_value

    base = m.group(1).upper()
    alpha = m.group(2)

    mapped = palette_map.get(base, base)
    return mapped.lower() + alpha.lower() if alpha else mapped.lower()


def map_semantic_value(ref_value, palette_map: dict[str, str]):
    """Map a semantic token value (string or dict with foreground/fontStyle)."""
    if isinstance(ref_value, str):
        return map_color(ref_value, palette_map)
    if isinstance(ref_value, dict):
        result = {}
        if "foreground" in ref_value:
            result["foreground"] = map_color(ref_value["foreground"], palette_map)
        if "fontStyle" in ref_value:
            result["fontStyle"] = ref_value["fontStyle"]
        return result
    return ref_value


def promote_colors(ref_theme: dict, target_theme: dict, palette_map: dict) -> tuple[dict, int]:
    """Add missing color keys from reference to target using palette mapping."""
    ref_colors = ref_theme.get("colors", {})
    target_colors = target_theme.setdefault("colors", {})

    added = 0
    for key, ref_val in sorted(ref_colors.items()):
        if key not in target_colors:
            mapped = map_color(ref_val, palette_map) if isinstance(ref_val, str) else ref_val
            target_colors[key] = mapped
            added += 1

    return target_colors, added


def promote_semantic_tokens(ref_theme: dict, target_theme: dict, palette_map: dict) -> tuple[dict, int]:
    """Add missing semantic token entries."""
    ref_st = ref_theme.get("semanticTokenColors", {})
    target_st = target_theme.setdefault("semanticTokenColors", {})

    added = 0
    for key, ref_val in sorted(ref_st.items()):
        if key not in target_st:
            target_st[key] = map_semantic_value(ref_val, palette_map)
            added += 1

    return target_st, added


def promote_token_rules(ref_theme: dict, target_theme: dict, palette_map: dict) -> tuple[list, int]:
    """Add missing textmate token rules."""
    ref_rules = ref_theme.get("tokenColors", [])
    target_rules = target_theme.setdefault("tokenColors", [])

    # Index existing target rules by scope signature
    def scope_sig(rule):
        scope = rule.get("scope", "")
        if isinstance(scope, list):
            return tuple(sorted(scope))
        return (scope,)

    existing = {scope_sig(r) for r in target_rules}

    added = 0
    for rule in ref_rules:
        sig = scope_sig(rule)
        if sig not in existing:
            new_rule = {"scope": rule.get("scope", "")}
            settings = {}
            for k, v in rule.get("settings", {}).items():
                if k == "foreground":
                    settings[k] = map_color(v, palette_map)
                else:
                    settings[k] = v
            new_rule["settings"] = settings
            if "name" in rule:
                new_rule["name"] = rule["name"]
            target_rules.append(new_rule)
            existing.add(sig)
            added += 1

    return target_rules, added


def run(target_name: str, dry_run: bool = False, reference: str | None = None) -> bool:
    target_file = TARGETS.get(target_name)
    if not target_file:
        print(f"  Unknown target: {target_name}")
        return False

    ref_file = reference or REFERENCE
    # Don't promote a theme against itself
    if ref_file == target_file:
        print(f"\n  ☥ Skipping {target_name}: same as reference")
        return True

    ref_path = THEMES_DIR / ref_file
    target_path = THEMES_DIR / target_file

    ref_theme = json.loads(ref_path.read_text(encoding="utf-8"))
    target_theme = json.loads(target_path.read_text(encoding="utf-8"))

    # Build palette map from reference → target color space
    ref_all_colors = {}
    ref_all_colors.update(ref_theme.get("colors", {}))
    for k, v in ref_theme.get("semanticTokenColors", {}).items():
        ref_all_colors[f"__sem_{k}"] = v

    target_all_colors = {}
    target_all_colors.update(target_theme.get("colors", {}))
    for k, v in target_theme.get("semanticTokenColors", {}).items():
        target_all_colors[f"__sem_{k}"] = v

    palette_map = build_palette_map(ref_all_colors, target_all_colors)

    print(f"\n  ☥ Promoting: {target_file}")
    print(f"    Reference: {ref_file}")
    print(f"    Palette map: {len(palette_map)} color mappings")

    _, colors_added = promote_colors(ref_theme, target_theme, palette_map)
    _, semantic_added = promote_semantic_tokens(ref_theme, target_theme, palette_map)
    _, tokens_added = promote_token_rules(ref_theme, target_theme, palette_map)

    total_colors = len(target_theme.get("colors", {}))
    total_semantic = len(target_theme.get("semanticTokenColors", {}))
    total_tokens = len(target_theme.get("tokenColors", []))

    print(f"    Colors: +{colors_added} → {total_colors} total")
    print(f"    Semantic tokens: +{semantic_added} → {total_semantic} total")
    print(f"    Token rules: +{tokens_added} → {total_tokens} total")

    if dry_run:
        print("    [DRY RUN — no files written]")
        return True

    # Sort colors alphabetically for readability
    if "colors" in target_theme:
        target_theme["colors"] = dict(sorted(target_theme["colors"].items()))

    # Backup before any modification
    bak_path = target_path.with_suffix(".bak")
    shutil.copy(target_path, bak_path)

    target_path.write_text(
        json.dumps(target_theme, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"    ✅ Written: {target_path.name}  (backup: {bak_path.name})")
    return True


def main():
    parser = argparse.ArgumentParser(description="Promote thin themes to full key coverage")
    parser.add_argument("--target", required=True,
                        choices=["mandala", "rogbiv", "decorator", "geology", "all"],
                        help="Which theme(s) to promote")
    parser.add_argument("--reference", default=None,
                        help="Override reference theme file (default: geology)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing files")
    parser.add_argument("--distance-metric", choices=["hsl", "euclidean"], default="hsl",
                        help="Color distance formula: hsl (default, perceptual HSL weighting) or euclidean (sRGB L2 norm)")
    args = parser.parse_args()

    print("☥ Theme Promote Master")

    targets = list(TARGETS.keys()) if args.target == "all" else [args.target]
    results = []
    for t in targets:
        results.append(run(t, args.dry_run, args.reference))

    if all(results):
        print("\n  ☥ Promotion complete. Run theme_parity.py to verify.")
    else:
        print("\n  ❌ Some promotions failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
