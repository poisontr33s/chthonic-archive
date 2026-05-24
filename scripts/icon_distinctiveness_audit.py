#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: icon_distinctiveness_audit.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Icon Distinctiveness Audit — Analyses motif uniqueness across all file
icons by comparing color usage, element counts, and bounding-box coverage
to flag potential visual collisions at 16px render size.

Covers WPTG Stage 2.1 (Motif Distinctiveness).

@SID:           TOOL_ICON_DISTINCTIVENESS_V1
@Shabti:          Utility
@Purpose:       Icon Distinctiveness Audit — Analyses motif uniqueness across all file
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from itertools import combinations

from scripts.lib.shared import configure_utf8_output


def find_repo_root() -> Path:
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / "Cargo.toml").exists():
            return p
        p = p.parent
    return Path(__file__).resolve().parent.parent


def find_icons_dir(repo: Path) -> Path:
    return repo / "extensions" / "chthonic-archive" / "themes" / "icons"


HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
NS = "{http://www.w3.org/2000/svg}"

# Stele base colors — these are shared by ALL file icons and should be excluded
# from distinctiveness comparison
STELE_COLORS = {"#0A0A0A", "#908672"}


def extract_fingerprint(svg_path: Path) -> dict:
    """
    Build a 'fingerprint' for an icon: motif color(s), element types,
    motif comment, and structural shape signature.
    """
    text = svg_path.read_text(encoding="utf-8")
    fp = {
        "file": svg_path.name,
        "motif_comment": "",
        "motif_colors": [],
        "element_types": {},
        "element_count": 0,
        "path_count": 0,
        "circle_count": 0,
        "line_count": 0,
        "rect_count": 0,
        "has_ellipse": False,
    }

    # Extract first comment as motif label
    cm = re.search(r"<!--\s*(.*?)\s*-->", text)
    if cm:
        fp["motif_comment"] = cm.group(1)

    # Extract all colors, then remove stele base colors
    all_colors = set()
    for c in HEX_RE.findall(text):
        c = c.upper()
        if len(c) == 4:
            c = "#" + c[1]*2 + c[2]*2 + c[3]*2
        all_colors.add(c)
    fp["motif_colors"] = sorted(all_colors - STELE_COLORS)

    # Parse XML and count elements
    try:
        tree = ET.parse(str(svg_path))
        root = tree.getroot()
    except ET.ParseError:
        return fp

    counts: dict[str, int] = {}
    total = 0
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "svg":
            continue
        counts[tag] = counts.get(tag, 0) + 1
        total += 1
    fp["element_types"] = counts
    fp["element_count"] = total
    fp["path_count"] = counts.get("path", 0)
    fp["circle_count"] = counts.get("circle", 0)
    fp["line_count"] = counts.get("line", 0)
    fp["rect_count"] = counts.get("rect", 0)
    fp["has_ellipse"] = "ellipse" in counts

    return fp


def similarity_score(fp1: dict, fp2: dict) -> float:
    """
    Compute a similarity score between two fingerprints.
    Range: 0.0 (completely different) to 1.0 (identical).

    Factors:
    1. Color overlap (weighted 40%)
    2. Element type profile similarity (weighted 30%)
    3. Element count proximity (weighted 15%)
    4. Shape composition similarity (weighted 15%)
    """
    # 1. Color overlap
    c1 = set(fp1["motif_colors"])
    c2 = set(fp2["motif_colors"])
    if c1 or c2:
        color_sim = len(c1 & c2) / max(len(c1 | c2), 1)
    else:
        color_sim = 1.0

    # 2. Element type profile (Jaccard on element types)
    t1 = set(fp1["element_types"].keys()) - {"rect"}  # Exclude stele rect
    t2 = set(fp2["element_types"].keys()) - {"rect"}
    if t1 or t2:
        type_sim = len(t1 & t2) / max(len(t1 | t2), 1)
    else:
        type_sim = 1.0

    # 3. Element count proximity
    n1 = fp1["element_count"]
    n2 = fp2["element_count"]
    max_n = max(n1, n2)
    count_sim = 1.0 - (abs(n1 - n2) / max_n) if max_n > 0 else 1.0

    # 4. Shape composition: normalized vector [path, circle, line, rect, ellipse]
    def shape_vec(fp):
        total = max(fp["element_count"], 1)
        return [
            fp["path_count"] / total,
            fp["circle_count"] / total,
            fp["line_count"] / total,
            fp["rect_count"] / total,
            1.0 if fp["has_ellipse"] else 0.0,
        ]

    v1 = shape_vec(fp1)
    v2 = shape_vec(fp2)
    # Cosine similarity
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = sum(a * a for a in v1) ** 0.5
    mag2 = sum(a * a for a in v2) ** 0.5
    shape_sim = dot / (mag1 * mag2) if (mag1 > 0 and mag2 > 0) else 0.0

    # Weighted sum
    return 0.40 * color_sim + 0.30 * type_sim + 0.15 * count_sim + 0.15 * shape_sim


def run_distinctiveness_audit(
    icons_dir: Path,
    threshold: float = 0.85,
) -> dict:
    """Run pairwise comparison across all file icons."""
    svgs = sorted(icons_dir.glob("file-*.svg"))
    fingerprints = [extract_fingerprint(svg) for svg in svgs]

    collisions = []
    for (i, fp1), (j, fp2) in combinations(enumerate(fingerprints), 2):
        score = similarity_score(fp1, fp2)
        if score >= threshold:
            collisions.append({
                "icon_a": fp1["file"],
                "icon_b": fp2["file"],
                "similarity": round(score, 3),
                "shared_colors": sorted(
                    set(fp1["motif_colors"]) & set(fp2["motif_colors"])
                ),
            })

    collisions.sort(key=lambda x: x["similarity"], reverse=True)

    # Motif distribution
    color_usage: dict[str, list[str]] = {}
    for fp in fingerprints:
        for c in fp["motif_colors"]:
            color_usage.setdefault(c, []).append(fp["file"])

    return {
        "total_file_icons": len(fingerprints),
        "threshold": threshold,
        "collisions": collisions,
        "collision_count": len(collisions),
        "color_distribution": {c: {"count": len(files), "icons": files} for c, files in sorted(color_usage.items())},
        "fingerprints": fingerprints,
    }


def print_report(audit: dict) -> None:
    s = audit

    print("=" * 72)
    print(" ☥ MOTIF DISTINCTIVENESS AUDIT — WPTG Stage 2.1")
    print("=" * 72)
    print()
    print(f"  File icons audited:   {s['total_file_icons']}")
    print(f"  Similarity threshold: {s['threshold']}")
    print()

    # Color distribution
    print("─" * 72)
    print(" COLOR DISTRIBUTION (motif colors only, excluding stele base)")
    print("─" * 72)
    for color, info in sorted(s["color_distribution"].items()):
        count = info["count"]
        bar = "█" * count
        print(f"  {color}  {count:>2d} icons  {bar}")
        if count >= 6:
            print(f"       ⚠ High concentration — consider diversifying")
    print()

    # Collisions
    print("─" * 72)
    if s["collisions"]:
        print(f" POTENTIAL COLLISIONS ({s['collision_count']} pairs above {s['threshold']} threshold)")
        print("─" * 72)
        for c in s["collisions"]:
            print(f"  ⚠ {c['icon_a']:<24s} ↔ {c['icon_b']:<24s}  sim={c['similarity']:.3f}")
            if c["shared_colors"]:
                print(f"       shared colors: {', '.join(c['shared_colors'])}")
    else:
        print(f" ✅ NO COLLISIONS (all pairs below {s['threshold']} threshold)")
        print("─" * 72)
    print()

    # Per-icon summary
    print("─" * 72)
    print(" PER-ICON FINGERPRINTS")
    print("─" * 72)
    for fp in s["fingerprints"]:
        colors = ", ".join(fp["motif_colors"]) or "(none)"
        motif = fp["motif_comment"][:50] if fp["motif_comment"] else "(no label)"
        print(f"  {fp['file']:<32s} colors=[{colors}]  elements={fp['element_count']}")
        print(f"       {motif}")
    print()


def main() -> None:
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        description="Icon Distinctiveness Audit — Stage 2.1 visual collision detector."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Similarity threshold above which pairs are flagged (0.0-1.0, default 0.85).",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Write structured JSON report.",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Repository root.",
    )
    args = parser.parse_args()

    repo = args.repo or find_repo_root()
    icons_dir = find_icons_dir(repo)

    if not icons_dir.exists():
        print(f"ERROR: Icons directory not found: {icons_dir}", file=sys.stderr)
        sys.exit(1)

    audit = run_distinctiveness_audit(icons_dir, threshold=args.threshold)
    print_report(audit)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(audit, f, indent=2, ensure_ascii=False)
        print(f"  ✏️  JSON report written to: {args.json}")


if __name__ == "__main__":
    main()
