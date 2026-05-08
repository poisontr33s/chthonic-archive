#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backends/a1111.py — AUTOMATIC1111 adapter (C2)

Implements: SDBackend

Mine source: AUTOMATIC1111/stable-diffusion-webui — filesystem sweep complete (§III, §XVII)

API surface:
    txt2img      → POST /sdapi/v1/txt2img
    img2img      → POST /sdapi/v1/img2img
    interrogate  → POST /sdapi/v1/interrogate  (CLIP + DeepBooru)
    model_path   → models/{Stable-diffusion,VAE,Lora,ControlNet}/  (canonical convention)
    sampler_names→ GET /sdapi/v1/samplers
    health       → GET /sdapi/v1/cmd-flags

Architecture note (MILF_ARCH_MATRIX.md §Mine-pass-1-finding):
    A1111 is the reference standard for the /sdapi/v1/ lineage. SD.NEXT + Forge +
    KoboldCpp are all A1111-API-compatible. A1111Adapter is therefore the thinnest
    adapter — it contains no abstraction beyond what the API itself provides.

    KoboldCpp adds A1111ForgeApi compatibility via its own layer; if you are hitting
    KoboldCpp specifically, use koboldcpp.py (deferred, [B5]).

Divergence from SDNextAdapter:
    - No pixel art script (SD.NEXT unique gold)
    - No JoyCaption model (SD.NEXT unique gold)
    - No SDNQ quantization params
    - Face restoration (CodeFormer + GFPGAN) — confirmed via §XVII.3; restore_faces param

TODO:
    - [ ] Implement _post() with retry, timeout, and structured error wrapping
    - [ ] Implement txt2img() — decode base64 response to PIL Image
    - [ ] Implement img2img() — encode image to base64, decode response
    - [ ] Implement interrogate() — CLIP + DeepBooru only (no JoyCaption on A1111)
    - [ ] Implement sampler_names() via GET /sdapi/v1/samplers
"""

from __future__ import annotations

import base64
import io
from typing import Any

import httpx
from PIL import Image

DEFAULT_URL = "http://127.0.0.1:7860"


class A1111Adapter:
    """
    Adapter for AUTOMATIC1111 stable-diffusion-webui (/sdapi/v1/ reference standard).

    Satisfies: SDBackend

    A1111 defines the canonical /sdapi/v1/ surface. All other lineage-family backends
    (SD.NEXT, Forge, KoboldCpp) are measured against this reference.
    """

    def __init__(self, base_url: str = DEFAULT_URL, timeout: float = 120.0) -> None:
        self._base = base_url.rstrip("/")
        self._client = httpx.Client(timeout=timeout)

    def txt2img(self, prompt: str, **params: Any) -> Image.Image:
        """
        Generate image from text prompt via POST /sdapi/v1/txt2img.

        Args:
            prompt: Positive prompt.
            **params: JSON keys — negative_prompt, steps, cfg_scale, sampler_name,
                      width, height, seed, restore_faces, …

        Returns:
            First generated PIL Image.

        Raises:
            NotImplementedError: Stub pending implementation.
        """
        raise NotImplementedError(
            "A1111Adapter.txt2img: implementation pending. "
            "See TODO in a1111.py."
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
            "A1111Adapter.img2img: implementation pending. "
            "See TODO in a1111.py."
        )

    def interrogate(self, image: Image.Image, model: str = "clip") -> str:
        """
        Caption/interrogate image via POST /sdapi/v1/interrogate.

        A1111 supports: "clip", "deepbooru".
        Note: "joycaption-alpha-two" is SD.NEXT only — raise ValueError if requested.

        Args:
            image: Source PIL Image.
            model: "clip" or "deepbooru".

        Returns:
            Caption string.

        Raises:
            ValueError: If model is not supported by A1111.
            NotImplementedError: Stub pending implementation.
        """
        if model not in ("clip", "deepbooru"):
            raise ValueError(
                f"A1111Adapter.interrogate: model {model!r} not supported. "
                "A1111 supports 'clip' and 'deepbooru'. "
                "For JoyCaption, use SDNextAdapter."
            )
        raise NotImplementedError(
            "A1111Adapter.interrogate: implementation pending. "
            "See TODO in a1111.py."
        )

    def model_path(self, model_type: str, name: str) -> str:
        """
        Resolve A1111 canonical model path.

        This is the reference convention — all /sdapi/v1/-lineage backends use it.

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
        Fetch available sampler names via GET /sdapi/v1/samplers.

        Returns:
            List of sampler name strings.

        Raises:
            NotImplementedError: Stub pending implementation.
        """
        raise NotImplementedError(
            "A1111Adapter.sampler_names: implementation pending."
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
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pil_to_b64(image: Image.Image) -> str:
        """Encode PIL Image to base64 PNG string for A1111 API."""
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    @staticmethod
    def _b64_to_pil(b64_str: str) -> Image.Image:
        """Decode base64 PNG string from A1111 API response to PIL Image."""
        data = base64.b64decode(b64_str)
        return Image.open(io.BytesIO(data))

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> A1111Adapter:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
