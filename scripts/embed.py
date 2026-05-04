#!/usr/bin/env python3
# @SID: embed — sentence-transformers embedding bridge for session-corpus G7
# Protocol: reads JSON-lines from stdin {id: str, text: str}
#           writes JSON-lines to stdout {id: str, vec: list[float]}
# Backend:  sentence-transformers/all-MiniLM-L6-v2 (384d, GPU-native, OFFLINE)
# Usage:    cat session_texts.jsonl | uv run scripts/embed.py
#           uv run scripts/embed.py --batch-size 32
#
# MODEL PROVENANCE (2026-05-04)
# ─────────────────────────────
# all-MiniLM-L6-v2 was selected as the G7 baseline because it was the only
# sentence-transformers model confirmed present in the local HF cache at time of
# implementation (TRANSFORMERS_OFFLINE=1 enforced; HF token was invalid/stale).
#
# Known limitations:
#   - 384d vectors (FLOAT[384] schema is now locked to this; migration needed for dim change)
#   - Max 256 word-pieces (session texts are truncated beyond that boundary)
#   - Trained for sentence/short-paragraph similarity; not optimised for code retrieval
#
# Upgrade candidates (require HF token + cache population):
#   nomic-embed-text-v1.5  — 768d, Matryoshka 64-768, 8192 ctx, GPLv3
#   BGE-M3                 — 1024d, multilingual, dense+sparse+colbert hybrid
#   Qwen3-Embedding        — flexible dims, 32k ctx, multilingual, top MTEB 2025-06
#   jina-embeddings-v3     — 1024d, task-aware, 8192 ctx
#
# Migration path: bump schema_version to 4, DROP vec_embeddings, recreate with new FLOAT[N],
# re-run --embed with updated MODEL_ID.

import os
import sys
import json

# MUST be set before any HF/transformers import (network blocked in this env)
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

import argparse

DIMS = 384
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"


def load_model():
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_ID, device="cuda")
    return model


def stream_embed(model, batch_size: int = 32):
    """Read JSON-lines from stdin, write JSON-lines to stdout."""
    buf: list[dict] = []

    def flush(batch: list[dict]):
        if not batch:
            return
        texts = [item["text"] for item in batch]
        vecs = model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        for item, vec in zip(batch, vecs):
            out = {"id": item["id"], "vec": vec.tolist()}
            sys.stdout.write(json.dumps(out) + "\n")
            sys.stdout.flush()

    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"[embed.py] JSON parse error: {e} — skipping line\n")
            continue
        buf.append(entry)
        if len(buf) >= batch_size:
            flush(buf)
            buf = []

    flush(buf)


def main():
    parser = argparse.ArgumentParser(description="Embedding bridge — stdin JSON-lines → stdout JSON-lines")
    parser.add_argument("--batch-size", type=int, default=32, help="Encode batch size (default: 32)")
    args = parser.parse_args()

    sys.stderr.write(f"[embed.py] Loading {MODEL_ID} on CUDA (OFFLINE mode)...\n")
    sys.stderr.flush()
    model = load_model()
    sys.stderr.write(f"[embed.py] Model ready. dims={DIMS}. Reading stdin...\n")
    sys.stderr.flush()

    stream_embed(model, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
