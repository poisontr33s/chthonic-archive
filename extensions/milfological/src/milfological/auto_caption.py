#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_caption.py — Tier 1 stub

Auto-captions entity reference images for LoRA training via SD.NEXT JoyCaption API.

Backend: SD.NEXT (vladmandic/automatic) JoyCaption integration
Report: §VII.3 — SD.NEXT Image Interrogation
Python: 3.12+

API surface (SD.NEXT):
    POST /sdapi/v1/interrogate  { image: <base64>, model: "joycaption-alpha-two" }
    → { caption: str }

TODO:
    - [ ] Implement SD.NEXT endpoint check (GET /sdapi/v1/cmd-flags)
    - [ ] Implement batch image captioning with retry logic
    - [ ] Add caption output formats: .txt sidecar, JSON manifest
    - [ ] Integrate with entity LoRA trainer workflow (see entity_lora_trainer stub)
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

import httpx
from PIL import Image

from milfological.backends.sdnext import SDNextAdapter


SDNEXT_DEFAULT_URL = "http://127.0.0.1:7860"
JOYCAPTION_MODEL = "joycaption-alpha-two"


def encode_image_b64(path: Path) -> str:
    """Encode image file as base64 string for SD.NEXT API."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def caption_image(image_path: Path, api_url: str = SDNEXT_DEFAULT_URL) -> str:
    """
    Caption a single image via SD.NEXT JoyCaption endpoint.

    Args:
        image_path: Path to source image (PNG/JPG/WEBP).
        api_url: SD.NEXT server base URL.

    Returns:
        Caption string.

    Raises:
        NotImplementedError: Stub — implementation pending.
    """
    img = Image.open(image_path)
    return SDNextAdapter(base_url=api_url).interrogate(img, model=JOYCAPTION_MODEL)


def caption_batch(
    input_dir: Path,
    output_dir: Path,
    api_url: str = SDNEXT_DEFAULT_URL,
    extensions: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".webp"),
) -> dict[str, str]:
    """
    Caption all images in input_dir and write .txt sidecars to output_dir.

    Args:
        input_dir: Directory containing reference images.
        output_dir: Directory for .txt caption sidecars.
        api_url: SD.NEXT server base URL.
        extensions: Image file extensions to process.

    Returns:
        Dict mapping filename → caption.

    Raises:
        NotImplementedError: Stub — implementation pending.
    """
    raise NotImplementedError(
        "auto_caption: batch captioning not yet implemented."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auto-caption entity images via SD.NEXT JoyCaption"
    )
    parser.add_argument("input", type=Path, help="Input image or directory")
    parser.add_argument("--output", "-o", type=Path, help="Output directory for captions")
    parser.add_argument("--api-url", default=SDNEXT_DEFAULT_URL, help="SD.NEXT API URL")
    args = parser.parse_args()

    print(
        f"[auto_caption] STUB — input={args.input} api={args.api_url}\n"
        "Implementation pending. See MILFOLOGICAL_OPPORTUNITY_REPORT.md §VII.3."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
