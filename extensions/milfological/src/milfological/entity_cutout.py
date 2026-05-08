#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
entity_cutout.py — Tier 1 stub

Entity background removal + segmentation mask via InvokeAI Grounding DINO + SAM2.

Backend: InvokeAI v5.x segment_anything / grounding_dino nodes
Report: §IX.2 — InvokeAI Grounding DINO + SAM2
Python: 3.12+

API surface (InvokeAI):
    POST /api/v1/invocations  (graph with GroundingDinoInvocation + SAM2Invocation)
    → mask image URL + cutout image URL

TODO:
    - [ ] Implement InvokeAI graph construction for Grounding DINO → SAM2 pipeline
    - [ ] Implement mask output (PNG with alpha) download + save
    - [ ] Add batch processing across entity reference image directories
    - [ ] Wire mask output to entity_pixelart pipeline (composition input)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx
from PIL import Image


INVOKEAI_DEFAULT_URL = "http://127.0.0.1:9090"


def build_segmentation_graph(
    image_url: str,
    prompt: str,
    box_threshold: float = 0.35,
    text_threshold: float = 0.25,
) -> dict:
    """
    Construct InvokeAI graph for Grounding DINO + SAM2 segmentation.

    Args:
        image_url: InvokeAI-internal image URL or uploaded image ID.
        prompt: Natural language entity description (e.g. 'character figure').
        box_threshold: Grounding DINO bounding box confidence threshold.
        text_threshold: Grounding DINO text token threshold.

    Returns:
        InvokeAI graph payload dict (ready for POST /api/v1/invocations).

    Raises:
        NotImplementedError: Stub — implementation pending.
    """
    raise NotImplementedError(
        "entity_cutout: InvokeAI graph construction not yet implemented. "
        "See §IX.2 of MILFOLOGICAL_OPPORTUNITY_REPORT.md."
    )


def cutout_entity(
    image_path: Path,
    prompt: str,
    output_path: Path,
    api_url: str = INVOKEAI_DEFAULT_URL,
) -> Path:
    """
    Remove background from entity reference image using Grounding DINO + SAM2.

    Args:
        image_path: Source image path.
        prompt: Entity description for DINO bounding box detection.
        output_path: Output PNG path (RGBA, transparent background).
        api_url: InvokeAI server base URL.

    Returns:
        Path to output cutout PNG.

    Raises:
        NotImplementedError: Stub — implementation pending.
    """
    raise NotImplementedError(
        "entity_cutout: background removal not yet implemented."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Entity cutout via InvokeAI Grounding DINO + SAM2"
    )
    parser.add_argument("input", type=Path, help="Input image path")
    parser.add_argument("prompt", help="Entity description (e.g. 'character figure')")
    parser.add_argument("--output", "-o", type=Path, help="Output RGBA PNG path")
    parser.add_argument("--api-url", default=INVOKEAI_DEFAULT_URL, help="InvokeAI API URL")
    args = parser.parse_args()

    print(
        f"[entity_cutout] STUB — input={args.input} prompt='{args.prompt}'\n"
        "Implementation pending. See MILFOLOGICAL_OPPORTUNITY_REPORT.md §IX.2."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
