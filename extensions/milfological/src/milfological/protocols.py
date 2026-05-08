#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
protocols.py — Provisional convergence surface (Mine Pass 1)

Derives from SHARED rows in docs/design/MILF_ARCH_MATRIX.md §Provisional-convergence-surface.

Three Protocol classes reflect what mine pass 1 found across 5 SD inference backends:

    SDBackend         — /sdapi/v1/-lineage family: SD.NEXT, A1111, Forge, KoboldCpp
    SegmentationBackend — text-prompt → entity mask: InvokeAI, ComfyUI, (SD.NEXT 🔍 MINE)
    PixelArtBackend   — DCT pixel art postprocessor: SD.NEXT only (unique gold)

This module is NOT a finished contract. It is a live read of convergence. Each mine
sweep may promote a UNIQUE row to SHARED, adding a new method, or split a SHARED row
into a VARIANT, requiring a method to move to per-backend adapters.

Cross-refs:
    MILF_ARCH_MATRIX.md §Provisional-convergence-surface
    SD_CANDIDATE_REGISTRY.md §3 Module→Backend Dependency Map
    backends/ — per-backend adapter implementations
    MILFOLOGICAL_OPPORTUNITY_REPORT.md §I–§XVII — full mine record

Backends status (mine pass 1):
    backends/sdnext.py    — C1 ✅ sweep complete
    backends/a1111.py     — C2 ✅ sweep complete
    backends/invokeai.py  — C4 ✅ sweep complete
    backends/comfyui.py   — C3 ✅ sweep complete
    backends/forge.py     — C5 ⚠️ partial sweep (modules_forge/ confirmed)
    backends/forge_ll.py  — C11 DEFERRED (LayerDiffuse + canonical UnetPatcher)
    backends/sd_cpp.py    — C10 DEFERRED (GGUF lane — Python binding: stable-diffusion-cpp-python)
    backends/koboldcpp.py — C6 ⚠️ web-research only (A1111ForgeApi confirmed)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from PIL import Image


@runtime_checkable
class SDBackend(Protocol):
    """
    Provisional convergence surface for the /sdapi/v1/-lineage family.

    Backends: SD.NEXT (C1), A1111 (C2), Forge/C5 (C5), forge-ll (C11), KoboldCpp (C6).

    Methods map 1-to-1 to SHARED rows in MILF_ARCH_MATRIX.md:

        txt2img       ← POST /sdapi/v1/txt2img
        img2img       ← POST /sdapi/v1/img2img
        interrogate   ← POST /sdapi/v1/interrogate  (SD.NEXT + A1111 + Forge; 🔍 MINE for KoboldCpp)
        model_path    ← models/{Stable-diffusion,VAE,Lora,ControlNet}/ (A1111 lineage convention)
        sampler_names ← GET /sdapi/v1/samplers
        health        ← GET /sdapi/v1/cmd-flags (or any fast endpoint)

    The interface grows. When a new SHARED row is confirmed by a mine sweep, add a
    method here and implement it in each backend adapter.
    """

    def txt2img(self, prompt: str, **params: object) -> Image.Image:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Positive prompt string.
            **params: Sampler, steps, CFG scale, seed, width, height, negative_prompt,
                      etc. — forwarded as-is to the backend JSON payload.

        Returns:
            Generated PIL Image (RGBA or RGB depending on backend).
        """
        ...

    def img2img(
        self,
        image: Image.Image,
        prompt: str,
        **params: object,
    ) -> Image.Image:
        """
        Denoise a source image with prompt guidance.

        Args:
            image: Source PIL Image.
            prompt: Positive prompt string.
            **params: denoising_strength, sampler, steps, etc.

        Returns:
            Denoised PIL Image.
        """
        ...

    def interrogate(self, image: Image.Image, model: str = "clip") -> str:
        """
        Caption / interrogate an image.

        Shared by SD.NEXT + A1111 + Forge via POST /sdapi/v1/interrogate.
        KoboldCpp status: 🔍 MINE (A1111ForgeApi — full coverage unconfirmed).

        Args:
            image: Source PIL Image.
            model: Interrogation model ID ("clip", "deepbooru", "joycaption-alpha-two").

        Returns:
            Caption string.
        """
        ...

    def model_path(self, model_type: str, name: str) -> str:
        """
        Resolve the canonical on-disk path for a model file.

        A1111-lineage convention:
            model_type="checkpoint" → models/Stable-diffusion/<name>
            model_type="vae"        → models/VAE/<name>
            model_type="lora"       → models/Lora/<name>
            model_type="controlnet" → models/ControlNet/<name>

        ComfyUI uses lowercase paths — the ComfyUI adapter overrides this.
        InvokeAI abstracts paths via ModelManager — the InvokeAI adapter raises
        NotImplementedError for this method.

        Args:
            model_type: One of "checkpoint", "vae", "lora", "controlnet", "embedding".
            name: Model filename or display name.

        Returns:
            Absolute or relative path string as the backend would expect it.
        """
        ...

    def sampler_names(self) -> list[str]:
        """
        Return the list of sampler names available on this backend.

        Same JSON key across /sdapi/v1/-lineage; different valid values per backend.
        The adapter holds the sampler map.

        Returns:
            List of sampler name strings.
        """
        ...

    def health(self) -> bool:
        """
        Lightweight liveness check.

        Returns:
            True if backend is reachable and ready; False otherwise.
        """
        ...


@runtime_checkable
class SegmentationBackend(Protocol):
    """
    Text-prompt → entity segmentation mask / cutout.

    Mine pass 1 coverage:
        InvokeAI (C4) — Grounding DINO + SAM2 (§XI)
        ComfyUI  (C3) — SAM3 node (§X)
        SD.NEXT  (C1) — SAM 2.1 present (§II.2); integration contract 🔍 MINE

    This Protocol may split when SD.NEXT SAM sweep is complete — SD.NEXT pipes
    through /sdapi/v1/ while InvokeAI and ComfyUI have native node-graph APIs.

    Used by: entity_cutout.py (refactor target — currently Tier 1 stub).
    """

    def segment(self, image: Image.Image, prompt: str) -> Image.Image:
        """
        Generate a binary segmentation mask from a text prompt.

        Args:
            image: Source PIL Image (RGB or RGBA).
            prompt: Natural-language entity description ("the character's hair", "torso").

        Returns:
            Grayscale PIL Image — mask where white == matched region.
        """
        ...

    def cutout(self, image: Image.Image, prompt: str) -> Image.Image:
        """
        Cut out a text-described region as an RGBA PNG (transparent background).

        Args:
            image: Source PIL Image.
            prompt: Natural-language entity description.

        Returns:
            RGBA PIL Image — entity pixels at full colour; background at alpha=0.
        """
        ...


@runtime_checkable
class PixelArtBackend(Protocol):
    """
    GPU-accelerated DCT pixel art postprocessor.

    Mine pass 1: SD.NEXT only (modules/postprocess/pixelart.py — §VII.1).
    Remains unique until another backend implements an equivalent DCT downscale path.

    Used by: entity_pixelart.py (refactor target — currently Tier 1 stub).

    Gold-vein note (from MILF_ARCH_MATRIX.md):
        SD.NEXT pixel art mode uses a genuine DCT path — not a simple nearest-neighbour
        or palette-quantize step. The block_size + sharpen parameters map directly to
        the DCT frequency coefficients that are kept vs discarded.
    """

    def pixelart(
        self,
        image: Image.Image,
        block_size: int = 8,
        sharpen: float = 0.0,
    ) -> Image.Image:
        """
        Convert an image to DCT pixel art.

        Args:
            image: Source PIL Image (RGB).
            block_size: DCT block size in pixels (4, 8, 16, 32).
            sharpen: Sharpening strength applied post-DCT (0.0 = none, 1.0 = max).

        Returns:
            Pixel-art PIL Image at original resolution (style applied, not resized).
        """
        ...
