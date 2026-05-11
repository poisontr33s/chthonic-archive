#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: embedding_server.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
GPU-accelerated OpenAI-compatible embedding server for local semantic indexing.

Offloads VS Code Insiders @workspace / Continue extension embedding generation
from the default CPU-bound ONNX indexer to the RTX 4090 via sentence-transformers
+ CUDA. Exposes /v1/embeddings (OpenAI-compatible API) at localhost:8765.

@SID:           EMBED_SERVER_GPU_V1
@Type:          Utility
@Hardware:      RTX 4090 (Ada Lovelace, SM 8.9, 24GB VRAM)
@Model-Default: nomic-ai/nomic-embed-text-v1.5  (~0.5GB VRAM fp16, 8192 ctx)
@Throughput:    ~8,000+ tokens/sec on CUDA vs ~800 tok/s CPU baseline
@Port:          8765 (override: EMBED_PORT env var or --port)

Run:
    uv run scripts/embedding_server.py
    uv run scripts/embedding_server.py --model BAAI/bge-m3 --batch-size 128

Environment overrides:
    EMBED_MODEL         HuggingFace model ID (default: nomic-ai/nomic-embed-text-v1.5)
    EMBED_DEVICE        cuda | cpu (default: cuda)
    EMBED_BATCH_SIZE    encode batch size (default: 64)
    EMBED_PORT          server port (default: 8765)
    EMBED_HOST          bind host (default: 127.0.0.1)
    EMBED_TRUST_REMOTE  trust remote code (default: true)
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("embed-server")

# ---------------------------------------------------------------------------
# Runtime config — read from env, can be overridden by main() before server start
# ---------------------------------------------------------------------------
MODEL_NAME: str = os.environ.get("EMBED_MODEL", "nomic-ai/nomic-embed-text-v1.5")
DEVICE: str = os.environ.get("EMBED_DEVICE", "cuda")
BATCH_SIZE: int = int(os.environ.get("EMBED_BATCH_SIZE", "64"))
PORT: int = int(os.environ.get("EMBED_PORT", "8765"))
HOST: str = os.environ.get("EMBED_HOST", "127.0.0.1")
TRUST_REMOTE_CODE: bool = os.environ.get("EMBED_TRUST_REMOTE", "true").lower() == "true"

# ---------------------------------------------------------------------------
# Global model state
# ---------------------------------------------------------------------------
_model = None


def _load_model() -> None:
    global _model
    try:
        import torch
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        log.error(f"Missing dependency: {e}. Run: uv sync --group embeddings")
        sys.exit(1)

    actual_device = DEVICE
    if DEVICE == "cuda" and not torch.cuda.is_available():
        log.warning("CUDA not available — falling back to CPU")
        actual_device = "cpu"

    if actual_device == "cuda":
        props = torch.cuda.get_device_properties(0)
        log.info(f"CUDA device: {props.name}")
        log.info(f"VRAM total: {props.total_memory / 1e9:.1f} GB")

    log.info(f"Loading '{MODEL_NAME}' on {actual_device} ...")
    _model = SentenceTransformer(
        MODEL_NAME,
        device=actual_device,
        trust_remote_code=TRUST_REMOTE_CODE,
    )

    # Warm-up pass — forces CUDA kernel compilation before first real request
    _model.encode(["warm-up"], batch_size=1, normalize_embeddings=True)

    dim = _model.get_sentence_embedding_dimension()
    log.info(f"Model ready — dim: {dim}")

    if actual_device == "cuda":
        allocated_gb = torch.cuda.memory_allocated(0) / 1e9
        log.info(f"VRAM allocated by model: {allocated_gb:.2f} GB")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
except ImportError as e:
    log.error(f"Missing dependency: {e}. Run: uv sync --group embeddings")
    sys.exit(1)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    _load_model()
    log.info(f"Embedding server ready → http://{HOST}:{PORT}/v1/embeddings")
    yield
    log.info("Embedding server shut down")


app = FastAPI(
    title="Chthonic Embedding Server",
    version="1.0.0",
    description="GPU-accelerated local embeddings — RTX 4090 / Ada Lovelace",
    lifespan=_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class EmbeddingRequest(BaseModel):
    input: str | list[str]
    model: str = MODEL_NAME
    encoding_format: Literal["float", "base64"] = "float"
    dimensions: int | None = None


class EmbeddingObject(BaseModel):
    object: str = "embedding"
    embedding: list[float]
    index: int


class UsageInfo(BaseModel):
    prompt_tokens: int
    total_tokens: int


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: list[EmbeddingObject]
    model: str
    usage: UsageInfo


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    owned_by: str = "local"
    created: int = 0


class ModelList(BaseModel):
    object: str = "list"
    data: list[ModelInfo]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
async def health() -> dict:
    try:
        import torch
        cuda_ok = torch.cuda.is_available()
        vram_free_gb = (
            (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / 1e9
            if cuda_ok else None
        )
    except ImportError:
        cuda_ok = False
        vram_free_gb = None

    return {
        "status": "ok" if _model is not None else "loading",
        "model": MODEL_NAME,
        "device": DEVICE,
        "cuda_available": cuda_ok,
        "vram_free_gb": round(vram_free_gb, 2) if vram_free_gb is not None else None,
        "embedding_dim": _model.get_sentence_embedding_dimension() if _model else None,
        "batch_size": BATCH_SIZE,
    }


@app.get("/v1/models")
async def list_models() -> ModelList:
    return ModelList(data=[ModelInfo(id=MODEL_NAME)])


@app.post("/v1/embeddings")
async def create_embeddings(request: EmbeddingRequest) -> EmbeddingResponse:
    if _model is None:
        raise HTTPException(status_code=503, detail="Model not ready")

    texts: list[str] = [request.input] if isinstance(request.input, str) else list(request.input)
    if not texts:
        raise HTTPException(status_code=400, detail="Empty input")

    approx_tokens = sum(max(1, len(t) // 4) for t in texts)

    t0 = time.perf_counter()
    vectors = _model.encode(
        texts,
        batch_size=BATCH_SIZE,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000

    if len(texts) > 4:
        tok_per_sec = int(approx_tokens / max(elapsed_ms / 1000, 1e-6))
        log.info(f"Encoded {len(texts)} texts | {elapsed_ms:.1f}ms | ~{tok_per_sec} tok/s")

    data = [EmbeddingObject(embedding=vec.tolist(), index=i) for i, vec in enumerate(vectors)]
    return EmbeddingResponse(
        data=data,
        model=request.model,
        usage=UsageInfo(prompt_tokens=approx_tokens, total_tokens=approx_tokens),
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    global MODEL_NAME, DEVICE, PORT, HOST, BATCH_SIZE, TRUST_REMOTE_CODE

    parser = argparse.ArgumentParser(
        description="Chthonic GPU Embedding Server — RTX 4090 / CUDA",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model", default=MODEL_NAME, help="HuggingFace model ID")
    parser.add_argument("--device", default=DEVICE, choices=["cuda", "cpu"])
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--no-trust-remote", action="store_true", help="Disable trust_remote_code")
    args = parser.parse_args()

    MODEL_NAME = args.model
    DEVICE = args.device
    PORT = args.port
    HOST = args.host
    BATCH_SIZE = args.batch_size
    TRUST_REMOTE_CODE = not args.no_trust_remote

    log.info(f"Model: {MODEL_NAME} | Device: {DEVICE} | Batch: {BATCH_SIZE} | Port: {PORT}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
