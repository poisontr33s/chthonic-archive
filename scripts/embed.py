#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: embed.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
embed.py — Script logic for embed.py.

@SID:           embed
@Shabti:        CLI Script
@Purpose:       Script logic for embed.py.
"""

# @SID: embed — sentence-transformers embedding bridge for session-corpus G7
# Protocol: reads JSON-lines from stdin {id: str, text: str}
#           writes JSON-lines to stdout {id: str, vec: list[float]}
# Backend:  Qwen/Qwen3-Embedding-0.6B (1024d, 32k ctx, Matryoshka, GPU-native)
# Usage:    cat session_texts.jsonl | uv run scripts/embed.py
#           uv run scripts/embed.py --batch-size 32
#
# MODEL PROVENANCE (2026-05-04 → 2026-05-04 upgrade)
# ────────────────────────────────────────────────────
# G7 baseline was all-MiniLM-L6-v2 (384d, OFFLINE-only, 256 token limit).
# Upgraded to Qwen/Qwen3-Embedding-0.6B per HF market sweep 2026-05-04:
#   - 1024d Matryoshka vectors (effective dims: 64, 128, 256, 512, 1024)
#   - 32k token context window — no more truncation on long session transcripts
#   - SOTA MTEB; 43.7M downloads; Apache-2.0; 595.8M params fit comfortably on RTX 4090
#   - trust_remote_code=True required
#   - Attention pooling: EOS token extraction (causal LM, NOT mean pooling)
#   - HF token (esabbr) required for first download — then cached locally
#
# CORPUS_SCHEMA_VERSION bump: 3 → 4 (FLOAT[384] → FLOAT[1024])
# Requires: bun run scripts/session-corpus.ts --rebuild --embed
#
# Remaining upgrade candidates (registry: scripts/embed_model_registry.json):
#   Qwen/Qwen3-Embedding-8B    — 4096d (Matryoshka to 1024d), 32k ctx, 7.5B params, max accuracy.
#   BAAI/bge-m3                — 1024d, 8192 ctx, MIT, 142.8M dl, hybrid dense+sparse+colbert.
#   nomic-embed-text-v1.5      — 768d, Matryoshka 64-768, 8192 ctx, Apache-2.0, 77.6M dl.
#   ibm-granite/granite-embed… — 384d (ZERO schema change!), ModernBERT arch, code-optimised.
#
# Track B (future — baby-Claudine fine-tune):
#   Base: Qwen3-0.6B-Base (raw LLM, NOT Qwen3-Embedding-0.6B — avoids spatial bias)
#   Framework: sentence-transformers v5.4+ (MatryoshkaLoss + CachedMNRL + Qwen3 native)
#   Data: ~15k-50k synthetic triplets via Poe API (Claude Sonnet 4.6 for hard negatives)
#   Loss: InfoNCE (L_InfoNCE + 2×L_distillation) per Jina v5 arxiv:2602.15547
#   Deploy: safetensors export + config.json model_type:qwen3 + TEI 1.9+ on RTX 4090

import os
import sys
import json
import argparse

DIMS = 1024
MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"


def load_model():
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_ID, device="cuda", trust_remote_code=True)
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

    sys.stderr.write(f"[embed.py] Loading {MODEL_ID} on CUDA...\n")
    sys.stderr.flush()
    model = load_model()
    sys.stderr.write(f"[embed.py] Model ready. dims={DIMS}. Reading stdin...\n")
    sys.stderr.flush()

    stream_embed(model, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
