#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# @SID: TOOL_POC_COLLAGE_V3

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: build_poc_collage.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: VIOLET
# ║ Temple-Ayllu Zone: 🖼️  THE REFERENCE GALLERY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ game/refs/poc01/README_POC01.md  (Pattern-anchor for the POCNN series)
# ║   └─◄ .gitattributes                    (LFS lane for game/refs/poc**/*.{png,webp,jxl,qoi})
# ║   └─◄ .gitignore                        (Allowlist for game/refs/**/*.{md,png,webp,jxl,qoi,json})
# ╚════════════════════════════════════════════════════════════════════════════

"""
POC Collage Builder V3 — Voronoi CVT + Salience-Aware Composition

Composes a directory of POC reference images into a single canvas-filling
collage whose cell topology is a Centroidal Voronoi Tessellation (CVT). Each
source is salience-scored via local entropy, sorted by salience, and assigned
to a Voronoi cell. Cells are clipped to the canvas via shapely; sources are
scaled to fit cell bounding boxes and masked to the cell polygon shape, so
the composition is non-rectangular by construction.

Outputs four lossless formats from the same pixel data: PNG, WebP, QOI, JXL.
Same input + same args = byte-identical re-runs.

ALGORITHMIC LINEAGE
===================
- Centroidal Voronoi Tessellation via Lloyd's relaxation (Bruls/Huijing-style
  variant; classical Lloyd 1982). Seeds are generated deterministically from
  a quasi-random Halton sequence and relaxed for N iterations until cells
  approximate equal-area hyperuniform distribution.
- scipy.spatial.Voronoi computes the tessellation; shapely.geometry.Polygon
  intersects cells with the canvas bounding box to bound infinite regions.
- Salience scoring per source via local Shannon entropy on grayscale-converted
  thumbnails (S_i(x,y) = -Σ p(g) log₂ p(g) over local neighborhood).
- Adaptive unsharp-mask after LANCZOS downscale, strength scaled by the
  downscale ratio (carried forward from V2).

@SID:           TOOL_POC_COLLAGE_V3
@Shabti:        Voronoi-CVT salience-aware reference-imagery compactor
@Heka-Ayni:     game/refs/pocNN/*.png → CVT cells + salience-ordered assignment → PNG + WebP + QOI + JXL
@Ankh-Tinku:    <POC_DIR>/POCNN_collage.{png,webp,qoi,jxl} + <POC_DIR>/POCNN_collage.manifest.json
@Purpose:       Replace V2 rectangular grid with non-rectangular CVT layout
                informed by per-source local-entropy salience, emitting
                multi-format lossless wallpaper-grade artifacts.
"""

from __future__ import annotations

import argparse
import colorsys
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.spatial import Voronoi
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry import box as shapely_box
import imagecodecs
import qoi

TOOL_SID = "TOOL_POC_COLLAGE_V3"
SOURCE_GLOB = "Example_POC*.png"

# 2K wallpaper canvas — matches QHD displays.
DEFAULT_CANVAS_W = 2560
DEFAULT_CANVAS_H = 1440
DEFAULT_LLOYD_ITERS = 40
DEFAULT_ORDER = "salience"
DEFAULT_FORMAT = "all"
DEFAULT_BG = "#000000"

ORDER_STRATEGIES = ("lex", "brightness", "hue", "salience")
FORMAT_CHOICES = ("png", "webp", "qoi", "jxl", "all")


# ─── Series tag derivation ──────────────────────────────────────────────────

def derive_series_tag(poc_dir: Path) -> str:
    name = poc_dir.name
    match = re.match(r"^(poc\d+)$", name, re.IGNORECASE)
    if not match:
        raise SystemExit(
            f"error: directory name {name!r} does not match pocNN pattern. "
            f"Pass --output to override."
        )
    return match.group(1).upper()


def parse_canvas(spec: str) -> tuple[int, int]:
    match = re.match(r"^(\d+)\s*[xX]\s*(\d+)$", spec)
    if not match:
        raise argparse.ArgumentTypeError(f"--canvas expects WxH, got {spec!r}")
    return int(match.group(1)), int(match.group(2))


def parse_hex_color(spec: str) -> tuple[int, int, int]:
    s = spec.lstrip("#")
    if len(s) != 6:
        raise argparse.ArgumentTypeError(f"--bg expects #RRGGBB, got {spec!r}")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


# ─── Halton sequence for deterministic quasi-random seeds ──────────────────

def _halton(index: int, base: int) -> float:
    """Halton sequence — deterministic low-discrepancy quasi-random."""
    result = 0.0
    f = 1.0
    i = index
    while i > 0:
        f /= base
        result += f * (i % base)
        i //= base
    return result


def halton_seeds(n: int, canvas_w: int, canvas_h: int) -> np.ndarray:
    """Generate n deterministic quasi-random seeds within the canvas."""
    seeds = np.zeros((n, 2), dtype=np.float64)
    # Skip first few indices (Halton(0..3) is degenerate near corners).
    for i in range(n):
        seeds[i, 0] = _halton(i + 4, 2) * canvas_w
        seeds[i, 1] = _halton(i + 4, 3) * canvas_h
    return seeds


# ─── Salience scoring ──────────────────────────────────────────────────────

def compute_salience(path: Path, thumb_size: int = 64) -> float:
    """Mean local Shannon entropy on grayscale thumbnail.

    Higher score = more visual information density. Computed on a thumbnail
    for speed (full-res entropy would be O(W·H·k²) per source).
    """
    with Image.open(path) as im:
        thumb = im.convert("L").resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        arr = np.asarray(thumb, dtype=np.uint8)
    # Global Shannon entropy as the score (sufficient for ordering).
    hist, _ = np.histogram(arr, bins=256, range=(0, 256))
    hist = hist[hist > 0]
    probs = hist / hist.sum()
    entropy = -np.sum(probs * np.log2(probs))
    return float(entropy)


def brightness_score(path: Path, thumb_size: int = 32) -> float:
    with Image.open(path) as im:
        thumb = im.convert("L").resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
    return float(np.asarray(thumb).mean())


def hue_score(path: Path, thumb_size: int = 32) -> tuple[float, float, float]:
    with Image.open(path) as im:
        thumb = im.convert("RGB").resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
    arr = np.asarray(thumb) / 255.0
    avg = arr.reshape(-1, 3).mean(axis=0)
    h, s, v = colorsys.rgb_to_hsv(avg[0], avg[1], avg[2])
    return (h, s, v)


def order_sources(sources: list[Path], strategy: str) -> tuple[list[Path], list]:
    if strategy == "lex":
        ordered = sorted(sources)
        return ordered, [s.name for s in ordered]
    if strategy == "brightness":
        keyed = sorted(((brightness_score(s), s) for s in sources), key=lambda t: (t[0], t[1].name))
        return [s for _, s in keyed], [k for k, _ in keyed]
    if strategy == "hue":
        keyed = sorted(((hue_score(s), s) for s in sources), key=lambda t: (t[0], t[1].name))
        return [s for _, s in keyed], [k for k, _ in keyed]
    if strategy == "salience":
        # Descending salience — most-information-dense cells get assigned first
        # (so they land near canvas center after Lloyd's relaxation centroids).
        keyed = sorted(((compute_salience(s), s) for s in sources), key=lambda t: (-t[0], t[1].name))
        return [s for _, s in keyed], [k for k, _ in keyed]
    raise SystemExit(f"error: unknown --order {strategy!r}")


# ─── Voronoi CVT + Lloyd's relaxation ───────────────────────────────────────

@dataclass
class CVTResult:
    seeds_initial: np.ndarray
    seeds_final: np.ndarray
    cells: list[ShapelyPolygon]
    iterations: int


def lloyd_relaxation(
    seeds: np.ndarray,
    canvas_w: int,
    canvas_h: int,
    iterations: int,
) -> CVTResult:
    """Iteratively move each seed to the centroid of its Voronoi cell.

    To bound infinite regions on the canvas boundary, we mirror seeds across
    each canvas edge before computing the Voronoi diagram. Only the original
    seeds' cells are kept; their cells are then intersected with the canvas
    polygon via shapely.
    """
    canvas_poly = shapely_box(0, 0, canvas_w, canvas_h)
    seeds_initial = seeds.copy()
    current = seeds.copy()

    for _ in range(iterations):
        # Mirror seeds across canvas edges to bound boundary cells.
        mirrored = _mirror_seeds(current, canvas_w, canvas_h)
        all_seeds = np.vstack([current, mirrored])
        vor = Voronoi(all_seeds)

        new_seeds = np.zeros_like(current)
        n_orig = len(current)
        for i in range(n_orig):
            region_idx = vor.point_region[i]
            region_verts = vor.regions[region_idx]
            if -1 in region_verts or len(region_verts) < 3:
                # Degenerate region — keep seed in place.
                new_seeds[i] = current[i]
                continue
            poly_verts = vor.vertices[region_verts]
            try:
                cell = ShapelyPolygon(poly_verts).intersection(canvas_poly)
            except Exception:
                new_seeds[i] = current[i]
                continue
            if cell.is_empty or cell.area == 0:
                new_seeds[i] = current[i]
                continue
            # Centroid of the (clipped) cell becomes the next seed position.
            c = cell.centroid
            new_seeds[i] = [c.x, c.y]
        current = new_seeds

    # Final pass to extract cell polygons.
    mirrored = _mirror_seeds(current, canvas_w, canvas_h)
    all_seeds = np.vstack([current, mirrored])
    vor = Voronoi(all_seeds)
    cells: list[ShapelyPolygon] = []
    for i in range(len(current)):
        region_idx = vor.point_region[i]
        region_verts = vor.regions[region_idx]
        if -1 in region_verts or len(region_verts) < 3:
            cells.append(canvas_poly)
            continue
        poly_verts = vor.vertices[region_verts]
        try:
            cell = ShapelyPolygon(poly_verts).intersection(canvas_poly)
        except Exception:
            cells.append(canvas_poly)
            continue
        if cell.is_empty:
            cells.append(canvas_poly)
        else:
            cells.append(cell if cell.geom_type == "Polygon" else max(cell.geoms, key=lambda g: g.area))

    return CVTResult(seeds_initial, current, cells, iterations)


def _mirror_seeds(seeds: np.ndarray, w: int, h: int) -> np.ndarray:
    """Reflect seeds across each canvas edge — bounds boundary Voronoi cells."""
    left = seeds.copy(); left[:, 0] = -seeds[:, 0]
    right = seeds.copy(); right[:, 0] = 2 * w - seeds[:, 0]
    bottom = seeds.copy(); bottom[:, 1] = -seeds[:, 1]
    top = seeds.copy(); top[:, 1] = 2 * h - seeds[:, 1]
    return np.vstack([left, right, bottom, top])


# ─── Cell rendering ─────────────────────────────────────────────────────────

def adaptive_unsharp(im: Image.Image, downscale_ratio: float) -> Image.Image:
    if downscale_ratio <= 1.5:
        return im
    radius = min(2.0, 0.5 + 0.3 * (downscale_ratio - 1.5))
    percent = int(min(150, 80 + 20 * (downscale_ratio - 1.5)))
    return im.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=2))


def render_source_into_cell(
    canvas: Image.Image,
    source_path: Path,
    cell: ShapelyPolygon,
    sharpen: bool,
) -> dict:
    """Scale source to fit cell bbox, mask to cell polygon, paste on canvas.

    Returns a dict of render metadata (cell area, scale factor, etc.) for the
    manifest.
    """
    minx, miny, maxx, maxy = cell.bounds
    cell_w = int(round(maxx - minx))
    cell_h = int(round(maxy - miny))
    if cell_w <= 1 or cell_h <= 1:
        return {"rendered": False, "reason": "cell too small"}

    with Image.open(source_path) as im:
        src_rgb = im.convert("RGB")
        src_w, src_h = src_rgb.size
        # Scale to fit cell bbox (fill, not contain — crop happens via mask).
        scale = max(cell_w / src_w, cell_h / src_h)
        new_w = max(cell_w, int(round(src_w * scale)))
        new_h = max(cell_h, int(round(src_h * scale)))
        resized = src_rgb.resize((new_w, new_h), Image.Resampling.LANCZOS)
        if sharpen:
            downscale_ratio = src_w / cell_w if cell_w else 1.0
            resized = adaptive_unsharp(resized, downscale_ratio)
        # Center-crop to cell bbox.
        crop_x = (new_w - cell_w) // 2
        crop_y = (new_h - cell_h) // 2
        cropped = resized.crop((crop_x, crop_y, crop_x + cell_w, crop_y + cell_h))

    # Build a mask from the cell polygon, translated to local cell-bbox coords.
    mask = Image.new("L", (cell_w, cell_h), 0)
    draw = ImageDraw.Draw(mask)
    coords = [(x - minx, y - miny) for x, y in cell.exterior.coords]
    draw.polygon(coords, fill=255)

    # Paste cropped source onto canvas at cell-bbox top-left, with mask.
    canvas.paste(cropped, (int(round(minx)), int(round(miny))), mask)

    return {
        "rendered": True,
        "cell_bbox": [int(round(minx)), int(round(miny)), cell_w, cell_h],
        "cell_area_px": round(cell.area, 1),
        "downscale_ratio": round(src_w / cell_w, 3),
        "polygon_vertices": [[round(x, 1), round(y, 1)] for x, y in cell.exterior.coords],
    }


# ─── Output encoding ────────────────────────────────────────────────────────

def save_png(im: Image.Image, path: Path) -> None:
    im.save(path, format="PNG", optimize=True, compress_level=9)


def save_webp(im: Image.Image, path: Path) -> None:
    im.save(path, format="WEBP", lossless=True, quality=100, method=6)


def save_qoi(im: Image.Image, path: Path) -> None:
    arr = np.asarray(im.convert("RGB"), dtype=np.uint8)
    encoded = qoi.encode(arr)
    path.write_bytes(encoded)


def save_jxl(im: Image.Image, path: Path) -> None:
    arr = np.asarray(im.convert("RGB"), dtype=np.uint8)
    encoded = imagecodecs.jpegxl_encode(arr, lossless=True)
    path.write_bytes(encoded)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ─── Main ──────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Voronoi-CVT salience-aware POC reference collage builder.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("poc_dir", type=Path, help="Directory containing Example_POC*.png files")
    parser.add_argument("--canvas", type=parse_canvas, default=(DEFAULT_CANVAS_W, DEFAULT_CANVAS_H),
                        help="Output canvas as WxH")
    parser.add_argument("--lloyd-iters", type=int, default=DEFAULT_LLOYD_ITERS,
                        help="Lloyd's relaxation iterations")
    parser.add_argument("--order", choices=ORDER_STRATEGIES, default=DEFAULT_ORDER,
                        help="Source ordering strategy")
    parser.add_argument("--format", choices=FORMAT_CHOICES, default=DEFAULT_FORMAT,
                        help="Output format(s); 'all' = png+webp+qoi+jxl")
    parser.add_argument("--bg", type=parse_hex_color, default=parse_hex_color(DEFAULT_BG),
                        help="Background color as #RRGGBB")
    parser.add_argument("--no-sharpen", action="store_true",
                        help="Disable adaptive post-downscale sharpening")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output collage base path (default: <POC_DIR>/<TAG>_collage)")
    parser.add_argument("--manifest", type=Path, default=None,
                        help="Manifest JSON path (default: alongside collage)")
    parser.add_argument("--source-glob", default=SOURCE_GLOB,
                        help="Glob for source PNGs")
    args = parser.parse_args(argv)

    poc_dir: Path = args.poc_dir.resolve()
    if not poc_dir.is_dir():
        print(f"error: {poc_dir} is not a directory", file=sys.stderr)
        return 2

    raw_sources = sorted(poc_dir.glob(args.source_glob))
    if not raw_sources:
        print(f"error: no sources matching {args.source_glob!r} in {poc_dir}", file=sys.stderr)
        return 2

    series_tag = derive_series_tag(poc_dir) if args.output is None else "CUSTOM"
    canvas_w, canvas_h = args.canvas
    n = len(raw_sources)

    print(f"[{TOOL_SID}] series={series_tag} sources={n} canvas={canvas_w}x{canvas_h}")
    print(f"[{TOOL_SID}] order={args.order} lloyd_iters={args.lloyd_iters}")

    # 1. Order sources.
    print(f"[{TOOL_SID}] computing source order ({args.order})…")
    ordered, sort_keys = order_sources(raw_sources, args.order)

    # 2. Generate seeds + Lloyd's relaxation.
    print(f"[{TOOL_SID}] generating {n} Halton seeds + Lloyd's relaxation…")
    initial_seeds = halton_seeds(n, canvas_w, canvas_h)
    cvt = lloyd_relaxation(initial_seeds, canvas_w, canvas_h, args.lloyd_iters)

    # 3. Render canvas.
    print(f"[{TOOL_SID}] compositing {n} cells…")
    canvas = Image.new("RGB", (canvas_w, canvas_h), args.bg)
    cell_meta = []
    for i, (src, cell) in enumerate(zip(ordered, cvt.cells)):
        meta = render_source_into_cell(canvas, src, cell, sharpen=not args.no_sharpen)
        meta.update({
            "index": i,
            "source": src.name,
            "sort_key": _key_to_jsonable(sort_keys[i]),
            "seed_initial": [round(float(cvt.seeds_initial[i][0]), 2),
                             round(float(cvt.seeds_initial[i][1]), 2)],
            "seed_final": [round(float(cvt.seeds_final[i][0]), 2),
                           round(float(cvt.seeds_final[i][1]), 2)],
        })
        cell_meta.append(meta)

    # 4. Save outputs.
    out_base = args.output if args.output else poc_dir / f"{series_tag}_collage"
    out_base.parent.mkdir(parents=True, exist_ok=True)

    requested = (("png", "webp", "qoi", "jxl") if args.format == "all" else (args.format,))
    outputs: dict[str, dict] = {}
    for fmt in requested:
        path = out_base.with_suffix(f".{fmt}")
        if fmt == "png":
            save_png(canvas, path)
        elif fmt == "webp":
            save_webp(canvas, path)
        elif fmt == "qoi":
            save_qoi(canvas, path)
        elif fmt == "jxl":
            save_jxl(canvas, path)
        outputs[fmt] = {
            "path": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        print(f"[{TOOL_SID}] {fmt} → {path.name} ({outputs[fmt]['bytes']:,} bytes)")

    # 5. Build manifest.
    out_manifest = args.manifest if args.manifest else out_base.with_suffix(".manifest.json")
    cwd = Path.cwd()
    manifest = {
        "tool": TOOL_SID,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "series": series_tag,
        "source_dir": str(poc_dir.relative_to(cwd)) if poc_dir.is_relative_to(cwd) else str(poc_dir),
        "source_glob": args.source_glob,
        "source_count": n,
        "algorithm": {
            "topology": "voronoi-cvt",
            "lloyd_iterations": args.lloyd_iters,
            "seed_distribution": "halton-2-3",
            "boundary_handling": "edge-mirror + canvas-intersect (shapely)",
        },
        "order_strategy": args.order,
        "canvas": {"w": canvas_w, "h": canvas_h},
        "bg_hex": "#{:02x}{:02x}{:02x}".format(*args.bg),
        "sharpen": (not args.no_sharpen),
        "outputs": outputs,
        "cells": cell_meta,
    }
    out_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[{TOOL_SID}] manifest → {out_manifest.name}")
    return 0


def _key_to_jsonable(k):
    if isinstance(k, tuple):
        return [round(float(v), 4) for v in k]
    if isinstance(k, float):
        return round(k, 4)
    return k


if __name__ == "__main__":
    raise SystemExit(main())
