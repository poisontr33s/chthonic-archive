#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: icon_svg_audit.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Icon SVG Audit — Structural validator, palette checker, and WCAG contrast
auditor for the Chthonic Archive icon set.

Covers WPTG Stages 1.0 (Rendering Validation), 1.1 (WCAG/Contrast Audit),
and 1.2 (Palette Coherence) as automated gates.

@SID:           TOOL_ICON_SVG_AUDIT_V1
@Shabti:          Utility
@Purpose:       Icon SVG Audit — Structural validator, palette checker, and WCAG contrast
"""

import argparse
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.lib.shared import configure_utf8_output

# ═══════════════════════════════════════════════════════════════════════════════
# SFS Canonical Palette — Sister Ferrum Scoriae
# ═══════════════════════════════════════════════════════════════════════════════
SFS_PALETTE: dict[str, str] = {
    "background":      "#050505",
    "stele-fill":      "#0A0A0A",   # legacy reference — not used in SVGs
    "stele-body":      "#2A2724",   # canonical SVG body fill (Gold 10.10)
    "foreground":      "#E8E2D2",
    "accent-gold":     "#F4C430",
    "keyword-copper":  "#D4714E",
    "function-amber":  "#D7B562",
    "type-rose-clay":  "#D4907A",
    "constant-patina": "#7AAAB2",
    "string-sandstone":"#B9A37A",
    "comment-weathered":"#908672",
    "error-kiln":      "#E05545",
    "success-verdigris":"#8CB87A",
}

# Hex values for quick lookup
SFS_HEX: set[str] = {v.upper() for v in SFS_PALETTE.values()}

# Background colors to test contrast against
# Includes canonical BG, stele-body, and all 4 theme sidebar.background values
CONTRAST_BACKGROUNDS: list[str] = [
    "#050505",   # canonical SFS background
    "#0A0A0A",   # legacy stele-fill
    "#2A2724",   # stele-body (SVG fill)
    "#100D0A",   # Geology sidebar
    "#171210",   # Mandala sidebar
    "#141110",   # Decorator sidebar
    "#100E18",   # ROGBIV sidebar
]

# WCAG AA minimum contrast ratio for normal text
WCAG_AA_RATIO = 4.5
# For large text / UI components (icons fall here)
WCAG_AA_LARGE_RATIO = 3.0


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    """Convert hex color (#RRGGBB or #RGB) to (R, G, B)."""
    h = h.lstrip("#")
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def relative_luminance(r: int, g: int, b: int) -> float:
    """WCAG 2.1 relative luminance from sRGB."""
    def linearize(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def contrast_ratio(hex1: str, hex2: str) -> float:
    """WCAG 2.1 contrast ratio between two hex colors."""
    l1 = relative_luminance(*hex_to_rgb(hex1))
    l2 = relative_luminance(*hex_to_rgb(hex2))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")


def extract_colors_from_svg(svg_path: Path) -> list[str]:
    """Extract all hex color references from an SVG file."""
    text = svg_path.read_text(encoding="utf-8")
    colors = HEX_RE.findall(text)
    # Normalize to uppercase 6-digit
    normalized = []
    for c in colors:
        c = c.upper()
        if len(c) == 4:  # #RGB
            c = "#" + c[1]*2 + c[2]*2 + c[3]*2
        normalized.append(c)
    return normalized


def audit_svg_structure(svg_path: Path) -> dict:
    """
    Stage 1.0 — Structural validation of a single SVG.

    Checks:
      - Valid XML
      - Has <svg> root with xmlns
      - viewBox is "0 0 16 16"
      - No external references (xlink:href to URLs)
      - No embedded raster data (data: URIs)
      - No <script> or <style> elements (security)
    """
    result = {
        "file": svg_path.name,
        "valid_xml": False,
        "has_svg_root": False,
        "has_xmlns": False,
        "viewbox": None,
        "viewbox_correct": False,
        "has_external_refs": False,
        "has_raster_data": False,
        "has_script_style": False,
        "issues": [],
    }

    text = svg_path.read_text(encoding="utf-8")

    try:
        tree = ET.parse(str(svg_path))
        root = tree.getroot()
        result["valid_xml"] = True
    except ET.ParseError as e:
        result["issues"].append(f"XML parse error: {e}")
        return result

    # Check root element
    ns = "{http://www.w3.org/2000/svg}"
    tag = root.tag
    if tag == f"{ns}svg" or tag == "svg":
        result["has_svg_root"] = True
    else:
        result["issues"].append(f"Root element is '{tag}', expected 'svg'")

    # Check xmlns
    xmlns = root.attrib.get("xmlns", "")
    if "w3.org/2000/svg" in xmlns or tag.startswith(ns):
        result["has_xmlns"] = True
    else:
        result["issues"].append("Missing xmlns='http://www.w3.org/2000/svg'")

    # Check viewBox
    vb = root.attrib.get("viewBox", "")
    result["viewbox"] = vb
    if vb == "0 0 16 16":
        result["viewbox_correct"] = True
    else:
        result["issues"].append(f"viewBox is '{vb}', expected '0 0 16 16'")

    # Check for external references
    if re.search(r'href\s*=\s*["\']https?://', text):
        result["has_external_refs"] = True
        result["issues"].append("Contains external URL references")

    # Check for embedded raster data
    if "data:" in text and ("base64" in text or "image/" in text):
        result["has_raster_data"] = True
        result["issues"].append("Contains embedded raster data")

    # Check for script/style elements
    for elem in root.iter():
        local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if local in ("script", "style"):
            result["has_script_style"] = True
            result["issues"].append(f"Contains <{local}> element")

    return result


def audit_palette_coherence(svg_path: Path) -> dict:
    """
    Stage 1.2 — Palette coherence check.

    Extracts all colors from the SVG and checks them against
    the SFS canonical palette. Reports on-palette and off-palette colors.
    """
    colors = extract_colors_from_svg(svg_path)
    unique = list(dict.fromkeys(colors))  # preserve order, deduplicate

    on_palette = [c for c in unique if c in SFS_HEX]
    off_palette = [c for c in unique if c not in SFS_HEX]

    return {
        "file": svg_path.name,
        "total_colors": len(unique),
        "on_palette": on_palette,
        "off_palette": off_palette,
        "palette_adherence": (
            len(on_palette) / len(unique) * 100 if unique else 100.0
        ),
    }


def audit_contrast(svg_path: Path) -> dict:
    """
    Stage 1.1 — WCAG contrast audit.

    Checks contrast ratio of each color used in the SVG against
    the SFS dark backgrounds (#050505, #0A0A0A). Icons are classified
    as "large text / UI components" so we use the AA-large threshold (3.0).
    """
    colors = extract_colors_from_svg(svg_path)
    unique = list(dict.fromkeys(colors))

    results = []
    all_pass = True

    # Colors that ARE the background — skip them in contrast checks
    bg_skip = {"#050505", "#0A0A0A", "#2A2724"}

    for color in unique:
        if color.upper() in bg_skip:
            continue

        for bg in CONTRAST_BACKGROUNDS:
            ratio = contrast_ratio(color, bg)
            passes = ratio >= WCAG_AA_LARGE_RATIO
            if not passes:
                all_pass = False
            results.append({
                "color": color,
                "background": bg,
                "ratio": round(ratio, 2),
                "passes_aa_large": passes,
            })

    return {
        "file": svg_path.name,
        "all_pass": all_pass,
        "checks": results,
    }


CHAMBER_OPACITY = "0.55"


def audit_chamber_transparency(svg_path: Path) -> dict | None:
    """
    Stage 1.3 — Chamber transparency check for closed folder pylons.

    Closed folders (folder-*.svg excluding *-open.svg) must have at least
    one rect with fill-opacity="0.55" (the inner chamber). This ensures
    theme background bleeds through the portal for automatic cross-theme
    tinting — see Gold 10.10 and ANKH_ICON_GRAMMAR Chamber Transparency Rule.

    Returns None for non-folder or open-folder SVGs (not applicable).
    """
    name = svg_path.stem
    if not name.startswith("folder-") or name.endswith("-open"):
        return None

    text = svg_path.read_text(encoding="utf-8")
    has_chamber = f'fill-opacity="{CHAMBER_OPACITY}"' in text

    result: dict = {
        "file": svg_path.name,
        "has_chamber_opacity": has_chamber,
        "expected_opacity": CHAMBER_OPACITY,
        "issues": [],
    }
    if not has_chamber:
        result["issues"].append(
            f"Closed folder missing fill-opacity=\"{CHAMBER_OPACITY}\" on inner chamber rect"
        )
    return result


def find_icons_dir(repo: Path) -> Path:
    """Locate the icons directory."""
    return repo / "extensions" / "chthonic-archive" / "themes" / "icons"


def find_repo_root() -> Path:
    """Walk up from this script's location to find the repo root."""
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / "Cargo.toml").exists():
            return p
        p = p.parent
    return Path(__file__).resolve().parent.parent


def run_audit(
    icons_dir: Path,
    include_product: bool = False,
) -> dict:
    """Run the full audit suite across all SVGs."""
    svgs = sorted(icons_dir.glob("*.svg"))
    if include_product:
        product_dir = icons_dir / "product"
        if product_dir.exists():
            svgs.extend(sorted(product_dir.glob("*.svg")))

    structure_results = []
    palette_results = []
    contrast_results = []
    chamber_results = []

    for svg in svgs:
        structure_results.append(audit_svg_structure(svg))
        palette_results.append(audit_palette_coherence(svg))
        contrast_results.append(audit_contrast(svg))
        chamber = audit_chamber_transparency(svg)
        if chamber is not None:
            chamber_results.append(chamber)

    # Aggregate stats
    total = len(svgs)
    struct_pass = sum(1 for r in structure_results if not r["issues"])
    palette_perfect = sum(1 for r in palette_results if not r["off_palette"])
    contrast_pass = sum(1 for r in contrast_results if r["all_pass"])
    chamber_total = len(chamber_results)
    chamber_pass = sum(1 for r in chamber_results if r["has_chamber_opacity"])

    return {
        "summary": {
            "total_svgs": total,
            "structure_pass": struct_pass,
            "structure_fail": total - struct_pass,
            "palette_perfect": palette_perfect,
            "palette_drift": total - palette_perfect,
            "contrast_pass": contrast_pass,
            "contrast_fail": total - contrast_pass,
            "chamber_total": chamber_total,
            "chamber_pass": chamber_pass,
            "chamber_fail": chamber_total - chamber_pass,
        },
        "stage_1_0_structure": structure_results,
        "stage_1_1_contrast": contrast_results,
        "stage_1_2_palette": palette_results,
        "stage_1_3_chamber": chamber_results,
    }


def print_report(audit: dict) -> None:
    """Print a human-readable audit report."""
    s = audit["summary"]

    print("=" * 72)
    print(" ☥ ICON SVG AUDIT — WPTG Stages 1.0 / 1.1 / 1.2")
    print("=" * 72)
    print()
    print(f"  Total SVGs audited:    {s['total_svgs']}")
    print()

    # Stage 1.0
    print("─" * 72)
    print(f" STAGE 1.0 — Structural Validation   [{s['structure_pass']}/{s['total_svgs']} pass]")
    print("─" * 72)
    for r in audit["stage_1_0_structure"]:
        status = "✅" if not r["issues"] else "❌"
        print(f"  {status} {r['file']:<32s} viewBox={r['viewbox'] or 'MISSING'}")
        for issue in r["issues"]:
            print(f"       ⚠ {issue}")
    print()

    # Stage 1.1
    print("─" * 72)
    print(f" STAGE 1.1 — WCAG Contrast Audit     [{s['contrast_pass']}/{s['total_svgs']} pass]")
    print("─" * 72)
    for r in audit["stage_1_1_contrast"]:
        status = "✅" if r["all_pass"] else "❌"
        print(f"  {status} {r['file']}")
        for chk in r["checks"]:
            if not chk["passes_aa_large"]:
                print(f"       ⚠ {chk['color']} vs {chk['background']} → {chk['ratio']}:1 (need ≥3.0)")
    print()

    # Stage 1.2
    print("─" * 72)
    print(f" STAGE 1.2 — Palette Coherence        [{s['palette_perfect']}/{s['total_svgs']} on-palette]")
    print("─" * 72)
    for r in audit["stage_1_2_palette"]:
        pct = r["palette_adherence"]
        status = "✅" if not r["off_palette"] else "⚠️"
        print(f"  {status} {r['file']:<32s} {pct:5.1f}%  on-palette={len(r['on_palette'])} off={len(r['off_palette'])}")
        for c in r["off_palette"]:
            # Find nearest SFS color
            nearest = min(SFS_HEX, key=lambda s: _color_distance(c, s))
            print(f"       drift: {c} → nearest SFS: {nearest}")
    print()

    # Stage 1.3
    if audit.get("stage_1_3_chamber"):
        print("─" * 72)
        print(f" STAGE 1.3 — Chamber Transparency     [{s['chamber_pass']}/{s['chamber_total']} pass]")
        print("─" * 72)
        for r in audit["stage_1_3_chamber"]:
            status = "✅" if r["has_chamber_opacity"] else "❌"
            print(f"  {status} {r['file']}")
            for issue in r["issues"]:
                print(f"       ⚠ {issue}")
        print()


def _color_distance(hex1: str, hex2: str) -> float:
    """Euclidean distance in RGB space."""
    r1, g1, b1 = hex_to_rgb(hex1)
    r2, g2, b2 = hex_to_rgb(hex2)
    return math.sqrt((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2)


def main() -> None:
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        description="Icon SVG Audit — structural, contrast, and palette validation."
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Write structured JSON audit report to this path.",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Repository root (auto-detected if omitted).",
    )
    parser.add_argument(
        "--include-product",
        action="store_true",
        help="Also audit product icons in the product/ subdirectory.",
    )
    args = parser.parse_args()

    repo = args.repo or find_repo_root()
    icons_dir = find_icons_dir(repo)

    if not icons_dir.exists():
        print(f"ERROR: Icons directory not found: {icons_dir}", file=sys.stderr)
        sys.exit(1)

    audit = run_audit(icons_dir, include_product=args.include_product)
    print_report(audit)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(audit, f, indent=2, ensure_ascii=False)
        print(f"  ✏️  JSON audit report written to: {args.json}")


if __name__ == "__main__":
    main()
