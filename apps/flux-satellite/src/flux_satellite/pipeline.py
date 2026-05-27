#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""FLUX orchestrator — text encoders + VAE in Python, DiT in C++ bridge via CUDA IPC.

Python owns: T5-XXL + CLIP-L text encoding (with sequential offload), the
scheduler / latent buffer, and the VAE decode. Per diffusion step, this module
exports CUDA IPC handles for every DiT input tensor (and an output buffer),
sends them over the bridge's Pipe-B as JSON, the bridge calls
`TrtEngine::RunDitIpc` against its already-loaded FP8 SM89 engine, and the
result lands in the output tensor's VRAM. PyTorch sees the updated bytes
without copy because the IPC memory IS the same VRAM allocation.

No tensorrt Python import here -- the bypass that keeps us on Python 3.14.
"""
from __future__ import annotations

import base64
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Final, Optional

import numpy as np
import torch
from PIL import Image

log: Final[logging.Logger] = logging.getLogger("flux.pipeline")

DEFAULT_DIT_PIPE: Final[str] = r"\\.\pipe\chthonic-flux-dit"


# ── IPC client to the bridge ────────────────────────────────────────────────


def _share_handle(tensor: torch.Tensor) -> dict:
    """Extract a (handle_b64, storage_size, storage_offset, shape) descriptor
    for a CUDA tensor so the bridge can `cudaIpcOpenMemHandle` it.

    PyTorch's `tensor.untyped_storage()._share_cuda_()` returns:
        (device, handle_bytes_64, storage_size_bytes,
         storage_offset_bytes, ref_counter_handle, ref_counter_offset,
         event_handle, event_sync_required)
    We only need handle / size / offset for synchronous request-response; the
    ref-counter and event handles cover async producer-consumer sharing which
    doesn't apply here (the producer's storage outlives the request).
    """
    if not tensor.is_cuda:
        raise RuntimeError(
            f"tensor not on CUDA (got device={tensor.device}); cannot share IPC handle"
        )
    if not tensor.is_contiguous():
        tensor = tensor.contiguous()
    storage = tensor.untyped_storage()
    shared = storage._share_cuda_()
    handle_bytes: bytes = shared[1]
    storage_size: int = int(shared[2])
    storage_offset: int = int(shared[3])
    return {
        "handle_b64": base64.b64encode(handle_bytes).decode("ascii"),
        "storage_size": storage_size,
        "storage_offset": storage_offset,
        "shape": list(tensor.shape),
        "dtype": str(tensor.dtype).replace("torch.", ""),
    }


class BridgeDitClient:
    """Per-step Pipe-B client. Each `run_dit` opens, writes, reads, closes."""

    def __init__(self, pipe_name: str = DEFAULT_DIT_PIPE, connect_timeout_ms: int = 60_000):
        self.pipe_name = pipe_name
        self.connect_timeout_ms = connect_timeout_ms

    def run_dit(self, inputs: dict, outputs: dict) -> int:
        """Send one DiT step request, return the bridge's measured ms."""
        import win32file
        import win32pipe
        import pywintypes

        payload = json.dumps(
            {"op": "run_dit", "inputs": inputs, "outputs": outputs},
            separators=(",", ":"),
        ).encode("utf-8")

        win32pipe.WaitNamedPipe(self.pipe_name, self.connect_timeout_ms)
        handle = win32file.CreateFile(
            self.pipe_name,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None, win32file.OPEN_EXISTING, 0, None,
        )
        try:
            win32pipe.SetNamedPipeHandleState(
                handle, win32pipe.PIPE_READMODE_MESSAGE, None, None,
            )
            win32file.WriteFile(handle, payload)
            buf = bytearray()
            while True:
                try:
                    _err, chunk = win32file.ReadFile(handle, 1 << 20)
                    if chunk:
                        buf.extend(chunk)
                    if _err == 0:
                        break
                except pywintypes.error as e:
                    if e.winerror == 234:  # ERROR_MORE_DATA
                        continue
                    if e.winerror == 109:  # ERROR_BROKEN_PIPE
                        break
                    raise
            resp = json.loads(bytes(buf).decode("utf-8"))
            if not resp.get("ok"):
                raise RuntimeError(
                    f"bridge run_dit failed: {resp.get('err_code')} {resp.get('err_msg')}"
                )
            return int(resp.get("ms", 0))
        finally:
            win32file.CloseHandle(handle)


# ── IpcDiTModule: drop-in for FluxTransformer2DModel ────────────────────────


class _TransformerOut:
    """Mimics diffusers' Transformer2DModelOutput. FluxPipeline accesses
    `.sample` or unpacks via tuple indexing."""

    __slots__ = ("sample",)

    def __init__(self, sample: torch.Tensor):
        self.sample = sample

    def __iter__(self):
        return iter((self.sample,))

    def __getitem__(self, idx):
        if idx != 0:
            raise IndexError(idx)
        return self.sample


class IpcDiTModule(torch.nn.Module):
    """Substitutes diffusers' FluxTransformer2DModel. On every forward call,
    exports IPC handles for the inputs + a freshly-allocated output tensor,
    sends them to the bridge over Pipe-B, and returns the output tensor.

    `.to() / .cuda() / .cpu()` are no-ops so diffusers' sequential CPU offload
    cannot evict this module from CUDA (the actual weights live in the
    bridge's TRT engine, not in PyTorch parameters).
    """

    def __init__(self, client: BridgeDitClient, device: str = "cuda:0"):
        super().__init__()
        self._client = client
        self._device = torch.device(device)
        self._dit_ms_history: list[int] = []

    @property
    def device(self) -> torch.device:
        return self._device

    @property
    def dtype(self) -> torch.dtype:
        return torch.bfloat16

    def to(self, *args, **kwargs):
        return self  # device-pinned via bridge

    def cuda(self, *args, **kwargs):
        return self

    def cpu(self):
        return self

    @torch.inference_mode()
    def forward(
        self,
        hidden_states: torch.Tensor,
        encoder_hidden_states: torch.Tensor,
        pooled_projections: torch.Tensor,
        timestep: torch.Tensor,
        img_ids: torch.Tensor,
        txt_ids: torch.Tensor,
        guidance: Optional[torch.Tensor] = None,
        joint_attention_kwargs: Optional[dict] = None,
        return_dict: bool = True,
        **_unused: Any,
    ):
        if guidance is None:
            guidance = torch.tensor([3.5], device=self._device, dtype=torch.bfloat16)

        # Allocate the output buffer in OUR CUDA context. The bridge maps its
        # IPC handle and writes the DiT result into it; once `run_dit` returns,
        # we can use the tensor directly.
        sample = torch.empty_like(hidden_states)

        inputs_handles = {
            "hidden_states":          _share_handle(hidden_states),
            "encoder_hidden_states":  _share_handle(encoder_hidden_states),
            "pooled_projections":     _share_handle(pooled_projections),
            "timestep":               _share_handle(timestep),
            "img_ids":                _share_handle(img_ids),
            "txt_ids":                _share_handle(txt_ids),
            "guidance":               _share_handle(guidance),
        }
        output_handles = {
            "sample": _share_handle(sample),
        }

        gen_ms = self._client.run_dit(inputs_handles, output_handles)
        self._dit_ms_history.append(gen_ms)

        if return_dict:
            return _TransformerOut(sample)
        return (sample,)


# ── Orchestrator: T5+CLIP encode -> 22-step DiT loop -> VAE decode ──────────


@dataclass
class GenerationRequest:
    prompt: str
    steps: int
    guidance: float
    width: int
    height: int
    seed: int


@dataclass
class GenerationResult:
    image_rgba: np.ndarray  # (H, W, 4) uint8
    gen_ms: int             # bridge-side DiT total
    wall_ms: int            # full pipeline wall time


class FluxOrchestrator:
    """Loads FluxPipeline with the DiT replaced by IpcDiTModule. The pipeline
    calls our forward(); the actual FP8 compute happens in the C++ bridge."""

    def __init__(
        self,
        client: BridgeDitClient,
        model_id: str = "black-forest-labs/FLUX.1-dev",
        device: str = "cuda:0",
    ):
        self.model_id = model_id
        self.device = torch.device(device)
        self._client = client
        self._pipe = None
        self._ipc_dit: Optional[IpcDiTModule] = None

    def _ensure_pipeline(self) -> None:
        if self._pipe is not None:
            return
        from diffusers import FluxPipeline

        log.info("loading FluxPipeline shell (bf16 CLIP-L + T5-XXL + VAE)")
        pipe = FluxPipeline.from_pretrained(
            self.model_id,
            transformer=None,           # we substitute with IpcDiTModule
            torch_dtype=torch.bfloat16,
        )
        self._ipc_dit = IpcDiTModule(self._client, device=str(self.device))
        pipe.transformer = self._ipc_dit
        # Sequential offload swings text_encoder / text_encoder_2 / vae between
        # CPU and CUDA per submodule. Our IpcDiTModule is device-pinned (its
        # `.to()` is a no-op) so the offload hooks cannot evict it.
        pipe.enable_sequential_cpu_offload()
        self._pipe = pipe
        log.info("FluxPipeline ready; DiT delegated to bridge over Pipe-B")

    @torch.inference_mode()
    def generate(self, req: GenerationRequest) -> GenerationResult:
        self._ensure_pipeline()
        assert self._pipe is not None and self._ipc_dit is not None
        if (req.width % 16) or (req.height % 16):
            raise ValueError("width and height must be multiples of 16")
        if req.steps < 1 or req.steps > 100:
            raise ValueError("steps must be in [1, 100]")

        generator = torch.Generator(device="cpu").manual_seed(int(req.seed))
        self._ipc_dit._dit_ms_history.clear()

        t0 = time.perf_counter()
        out = self._pipe(
            prompt=req.prompt,
            height=req.height,
            width=req.width,
            guidance_scale=req.guidance,
            num_inference_steps=req.steps,
            generator=generator,
            output_type="pil",
        )
        wall_ms = int((time.perf_counter() - t0) * 1000)
        gen_ms = sum(self._ipc_dit._dit_ms_history)

        pil_image: Image.Image = out.images[0]
        if pil_image.mode != "RGBA":
            pil_image = pil_image.convert("RGBA")
        arr = np.asarray(pil_image, dtype=np.uint8)
        if arr.shape != (req.height, req.width, 4):
            raise RuntimeError(
                f"pipeline returned shape {arr.shape}; expected "
                f"({req.height}, {req.width}, 4)"
            )
        log.info(
            "generated %dx%d in %d ms (bridge DiT %d ms across %d steps)",
            req.width, req.height, wall_ms, gen_ms, req.steps,
        )
        return GenerationResult(image_rgba=arr, gen_ms=gen_ms, wall_ms=wall_ms)
