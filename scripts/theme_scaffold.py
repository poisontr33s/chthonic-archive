#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: theme_scaffold.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Theme Scaffold — generates a complete VS Code color theme JSON from
a character's palette specification in milf_scanner.py.

Uses the Flesh & Earth (Decorator) theme as the structural template,
remapping all colors to the target character's palette.  The output
is a fully functional theme JSON ready for manual refinement.

@SID:           TOOL_THEME_SCAFFOLD_V1
@Shabti:          Utility
@Purpose:       Theme Scaffold — generates a complete VS Code color theme JSON from
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import json
import sys
from pathlib import Path

from scripts.lib.shared import configure_utf8_output
from scripts.milf_scanner import CHARACTERS, get_character

REPO = Path(__file__).resolve().parent.parent
THEME_DIR = REPO / "extensions" / "chthonic-archive" / "themes"
TEMPLATE_FILE = THEME_DIR / "chthonic-mandala-color-theme.json"

# Canonical mapping from palette role → template hex (Flesh & Earth values)
TEMPLATE_PALETTE = CHARACTERS["decorator"]["palette"]


def _hex_lower(h: str) -> str:
    """Normalise a hex color to lowercase 7-char form."""
    return h[:7].lower()


def _build_color_map(source_palette: dict, target_palette: dict) -> dict[str, str]:
    """Build a mapping from template hex values → target hex values."""
    cmap: dict[str, str] = {}
    for role in source_palette:
        src = _hex_lower(source_palette[role])
        tgt = target_palette.get(role)
        if tgt:
            cmap[src] = _hex_lower(tgt)
    return cmap


def _remap_color(value: str, cmap: dict[str, str]) -> str:
    """Remap a single color value, preserving any alpha suffix."""
    if not value or not value.startswith("#") or len(value) < 7:
        return value
    base = _hex_lower(value)
    alpha_suffix = value[7:] if len(value) > 7 else ""
    replacement = cmap.get(base)
    if replacement:
        return replacement + alpha_suffix
    return value


def scaffold_theme(char_id: str, dest_path: str | None = None) -> None:
    """Generate a theme JSON for the given character."""
    char = get_character(char_id)
    if not char:
        print(f"Unknown character: {char_id}", file=sys.stderr)
        print(f"Available: {', '.join(CHARACTERS)}", file=sys.stderr)
        sys.exit(1)

    if not TEMPLATE_FILE.exists():
        print(f"Template not found: {TEMPLATE_FILE}", file=sys.stderr)
        sys.exit(1)

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        theme = json.load(f)

    cmap = _build_color_map(TEMPLATE_PALETTE, char["palette"])

    # Rewrite identity
    theme_id = char.get("theme_id")
    if not theme_id:
        # Generate a provisional name for unmapped characters
        aesthetic = char.get("aesthetic", char_id.title()).split(",")[0].split("—")[0].strip()
        theme_id = f"Chthonic — {aesthetic} ({char['name']})"
    theme["name"] = theme_id

    # Remap workbench colors
    colors = theme.get("colors", {})
    for key in colors:
        colors[key] = _remap_color(colors[key], cmap)

    # Remap tokenColors foreground values
    for tc in theme.get("tokenColors", []):
        settings = tc.get("settings", {})
        if "foreground" in settings:
            settings["foreground"] = _remap_color(settings["foreground"], cmap)

    # Remap semanticTokenColors (can be string or dict with "foreground")
    stc = theme.get("semanticTokenColors", {})
    for key in stc:
        val = stc[key]
        if isinstance(val, str):
            stc[key] = _remap_color(val, cmap)
        elif isinstance(val, dict) and "foreground" in val:
            val["foreground"] = _remap_color(val["foreground"], cmap)

    # Determine output path
    if dest_path:
        out = Path(dest_path)
    else:
        out = THEME_DIR / f"chthonic-{char_id}-color-theme.json"

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(theme, f, indent=2, ensure_ascii=False)
        f.write("\n")

    total_remapped = sum(
        1 for v in colors.values()
        if v and v.startswith("#") and _hex_lower(v) in cmap.values()
    )
    print(f"✅ Scaffolded: {out.name}")
    print(f"   Character: {char['name']} {char['sigil']}")
    print(f"   Theme ID:  {theme_id}")
    print(f"   Colors remapped via {len(cmap)} palette slots")
    print(f"   Output:    {out}")


def main() -> None:
    configure_utf8_output()

    if len(sys.argv) < 2:
        print("Usage: theme_scaffold.py <char_id> [dest_path]")
        print()
        print("Characters:")
        for cid, c in CHARACTERS.items():
            mapped = "✅" if c.get("theme_id") else "⬜"
            print(f"  {mapped} {cid:12s} {c['name']}")
        sys.exit(0)

    char_id = sys.argv[1]
    dest_path = sys.argv[2] if len(sys.argv) > 2 else None
    scaffold_theme(char_id, dest_path)


if __name__ == "__main__":
    main()
