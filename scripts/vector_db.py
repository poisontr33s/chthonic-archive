#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: vector_db.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Vector DB for overnight archaeology — tracks debt baselines and file embeddings over time.

Uses Qdrant embedded mode (on-disk, no server needed).
Stores nightly ore embeddings + debt scores for trend analysis.

@SID:           TOOL_VECTOR_DB_V1
@Shabti:          Utility
@Purpose:       Vector DB for overnight archaeology — tracks debt baselines and file embeddings over time.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


import json
import os
import sys
from datetime import datetime
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
QDRANT_PATH = REPO_ROOT / "data" / "qdrant"
EMBEDDINGS_DIR = REPO_ROOT / "dumpster-dive" / "intake" / "embeddings"
COLLECTION_NAME = "archaeology_ore"
VECTOR_DIM = 384  # snowflake-arctic-embed-xs (upgraded from MiniLM-L6-v2)


def get_client():
    """Get or create Qdrant embedded client."""
    from qdrant_client import QdrantClient
    QDRANT_PATH.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(QDRANT_PATH))


def init_collection(client=None):
    """Create the archaeology ore collection if it doesn't exist."""
    from qdrant_client.http.models import Distance, VectorParams
    if client is None:
        client = get_client()
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )
        print(f"Created collection '{COLLECTION_NAME}' ({VECTOR_DIM}d cosine)")
    else:
        info = client.get_collection(COLLECTION_NAME)
        print(f"Collection '{COLLECTION_NAME}': {info.points_count} points")
    return client


def ingest_embeddings(embeddings_path: Path | None = None):
    """Ingest ore embeddings into Qdrant with metadata."""
    from qdrant_client.http.models import PointStruct

    if embeddings_path is None:
        candidates = sorted(EMBEDDINGS_DIR.glob("ore_embeddings_*.json"), reverse=True)
        if not candidates:
            print("No embeddings found. Run embed_ore.py first.")
            return
        embeddings_path = candidates[0]

    with open(embeddings_path, "r", encoding="utf-8") as f:
        embeddings = json.load(f)

    # Extract timestamp from filename: ore_embeddings_arch-2026-02-11T03-00-12.json
    ts_str = embeddings_path.stem.replace("ore_embeddings_", "")
    run_date = datetime.now().isoformat()

    client = init_collection()

    # Batch upsert
    points = []
    for i, (file_path, vector) in enumerate(embeddings.items()):
        points.append(PointStruct(
            id=hash(f"{ts_str}:{file_path}") % (2**63),
            vector=vector,
            payload={
                "path": file_path,
                "run": ts_str,
                "ingested": run_date,
                "ext": Path(file_path).suffix,
            },
        ))

    # Upsert in batches of 500
    batch_size = 500
    for start in range(0, len(points), batch_size):
        batch = points[start:start + batch_size]
        client.upsert(collection_name=COLLECTION_NAME, points=batch)

    info = client.get_collection(COLLECTION_NAME)
    print(f"Ingested {len(points)} points from {ts_str}")
    print(f"Total collection: {info.points_count} points")


def search(query_text: str, top_k: int = 10):
    """Semantic search across all ingested ore."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("Snowflake/snowflake-arctic-embed-xs")
    query_vec = model.encode([query_text])[0].tolist()

    client = init_collection()
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vec,
        limit=top_k,
    )

    print(f"\nTop {top_k} matches for: '{query_text}'")
    for point in results.points:
        print(f"  {point.score:.3f}  {point.payload.get('path', '?')}  [{point.payload.get('run', '?')}]")


def stats():
    """Show collection statistics."""
    client = init_collection()
    info = client.get_collection(COLLECTION_NAME)
    print(f"Collection: {COLLECTION_NAME}")
    print(f"  Points: {info.points_count}")
    print(f"  Vectors: {VECTOR_DIM}d cosine")
    print(f"  Status: {info.status}")
    print(f"  On-disk: {QDRANT_PATH}")


# ── CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "ingest"

    if cmd == "ingest":
        ingest_embeddings()
    elif cmd == "search":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "authentication security"
        search(query)
    elif cmd == "stats":
        stats()
    elif cmd == "init":
        init_collection()
    else:
        print(f"Usage: {Path(__file__).name} [ingest|search <query>|stats|init]")
