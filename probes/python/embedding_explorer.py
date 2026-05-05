#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @SID: EMBEDDING_EXPLORER_V2_G9
#
# LOCALHOST GRADIO — Embedding Explorer / TRT Build Pipeline
# ─────────────────────────────────────────────────────────────────────────────
# Architecture: same as A1111 / SD.NEXT with TRT — Gradio shell over a 3-tier backend
#
#   Tier 1 — sentence-transformers (default)
#     PyTorch BF16, cuda — baseline, already validated in G9
#
#   Tier 2 — ONNX Runtime + CUDAExecutionProvider  (--backend onnx)
#     No PyTorch overhead. Same tensor cores. Model must be exported to ONNX first.
#
#   Tier 3 — ONNX Runtime + TensorrtExecutionProvider  (--backend trt)
#     FP16 compiled engine, cached on disk. First run = JIT compile (~5min).
#     Subsequent runs = instant load from cache. This IS the libnvinfer.dll path.
#     Same execution contract DLSS uses — no DLL hooking, it is the public API.
#
# Build pipeline (Setup tab in UI):
#   Step 1 — Export ONNX       → models/qwen3_embed.onnx
#   Step 2 — Warm TRT engine   → models/trt_cache/*.engine (auto-compiled by ORT)
#
# Gradio tabs:
#   Setup    — pipeline builder: ONNX export + TRT warm-up + GPU status
#   Search   — live corpus similarity search (all 3 backends)
#   Bench    — latency comparison across tiers
#
# Run:
#   uv run probes/python/embedding_explorer.py
#   uv run probes/python/embedding_explorer.py --backend onnx
#   uv run probes/python/embedding_explorer.py --backend trt   (first run = engine compile)
#   uv run probes/python/embedding_explorer.py --port 7861
#
# Dependencies:
#   gradio, sentence-transformers, onnxruntime-gpu, optimum[onnxruntime-gpu], torch, numpy
#   All in pyproject.toml embeddings group.

from __future__ import annotations

import argparse
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")

repo_root = Path(__file__).resolve().parent.parent.parent
corpus_path = repo_root / "manifest" / "corpus.sqlite"
onnx_path   = repo_root / "models" / "qwen3_embed.onnx"
trt_cache_dir = repo_root / "models" / "trt_cache"
model_id = "Qwen/Qwen3-Embedding-0.6B"

# ─────────────────────────────────────────────────────────────
# Args
# ─────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(
    description="Gradio embedding explorer — same Gradio+TRT architecture as A1111/SD.NEXT"
)
parser.add_argument("--port", type=int, default=7860)
parser.add_argument(
    "--backend",
    choices=["st", "onnx", "trt"],
    default="st",
    help=(
        "st  = sentence-transformers (PyTorch BF16, CUDA) — baseline\n"
        "onnx= ONNX Runtime + CUDAExecutionProvider — no PyTorch overhead\n"
        "trt = ONNX Runtime + TensorrtExecutionProvider — FP16, engine cached, fastest\n"
        "     (first run compiles engine, ~5min; cached runs are instant)"
    ),
)
parser.add_argument("--top-k", type=int, default=10)
parser.add_argument("--share", action="store_true")
args = parser.parse_args()


# ─────────────────────────────────────────────────────────────
# Backend state (lazy-loaded, cached)
# ─────────────────────────────────────────────────────────────
_st_model   = None   # sentence-transformers SentenceTransformer
_ort_sess   = None   # onnxruntime InferenceSession (CUDA or TRT EP)
_tokenizer  = None   # HF AutoTokenizer (shared by onnx + trt paths)
_active_backend: str = "none"


def _get_device() -> str:
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


def _get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        from transformers import AutoTokenizer
        _tokenizer = AutoTokenizer.from_pretrained(model_id)
    return _tokenizer


# ── Tier 1: sentence-transformers ────────────────────────────
def _load_st():
    global _st_model, _active_backend
    if _st_model is not None:
        return
    import torch
    from sentence_transformers import SentenceTransformer
    device = _get_device()
    _st_model = SentenceTransformer(
        model_id,
        device=device,
        model_kwargs={"torch_dtype": torch.bfloat16} if device == "cuda" else {},
    )
    _active_backend = f"sentence-transformers ({device})"


# ── Tier 2: ONNX Runtime + CUDAExecutionProvider ─────────────
def _load_onnx_cuda():
    global _ort_sess, _active_backend
    if _ort_sess is not None:
        return
    if not onnx_path.exists():
        raise FileNotFoundError(f"ONNX model not found: {onnx_path}\nUse the Setup tab to export it first.")
    import onnxruntime as ort
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    _ort_sess = ort.InferenceSession(str(onnx_path), sess_options=opts, providers=providers)
    _get_tokenizer()
    _active_backend = f"onnxruntime ({_ort_sess.get_providers()[0]})"


# ── Tier 3: ONNX Runtime + TensorrtExecutionProvider ─────────
# This is the SD.NEXT/A1111 TRT pattern:
#   - First run: ORT compiles ONNX → TRT FP16 engine, saves to trt_cache_dir
#   - Subsequent runs: loads from cache (instant)
#   - Engine = libnvinfer.dll path via public API. No hooking needed.
def _load_onnx_trt():
    global _ort_sess, _active_backend
    if _ort_sess is not None:
        return
    if not onnx_path.exists():
        raise FileNotFoundError(f"ONNX model not found: {onnx_path}\nUse the Setup tab to export it first.")
    trt_cache_dir.mkdir(parents=True, exist_ok=True)
    import onnxruntime as ort
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    providers = [
        (
            "TensorrtExecutionProvider",
            {
                "trt_engine_cache_enable": True,
                "trt_engine_cache_path": str(trt_cache_dir),
                "trt_fp16_enable": True,                 # FP16 on 4th-gen tensor cores
                "trt_max_workspace_size": 4 * 1024 ** 3, # 4 GB workspace
                "trt_min_subgraph_size": 3,
                "trt_dla_enable": False,
            },
        ),
        "CUDAExecutionProvider",
        "CPUExecutionProvider",
    ]
    _ort_sess = ort.InferenceSession(str(onnx_path), sess_options=opts, providers=providers)
    _get_tokenizer()
    ep = _ort_sess.get_providers()[0]
    cached = list(trt_cache_dir.glob("*.engine"))
    _active_backend = f"onnxruntime ({ep}, {len(cached)} engine(s) cached)"


def load_backend():
    """Load the backend selected via --backend flag."""
    if args.backend == "trt":
        _load_onnx_trt()
    elif args.backend == "onnx":
        _load_onnx_cuda()
    else:
        _load_st()


def embed_text(text: str) -> "np.ndarray":
    """Embed a single string → normalized float32 (1024,) numpy array."""
    import numpy as np
    load_backend()

    if args.backend in ("onnx", "trt"):
        tok = _get_tokenizer()
        enc = tok(text, return_tensors="np", truncation=True, max_length=512, padding=True)
        out = _ort_sess.run(None, dict(enc))
        hidden = out[0]                         # (1, seq_len, hidden)
        vec = hidden.mean(axis=1)[0]            # (hidden,)
        norm = np.linalg.norm(vec)
        return (vec / (norm + 1e-9)).astype(np.float32)
    else:
        return _st_model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0].astype(np.float32)


def embed_batch(texts: list[str]) -> "np.ndarray":
    """Embed a list of strings → (N, 1024) float32 numpy array."""
    import numpy as np
    load_backend()

    if args.backend in ("onnx", "trt"):
        return np.array([embed_text(t) for t in texts], dtype=np.float32)
    else:
        return _st_model.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=True).astype(np.float32)


# ─────────────────────────────────────────────────────────────
# ONNX Export (Step 1 of build pipeline)
# ─────────────────────────────────────────────────────────────
def export_onnx() -> str:
    """Export Qwen3-Embedding-0.6B to ONNX. One-time operation, ~2min."""
    if onnx_path.exists():
        return f"✅ ONNX already exported: `{onnx_path}`"
    onnx_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from optimum.exporters.onnx import main_export  # type: ignore
        main_export(model_id, output=str(onnx_path.parent), task="feature-extraction")
        # optimum exports to a directory — find the model file
        candidates = list(onnx_path.parent.glob("*.onnx"))
        if candidates and not onnx_path.exists():
            candidates[0].rename(onnx_path)
        return f"✅ Exported to `{onnx_path}`  ({onnx_path.stat().st_size / 1024**2:.0f} MB)"
    except ImportError:
        return (
            "❌ `optimum` not installed.\n"
            "Run: `uv add optimum[onnxruntime-gpu]`  then retry."
        )
    except Exception as e:
        return f"❌ Export failed: {e}"


# ─────────────────────────────────────────────────────────────
# TRT Engine Warm-up (Step 2 of build pipeline)
# ─────────────────────────────────────────────────────────────
def warm_trt_engine() -> str:
    """
    First inference with TensorrtExecutionProvider triggers JIT compilation
    of the ONNX model to a TRT FP16 engine.  Saved to trt_cache_dir.
    This is the same mechanism SD.NEXT uses for CLIP/UNet/VAE.
    Expect ~5 min on RTX 4090.  Subsequent runs load from cache in <1s.
    """
    global _ort_sess
    if not onnx_path.exists():
        return "❌ ONNX model not found. Run Step 1 (Export ONNX) first."

    # Force fresh TRT session even if ONNX-CUDA session is cached
    _ort_sess = None
    prev = args.backend
    args.backend = "trt"  # type: ignore[assignment]
    try:
        t0 = time.perf_counter()
        _load_onnx_trt()
        # Trigger compilation with a dummy inference
        _ = embed_text("TRT engine warm-up: compiling to FP16 via libnvinfer")
        elapsed = time.perf_counter() - t0
        cached = list(trt_cache_dir.glob("*.engine"))
        return (
            f"✅ TRT engine compiled + cached in {elapsed:.1f}s\n"
            f"Engine file(s): {[f.name for f in cached]}\n"
            f"Cache: `{trt_cache_dir}`\n"
            f"Active provider: {_ort_sess.get_providers()[0]}"
        )
    except Exception as e:
        return f"❌ TRT warm-up failed: {e}"
    finally:
        args.backend = prev  # type: ignore[assignment]


# ─────────────────────────────────────────────────────────────
# Corpus index (lazy, built once)
# ─────────────────────────────────────────────────────────────
_corpus_turns: list[dict] = []
_corpus_matrix = None  # np.ndarray (N, 1024)


def build_corpus_index() -> None:
    global _corpus_turns, _corpus_matrix
    if _corpus_matrix is not None:
        return

    import numpy as np

    if not corpus_path.exists():
        _corpus_turns = []
        _corpus_matrix = np.zeros((0, 1024), dtype=np.float32)
        return

    con = sqlite3.connect(str(corpus_path))
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    turn_map: dict[tuple[str, int], list[str]] = {}

    for row in cur.execute(
        "SELECT sessionId, turn, toolName, resultSnippet FROM tool_calls ORDER BY sessionId, turn"
    ):
        key = (row["sessionId"], row["turn"])
        turn_map.setdefault(key, []).append(
            f"[{row['toolName']}] {(row['resultSnippet'] or '')[:200]}"
        )
    for row in cur.execute(
        "SELECT sessionId, turn, lang, preview FROM code_blocks ORDER BY sessionId, turn"
    ):
        key = (row["sessionId"], row["turn"])
        turn_map.setdefault(key, []).append(f"[code:{row['lang']}] {(row['preview'] or '')[:300]}")
    for row in cur.execute(
        "SELECT sessionId, turn, command FROM terminal_cmds ORDER BY sessionId, turn"
    ):
        key = (row["sessionId"], row["turn"])
        turn_map.setdefault(key, []).append(f"[cmd] {row['command'][:200]}")
    con.close()

    if not turn_map:
        _corpus_turns = []
        _corpus_matrix = np.zeros((0, 1024), dtype=np.float32)
        return

    keys  = list(turn_map.keys())
    texts = [" | ".join(parts[:3]) for parts in turn_map.values()]
    print(f"Indexing {len(keys)} corpus turns via {_active_backend}...")
    t0 = time.perf_counter()
    vecs = embed_batch(texts)
    print(f"Index ready in {time.perf_counter()-t0:.1f}s")

    _corpus_turns  = [{"session": k[0][:8], "turn": k[1], "text": t} for k, t in zip(keys, texts)]
    _corpus_matrix = vecs


# ─────────────────────────────────────────────────────────────
# Search
# ─────────────────────────────────────────────────────────────
def search_corpus(query: str, top_k: int) -> str:
    if not query.strip():
        return "Enter a query above."
    import numpy as np
    try:
        build_corpus_index()
    except Exception as e:
        return f"**Index build failed:** {e}"
    if _corpus_matrix is None or _corpus_matrix.shape[0] == 0:
        return "Corpus is empty. Click **⚡ Load** first."
    try:
        t0 = time.perf_counter()
        q_vec = embed_text(query)
        sims  = _corpus_matrix @ q_vec
        top_i = sims.argsort()[::-1][:top_k]
        ms    = (time.perf_counter() - t0) * 1000
        rows  = [
            f"**Query:** `{query[:120]}`  ·  `{_active_backend}`  ·  {ms:.1f}ms\n",
            "| # | Session | Turn | Score | Signal |",
            "|---|---------|------|-------|--------|",
        ]
        for rank, idx in enumerate(top_i, 1):
            e = _corpus_turns[idx]
            rows.append(
                f"| {rank} | `{e['session']}` | {e['turn']} | {sims[idx]:.4f} | {e['text'][:80].replace('|','│')} |"
            )
        return "\n".join(rows)
    except Exception as e:
        return f"**Search error:** {e}"


# ─────────────────────────────────────────────────────────────
# Benchmark (latency comparison across all tiers)
# ─────────────────────────────────────────────────────────────
def bench_all(text: str, n_runs: int) -> str:
    """
    Time each available backend on `n_runs` single-text inferences.
    Mirrors the benchmark SD.NEXT shows when comparing PyTorch vs ONNX vs TRT.
    """
    import numpy as np

    text = text.strip() or "The RTX 4090 tensor core path used by DLSS and this embedder is identical."
    results = []

    def _time_backend(backend_key: str, load_fn, embed_fn) -> tuple[str, float, str]:
        try:
            load_fn()
            # warmup
            embed_fn(text)
            times = []
            for _ in range(n_runs):
                t0 = time.perf_counter()
                embed_fn(text)
                times.append((time.perf_counter() - t0) * 1000)
            avg = sum(times) / len(times)
            return backend_key, avg, "✅"
        except Exception as e:
            return backend_key, 0.0, f"❌ {str(e)[:60]}"

    # --- ST ---
    old_backend = args.backend
    args.backend = "st"  # type: ignore
    label, ms, status = _time_backend(
        "sentence-transformers (PyTorch BF16)",
        _load_st,
        lambda t: (_st_model.encode([t], normalize_embeddings=True, show_progress_bar=False) if _st_model else None),
    )
    results.append((label, ms, status))

    # --- ONNX CUDA ---
    if onnx_path.exists():
        global _ort_sess, _active_backend
        _ort_sess = None
        args.backend = "onnx"  # type: ignore
        label, ms, status = _time_backend("ONNX Runtime (CUDAExecutionProvider)", _load_onnx_cuda, embed_text)
        results.append((label, ms, status))
        _ort_sess = None

    # --- TRT ---
    if onnx_path.exists() and list(trt_cache_dir.glob("*.engine")):
        args.backend = "trt"  # type: ignore
        label, ms, status = _time_backend("ONNX Runtime (TensorrtExecutionProvider FP16)", _load_onnx_trt, embed_text)
        results.append((label, ms, status))
        _ort_sess = None

    args.backend = old_backend  # type: ignore

    # restore original backend for subsequent searches
    load_backend()

    rows = [
        f"**Benchmark** — `n={n_runs}` runs per backend  ·  text len={len(text)}\n",
        "| Backend | Avg ms | Status |",
        "|---------|--------|--------|",
    ]
    fastest = min((r for r in results if r[2] == "✅"), key=lambda r: r[1], default=None)
    for label, ms, status in results:
        suffix = "  **← fastest**" if (fastest and label == fastest[0]) else ""
        rows.append(f"| {label} | {ms:.1f} | {status}{suffix} |")

    if fastest:
        speedups = []
        base_ms = next(r[1] for r in results if "sentence-transformers" in r[0])
        for label, ms, status in results:
            if status == "✅" and ms > 0 and label != fastest[0]:
                speedups.append(f"`{label.split('(')[1].rstrip(')')}`→`{fastest[0].split('(')[1].rstrip(')')}`  {base_ms/ms:.2f}×")
        if speedups:
            rows.append("\n**Speedup:** " + "  ·  ".join(speedups))

    rows.append("\n> TRT FP16 uses the same hardware path as DLSS / libnvinfer.dll — no DLL hooking required.")
    return "\n".join(rows)


# ─────────────────────────────────────────────────────────────
# Status helpers
# ─────────────────────────────────────────────────────────────
def get_status() -> str:
    import torch
    device    = _get_device()
    gpu_name  = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none"
    vram_used = ""
    if torch.cuda.is_available():
        mb_used  = torch.cuda.memory_allocated(0) / 1024**2
        mb_total = torch.cuda.get_device_properties(0).total_memory / 1024**2
        vram_used = f"  ·  VRAM {mb_used:.0f}/{mb_total:.0f} MB"
    onnx_ok  = "✅" if onnx_path.exists() else "❌ not exported"
    trt_ok   = f"✅ {len(list(trt_cache_dir.glob('*.engine')))} engine(s)" if trt_cache_dir.exists() and list(trt_cache_dir.glob("*.engine")) else "❌ not compiled"
    n_turns  = len(_corpus_turns)
    indexed  = f"{n_turns} turns indexed" if n_turns else "not indexed"

    return (
        f"**GPU:** {gpu_name} ({device}){vram_used}  \n"
        f"**Backend (active):** `{_active_backend if _active_backend != 'none' else args.backend}`  \n"
        f"**Model:** `{model_id}`  \n"
        f"**ONNX:** {onnx_ok}  \n"
        f"**TRT engine:** {trt_ok}  \n"
        f"**Corpus:** {indexed}"
    )


def do_warm_up() -> str:
    try:
        load_backend()
        build_corpus_index()
        return get_status()
    except Exception as e:
        return f"**Warm-up failed:** {e}"


# ─────────────────────────────────────────────────────────────
# Gradio UI — 3 tabs, same pattern as A1111/SD.NEXT
# ─────────────────────────────────────────────────────────────
def build_ui():
    import gradio as gr
    theme = gr.themes.Monochrome()

    with gr.Blocks(title="Chthonic — Embedding Explorer", theme=theme) as demo:

        gr.Markdown(
            "# Chthonic — Embedding Explorer\n"
            "Local GPU inference · RTX 4090 tensor cores · same Gradio+TRT architecture as A1111/SD.NEXT  \n"
            "> **Tier 1** `sentence-transformers` (PyTorch BF16)  ·  "
            "**Tier 2** `ONNX Runtime + CUDA EP`  ·  "
            "**Tier 3** `ONNX Runtime + TRT EP (FP16, engine cached)`"
        )

        # ── Tab 1: Setup / Build Pipeline ──────────────────────
        with gr.Tab("⚙ Setup"):
            gr.Markdown(
                "### Build Pipeline\n"
                "Mirrors the SD.NEXT TRT tab: export → compile → cached engine.  \n"
                "After Step 2, the TRT engine loads in <1s on every subsequent run."
            )
            status_md = gr.Markdown(get_status())
            gr.Markdown("---")

            with gr.Row():
                warm_btn   = gr.Button("⚡ Load Model + Index Corpus", variant="primary")
                refresh_btn = gr.Button("↻ Refresh Status")

            gr.Markdown("---")
            gr.Markdown(
                "**Step 1 — Export ONNX**  \n"
                f"Exports `{model_id}` to `models/qwen3_embed.onnx` via `optimum`.  \n"
                "Required for Tier 2 (ONNX CUDA) and Tier 3 (TRT). One-time, ~2min."
            )
            with gr.Row():
                export_btn  = gr.Button("📦 Export ONNX", variant="secondary")
            export_out  = gr.Markdown()

            gr.Markdown(
                "**Step 2 — Build TRT Engine**  \n"
                "ONNX Runtime compiles the ONNX model to a FP16 TRT engine via `libnvinfer.dll`.  \n"
                "Same mechanism DLSS uses — public TRT API, no hooking. First run ~5min, cached forever."
            )
            with gr.Row():
                trt_btn = gr.Button("🔥 Compile TRT Engine (FP16)", variant="secondary")
            trt_out = gr.Markdown()

            warm_btn.click(fn=do_warm_up, outputs=status_md)
            refresh_btn.click(fn=get_status, outputs=status_md)
            export_btn.click(fn=export_onnx, outputs=export_out)
            trt_btn.click(fn=warm_trt_engine, outputs=trt_out)

        # ── Tab 2: Corpus Search ────────────────────────────────
        with gr.Tab("🔍 Search Corpus"):
            gr.Markdown(
                "Query the session corpus via cosine similarity.  \n"
                "Click **⚡ Load** in Setup first to index corpus turns."
            )
            with gr.Row():
                with gr.Column(scale=3):
                    query_box = gr.Textbox(
                        label="Query",
                        placeholder="e.g. 'vulkan compute shader euler scoring'  ·  'cargo MSVC linker error'",
                        lines=3,
                    )
                with gr.Column(scale=1):
                    topk_slider = gr.Slider(1, 50, value=args.top_k, step=1, label="Top K")
                    search_btn  = gr.Button("Search", variant="secondary")

            results_md = gr.Markdown("Results appear here.")
            search_btn.click(fn=search_corpus, inputs=[query_box, topk_slider], outputs=results_md)
            query_box.submit(fn=search_corpus, inputs=[query_box, topk_slider], outputs=results_md)

        # ── Tab 3: Benchmark ────────────────────────────────────
        with gr.Tab("⏱ Benchmark"):
            gr.Markdown(
                "Compare latency across all available backends.  \n"
                "`ONNX CUDA EP` and `TRT EP` require ONNX export (Step 1) and TRT compile (Step 2) respectively."
            )
            with gr.Row():
                bench_text = gr.Textbox(
                    label="Benchmark text",
                    value="The RTX 4090 tensor core path used by DLSS and this embedder is identical.",
                    lines=2,
                )
                n_runs_slider = gr.Slider(1, 50, value=10, step=1, label="Runs per backend")
            bench_btn = gr.Button("▶ Run Benchmark", variant="primary")
            bench_md  = gr.Markdown("Results appear here.")
            bench_btn.click(fn=bench_all, inputs=[bench_text, n_runs_slider], outputs=bench_md)

    return demo


if __name__ == "__main__":
    import gradio  # validate import
    print(f"Starting Embedding Explorer  http://localhost:{args.port}")
    print(f"Active backend: {args.backend}")
    print(f"ONNX model:     {'exists' if onnx_path.exists() else 'not exported (use Setup tab)'}")
    trt_engines = list(trt_cache_dir.glob("*.engine")) if trt_cache_dir.exists() else []
    print(f"TRT engines:    {len(trt_engines)} cached")
    ui = build_ui()
    ui.launch(server_port=args.port, share=args.share, inbrowser=True)

