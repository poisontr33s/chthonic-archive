#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
entity_pixelart.py — Tier 1 stub

Entity sprite → pixel-art tileset conversion via SD.NEXT img_to_pixelart pipeline.

Backend: SD.NEXT (vladmandic/automatic) img2img + pixel-art ControlNet/LoRA
Report: §VII.5 — SD.NEXT Pixel Art Generation
Python: 3.12+

API surface (SD.NEXT):
    POST /sdapi/v1/img2img  { init_images: [<base64>], prompt: ..., controlnet_units: [...] }
    → images: [<base64>]

Pipeline:
    1. entity_cutout.py → RGBA cutout PNG
    2. entity_pixelart.py → SD.NEXT img2img with pixelart ControlNet/LoRA
    3. Output: indexed-palette PNG sprite sheet (16px / 32px / 64px tile variants)

TODO:
    - [ ] Implement SD.NEXT img2img call with pixel-art prompt template
    - [ ] Add ControlNet unit for structure preservation (lineart / depth)
    - [ ] Add pixel-art LoRA injection (via Forge UnetPatcher or SD.NEXT script API)
    - [ ] Implement sprite sheet tiling (N×M grid packing for tileset export)
    - [ ] Integrate palette quantization (Pillow quantize to indexed PNG)
    - [ ] Wire to auto_caption.py captions for coherent entity tagging
"""

from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

from PIL import Image

from milfological.backends.sdnext import SDNextAdapter


SDNEXT_DEFAULT_URL = "http://127.0.0.1:7860"

PIXELART_PROMPT_TEMPLATE = (
    "pixel art sprite, {entity_desc}, "
    "16-bit game aesthetic, sharp edges, limited palette, "
    "no anti-aliasing, RPG character sprite"
)
PIXELART_NEGATIVE = (
    "blurry, smooth gradients, photorealistic, 3D render, "
    "anti-aliasing, watermark, text"
)

TILE_SIZES = (16, 32, 64)


def encode_image_b64(path: Path) -> str:
    """Encode image as base64 for SD.NEXT API payload."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def pixelart_entity(
    cutout_path: Path,
    entity_desc: str,
    output_dir: Path,
    tile_size: int = 32,
    api_url: str = SDNEXT_DEFAULT_URL,
) -> Path:
    """
    Convert entity cutout PNG to pixel-art sprite via SD.NEXT img2img.

    Args:
        cutout_path: RGBA cutout PNG (output of entity_cutout.py).
        entity_desc: Entity description for prompt construction.
        output_dir: Directory for output sprite tiles.
        tile_size: Target tile size in pixels (16/32/64).
        api_url: SD.NEXT API base URL.

    Returns:
        Path to output sprite PNG.

    Raises:
        NotImplementedError: Stub — implementation pending.
    """
    img = Image.open(cutout_path)
    sprite: Image.Image = SDNextAdapter(base_url=api_url).pixelart(img, block_size=tile_size)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{cutout_path.stem}_sprite_{tile_size}px.png"
    sprite.save(str(output_path), format="PNG")
    return output_path


def pack_sprite_sheet(
    sprites: list[Path],
    output_path: Path,
    columns: int = 8,
    tile_size: int = 32,
) -> Path:
    """
    Pack individual sprites into a tileset sprite sheet.

    Args:
        sprites: List of sprite PNG paths.
        output_path: Output sprite sheet PNG path.
        columns: Number of columns in the sheet.
        tile_size: Size of each tile (pixels).

    Returns:
        Path to output sprite sheet.

    Raises:
        NotImplementedError: Stub — implementation pending.
    """
    raise NotImplementedError(
        "entity_pixelart: sprite sheet packing not yet implemented."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Entity sprite → pixel-art tileset via SD.NEXT"
    )
    parser.add_argument("input", type=Path, help="Input RGBA cutout PNG")
    parser.add_argument("entity_desc", help="Entity description for prompt (e.g. 'warrior woman')")
    parser.add_argument("--output", "-o", type=Path, default=Path("output"), help="Output directory")
    parser.add_argument("--tile-size", type=int, choices=TILE_SIZES, default=32)
    parser.add_argument("--api-url", default=SDNEXT_DEFAULT_URL)
    args = parser.parse_args()

    print(
        f"[entity_pixelart] STUB — input={args.input} entity='{args.entity_desc}' tile={args.tile_size}px\n"
        "Implementation pending. See MILFOLOGICAL_OPPORTUNITY_REPORT.md §VII.5."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
