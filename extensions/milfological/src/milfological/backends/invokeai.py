#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backends/invokeai.py — InvokeAI adapter (C4)

Implements: SegmentationBackend

Mine source: invoke-ai/InvokeAI — filesystem sweep complete (§XI, SD_CANDIDATE_REGISTRY.md §2.C4)

API surface:
    /api/v1/ — named workflow REST API (NOT /sdapi/v1/)
    segment  → POST /api/v1/images/upload + named segmentation workflow
    cutout   → POST named workflow → Grounding DINO → SAM2 → RGBA output

Architecture divergence (MILF_ARCH_MATRIX.md):
    InvokeAI does NOT implement /sdapi/v1/. It uses /api/v1/ with named workflows.
    All generation paths are graph-based (InvokeAI node graph = analogous to ComfyUI
    node graph, but with a different JSON schema and REST endpoint shape).

    model_path(): InvokeAI abstracts paths entirely via ModelManager.
    This adapter does NOT implement SDBackend.model_path() — raise NotImplementedError.

Gold veins unique to InvokeAI (mine pass 1):
    Grounding DINO + SAM2 text-prompt entity cutout  → entity_cutout.py (primary target)
    Z-Image regional prompting                        → Future entity_regional.py
    Flux Kontext reference conditioning               → entity_ipadapter.py

    These are the reason InvokeAI is a Tier 1 candidate despite the API divergence.
    The segmentation capability (Grounding DINO → SAM2) is first-class — no A1111
    lineage backend provides equivalent text-prompt entity isolation.

Workflow contract (mine pass 1 — §XI):
    InvokeAI 4.x uses invocation graphs posted to /api/v1/invocations/ (async).
    Response is streamed via /api/v1/events/ (SSE). The segment/cutout methods below
    must construct the correct graph JSON and poll the event stream for completion.
    Full graph schema: dev/sd-candidates/invokeai/invokeai/app/invocations/

TODO:
    - [ ] Map /api/v1/events/ SSE stream for async result retrieval
    - [ ] Implement segment() — Grounding DINO → SAM2 via named workflow
    - [ ] Implement cutout() — segment() output → alpha composite to RGBA PNG
    - [ ] Add Z-Image regional prompting helper (deferred — separate stub)
    - [ ] Add Flux Kontext conditioning helper (deferred — entity_ipadapter.py)
"""

from __future__ import annotations

import base64
import io
from typing import Any

import httpx
from PIL import Image

DEFAULT_URL = "http://127.0.0.1:9090"


class InvokeAIAdapter:
    """
    Adapter for InvokeAI (/api/v1/ — named workflow + Grounding DINO/SAM2).

    Satisfies: SegmentationBackend

    Primary value: Grounding DINO + SAM2 text-prompt entity segmentation/cutout.
    This is the unique gold from InvokeAI — not available in any /sdapi/v1/ lineage backend.
    """

    def __init__(self, base_url: str = DEFAULT_URL, timeout: float = 120.0) -> None:
        self._base = base_url.rstrip("/")
        self._client = httpx.Client(timeout=timeout)

    # ------------------------------------------------------------------
    # SegmentationBackend surface
    # ------------------------------------------------------------------

    def segment(self, image: Image.Image, prompt: str) -> Image.Image:
        """
        Generate a binary mask from a text-prompt via Grounding DINO + SAM2.

        InvokeAI pipeline (mine pass 1 — §XI):
            1. Upload image to /api/v1/images/upload
            2. POST segmentation invocation graph (GroundingDinoInvocation → SAMInvocation)
            3. Poll /api/v1/events/ SSE stream for graph completion
            4. Fetch mask output from /api/v1/images/<result_id>

        Args:
            image: Source PIL Image (RGB or RGBA).
            prompt: Entity description ("the character's torso", "hair", "sword").

        Returns:
            Grayscale PIL Image — white == matched entity region.

        Raises:
            NotImplementedError: Stub pending implementation.
        """
        raise NotImplementedError(
            "InvokeAIAdapter.segment: Grounding DINO + SAM2 workflow not yet implemented. "
            "See TODO in invokeai.py."
        )

    def cutout(self, image: Image.Image, prompt: str) -> Image.Image:
        """
        Cut out text-described entity region as RGBA PNG.

        Calls segment() to get the mask, then composites source image against mask.

        Args:
            image: Source PIL Image.
            prompt: Entity description.

        Returns:
            RGBA PIL Image — entity at full colour; background at alpha=0.

        Raises:
            NotImplementedError: Stub pending implementation (depends on segment()).
        """
        raise NotImplementedError(
            "InvokeAIAdapter.cutout: depends on segment(). "
            "See TODO in invokeai.py."
        )

    # ------------------------------------------------------------------
    # Liveness
    # ------------------------------------------------------------------

    def health(self) -> bool:
        """
        Liveness check — GET /api/v1/app/version.

        Returns:
            True if reachable; False otherwise.
        """
        try:
            resp = self._client.get(f"{self._base}/api/v1/app/version")
            return resp.status_code == 200
        except httpx.TransportError:
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pil_to_b64png(image: Image.Image) -> str:
        """Encode PIL Image as base64 PNG for InvokeAI upload."""
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> InvokeAIAdapter:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
