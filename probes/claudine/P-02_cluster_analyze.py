#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @SID: claudine-lora/P-02
# @PROBE: cluster_analyze
# @GATE: C-G2
# @DESC: UMAP + HDBSCAN cluster analysis over P-01 embeddings
#        Reads: manifest/claudine_corpus_embed.npz + manifest/claudine_corpus_meta.json
#        Emits: manifest/claudine_clusters.json
# @RUN:  uv run probes/claudine/P-02_cluster_analyze.py [--n-neighbors 15]
# @DEPS: C-G1 (P-01 must have run first)
# @MANIFEST: manifest/claudine_clusters.json

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

MANIFEST_DIR = Path(r"C:\Users\eldno\chthonic-archive\manifest")
EMBED_NPZ    = MANIFEST_DIR / "claudine_corpus_embed.npz"
META_JSON    = MANIFEST_DIR / "claudine_corpus_meta.json"
CLUSTER_JSON = MANIFEST_DIR / "claudine_clusters.json"


def load_embeddings() -> tuple[np.ndarray, dict]:
    if not EMBED_NPZ.exists():
        raise FileNotFoundError(f"Run P-01 first: {EMBED_NPZ} not found")
    data = np.load(EMBED_NPZ)
    embeddings = data["embeddings"]
    meta = json.loads(META_JSON.read_text(encoding="utf-8"))
    return embeddings, meta


def run_umap(embeddings: np.ndarray, n_neighbors: int, n_components: int = 2) -> np.ndarray:
    import umap  # type: ignore
    print(f"[P-02] UMAP: {embeddings.shape} → {n_components}D  n_neighbors={n_neighbors}")
    t0 = time.time()
    reducer = umap.UMAP(
        n_neighbors=n_neighbors,
        n_components=n_components,
        metric="cosine",
        min_dist=0.05,
        random_state=42,
        verbose=True,
    )
    reduced = reducer.fit_transform(embeddings)
    print(f"[P-02] UMAP done in {time.time()-t0:.1f}s")
    return reduced


def run_hdbscan(reduced: np.ndarray, min_cluster_size: int) -> np.ndarray:
    import hdbscan  # type: ignore
    print(f"[P-02] HDBSCAN min_cluster_size={min_cluster_size}")
    t0 = time.time()
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(reduced)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = int((labels == -1).sum())
    print(f"[P-02] HDBSCAN: {n_clusters} clusters, {n_noise} noise points  ({time.time()-t0:.1f}s)")
    return labels


def summarize_clusters(labels: np.ndarray, reduced: np.ndarray, chunk_metas: list[dict]) -> list[dict]:
    """Build per-cluster summary: centroid, top files by chunk count, label."""
    from collections import Counter

    unique = sorted(set(labels))
    summaries = []
    for cid in unique:
        mask = labels == cid
        idxs = np.where(mask)[0]
        files = [chunk_metas[i]["file"] for i in idxs]
        file_counts = Counter(files).most_common(10)
        centroid = reduced[idxs].mean(axis=0).tolist()
        summaries.append({
            "cluster_id": int(cid),
            "is_noise": bool(cid == -1),
            "n_chunks": int(mask.sum()),
            "n_files": len(set(files)),
            "centroid_2d": centroid,
            "top_files": [{"file": f, "chunks": c} for f, c in file_counts],
        })
    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(description="Claudine corpus cluster analysis P-02")
    parser.add_argument("--n-neighbors", type=int, default=15, help="UMAP n_neighbors (default 15)")
    parser.add_argument("--min-cluster-size", type=int, default=8, help="HDBSCAN min_cluster_size (default 8)")
    args = parser.parse_args()

    t_start = time.time()

    embeddings, meta = load_embeddings()
    chunk_metas: list[dict] = meta["chunks"]
    print(f"[P-02] Loaded {embeddings.shape[0]:,} embeddings from {meta['num_files']:,} files")

    reduced   = run_umap(embeddings, n_neighbors=args.n_neighbors)
    labels    = run_hdbscan(reduced, min_cluster_size=args.min_cluster_size)
    summaries = summarize_clusters(labels, reduced, chunk_metas)

    n_clusters = sum(1 for s in summaries if not s["is_noise"])
    noise_chunks = sum(s["n_chunks"] for s in summaries if s["is_noise"])

    payload = {
        "gate": "C-G2",
        "status": "admitted",
        "probe": "P-02_cluster_analyze",
        "elapsed_s": round(time.time() - t_start, 2),
        "num_chunks": int(len(labels)),
        "num_clusters": n_clusters,
        "noise_chunks": noise_chunks,
        "umap_params": {"n_neighbors": args.n_neighbors, "n_components": 2, "metric": "cosine"},
        "hdbscan_params": {"min_cluster_size": args.min_cluster_size},
        "clusters": summaries,
    }
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    CLUSTER_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[P-02] GATE C-G2 → admitted")
    print(f"       clusters={n_clusters}  noise={noise_chunks}  → {CLUSTER_JSON}")


if __name__ == "__main__":
    main()
