#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backends/sdnext.py — SD.NEXT adapter (C1)

Implements: SDBackend, PixelArtBackend

Mine source: vladmandic/automatic — filesystem sweep complete (§I–§IX, SD_CANDIDATE_REGISTRY.md §2.C1)

API surface:
    txt2img      → POST /sdapi/v1/txt2img
    img2img      → POST /sdapi/v1/img2img
    interrogate  → POST /sdapi/v1/interrogate  (JoyCaption + CLIP + DeepBooru)
    model_path   → models/{Stable-diffusion,VAE,Lora,ControlNet}/
    sampler_names→ GET /sdapi/v1/samplers
    health       → GET /sdapi/v1/cmd-flags
    pixelart     → POST /sdapi/v1/txt2img with script_name="Pixel art"
                   (modules/postprocess/pixelart.py — DCT path, §VII.1)

Gold veins (unique to SD.NEXT — no backend param for these yet):
    SDNQ 4-bit native quantization   → params key: "sd_model_checkpoint" + SDNQ suffix
    CivitAI integration              → POST /sdapi/v1/civitai (§VIII)
    JoyCaption-alpha-two             → model="joycaption-alpha-two" on interrogate
    DCT pixel art script             → script_name="Pixel art" on txt2img/img2img

TODO:
    - [ ] Implement _post() with retry, timeout, and structured error wrapping
    - [ ] Implement txt2img() — decode base64 response to PIL Image
    - [ ] Implement img2img() — encode image to base64, decode response
    - [ ] Implement interrogate() — used by auto_caption.py
    - [ ] Implement pixelart() — send txt2img with pixel art script params
    - [ ] Add sampler_names() and model_path() once API surface is confirmed live
"""

from __future__ import annotations

import base64
import io
from typing import Any

import httpx
from PIL import Image

from milfological.protocols import PixelArtBackend, SDBackend

DEFAULT_URL = "http://127.0.0.1:7860"
_PIXEL_ART_SCRIPT = "Pixel art"


class SDNextAdapter:
    """
    Adapter for SD.NEXT (/sdapi/v1/ lineage + pixel art DCT gold).

    Satisfies: SDBackend, PixelArtBackend

    Instantiate once per server process and reuse — httpx.Client is kept open.
    """

    def __init__(self, base_url: str = DEFAULT_URL, timeout: float = 120.0) -> None:
        self._base = base_url.rstrip("/")
        self._client = httpx.Client(timeout=timeout)

    # ------------------------------------------------------------------
    # SDBackend surface
    # ------------------------------------------------------------------

    def txt2img(self, prompt: str, **params: Any) -> Image.Image:
        """
        Generate image from text prompt via POST /sdapi/v1/txt2img.

        Args:
            prompt: Positive prompt.
            **params: Any /sdapi/v1/txt2img JSON keys (negative_prompt, steps, cfg_scale,
                      sampler_name, width, height, seed, …).

        Returns:
            First generated PIL Image.

        Raises:
            NotImplementedError: Stub pending implementation.
        """
        raise NotImplementedError(
            "SDNextAdapter.txt2img: implementation pending. "
            "See TODO in sdnext.py."
        )

    def img2img(
        self,
        image: Image.Image,
        prompt: str,
        **params: Any,
    ) -> Image.Image:
        """
        Denoise source image via POST /sdapi/v1/img2img.

        Args:
            image: Source PIL Image.
            prompt: Positive prompt.
            **params: denoising_strength, steps, cfg_scale, sampler_name, …

        Returns:
            Denoised PIL Image.

        Raises:
            NotImplementedError: Stub pending implementation.
        """
        raise NotImplementedError(
            "SDNextAdapter.img2img: implementation pending. "
            "See TODO in sdnext.py."
        )

    def interrogate(self, image: Image.Image, model: str = "clip") -> str:
        """
        Caption/interrogate image via POST /sdapi/v1/interrogate.

        SD.NEXT supports: "clip", "deepbooru", "joycaption-alpha-two".
        Used by: auto_caption.py (JoyCaption integration).

        Args:
            image: Source PIL Image.
            model: Interrogation model ID.

        Returns:
            Caption string.

        Raises:
            NotImplementedError: Stub pending implementation.
        """
        raise NotImplementedError(
            "SDNextAdapter.interrogate: implementation pending. "
            "See TODO in sdnext.py."
        )

    def model_path(self, model_type: str, name: str) -> str:
        """
        Resolve A1111-lineage model path for SD.NEXT.

        Folder convention:
            checkpoint → models/Stable-diffusion/<name>
            vae        → models/VAE/<name>
            lora       → models/Lora/<name>
            controlnet → models/ControlNet/<name>
            embedding  → embeddings/<name>

        Args:
            model_type: One of "checkpoint", "vae", "lora", "controlnet", "embedding".
            name: Model filename.

        Returns:
            Relative path string.
        """
        _paths: dict[str, str] = {
            "checkpoint": "models/Stable-diffusion",
            "vae": "models/VAE",
            "lora": "models/Lora",
            "controlnet": "models/ControlNet",
            "embedding": "embeddings",
        }
        folder = _paths.get(model_type.lower())
        if folder is None:
            raise ValueError(f"Unknown model_type: {model_type!r}")
        return f"{folder}/{name}"

    def sampler_names(self) -> list[str]:
        """
        Fetch available sampler names from SD.NEXT via GET /sdapi/v1/samplers.

        Returns:
            List of sampler name strings.

        Raises:
            NotImplementedError: Stub pending implementation.
        """
        raise NotImplementedError(
            "SDNextAdapter.sampler_names: implementation pending."
        )

    def health(self) -> bool:
        """
        Liveness check — GET /sdapi/v1/cmd-flags.

        Returns:
            True if reachable; False otherwise.
        """
        try:
            resp = self._client.get(f"{self._base}/sdapi/v1/cmd-flags")
            return resp.status_code == 200
        except httpx.TransportError:
            return False

    # ------------------------------------------------------------------
    # PixelArtBackend surface (SD.NEXT unique gold — §VII.1)
    # ------------------------------------------------------------------

    def pixelart(
        self,
        image: Image.Image,
        block_size: int = 8,
        sharpen: float = 0.0,
    ) -> Image.Image:
        """
        Apply SD.NEXT DCT pixel art postprocessing via POST /sdapi/v1/img2img.

        Mine source: modules/postprocess/pixelart.py — DCT frequency-domain downscale.
        This is NOT a nearest-neighbour resize — the DCT path preserves frequency
        content controlled by block_size and sharpen.

        Script params forwarded to SD.NEXT:
            script_name = "Pixel art"
            script_args = [block_size, sharpen]
            denoising_strength = 0.0  (postprocess only — no diffusion step)

        Args:
            image: Source PIL Image (RGB).
            block_size: DCT block size in pixels (4, 8, 16, 32).
            sharpen: Post-DCT sharpening strength (0.0 = none, 1.0 = max).

        Returns:
            Pixel-art PIL Image.

        Raises:
            NotImplementedError: Stub pending implementation.
        """
        raise NotImplementedError(
            "SDNextAdapter.pixelart: implementation pending. "
            "See TODO in sdnext.py."
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pil_to_b64(image: Image.Image) -> str:
        """Encode PIL Image to base64 PNG string for SD.NEXT API."""
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    @staticmethod
    def _b64_to_pil(b64_str: str) -> Image.Image:
        """Decode base64 PNG string from SD.NEXT API response to PIL Image."""
        data = base64.b64decode(b64_str)
        return Image.open(io.BytesIO(data))

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> SDNextAdapter:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


# Runtime Protocol checks (fail fast at import time if the class diverges)
assert isinstance(SDNextAdapter, type)
# Note: runtime_checkable Protocol checks require an *instance* — checked in tests
