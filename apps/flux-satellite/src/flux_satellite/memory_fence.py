#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""Post-generation VRAM fence.

After every inference cycle:
  - drop Python references to latents and intermediate tensors
  - synchronize the active CUDA stream
  - flush the PyTorch caching allocator back to the system pool
  - call ipc_collect to release CUDA IPC handles

The TRT engine's CUDA context is held outside the PyTorch caching allocator,
so empty_cache() does not evict it. Only the diffusion-step scratch is fenced.
"""
from __future__ import annotations

import gc
import logging
from typing import Final

import torch

log: Final[logging.Logger] = logging.getLogger("flux.fence")


def post_generation_fence(label: str = "post_gen") -> None:
    """Run the fence. Idempotent; safe to call when no CUDA is present."""
    gc.collect()
    if not torch.cuda.is_available():
        return
    torch.cuda.synchronize()
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()
    try:
        import pynvml
        pynvml.nvmlInit()
        try:
            h = pynvml.nvmlDeviceGetHandleByIndex(0)
            mem = pynvml.nvmlDeviceGetMemoryInfo(h)
            log.info(
                "[%s] vram used=%d MB free=%d MB total=%d MB",
                label, mem.used >> 20, mem.free >> 20, mem.total >> 20,
            )
        finally:
            pynvml.nvmlShutdown()
    except Exception:
        log.debug("[%s] pynvml unavailable for VRAM telemetry", label)
