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
import hashlib
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
CACHE_PATH = EMBEDDINGS_DIR / ".embedding_cache.json"


def _file_hash(path: Path) -> str:
    """SHA-256 of file content for cache keying."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f)


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


def embed_ore(ore_path: Path | None = None, recompute: bool = False) -> dict:
    """
    Embed all file descriptions from the latest ore JSON.
    Returns {path: embedding_vector} dict.
    Embeddings are cached in CACHE_PATH keyed by ore file SHA-256.
    Pass recompute=True (or --recompute on CLI) to bypass cache.
    """
    if ore_path is None:
        ore_dir = REPO_ROOT / "dumpster-dive" / "intake" / "overnight-intelligence"
        candidates = sorted(ore_dir.glob("*/L1-ore.json"), reverse=True)
        if not candidates:
            print("No ore.json found")
            return {}
        ore_path = candidates[0]

    ore_hash = _file_hash(ore_path)
    if not recompute:
        cache = _load_cache()
        if ore_hash in cache:
            print(f"Cache hit for {ore_path.name} [{ore_hash[:8]}] — use --recompute to force")
            return cache[ore_hash]

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

    # Persist to hash-keyed cache
    cache = _load_cache()
    cache[ore_hash] = result
    _save_cache(cache)
    print(f"Saved {len(result)} embeddings \u2192 {CACHE_PATH.relative_to(REPO_ROOT)} [{ore_hash[:8]}]")

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
    recompute = "--recompute" in sys.argv
    filtered_args = [a for a in sys.argv[1:] if a != "--recompute"]
    if filtered_args and filtered_args[0] == "search":
        query = " ".join(filtered_args[1:]) if len(filtered_args) > 1 else "CUDA GPU configuration"
        # Load latest embeddings from cache
        cache = _load_cache()
        if not cache:
            print("No embeddings found. Run without args first to embed ore.")
            sys.exit(1)
        # Use the last-cached embedding set
        latest_key = list(cache.keys())[-1]
        embeddings = cache[latest_key]
        results = find_similar(query, embeddings)
        print(f"\nTop matches for: '{query}'")
        for path, score in results:
            print(f"  {score:.3f}  {path}")
    else:
        embed_ore(recompute=recompute)
