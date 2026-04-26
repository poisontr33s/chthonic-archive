"""
tabby-modern model state — exllamav2 container lifecycle.
Backend: exllamav2 (EXL2 quantized models). Container owns CUDA resources.
PYTORCH_CUDA_ALLOC_CONF=backend:cudaMallocAsync is set at process start (__main__).

Backend history:
  v0.1 — exllamav3 (G10 attempt): EXL2 model format not supported by exllamav3.
          exllamav3 requires EXL3 or standard HF safetensors (BF16/FP16/GPTQ).
  v0.2 — exllamav2 (current): EXL2 format natively supported; G4/G8 admitted.
"""

from __future__ import annotations

import asyncio
import pathlib
from typing import Optional

from loguru import logger


class ModelState:
    """Thread-safe exllamav2 model container lifecycle manager."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._model: Optional[object] = None
        self._tokenizer: Optional[object] = None
        self._model_name: Optional[str] = None

    @property
    def loaded(self) -> bool:
        return self._model is not None

    @property
    def model_name(self) -> Optional[str]:
        return self._model_name

    async def load(self, model_path: pathlib.Path) -> None:
        async with self._lock:
            if self._model is not None:
                logger.warning("model already loaded — unloading first")
                await self._unload_unsafe()
            await asyncio.get_running_loop().run_in_executor(
                None, self._load_blocking, model_path
            )

    async def unload(self) -> None:
        async with self._lock:
            await self._unload_unsafe()

    def _load_blocking(self, model_path: pathlib.Path) -> None:
        """Runs in executor — exllamav2 model load is CPU-bound (CUDA alloc)."""
        try:
            from exllamav2 import ExLlamaV2, ExLlamaV2Config, ExLlamaV2Tokenizer
        except ImportError as exc:
            raise RuntimeError(
                "exllamav2 not available — check container image / FAF Gate 4/G8"
            ) from exc

        logger.info("loading model from {}", model_path)
        cfg = ExLlamaV2Config(str(model_path))

        # FAF Gate 3: CUDA availability was validated at container build time.
        # We do NOT probe here — loading fails explicitly if CUDA is absent.

        self._model = ExLlamaV2(cfg)
        self._model.load()  # type: ignore[union-attr]
        self._tokenizer = ExLlamaV2Tokenizer(cfg)
        self._model_name = model_path.name
        logger.info("model loaded: {}", self._model_name)

    async def _unload_unsafe(self) -> None:
        """Must be called under self._lock."""
        if self._model is None:
            return
        await asyncio.get_running_loop().run_in_executor(
            None, self._unload_blocking
        )

    def _unload_blocking(self) -> None:
        try:
            if hasattr(self._model, "unload"):
                self._model.unload()  # type: ignore[union-attr]
        except Exception:
            pass
        self._model = None
        self._tokenizer = None
        name = self._model_name
        self._model_name = None
        logger.info("model unloaded: {}", name)
