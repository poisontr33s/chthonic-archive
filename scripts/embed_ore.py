#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: embed_ore.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Embedding utility for overnight archaeology — semantic similarity on ore files.

Uses sentence-transformers/all-MiniLM-L6-v2 (22.7M params, 384-dim, ~80MB).
Computes embeddings for ore file descriptions, enables semantic clustering
and deduplication of archaeology results.

@SID:           TOOL_EMBEDDINGS_V1
@Shabti:          Utility
@Purpose:       Embedding utility for overnight archaeology — semantic similarity on ore files.
"""

from __future__ import annotations
import json
import sys
import os
from pathlib import Path

# Fix Windows console encoding
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ── Shared config ────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
MODEL_NAME = "Snowflake/snowflake-arctic-embed-xs"  # Upgraded from all-MiniLM-L6-v2 (better retrieval, same speed)
EMBEDDINGS_DIR = REPO_ROOT / "dumpster-dive" / "intake" / "embeddings"


def get_model():
    """Lazy-load the sentence-transformer model."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: list[str], model=None) -> list[list[float]]:
    """Embed a list of texts into 384-dim vectors."""
    if model is None:
        model = get_model()
    embeddings = model.encode(texts, show_progress_bar=len(texts) > 50)
    return embeddings.tolist()


def embed_ore(ore_path: Path | None = None) -> dict:
    """
    Embed all file descriptions from the latest ore JSON.
    Returns {path: embedding_vector} dict.
    """
    if ore_path is None:
        ore_dir = REPO_ROOT / "dumpster-dive" / "intake" / "overnight-intelligence"
        candidates = sorted(ore_dir.glob("*/L1-ore.json"), reverse=True)
        if not candidates:
            print("No ore.json found")
            return {}
        ore_path = candidates[0]

    with open(ore_path, "r", encoding="utf-8") as f:
        ore = json.load(f)

    # Ore is a flat list of file entries with path, nameSignals, gold, etc.
    texts = []
    paths = []
    for entry in (ore if isinstance(ore, list) else []):
        file_path = entry.get("path", "")
        signals = entry.get("nameSignals", [])
        gold = entry.get("gold", {})
        desc_parts = [file_path]
        if signals:
            desc_parts.append(" ".join(s.get("signal", "") if isinstance(s, dict) else str(s) for s in signals))
        if isinstance(gold, dict) and gold.get("category"):
            desc_parts.append(f"{gold['category']} tier:{gold.get('tier', '?')}")
        if file_path:
            texts.append(" | ".join(desc_parts))
            paths.append(file_path)

    if not texts:
        print("No embeddable entries in ore")
        return {}

    print(f"Embedding {len(texts)} ore entries...")
    model = get_model()
    vectors = embed_texts(texts, model)

    result = {p: v for p, v in zip(paths, vectors)}

    # Save embeddings
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = EMBEDDINGS_DIR / f"ore_embeddings_{ore_path.parent.name}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f)
    print(f"Saved {len(result)} embeddings → {out_path.relative_to(REPO_ROOT)}")

    return result


def find_similar(query: str, embeddings: dict, top_k: int = 10) -> list[tuple[str, float]]:
    """Find the top-k most similar files to a query string."""
    import numpy as np

    model = get_model()
    query_vec = model.encode([query])[0]

    scores = []
    for path, vec in embeddings.items():
        vec_arr = np.array(vec)
        sim = float(np.dot(query_vec, vec_arr) / (np.linalg.norm(query_vec) * np.linalg.norm(vec_arr)))
        scores.append((path, sim))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


# ── CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "search":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "CUDA GPU configuration"
        # Load latest embeddings
        candidates = sorted(EMBEDDINGS_DIR.glob("ore_embeddings_*.json"), reverse=True)
        if not candidates:
            print("No embeddings found. Run without args first to embed ore.")
            sys.exit(1)
        with open(candidates[0], "r", encoding="utf-8") as f:
            embeddings = json.load(f)
        results = find_similar(query, embeddings)
        print(f"\nTop matches for: '{query}'")
        for path, score in results:
            print(f"  {score:.3f}  {path}")
    else:
        embed_ore()
