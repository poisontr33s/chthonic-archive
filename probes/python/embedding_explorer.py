#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @SID: EMBEDDING_EXPLORER_V3_G9
#
# LOCALHOST GRADIO — Multi-Model Embedding Explorer
# ─────────────────────────────────────────────────────────────────────────────
# Architecture: same hook pattern as A1111 / SD.NEXT / ComfyUI
#
#   How A1111/SD.NEXT discover models:
#     scan models/ dir → read config.json / model_index.json → populate dropdown
#   How WE discover embedding models (same pattern):
#     scan ~/.cache/huggingface/hub/models--* → read config.json +
#       sentence_bert_config.json + 1_Pooling/config.json → populate model dropdown
#
#   The "libraries that pull LORAs/embeddings/encoders":
#     sentence_transformers.SentenceTransformer.from_pretrained()
#     transformers.AutoModel.from_pretrained()
#     huggingface_hub.snapshot_download()
#   All hit the same HF Hub infrastructure. We hook the same way.
#
# Three backends (per model):
#   st   — sentence-transformers BF16 CUDA (baseline)
#   onnx — ONNX Runtime + CUDAExecutionProvider
#   trt  — ONNX Runtime + TensorrtExecutionProvider FP16 (engine cached per model)
#
# Four Gradio tabs:
#   🧩 Models  — HF cache scanner, metadata card, model selector, Pull from Hub
#   ⚙ Setup   — per-model ONNX export + TRT compile pipeline
#   🔍 Search  — cosine similarity over corpus.sqlite turns
#   ⏱ Bench   — cross-model × cross-backend latency table
#
# Per-model ONNX/TRT paths:
#   models/<Org--ModelName>/model.onnx
#   models/<Org--ModelName>/trt_cache/*.engine
#
# Run:
#   uv run probes/python/embedding_explorer.py
#   uv run probes/python/embedding_explorer.py --model BAAI/bge-large-en-v1.5
#   uv run probes/python/embedding_explorer.py --backend trt
#   uv run probes/python/embedding_explorer.py --port 7861
#
# Dependencies:
#   gradio, sentence-transformers, onnxruntime-gpu, optimum[onnxruntime-gpu],
#   torch, numpy, huggingface_hub, transformers
#   All in pyproject.toml embeddings group.

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

os.environ.setdefault("HF_HUB_OFFLINE", "1")

repo_root   = Path(__file__).resolve().parent.parent.parent
corpus_path = repo_root / "manifest" / "corpus.sqlite"

# ─────────────────────────────────────────────────────────────
# Args
# ─────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(
    description="Multi-model Gradio embedding explorer — same HF Hub hook as A1111/SD.NEXT/ComfyUI",
    formatter_class=argparse.RawTextHelpFormatter,
)
parser.add_argument("--port",    type=int,  default=7860)
parser.add_argument("--top-k",  type=int,  default=10)
parser.add_argument("--share",  action="store_true")
parser.add_argument(
    "--backend", choices=["st", "onnx", "trt"], default="st",
    help=(
        "st   = sentence-transformers BF16 CUDA (default, always works)\n"
        "onnx = ONNX Runtime + CUDAExecutionProvider (export ONNX first)\n"
        "trt  = ONNX Runtime + TensorrtExecutionProvider FP16 (compile engine first)"
    ),
)
parser.add_argument(
    "--model", default=None,
    help="Force a specific model ID as active (default: auto-select from HF cache scan)",
)
args = parser.parse_args()


# ─────────────────────────────────────────────────────────────
# EmbedModelSpec — metadata read from HF cache files
# Same files A1111/ComfyUI read when populating their model dropdowns:
#   config.json → hidden_size, max_position_embeddings, architectures
#   tokenizer_config.json → model_max_length
#   sentence_bert_config.json → word_embedding_dimension, max_seq_length (ST models)
#   1_Pooling/config.json → pooling_mode_mean/cls/max (ST models)
#   README.md → MTEB average score (model card frontmatter)
# ─────────────────────────────────────────────────────────────
@dataclass
class EmbedModelSpec:
    model_id:   str
    hidden_size: int             = 768
    max_seq_len: int             = 512
    pooling:     str             = "mean"   # mean | cls | max | weightedmean
    model_type:  str             = "auto"   # sentence-transformers | auto
    local_path:  Path | None     = None     # snapshot dir in HF hub cache
    mteb_score:  float           = 0.0

    @property
    def display_name(self) -> str:
        short = self.model_id.split("/")[-1]
        return f"{short}  [{self.hidden_size}d · {self.pooling} · {self.max_seq_len}tok]"

    @property
    def slug(self) -> str:
        """Org/ModelName → Org--ModelName  (filesystem-safe, mirrors HF cache convention)"""
        return self.model_id.replace("/", "--")

    @property
    def onnx_path(self) -> Path:
        return repo_root / "models" / self.slug / "model.onnx"

    @property
    def trt_cache(self) -> Path:
        return repo_root / "models" / self.slug / "trt_cache"

    def metadata_card(self) -> str:
        src   = "`sentence-transformers`" if self.model_type == "sentence-transformers" else "`transformers` / auto"
        local = f"`{self.local_path}`" if self.local_path else "❌ not in local cache"
        onnx  = "✅" if self.onnx_path.exists() else "❌ not exported"
        engines = list(self.trt_cache.glob("*.engine")) if self.trt_cache.exists() else []
        trt   = f"✅ {len(engines)} engine(s)" if engines else "❌ not compiled"
        mteb  = f"{self.mteb_score:.2f}" if self.mteb_score else "—"
        return (
            f"| Field | Value |\n"
            f"|-------|-------|\n"
            f"| Model ID | `{self.model_id}` |\n"
            f"| Hidden size | **{self.hidden_size}** |\n"
            f"| Max seq len | {self.max_seq_len} tokens |\n"
            f"| Pooling | `{self.pooling}` |\n"
            f"| Library | {src} |\n"
            f"| MTEB avg | {mteb} |\n"
            f"| Local cache | {local} |\n"
            f"| ONNX | {onnx} |\n"
            f"| TRT engine | {trt} |"
        )


# ─────────────────────────────────────────────────────────────
# HF Cache Scanner
# Mirrors what A1111/SD.NEXT/ComfyUI do when they scan their models/ folder
# ─────────────────────────────────────────────────────────────
def _hf_cache_root() -> Path:
    """Respect HF_HOME / HUGGINGFACE_HUB_CACHE exactly as huggingface_hub does."""
    hf_home = os.environ.get(
        "HF_HOME",
        os.path.join(os.path.expanduser("~"), ".cache", "huggingface"),
    )
    return Path(os.environ.get("HUGGINGFACE_HUB_CACHE", os.path.join(hf_home, "hub")))


def _read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _extract_pooling(snap: Path) -> str:
    """Read 1_Pooling/config.json — written by sentence-transformers on export."""
    cfg = _read_json(snap / "1_Pooling" / "config.json")
    if cfg.get("pooling_mode_cls_token"):         return "cls"
    if cfg.get("pooling_mode_max_tokens"):         return "max"
    if cfg.get("pooling_mode_weightedmean_tokens"): return "weightedmean"
    return "mean"


def _extract_mteb(snap: Path) -> float:
    """Scan README.md for an MTEB average score if the model card mentions one."""
    readme = snap / "README.md"
    if not readme.exists():
        return 0.0
    try:
        text = readme.read_text(encoding="utf-8", errors="ignore")[:6000]
        for pat in [
            r"Average.*?:\s*(\d+\.\d+)",
            r"avg_score[\"']?\s*:\s*(\d+\.\d+)",
            r"MTEB.*?(\d+\.\d+)",
        ]:
            m = re.search(pat, text)
            if m:
                return float(m.group(1))
    except Exception:
        pass
    return 0.0


# Keywords that flag a model as embedding-capable
_EMBED_SIGNALS = ("embed", "e5", "bge", "gte", "nomic", "minilm", "mpnet",
                  "simcse", "roberta", "deberta", "sentence", "retriev")

def scan_hf_cache(extra_ids: list[str] | None = None) -> dict[str, EmbedModelSpec]:
    """
    Scan the local HF hub cache for embedding-capable models.
    Returns dict[model_id → EmbedModelSpec].

    Detection logic (same heuristic ComfyUI uses for model type detection):
      - has sentence_bert_config.json or modules.json → sentence-transformers model → include
      - model_id or architecture name contains an embedding keyword → include
      - otherwise → skip (weights-only LLMs, vision models, etc.)
    """
    cache = _hf_cache_root()
    specs: dict[str, EmbedModelSpec] = {}

    if cache.exists():
        for model_dir in sorted(cache.glob("models--*")):
            # Reconstruct model_id: models--Org--Name → Org/Name
            raw = model_dir.name[len("models--"):]
            model_id = raw.replace("--", "/", 1)

            snapshots_dir = model_dir / "snapshots"
            if not snapshots_dir.exists():
                continue
            snap_dirs = sorted(
                snapshots_dir.iterdir(),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if not snap_dirs:
                continue
            snap = snap_dirs[0]

            # Read config.json (universal HF format)
            cfg    = _read_json(snap / "config.json")
            hidden = cfg.get("hidden_size", cfg.get("d_model", 768))
            max_p  = cfg.get("max_position_embeddings", 512)
            archs  = " ".join(cfg.get("architectures", [])).lower()
            mtype  = cfg.get("model_type", "").lower()

            # Read tokenizer_config.json (may have tighter max_seq_length)
            tok_cfg  = _read_json(snap / "tokenizer_config.json")
            max_tok  = tok_cfg.get("model_max_length", max_p)
            if isinstance(max_tok, (int, float)) and max_tok > 32768:
                max_tok = 512  # some models set 999999999

            model_type = "auto"
            st_cfg = _read_json(snap / "sentence_bert_config.json")
            if st_cfg or (snap / "modules.json").exists():
                model_type = "sentence-transformers"
                if "word_embedding_dimension" in st_cfg:
                    hidden = st_cfg["word_embedding_dimension"]
                if "max_seq_length" in st_cfg:
                    max_tok = st_cfg["max_seq_length"]

            # Embedding signal check
            signals = [model_id.lower(), archs, mtype]
            is_embed = (
                model_type == "sentence-transformers"
                or any(kw in s for kw in _EMBED_SIGNALS for s in signals)
            )
            if not is_embed:
                continue

            pooling = _extract_pooling(snap)
            mteb    = _extract_mteb(snap)

            specs[model_id] = EmbedModelSpec(
                model_id   = model_id,
                hidden_size= int(hidden) if hidden else 768,
                max_seq_len= int(max_tok) if max_tok else 512,
                pooling    = pooling,
                model_type = model_type,
                local_path = snap,
                mteb_score = mteb,
            )

    # Manually specified models (not necessarily cached yet)
    for mid in (extra_ids or []):
        mid = (mid or "").strip()
        if mid and mid not in specs:
            specs[mid] = EmbedModelSpec(model_id=mid)

    return specs


# ─────────────────────────────────────────────────────────────
# Per-model backend state (lazy-loaded, keyed on model_id)
# ─────────────────────────────────────────────────────────────
@dataclass
class ModelBackend:
    spec:       EmbedModelSpec
    st_model:   Any = None    # SentenceTransformer
    ort_sess:   Any = None    # onnxruntime.InferenceSession
    tokenizer:  Any = None    # transformers.AutoTokenizer
    active_ep:  str = "none"


_registry:        dict[str, EmbedModelSpec] = {}
_backends:        dict[str, ModelBackend]   = {}
_active_model_id: str                       = ""


def _active_spec() -> EmbedModelSpec:
    return _registry.get(_active_model_id) or EmbedModelSpec(model_id="Qwen/Qwen3-Embedding-0.6B")


def _active_be() -> ModelBackend:
    spec = _active_spec()
    return _backends.setdefault(spec.model_id, ModelBackend(spec=spec))


def _tokenizer_for(spec: EmbedModelSpec) -> Any:
    be = _backends.setdefault(spec.model_id, ModelBackend(spec=spec))
    if be.tokenizer is None:
        from transformers import AutoTokenizer
        be.tokenizer = AutoTokenizer.from_pretrained(spec.model_id)
    return be.tokenizer


# ─────────────────────────────────────────────────────────────
# Tier loaders
# ─────────────────────────────────────────────────────────────
def _load_st(spec: EmbedModelSpec) -> ModelBackend:
    be = _backends.setdefault(spec.model_id, ModelBackend(spec=spec))
    if be.st_model is not None:
        return be
    import torch
    from sentence_transformers import SentenceTransformer
    device = "cuda" if torch.cuda.is_available() else "cpu"
    be.st_model = SentenceTransformer(
        spec.model_id, device=device,
        model_kwargs={"torch_dtype": torch.bfloat16} if device == "cuda" else {},
    )
    be.active_ep = f"sentence-transformers ({device})"
    return be


def _load_ort(spec: EmbedModelSpec, use_trt: bool) -> ModelBackend:
    be = _backends.setdefault(spec.model_id, ModelBackend(spec=spec))
    if be.ort_sess is not None:
        return be
    if not spec.onnx_path.exists():
        raise FileNotFoundError(
            f"ONNX model not found: {spec.onnx_path}\n"
            "Go to Models tab → select this model → Setup tab → Export ONNX."
        )
    spec.trt_cache.mkdir(parents=True, exist_ok=True)
    import onnxruntime as ort
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    if use_trt:
        providers = [
            ("TensorrtExecutionProvider", {
                "trt_engine_cache_enable":  True,
                "trt_engine_cache_path":    str(spec.trt_cache),
                "trt_fp16_enable":          True,
                "trt_max_workspace_size":   4 * 1024 ** 3,
                "trt_min_subgraph_size":    3,
            }),
            "CUDAExecutionProvider",
            "CPUExecutionProvider",
        ]
    else:
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    be.ort_sess = ort.InferenceSession(str(spec.onnx_path), sess_options=opts, providers=providers)
    _tokenizer_for(spec)
    be.active_ep = f"onnxruntime ({be.ort_sess.get_providers()[0]})"
    return be


def load_model(model_id: str | None = None, backend: str | None = None) -> ModelBackend:
    global _active_model_id
    spec = _registry.get(model_id or _active_model_id) or _active_spec()
    _active_model_id = spec.model_id
    bk = backend or args.backend
    if   bk == "trt":  return _load_ort(spec, use_trt=True)
    elif bk == "onnx": return _load_ort(spec, use_trt=False)
    else:              return _load_st(spec)


# ─────────────────────────────────────────────────────────────
# Embedding — pooling-strategy-aware
# ─────────────────────────────────────────────────────────────
def _pool(hidden: "np.ndarray", pooling: str) -> "np.ndarray":
    """(1, seq, dim) → (dim,)"""
    import numpy as np
    if   pooling == "cls": return hidden[0, 0, :]
    elif pooling == "max":  return hidden[0].max(axis=0)
    else:                   return hidden[0].mean(axis=0)   # mean / weightedmean fallback


def embed_text(text: str, model_id: str | None = None, backend: str | None = None) -> "np.ndarray":
    import numpy as np
    be = load_model(model_id, backend)
    bk = backend or args.backend
    if bk in ("onnx", "trt") and be.ort_sess is not None:
        tok = _tokenizer_for(be.spec)
        enc = tok(text, return_tensors="np", truncation=True,
                  max_length=min(be.spec.max_seq_len, 512), padding=True)
        out  = be.ort_sess.run(None, dict(enc))
        vec  = _pool(out[0], be.spec.pooling)
        norm = np.linalg.norm(vec)
        return (vec / (norm + 1e-9)).astype(np.float32)
    else:
        return be.st_model.encode(
            [text], normalize_embeddings=True, show_progress_bar=False
        )[0].astype(np.float32)


def embed_batch(texts: list[str], model_id: str | None = None, backend: str | None = None) -> "np.ndarray":
    import numpy as np
    be = load_model(model_id, backend)
    bk = backend or args.backend
    if bk in ("onnx", "trt"):
        return np.array([embed_text(t, model_id, backend) for t in texts], dtype=np.float32)
    else:
        return be.st_model.encode(
            texts, normalize_embeddings=True, batch_size=64, show_progress_bar=True
        ).astype(np.float32)


# ─────────────────────────────────────────────────────────────
# ONNX Export  (per-model, writes to models/<slug>/model.onnx)
# Exactly how SD.NEXT exports its UNet/CLIP/VAE to ONNX before TRT compile
# ─────────────────────────────────────────────────────────────
def export_onnx(model_id: str | None = None) -> str:
    spec = _registry.get(model_id or _active_model_id) or _active_spec()
    if spec.onnx_path.exists():
        return f"✅ Already exported: `{spec.onnx_path}`"
    spec.onnx_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from optimum.exporters.onnx import main_export  # type: ignore
        main_export(spec.model_id, output=str(spec.onnx_path.parent), task="feature-extraction")
        # optimum exports to dir; rename canonical ONNX if needed
        candidates = sorted(spec.onnx_path.parent.glob("*.onnx"), key=lambda p: p.stat().st_size, reverse=True)
        if candidates and not spec.onnx_path.exists():
            candidates[0].rename(spec.onnx_path)
        sz = spec.onnx_path.stat().st_size / 1024 ** 2
        return f"✅ `{spec.model_id}` → `{spec.onnx_path}`  ({sz:.0f} MB)"
    except ImportError:
        return "❌ `optimum` missing — run: `uv add optimum[onnxruntime-gpu]`"
    except Exception as e:
        return f"❌ Export failed: {e}"


# ─────────────────────────────────────────────────────────────
# TRT Compile  (per-model, writes .engine to models/<slug>/trt_cache/)
# Mirrors SD.NEXT's "Build TRT" button: first inference → JIT compile → cache
# ─────────────────────────────────────────────────────────────
def compile_trt(model_id: str | None = None) -> str:
    spec = _registry.get(model_id or _active_model_id) or _active_spec()
    if not spec.onnx_path.exists():
        return f"❌ ONNX not found for `{spec.model_id}`. Export first."
    # Reset ORT session to force fresh TRT EP load
    if spec.model_id in _backends:
        _backends[spec.model_id].ort_sess = None
    try:
        t0 = time.perf_counter()
        be = _load_ort(spec, use_trt=True)
        _ = embed_text("TRT compile warmup — FP16 via libnvinfer", spec.model_id, "trt")
        elapsed = time.perf_counter() - t0
        engines = list(spec.trt_cache.glob("*.engine"))
        return (
            f"✅ TRT engine compiled in {elapsed:.1f}s  \n"
            f"Engine(s): `{[e.name for e in engines]}`  \n"
            f"Cache: `{spec.trt_cache}`  \n"
            f"EP: `{be.active_ep}`"
        )
    except Exception as e:
        return f"❌ TRT compile failed: {e}"


# ─────────────────────────────────────────────────────────────
# HF Hub Pull  (same snapshot_download A1111/ComfyUI use for new model downloads)
# ─────────────────────────────────────────────────────────────
def pull_model(model_id: str) -> str:
    model_id = (model_id or "").strip()
    if not model_id:
        return "Enter a model ID."
    try:
        # Lift offline mode temporarily — the pull IS the point
        saved = os.environ.pop("HF_HUB_OFFLINE", None)
        from huggingface_hub import snapshot_download  # type: ignore
        path = snapshot_download(model_id, ignore_patterns=["*.msgpack", "flax_model*", "tf_model*"])
        if saved is not None:
            os.environ["HF_HUB_OFFLINE"] = saved
        # Re-scan and add to registry
        new = scan_hf_cache([model_id])
        _registry.update(new)
        spec = _registry.get(model_id, EmbedModelSpec(model_id=model_id))
        return f"✅ Downloaded `{model_id}` → `{path}`\n\n{spec.metadata_card()}"
    except Exception as e:
        return f"❌ Pull failed: {e}"


# ─────────────────────────────────────────────────────────────
# Corpus index  (keyed on model_id:backend — same model in two backends = two caches)
# ─────────────────────────────────────────────────────────────
_corpus_cache: dict[str, tuple[list[dict], Any]] = {}   # "model_id:backend" → (turns, matrix)


def _ckey() -> str:
    return f"{_active_model_id}:{args.backend}"


def build_corpus_index() -> None:
    import numpy as np
    key = _ckey()
    if key in _corpus_cache:
        return
    spec = _active_spec()
    if not corpus_path.exists():
        _corpus_cache[key] = ([], np.zeros((0, spec.hidden_size), dtype=np.float32))
        return

    con = sqlite3.connect(str(corpus_path))
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    turn_map: dict[tuple[str, int], list[str]] = {}

    for row in cur.execute("SELECT sessionId, turn, toolName, resultSnippet FROM tool_calls ORDER BY sessionId, turn"):
        k = (row["sessionId"], row["turn"])
        turn_map.setdefault(k, []).append(f"[{row['toolName']}] {(row['resultSnippet'] or '')[:200]}")
    for row in cur.execute("SELECT sessionId, turn, lang, preview FROM code_blocks ORDER BY sessionId, turn"):
        k = (row["sessionId"], row["turn"])
        turn_map.setdefault(k, []).append(f"[code:{row['lang']}] {(row['preview'] or '')[:300]}")
    for row in cur.execute("SELECT sessionId, turn, command FROM terminal_cmds ORDER BY sessionId, turn"):
        k = (row["sessionId"], row["turn"])
        turn_map.setdefault(k, []).append(f"[cmd] {row['command'][:200]}")
    con.close()

    if not turn_map:
        _corpus_cache[key] = ([], np.zeros((0, spec.hidden_size), dtype=np.float32))
        return

    keys  = list(turn_map.keys())
    texts = [" | ".join(p[:3]) for p in turn_map.values()]
    print(f"[{spec.model_id}:{args.backend}] indexing {len(keys)} turns...")
    t0 = time.perf_counter()
    vecs  = embed_batch(texts)
    turns = [{"session": k[0][:8], "turn": k[1], "text": t} for k, t in zip(keys, texts)]
    print(f"[{spec.model_id}:{args.backend}] ready in {time.perf_counter()-t0:.1f}s")
    _corpus_cache[key] = (turns, vecs)


# ─────────────────────────────────────────────────────────────
# Search
# ─────────────────────────────────────────────────────────────
def search_corpus(query: str, top_k: int) -> str:
    if not query.strip():
        return "Enter a query."
    import numpy as np
    try:
        load_model()
        build_corpus_index()
    except Exception as e:
        return f"**Load failed:** {e}"
    turns, matrix = _corpus_cache.get(_ckey(), ([], None))
    if matrix is None or matrix.shape[0] == 0:
        return "Corpus not indexed. Click ⚡ Load in Setup."
    try:
        t0   = time.perf_counter()
        q    = embed_text(query)
        sims = matrix @ q
        top  = sims.argsort()[::-1][:top_k]
        ms   = (time.perf_counter() - t0) * 1000
        be   = _active_be()
        rows = [
            f"**Query:** `{query[:100]}`  ·  `{be.active_ep}`  ·  {ms:.1f}ms  ·  {_active_model_id}\n",
            "| # | Session | Turn | Score | Signal |",
            "|---|---------|------|-------|--------|",
        ]
        for rank, idx in enumerate(top, 1):
            e = turns[idx]
            rows.append(f"| {rank} | `{e['session']}` | {e['turn']} | {sims[idx]:.4f} | {e['text'][:80].replace('|','│')} |")
        return "\n".join(rows)
    except Exception as e:
        return f"**Search error:** {e}"


# ─────────────────────────────────────────────────────────────
# Benchmark  (cross-model × cross-backend)
# Same table SD.NEXT shows when comparing PyTorch/ONNX/TRT paths
# ─────────────────────────────────────────────────────────────
def _time_one(text: str, n: int, mid: str, bk: str) -> tuple[float, str]:
    try:
        load_model(mid, bk)
        embed_text(text, mid, bk)   # warmup
        t0 = time.perf_counter()
        for _ in range(n): embed_text(text, mid, bk)
        return (time.perf_counter() - t0) * 1000 / n, "✅"
    except Exception as e:
        return 0.0, f"❌ {str(e)[:60]}"


def bench_all(text: str, n_runs: int) -> str:
    text = text.strip() or "RTX 4090 tensor core embedding benchmark"
    rows = [
        f"**Benchmark** — `n={n_runs}` per backend  ·  len={len(text)}\n",
        "| Model | Backend | Avg ms | Dim | Status |",
        "|-------|---------|--------|-----|--------|",
    ]
    results = []
    for mid, spec in _registry.items():
        for bk, label in [("st", "ST BF16"), ("onnx", "ONNX CUDA EP"), ("trt", "ONNX TRT FP16")]:
            if bk in ("onnx", "trt") and not spec.onnx_path.exists():
                rows.append(f"| `{spec.slug[:28]}` | {label} | — | {spec.hidden_size} | ⚠ no ONNX |")
                continue
            if bk == "trt" and not list(spec.trt_cache.glob("*.engine")):
                rows.append(f"| `{spec.slug[:28]}` | {label} | — | {spec.hidden_size} | ⚠ no engine |")
                continue
            ms, status = _time_one(text, n_runs, mid, bk)
            results.append((mid, label, ms, spec.hidden_size, status))
            rows.append(f"| `{spec.slug[:28]}` | {label} | {ms:.1f} | {spec.hidden_size} | {status} |")
    ok = [r for r in results if r[4] == "✅"]
    if ok:
        fastest = min(ok, key=lambda r: r[2])
        rows.append(f"\n**Fastest:** `{fastest[0]}` via `{fastest[1]}` → **{fastest[2]:.1f}ms**")
    return "\n".join(rows)


# ─────────────────────────────────────────────────────────────
# Status
# ─────────────────────────────────────────────────────────────
def full_status() -> str:
    import torch
    gpu  = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none"
    vram = ""
    if torch.cuda.is_available():
        used  = torch.cuda.memory_allocated(0) / 1024 ** 2
        total = torch.cuda.get_device_properties(0).total_memory / 1024 ** 2
        vram  = f"  ·  VRAM {used:.0f}/{total:.0f} MB"
    spec   = _active_spec()
    loaded = sum(1 for be in _backends.values() if be.st_model or be.ort_sess)
    return (
        f"**GPU:** {gpu}{vram}  \n"
        f"**Active model:** `{spec.model_id}` ({spec.hidden_size}d · {spec.pooling})  \n"
        f"**Backend:** `{args.backend}`  \n"
        f"**Registry:** {len(_registry)} model(s) discovered  ·  {loaded} loaded  \n"
        f"**Corpus caches:** {len(_corpus_cache)} keyed"
    )


def warm_up() -> str:
    try:
        load_model()
        build_corpus_index()
        return full_status()
    except Exception as e:
        return f"**Warm-up failed:** {e}\n\n{full_status()}"


# ─────────────────────────────────────────────────────────────
# Gradio UI  (4 tabs)
# ─────────────────────────────────────────────────────────────
def build_ui():
    import gradio as gr
    global _active_model_id

    choices  = [(s.display_name, mid) for mid, s in _registry.items()] or [("(none)", "")]
    default  = _active_model_id or (list(_registry.keys())[0] if _registry else "")

    with gr.Blocks(title="Chthonic — Embedding Explorer", theme=gr.themes.Monochrome()) as demo:

        gr.Markdown(
            "# Chthonic — Embedding Explorer\n"
            "Multi-model · RTX 4090 · same HF Hub hook as A1111/SD.NEXT/ComfyUI  \n"
            "> Scans local HF cache → reads `config.json` + `sentence_bert_config.json` + `1_Pooling/config.json` "
            "→ model dropdown + metadata. Per-model ONNX export + TRT FP16 engine cache."
        )

        # ── Tab 1: Models ─────────────────────────────────────
        with gr.Tab("🧩 Models"):
            gr.Markdown(
                "### Discovered Models\n"
                "Scanned from your local HF hub cache. Select one to see its metadata card.  \n"
                "**Pull** downloads new models via `huggingface_hub.snapshot_download` — "
                "the same function A1111/ComfyUI/SD.NEXT call when you add a new model."
            )
            with gr.Row():
                model_dd   = gr.Dropdown(choices=choices, value=default, label="Active Model", allow_custom_value=True)
                set_btn    = gr.Button("✔ Set Active", variant="primary")
            meta_md = gr.Markdown(
                _registry[default].metadata_card() if default in _registry else "No model selected."
            )
            gr.Markdown("---")
            gr.Markdown(
                "### Pull New Model  \n"
                "Popular embedding models (all free, all on HF Hub — same repos A1111 links to):  \n"
                "`sentence-transformers/all-MiniLM-L6-v2` (80MB, 384d) · "
                "`BAAI/bge-large-en-v1.5` (1.3GB, 1024d) · "
                "`nomic-ai/nomic-embed-text-v1.5` (548MB, 768d) · "
                "`mixedbread-ai/mxbai-embed-large-v1` (1.3GB, 1024d) · "
                "`thenlper/gte-large` (1.3GB, 1024d)"
            )
            with gr.Row():
                pull_box = gr.Textbox(label="Model ID", placeholder="org/model-name", scale=4)
                pull_btn = gr.Button("⬇ Pull from Hub", variant="secondary", scale=1)
            pull_out = gr.Markdown()

            def _set_model(mid):
                global _active_model_id
                if mid and mid in _registry:
                    _active_model_id = mid
                    return _registry[mid].metadata_card()
                return f"`{mid}` not in registry — Pull it first."

            set_btn.click(fn=_set_model, inputs=model_dd, outputs=meta_md)
            model_dd.change(fn=lambda m: _registry[m].metadata_card() if m in _registry else "", inputs=model_dd, outputs=meta_md)
            pull_btn.click(fn=pull_model, inputs=pull_box, outputs=pull_out)

        # ── Tab 2: Setup ──────────────────────────────────────
        with gr.Tab("⚙ Setup"):
            gr.Markdown(
                "### Per-Model Pipeline\n"
                "Each model gets its own ONNX file and TRT engine cache under `models/<slug>/`.  \n"
                "Step 1 = export ONNX (one-time, ~2min). Step 2 = compile TRT FP16 engine (~5min).  \n"
                "After Step 2: runs from cache in <1s. Same pattern as SD.NEXT's TRT build tab."
            )
            status_md  = gr.Markdown(full_status())
            with gr.Row():
                warm_btn    = gr.Button("⚡ Load + Index Corpus", variant="primary")
                refresh_btn = gr.Button("↻ Status")
            gr.Markdown("---")
            with gr.Row():
                export_btn = gr.Button("📦 Step 1 — Export ONNX (active model)", variant="secondary")
                trt_btn    = gr.Button("🔥 Step 2 — Compile TRT Engine FP16", variant="secondary")
            pipe_out = gr.Markdown()
            warm_btn.click(fn=warm_up, outputs=status_md)
            refresh_btn.click(fn=full_status, outputs=status_md)
            export_btn.click(fn=lambda: export_onnx(), outputs=pipe_out)
            trt_btn.click(fn=lambda: compile_trt(), outputs=pipe_out)

        # ── Tab 3: Search ─────────────────────────────────────
        with gr.Tab("🔍 Search"):
            gr.Markdown("Cosine similarity over corpus.sqlite turns. Load model in Setup tab first.")
            with gr.Row():
                with gr.Column(scale=3):
                    qbox = gr.Textbox(label="Query", placeholder="vulkan compute · MSVC linker · batch GPU truncation", lines=3)
                with gr.Column(scale=1):
                    topk    = gr.Slider(1, 50, value=args.top_k, step=1, label="Top K")
                    sbtn    = gr.Button("Search", variant="secondary")
            res_md = gr.Markdown()
            sbtn.click(fn=search_corpus, inputs=[qbox, topk], outputs=res_md)
            qbox.submit(fn=search_corpus, inputs=[qbox, topk], outputs=res_md)

        # ── Tab 4: Benchmark ──────────────────────────────────
        with gr.Tab("⏱ Bench"):
            gr.Markdown(
                "**Cross-model × cross-backend latency table.**  \n"
                "All registered models × all 3 backends. TRT requires export + compiled engine.  \n"
                "Mirrors the benchmark SD.NEXT/ComfyUI expose in their TRT performance tabs."
            )
            with gr.Row():
                btxt  = gr.Textbox(label="Probe text", value="RTX 4090 tensor core embedding — DLSS and TRT EP same libnvinfer path", lines=2, scale=4)
                bruns = gr.Slider(1, 50, value=10, step=1, label="Runs", scale=1)
            brun_btn = gr.Button("▶ Run Benchmark", variant="primary")
            bench_md = gr.Markdown()
            brun_btn.click(fn=bench_all, inputs=[btxt, bruns], outputs=bench_md)

    return demo


# ─────────────────────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import gradio  # validate import

    print("Scanning HF cache for embedding models...")
    _registry = scan_hf_cache([args.model] if args.model else None)

    if not _registry:
        # G9 fallback — we know this one exists from the GPU scoring runs
        fallback = "Qwen/Qwen3-Embedding-0.6B"
        _registry[fallback] = EmbedModelSpec(model_id=fallback)
        print(f"  No models found in cache — registered fallback: {fallback}")
    else:
        for mid, spec in _registry.items():
            mteb = f"  MTEB≈{spec.mteb_score:.1f}" if spec.mteb_score else ""
            print(f"  {mid}  ({spec.hidden_size}d · {spec.pooling} · {spec.model_type}){mteb}")

    # Set active model
    if args.model and args.model in _registry:
        _active_model_id = args.model
    else:
        _active_model_id = next(iter(_registry.keys()))

    print(f"\nActive model : {_active_model_id}")
    print(f"Backend      : {args.backend}")
    print(f"Port         : http://localhost:{args.port}")

    ui = build_ui()
    ui.launch(server_port=args.port, share=args.share, inbrowser=True)


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

