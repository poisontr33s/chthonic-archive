#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backends — per-backend adapter implementations for the MILFOLOGICAL pipeline.

Each module implements one or more Protocol classes from protocols.py.

Adapters (mine pass 1):
    sdnext.py    — SDBackend + PixelArtBackend (C1 — SD.NEXT /sdapi/v1/ + DCT pixel art)
    a1111.py     — SDBackend (C2 — A1111 /sdapi/v1/ reference standard)
    invokeai.py  — SegmentationBackend (C4 — InvokeAI /api/v1/ named workflow)
    comfyui.py   — SegmentationBackend (C3 — ComfyUI JSON graph + WebSocket)

Deferred adapters:
    forge.py     — [B2] Forge UnetPatcher hooks (C5 — partial sweep; modules_forge/ confirmed)
    forge_ll.py  — [B7] LayerDiffuse + canonical UnetPatcher (C11 — trigger: sprite alpha)
    koboldcpp.py — [B5] A1111ForgeApi wrapper (C6 — trigger: KoboldCpp sweep complete)
    sd_cpp.py    — [B6] stable-diffusion-cpp-python CLI (C10 — trigger: GGUF/Vulkan lane)

Cross-refs:
    ../protocols.py — Protocol definitions
    docs/design/MILF_ARCH_MATRIX.md — convergence / divergence surface
    docs/design/SD_CANDIDATE_REGISTRY.md — mine state + task sequencing
"""
