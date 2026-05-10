#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @SID: claudine-lora/P-01
# @PROBE: corpus_embed
# @GATE: C-G1
# @DESC: Embed PsychoNoir-Kontrapunkt .md corpus → manifest/claudine_corpus_embed.npz
#        Sliding-window chunking (512 tokens, 64 overlap) → nomic-embed-text-v1.5 (CUDA)
#        Emits: manifest/claudine_corpus_embed.npz + manifest/claudine_corpus_meta.json
# @RUN:  uv run probes/claudine/P-01_corpus_embed.py [--dry-run]
# @MANIFEST: manifest/claudine_corpus_embed.npz, manifest/claudine_corpus_meta.json

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

CORPUS_ROOT = Path(r"C:\Users\eldno\PsychoNoir-Kontrapunkt")
MANIFEST_DIR = Path(r"C:\Users\eldno\chthonic-archive\manifest")
EMBED_NPZ    = MANIFEST_DIR / "claudine_corpus_embed.npz"
META_JSON    = MANIFEST_DIR / "claudine_corpus_meta.json"

EMBED_MODEL  = "nomic-ai/nomic-embed-text-v1.5"
CHUNK_CHARS  = 1800   # ~512 tokens at ~3.5 chars/tok
OVERLAP_CHARS = 200
BATCH_SIZE   = 64


@dataclass
class ChunkMeta:
    file: str          # relative path from CORPUS_ROOT
    chunk_idx: int
    char_start: int
    char_end: int
    file_size: int


def chunk_text(text: str, chunk: int = CHUNK_CHARS, overlap: int = OVERLAP_CHARS) -> list[tuple[int, int]]:
    """Return (start, end) character spans."""
    spans: list[tuple[int, int]] = []
    start = 0
    while start < len(text):
        end = min(start + chunk, len(text))
        spans.append((start, end))
        if end == len(text):
            break
        start += chunk - overlap
    return spans


def collect_chunks(corpus: Path, dry_run: bool = False) -> tuple[list[str], list[ChunkMeta]]:
    md_files = sorted(corpus.rglob("*.md"))
    if dry_run:
        md_files = md_files[:10]

    texts: list[str] = []
    metas: list[ChunkMeta] = []

    for md in md_files:
        try:
            content = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if not content.strip():
            continue
        rel = str(md.relative_to(corpus))
        spans = chunk_text(content)
        for idx, (s, e) in enumerate(spans):
            texts.append(content[s:e])
            metas.append(ChunkMeta(
                file=rel,
                chunk_idx=idx,
                char_start=s,
                char_end=e,
                file_size=len(content),
            ))

    return texts, metas


def embed_chunks(texts: list[str]) -> np.ndarray:
    from sentence_transformers import SentenceTransformer
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[P-01] Loading {EMBED_MODEL} on {device}")
    model = SentenceTransformer(EMBED_MODEL, device=device, trust_remote_code=True)

    # nomic-embed requires task prefix for asymmetric retrieval — clustering uses "clustering:"
    prefixed = [f"clustering: {t}" for t in texts]

    print(f"[P-01] Embedding {len(prefixed):,} chunks in batches of {BATCH_SIZE}")
    t0 = time.time()
    embeddings = model.encode(
        prefixed,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    elapsed = time.time() - t0
    print(f"[P-01] Embedded {len(embeddings):,} vectors in {elapsed:.1f}s  shape={embeddings.shape}")
    return embeddings


def write_manifest(embeddings: np.ndarray, metas: list[ChunkMeta], elapsed_total: float, dry_run: bool) -> None:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(EMBED_NPZ, embeddings=embeddings)
    print(f"[P-01] Wrote {EMBED_NPZ}")

    meta_payload = {
        "gate": "C-G1",
        "status": "admitted",
        "probe": "P-01_corpus_embed",
        "dry_run": dry_run,
        "corpus_root": str(CORPUS_ROOT),
        "embed_model": EMBED_MODEL,
        "num_chunks": len(metas),
        "num_files": len({m.file for m in metas}),
        "embed_shape": list(embeddings.shape),
        "elapsed_s": round(elapsed_total, 2),
        "chunks": [asdict(m) for m in metas],
    }
    META_JSON.write_text(json.dumps(meta_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[P-01] Wrote {META_JSON}")

    print(f"\n[P-01] GATE C-G1 → admitted")
    print(f"       files={meta_payload['num_files']:,}  chunks={len(metas):,}  dim={embeddings.shape[1]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Claudine corpus embedding probe P-01")
    parser.add_argument("--dry-run", action="store_true", help="Process only first 10 .md files")
    args = parser.parse_args()

    t_start = time.time()

    print(f"[P-01] Collecting chunks from {CORPUS_ROOT}")
    texts, metas = collect_chunks(CORPUS_ROOT, dry_run=args.dry_run)
    print(f"[P-01] {len({m.file for m in metas}):,} files → {len(texts):,} chunks")

    if not texts:
        print("[P-01] ERROR: no chunks found — check CORPUS_ROOT path")
        raise SystemExit(1)

    embeddings = embed_chunks(texts)
    write_manifest(embeddings, metas, time.time() - t_start, args.dry_run)


if __name__ == "__main__":
    main()
