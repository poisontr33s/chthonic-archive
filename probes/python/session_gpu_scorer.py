#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# @SID: SESSION_GPU_SCORER_V1_G9
#
# GPU-ACCELERATED TURN SEMANTIC SCORER — Phase B of G9 truncation
# ─────────────────────────────────────────────────────────────────────────────
# Hardware: RTX 4090 (CUDA 12.8 / SM 8.9) via PyTorch + flash_attn
# Embedding: Qwen/Qwen3-Embedding-0.6B (1024-dim) — same model already in corpus pipeline
# Algorithm:
#   1. Pull all tool_calls.argsJson + resultSnippet for each turn in the session
#   2. Build per-turn text chunks (truncated to 512 tokens)
#   3. Batch embed on GPU (flash_attn attention, BF16, no grad)
#   4. Compute information density score:
#      - cosine distance from session centroid (high dist = unique signal = high score)
#      - within-cluster deduplication (similar turns collapse to one rep)
#   5. Emit manifest/gpu_scores_<session_prefix>.json
#
# Usage (from session-truncator.ts via spawnSync):
#   uv run probes/python/session_gpu_scorer.py \
#     --session <id> --corpus <path> --out <out.json>
#
# Standalone usage:
#   uv run probes/python/session_gpu_scorer.py --session <id> --list-scores
#
# Dependencies (all already present from G6 flash_attn gate):
#   torch, sentence-transformers or transformers, sqlite3 (stdlib)
#   CUDA 12.8 / flash_attn 2.8.3 optional (falls back to standard attention)

from __future__ import annotations

import argparse
import json
import os
import sqlite3

# Prevent huggingface_hub from hitting the network on every model init.
# Model is already cached locally — the metadata check adds nothing.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
import sys
import time
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────
# Argument parsing
# ─────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="GPU-accelerated session turn scorer (G9)")
parser.add_argument("--session", required=True, help="Session ID to score")
parser.add_argument("--corpus", default=None, help="Path to corpus.sqlite (default: manifest/corpus.sqlite)")
parser.add_argument("--out", default=None, help="Output JSON path (default: manifest/gpu_scores_<prefix>.json)")
parser.add_argument("--model", default="Qwen/Qwen3-Embedding-0.6B", help="Embedding model name")
parser.add_argument("--batch-size", type=int, default=32, help="GPU batch size")
parser.add_argument("--max-tokens", type=int, default=512, help="Max tokens per turn chunk")
parser.add_argument("--list-scores", action="store_true", help="Print scores table to stdout")
parser.add_argument("--no-flash-attn", action="store_true", help="Disable flash_attn even if available")
args = parser.parse_args()

repo_root = Path(__file__).resolve().parent.parent.parent
corpus_path = Path(args.corpus) if args.corpus else repo_root / "manifest" / "corpus.sqlite"
out_path = (
    Path(args.out)
    if args.out
    else repo_root / "manifest" / f"gpu_scores_{args.session[:8]}.json"
)

if not corpus_path.exists():
    print(f"ERROR: corpus not found at {corpus_path}", file=sys.stderr)
    sys.exit(1)

# ─────────────────────────────────────────────────────────────
# Pull turn data from corpus
# ─────────────────────────────────────────────────────────────
def build_turn_texts(session_id: str) -> dict[int, str]:
    """Build a text representation for each turn in the session."""
    con = sqlite3.connect(str(corpus_path))
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    turn_texts: dict[int, list[str]] = {}

    def add(turn: int, text: str) -> None:
        if turn not in turn_texts:
            turn_texts[turn] = []
        if text:
            turn_texts[turn].append(text[:args.max_tokens * 4])  # rough char limit

    # Tool calls: args + result snippet
    for row in cur.execute(
        "SELECT turn, toolName, argsJson, resultSnippet FROM tool_calls WHERE sessionId = ? ORDER BY turn",
        (session_id,),
    ):
        args_preview = ""
        if row["argsJson"]:
            try:
                parsed = json.loads(row["argsJson"])
                # Extract the most signal-rich field
                for key in ("query", "filePath", "command", "pattern", "explanation", "oldString"):
                    if key in parsed:
                        args_preview = f"{key}={str(parsed[key])[:200]}"
                        break
                if not args_preview:
                    args_preview = str(parsed)[:200]
            except Exception:
                args_preview = row["argsJson"][:200]
        text = f"[{row['toolName']}] {args_preview} → {(row['resultSnippet'] or '')[:300]}"
        add(row["turn"], text)

    # Code blocks
    for row in cur.execute(
        "SELECT turn, lang, preview FROM code_blocks WHERE sessionId = ?", (session_id,)
    ):
        add(row["turn"], f"[code:{row['lang']}] {(row['preview'] or '')[:400]}")

    # Terminal commands
    for row in cur.execute(
        "SELECT turn, command, goal FROM terminal_cmds WHERE sessionId = ?", (session_id,)
    ):
        add(row["turn"], f"[cmd] {row['command'][:200]} goal={row['goal'] or ''}")

    # File edits
    for row in cur.execute(
        "SELECT turn, filePath, tool FROM file_edits WHERE sessionId = ?", (session_id,)
    ):
        add(row["turn"], f"[edit:{row['tool']}] {row['filePath']}")

    con.close()

    # Collapse each turn's signals into one string
    return {turn: " | ".join(parts) for turn, parts in turn_texts.items() if parts}


# ─────────────────────────────────────────────────────────────
# GPU embedding + scoring
# ─────────────────────────────────────────────────────────────
def score_turns_gpu(turn_texts: dict[int, str]) -> tuple[list[dict], str, str, int]:
    t0 = time.perf_counter()
    turns = list(turn_texts.keys())
    texts = [turn_texts[t] for t in turns]

    if not texts:
        return [], "none", "none", 0

    try:
        import torch
        import numpy as np
    except ImportError as e:
        print(f"WARNING: torch/numpy unavailable: {e}", file=sys.stderr)
        results = [{"turn": t, "semanticScore": 0.0, "clusterLabel": 0, "cosineSimilarityToCentroid": 0.5} for t in turns]
        return results, "none", "none", 0

    # ── Model loading ──────────────────────────────────────────
    device_name = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device_name)
    use_flash = device_name == "cuda" and not args.no_flash_attn

    model_loaded = False
    embeddings = None  # type: ignore[var-annotated]

    # Try sentence-transformers first (clean API)
    try:
        from sentence_transformers import SentenceTransformer
        st_model = SentenceTransformer(
            args.model,
            device=device_name,
            model_kwargs={"torch_dtype": torch.bfloat16} if device_name == "cuda" else {},
        )
        if use_flash:
            try:
                st_model._first_module().auto_model.config.attn_implementation = "flash_attention_2"
            except Exception:
                pass
        embeddings = st_model.encode(
            texts,
            batch_size=args.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        model_loaded = True
        embedding_model = f"{args.model} (sentence-transformers)"
    except ImportError:
        pass

    # Fallback: transformers directly
    if not model_loaded:
        try:
            from transformers import AutoTokenizer, AutoModel

            tokenizer = AutoTokenizer.from_pretrained(args.model)
            hf_model = AutoModel.from_pretrained(
                args.model,
                torch_dtype=torch.bfloat16 if device_name == "cuda" else torch.float32,
                attn_implementation="flash_attention_2" if use_flash else "eager",
            ).to(device)
            hf_model.eval()

            all_embs = []
            with torch.no_grad():
                for i in range(0, len(texts), args.batch_size):
                    batch = texts[i : i + args.batch_size]
                    enc = tokenizer(batch, return_tensors="pt", padding=True, truncation=True,
                                    max_length=args.max_tokens).to(device)
                    out = hf_model(**enc)
                    # Mean pool last hidden state
                    hidden = out.last_hidden_state
                    mask = enc["attention_mask"].unsqueeze(-1).float()
                    pooled = (hidden * mask).sum(1) / mask.sum(1)
                    pooled = torch.nn.functional.normalize(pooled, dim=-1)
                    all_embs.append(pooled.cpu().float().numpy())
            embeddings = np.vstack(all_embs)
            model_loaded = True
            embedding_model = f"{args.model} (transformers)"
        except Exception as e:
            print(f"WARNING: embedding failed: {e}", file=sys.stderr)
            embedding_model = "none"

    # ── Scoring ───────────────────────────────────────────────
    results = []
    if embeddings is not None:
        import numpy as np

        # Session centroid
        centroid = embeddings.mean(axis=0, keepdims=True)
        centroid_norm = centroid / (np.linalg.norm(centroid, axis=1, keepdims=True) + 1e-8)
        emb_norm = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)

        # Cosine distance from centroid: unique turns score high
        cos_sims = (emb_norm @ centroid_norm.T).squeeze()
        # Distance [0..1]: 0 = identical to centroid (noise), 1 = maximally different (signal)
        distances = (1.0 - cos_sims).clip(0.0, 1.0)

        # Within-session pairwise similarity → detect duplicate clusters
        # Efficient: only compute if corpus ≤ 1000 turns (avoid O(n²) on giant sessions)
        cluster_labels = list(range(len(turns)))
        if len(turns) <= 1000:
            sim_matrix = emb_norm @ emb_norm.T
            visited = [False] * len(turns)
            cluster_id = 0
            for i in range(len(turns)):
                if not visited[i]:
                    cluster_labels[i] = cluster_id
                    for j in range(i + 1, len(turns)):
                        if not visited[j] and sim_matrix[i, j] > 0.92:
                            cluster_labels[j] = cluster_id
                            visited[j] = True
                    visited[i] = True
                    cluster_id += 1

        # Normalize distance → semantic score [0..10]
        if distances.max() > distances.min():
            normalized = (distances - distances.min()) / (distances.max() - distances.min())
        else:
            normalized = np.ones(len(turns)) * 0.5
        semantic_scores = (normalized * 10.0).tolist()

        for i, turn in enumerate(turns):
            results.append({
                "turn": turn,
                "semanticScore": round(semantic_scores[i], 3),
                "clusterLabel": int(cluster_labels[i]),
                "cosineSimilarityToCentroid": round(float(cos_sims[i] if hasattr(cos_sims, "__len__") else cos_sims), 4),
            })
    else:
        # No GPU/model available — emit zero scores (Phase A structural only)
        for turn in turns:
            results.append({"turn": turn, "semanticScore": 0.0, "clusterLabel": 0, "cosineSimilarityToCentroid": 0.5})
        embedding_model = "none"

    duration_ms = int((time.perf_counter() - t0) * 1000)

    return results, embedding_model, device_name, duration_ms


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────
def main() -> None:
    turn_texts = build_turn_texts(args.session)
    if not turn_texts:
        print(f"No turn data found for session {args.session[:8]}", file=sys.stderr)
        # Emit empty result rather than failing — Phase A can proceed alone
        result = {
            "sessionId": args.session,
            "scoredTurns": [],
            "embeddingModel": "none",
            "device": "none",
            "durationMs": 0,
        }
    else:
        scored, model_name, device_name, dur = score_turns_gpu(turn_texts)
        result = {
            "sessionId": args.session,
            "scoredTurns": scored,
            "embeddingModel": model_name,
            "device": device_name,
            "durationMs": dur,
        }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    if args.list_scores:
        print(f"{'Turn':>6}  {'Semantic':>8}  {'Cluster':>7}  {'CosSim':>7}")
        print("-" * 40)
        for entry in sorted(result["scoredTurns"], key=lambda x: x["semanticScore"], reverse=True)[:30]:
            print(f"{entry['turn']:>6}  {entry['semanticScore']:>8.3f}  {entry['clusterLabel']:>7}  {entry.get('cosineSimilarityToCentroid', 0):>7.4f}")
    else:
        print(
            f"[G9-GPU] {args.session[:8]}  {len(result['scoredTurns'])} turns  "
            f"model={result['embeddingModel']}  device={result['device']}  {result['durationMs']}ms"
        )


if __name__ == "__main__":
    main()
