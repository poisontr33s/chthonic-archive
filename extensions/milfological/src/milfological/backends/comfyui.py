#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backends/comfyui.py — ComfyUI adapter (C3)

Implements: SegmentationBackend

Mine source: comfyanonymous/ComfyUI — filesystem sweep complete (§X, SD_CANDIDATE_REGISTRY.md §2.C3)

API surface:
    /api/ — JSON graph REST + WebSocket event stream
    segment → POST /api/prompt (KSampler graph + SAM3 node) + WebSocket
    cutout  → same graph → RGBA output node

Architecture divergence (MILF_ARCH_MATRIX.md):
    ComfyUI uses a JSON node graph API, not /sdapi/v1/. Every operation is expressed
    as a graph of nodes posted to /api/prompt. Execution events arrive via WebSocket
    at /ws?clientId=<uuid>. The graph schema is defined by node class names
    (e.g., "KSampler", "SAMModelLoader", "SAMDetectorSegmented").

    ComfyUI does NOT implement SDBackend — it has its own architecture.
    model_path() convention: lowercase variants (models/checkpoints/, models/loras/, …)
    vs A1111 lineage (models/Stable-diffusion/, models/Lora/, …).

Gold veins unique to ComfyUI (mine pass 1):
    SAM3 video tracking          → entity_video_track.py
    GLSL shader nodes            → entity_glsl_vfx.py
    In-graph LoRA trainer (fp4)  → entity_lora_trainer.py
    ElevenLabs / Kling / Veo2 API nodes → entity_video.py (API route)
    Flux Kontext ref conditioning → entity_ipadapter.py

    The WebSocket API + node graph is the correct abstraction for ComfyUI —
    do not try to wrap it in /sdapi/v1/ shape. Each ComfyUI gold vein is a
    distinct graph topology; implement them as named graph builders.

Graph contract (mine pass 1 — §X):
    POST /api/prompt → { "client_id": str, "prompt": { node_id: { class_type, inputs } } }
    Response: { "prompt_id": str }
    WebSocket: ws://<host>/ws?clientId=<uuid> → execution events → "executed" → outputs

TODO:
    - [ ] Implement WebSocket listener for execution completion
    - [ ] Implement _build_sam_cutout_graph() — SAM3 node graph for entity segmentation
    - [ ] Implement segment() — upload image → graph POST → WS poll → mask fetch
    - [ ] Implement cutout() — segment() mask → RGBA composite
    - [ ] Add GLSL shader node graph builder (deferred — entity_glsl_vfx.py)
    - [ ] Add LoRA trainer graph builder (deferred — entity_lora_trainer.py)
"""

from __future__ import annotations

import base64
import io
import uuid
from typing import Any

import httpx
from PIL import Image

DEFAULT_URL = "http://127.0.0.1:8188"


class ComfyUIAdapter:
    """
    Adapter for ComfyUI (/api/ JSON node graph + WebSocket).

    Satisfies: SegmentationBackend

    Each operation is a node graph. This adapter exposes the SegmentationBackend
    surface via a SAM3-based graph. Additional gold veins (GLSL, LoRA trainer,
    video tracking) are deferred to their own module surfaces.
    """

    def __init__(self, base_url: str = DEFAULT_URL, timeout: float = 120.0) -> None:
        self._base = base_url.rstrip("/")
        self._client_id = str(uuid.uuid4())
        self._client = httpx.Client(timeout=timeout)

    # ------------------------------------------------------------------
    # SegmentationBackend surface
    # ------------------------------------------------------------------

    def segment(self, image: Image.Image, prompt: str) -> Image.Image:
        """
        Generate binary mask via ComfyUI SAM3 node graph.

        ComfyUI pipeline (mine pass 1 — §X):
            1. Upload image via POST /api/upload/image
            2. Build node graph: SAMModelLoader → GroundingDINOModelLoader →
               SAMDetectorSegmented (prompt input) → MaskToImage node
            3. POST graph to /api/prompt with client_id
            4. Listen on WebSocket /ws?clientId=<uuid> for "executed" event
            5. Fetch mask image from /api/view?filename=<output>

        Args:
            image: Source PIL Image (RGB or RGBA).
            prompt: Entity description ("hair", "sword hilt", "character torso").

        Returns:
            Grayscale PIL Image — white == matched entity region.

        Raises:
            NotImplementedError: Stub pending implementation.
        """
        raise NotImplementedError(
            "ComfyUIAdapter.segment: SAM3 graph not yet implemented. "
            "See TODO in comfyui.py."
        )

    def cutout(self, image: Image.Image, prompt: str) -> Image.Image:
        """
        Cut out text-described entity as RGBA PNG via ComfyUI SAM3 graph.

        Args:
            image: Source PIL Image.
            prompt: Entity description.

        Returns:
            RGBA PIL Image — entity at full colour; background at alpha=0.

        Raises:
            NotImplementedError: Stub pending implementation.
        """
        raise NotImplementedError(
            "ComfyUIAdapter.cutout: depends on segment(). "
            "See TODO in comfyui.py."
        )

    # ------------------------------------------------------------------
    # Graph helpers (to be filled during implementation)
    # ------------------------------------------------------------------

    def _post_prompt(self, graph: dict[str, Any]) -> str:
        """
        POST a node graph to /api/prompt.

        Args:
            graph: ComfyUI node graph dict { node_id: { class_type, inputs } }.

        Returns:
            prompt_id string.

        Raises:
            NotImplementedError: Stub pending implementation.
        """
        raise NotImplementedError(
            "ComfyUIAdapter._post_prompt: WebSocket integration pending."
        )

    # ------------------------------------------------------------------
    # Liveness
    # ------------------------------------------------------------------

    def health(self) -> bool:
        """
        Liveness check — GET /api/system_stats.

        Returns:
            True if reachable; False otherwise.
        """
        try:
            resp = self._client.get(f"{self._base}/api/system_stats")
            return resp.status_code == 200
        except httpx.TransportError:
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pil_to_bytes(image: Image.Image) -> bytes:
        """Encode PIL Image as PNG bytes for ComfyUI upload."""
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> ComfyUIAdapter:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
