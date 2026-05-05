#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @SID: EMBEDDING_EXPLORER_V1_G9
#
# LOCALHOST GRADIO — Embedding Explorer / Corpus Similarity Probe
# ─────────────────────────────────────────────────────────────────────────────
# Hardware: RTX 4090 via ONNX Runtime CUDAExecutionProvider (same tensor cores as DLSS)
# Model: Qwen/Qwen3-Embedding-0.6B (cached locally — HF_HUB_OFFLINE=1)
# Purpose:
#   - Live text query → cosine similarity against corpus.sqlite turns
#   - Validate that the ONNX Runtime CUDA path produces correct embeddings
#   - Proof-of-concept for replacing sentence-transformers with local ONNX engine
#
# Run:
#   uv run probes/python/embedding_explorer.py
#   uv run probes/python/embedding_explorer.py --port 7861
#   uv run probes/python/embedding_explorer.py --onnx   (use ONNX Runtime instead of ST)
#
# Dependencies:
#   gradio, sentence-transformers (or onnxruntime-gpu), torch, numpy, scikit-learn
#   All already present in pyproject.toml dev/embeddings groups.

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Optional

os.environ.setdefault("HF_HUB_OFFLINE", "1")

repo_root = Path(__file__).resolve().parent.parent.parent
corpus_path = repo_root / "manifest" / "corpus.sqlite"
model_id = "Qwen/Qwen3-Embedding-0.6B"

# ─────────────────────────────────────────────────────────────
# Args
# ─────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Gradio embedding explorer")
parser.add_argument("--port", type=int, default=7860)
parser.add_argument("--onnx", action="store_true", help="Use ONNX Runtime instead of sentence-transformers")
parser.add_argument("--top-k", type=int, default=10, help="Number of similar turns to return")
parser.add_argument("--share", action="store_true", help="Gradio public share link")
args = parser.parse_args()


# ─────────────────────────────────────────────────────────────
# Model loading (lazy, cached after first call)
# ─────────────────────────────────────────────────────────────
_model = None
_backend: str = "none"


def load_model():
    global _model, _backend
    if _model is not None:
        return _model, _backend

    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"

    if args.onnx:
        # ONNX Runtime CUDA path — same tensor cores, zero Python-side overhead per batch
        # Requires: uv pip install onnxruntime-gpu
        # Model ONNX export: see docs/reference/ONNX_EXPORT.md (to be created)
        onnx_path = repo_root / "models" / "qwen3_embed.onnx"
        if not onnx_path.exists():
            raise FileNotFoundError(
                f"ONNX model not found at {onnx_path}.\n"
                "Export it first:\n"
                "  uv run -c 'from optimum.exporters.onnx import main_export; "
                f"main_export(\"{model_id}\", output=\"models/qwen3_embed.onnx\")'"
            )
        import onnxruntime as ort
        sess_opts = ort.SessionOptions()
        sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        _model = ort.InferenceSession(str(onnx_path), sess_options=sess_opts, providers=providers)
        active = _model.get_providers()
        _backend = f"onnxruntime ({active[0]})"
    else:
        # sentence-transformers path (default — already validated in G9)
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(
            model_id,
            device=device,
            model_kwargs={"torch_dtype": torch.bfloat16} if device == "cuda" else {},
        )
        _backend = f"sentence-transformers ({device})"

    return _model, _backend


def embed_text(text: str) -> "np.ndarray":
    """Embed a single text string → 1024-dim float32 numpy array."""
    import numpy as np

    model, backend = load_model()

    if args.onnx:
        # ONNX Runtime inference — tokenize manually
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        enc = tokenizer(text, return_tensors="np", truncation=True, max_length=512, padding=True)
        out = model.run(None, {k: v for k, v in enc.items()})
        # Mean pool last hidden state
        hidden = out[0]  # (1, seq_len, 1024)
        vec = hidden.mean(axis=1)[0]  # (1024,)
        norm = np.linalg.norm(vec)
        return vec / (norm + 1e-9)
    else:
        vec = model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0]
        return vec


# ─────────────────────────────────────────────────────────────
# Corpus index (lazy, built once)
# ─────────────────────────────────────────────────────────────
_corpus_turns: list[dict] = []
_corpus_matrix = None  # np.ndarray (N, 1024)


def build_corpus_index():
    """Pull all instrumented turns from corpus.sqlite and embed them."""
    global _corpus_turns, _corpus_matrix

    if _corpus_matrix is not None:
        return

    import numpy as np

    if not corpus_path.exists():
        print(f"WARNING: corpus not found at {corpus_path}")
        _corpus_turns = []
        _corpus_matrix = np.zeros((0, 1024), dtype=np.float32)
        return

    con = sqlite3.connect(str(corpus_path))
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # Collect one representative text per (sessionId, turn)
    turn_map: dict[tuple[str, int], list[str]] = {}

    for row in cur.execute(
        "SELECT sessionId, turn, toolName, argsJson, resultSnippet FROM tool_calls ORDER BY sessionId, turn"
    ):
        key = (row["sessionId"], row["turn"])
        if key not in turn_map:
            turn_map[key] = []
        snippet = f"[{row['toolName']}] {(row['resultSnippet'] or '')[:200]}"
        turn_map[key].append(snippet)

    for row in cur.execute(
        "SELECT sessionId, turn, lang, preview FROM code_blocks ORDER BY sessionId, turn"
    ):
        key = (row["sessionId"], row["turn"])
        if key not in turn_map:
            turn_map[key] = []
        turn_map[key].append(f"[code:{row['lang']}] {(row['preview'] or '')[:300]}")

    for row in cur.execute(
        "SELECT sessionId, turn, command, goal FROM terminal_cmds ORDER BY sessionId, turn"
    ):
        key = (row["sessionId"], row["turn"])
        if key not in turn_map:
            turn_map[key] = []
        turn_map[key].append(f"[cmd] {row['command'][:200]}")

    con.close()

    if not turn_map:
        _corpus_turns = []
        _corpus_matrix = np.zeros((0, 1024), dtype=np.float32)
        return

    print(f"Indexing {len(turn_map)} corpus turns...")
    t0 = time.perf_counter()

    model, backend = load_model()
    keys = list(turn_map.keys())
    texts = [" | ".join(parts[:3]) for parts in turn_map.values()]

    if args.onnx:
        vecs = np.array([embed_text(t) for t in texts], dtype=np.float32)
    else:
        vecs = model.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=True)
        vecs = vecs.astype(np.float32)

    _corpus_turns = [{"session": k[0][:8], "turn": k[1], "text": t} for k, t in zip(keys, texts)]
    _corpus_matrix = vecs

    elapsed = time.perf_counter() - t0
    print(f"Corpus index ready: {len(keys)} turns in {elapsed:.1f}s via {backend}")


# ─────────────────────────────────────────────────────────────
# Search function (called by Gradio)
# ─────────────────────────────────────────────────────────────
def search_corpus(query: str, top_k: int) -> str:
    """Embed query, return top-k most similar corpus turns as markdown table."""
    if not query.strip():
        return "Enter a query above."

    import numpy as np

    try:
        build_corpus_index()
    except Exception as e:
        return f"**Index build failed:** {e}"

    if _corpus_matrix is None or _corpus_matrix.shape[0] == 0:
        return "Corpus is empty or not loaded."

    try:
        t0 = time.perf_counter()
        q_vec = embed_text(query).astype(np.float32)
        sims = _corpus_matrix @ q_vec  # cosine sim (vecs are normalized)
        top_idx = np.argsort(sims)[::-1][:top_k]
        elapsed_ms = (time.perf_counter() - t0) * 1000

        _, backend = load_model()

        lines = [
            f"**Query:** `{query[:120]}`  |  backend: `{backend}`  |  {elapsed_ms:.1f}ms\n",
            "| Rank | Session | Turn | Score | Signal |",
            "|------|---------|------|-------|--------|",
        ]
        for rank, idx in enumerate(top_idx, 1):
            entry = _corpus_turns[idx]
            score = float(sims[idx])
            signal = entry["text"][:80].replace("|", "│")
            lines.append(f"| {rank} | `{entry['session']}` | {entry['turn']} | {score:.4f} | {signal} |")

        return "\n".join(lines)

    except Exception as e:
        return f"**Search error:** {e}"


def get_status() -> str:
    """Return current model + corpus status."""
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none"
    n_turns = len(_corpus_turns)
    indexed = "not indexed" if n_turns == 0 else f"{n_turns} turns indexed"
    model_status = "not loaded" if _model is None else f"loaded via {_backend}"
    return (
        f"**GPU:** {gpu_name} ({device})  \n"
        f"**Model:** {model_id} — {model_status}  \n"
        f"**Corpus:** {indexed}  \n"
        f"**Backend:** {'ONNX Runtime' if args.onnx else 'sentence-transformers'}"
    )


def warm_up() -> str:
    """Trigger model load + corpus index. Called via UI button."""
    try:
        load_model()
        build_corpus_index()
        return get_status()
    except Exception as e:
        return f"**Warm-up failed:** {e}"


# ─────────────────────────────────────────────────────────────
# Gradio UI
# ─────────────────────────────────────────────────────────────
def build_ui():
    import gradio as gr

    with gr.Blocks(title="Chthonic Embedding Explorer", theme=gr.themes.Monochrome()) as demo:
        gr.Markdown("# Chthonic — Embedding Explorer\nLocal GPU inference via RTX 4090 tensor cores. No HF network calls.")

        with gr.Row():
            status_box = gr.Markdown(get_status())
            warm_btn = gr.Button("⚡ Load Model + Index Corpus", variant="primary")

        gr.Markdown("---")

        with gr.Row():
            with gr.Column(scale=3):
                query_box = gr.Textbox(
                    label="Query",
                    placeholder="e.g. 'vulkan compute shader euler scoring' or 'cargo build MSVC linker'",
                    lines=3,
                )
            with gr.Column(scale=1):
                top_k_slider = gr.Slider(minimum=1, maximum=50, value=args.top_k, step=1, label="Top K")
                search_btn = gr.Button("Search", variant="secondary")

        results_box = gr.Markdown("Results will appear here after warm-up.")

        warm_btn.click(fn=warm_up, outputs=status_box)
        search_btn.click(fn=search_corpus, inputs=[query_box, top_k_slider], outputs=results_box)
        query_box.submit(fn=search_corpus, inputs=[query_box, top_k_slider], outputs=results_box)

    return demo


if __name__ == "__main__":
    import gradio as gr  # validate import before spinning up
    print(f"Starting Embedding Explorer on http://localhost:{args.port}")
    print(f"Backend: {'ONNX Runtime' if args.onnx else 'sentence-transformers'}")
    print(f"Corpus: {corpus_path}")
    ui = build_ui()
    ui.launch(server_port=args.port, share=args.share, inbrowser=True)
