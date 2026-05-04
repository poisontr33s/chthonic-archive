#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @SID: P-11
# @Title: Embedding Backend E2E Probe
# @Gate: G7-prereq — evaluate all available embedding paths before sqlite-vec integration
# @Emits: manifest/P-11.json
# @Run: uv run probes/python/P-11.py

import json
import os
import time
import sys
import importlib
from pathlib import Path

# Force offline mode — HF Hub network calls are blocked in this environment.
# Models must be pre-cached. nomic-embed-text-v1.5 and all-MiniLM-L6-v2 are cached.
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

MANIFEST_PATH = Path("manifest/P-11.json")
MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

HF_TOKEN = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")

# Model preference order (first available wins for GPU backends)
# nomic-embed-text-v1.5 (768d, gated — needs HF_TOKEN)
# all-MiniLM-L6-v2 (384d, public — cached locally)
CANDIDATE_MODELS = [
    ("nomic-ai/nomic-embed-text-v1.5", 768, True),   # (model_id, expected_dims, needs_trust_remote_code)
    ("sentence-transformers/all-MiniLM-L6-v2", 384, False),
]

TEST_TEXT = "session corpus embedding probe — semantic search over chthonic archive sessions"
TEST_BATCH = [
    "vulkan cli renderer gate architecture G0 through G9",
    "sqlite-vec nomic embeddings semantic search corpus",
    "Python 3.14 GPU inference flash attention CUDA",
    "Iron Maiden entity Claudine Rustbeltet district",
    "todo roulette manifest weight euler score spin",
    "session vampire drain corpus nightly escapades",
    "SSOT entity profile Triumvirate Pentea Thalamus",
    "Bun TypeScript corpus-native satellite federation",
    "sentence transformers nomic embed text GPU",
    "chthonic archive wet paper to gold methodology",
]

results = {
    "probe": "P-11",
    "gate": "G7-prereq",
    "run_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "python_version": sys.version,
    "hf_token_present": bool(HF_TOKEN),
    "backends": {},
    "sqlite_vec": {},
    "recommendation": None,
}


def check_import(module: str) -> bool:
    try:
        importlib.import_module(module)
        return True
    except ImportError:
        return False


# ── Backend 1: sentence-transformers ─────────────────────────────────────────
print("[P-11] Backend 1: sentence-transformers", flush=True)
backend = {"id": "sentence_transformers", "available": False}
try:
    from sentence_transformers import SentenceTransformer
    import torch

    cuda_available = torch.cuda.is_available()
    device = "cuda" if cuda_available else "cpu"
    backend["cuda_available"] = cuda_available
    backend["device"] = device

    # Try each candidate model in preference order
    loaded_model = None
    for model_name, expected_dims, needs_trust in CANDIDATE_MODELS:
        try:
            kwargs = {"trust_remote_code": True} if needs_trust else {}
            if HF_TOKEN:
                kwargs["token"] = HF_TOKEN
            t0 = time.perf_counter()
            loaded_model = SentenceTransformer(model_name, device=device, **kwargs)
            load_ms = round((time.perf_counter() - t0) * 1000, 1)
            backend["model"] = model_name
            backend["load_ms"] = load_ms
            print(f"  Loaded: {model_name} ({load_ms}ms)", flush=True)
            break
        except Exception as me:
            print(f"  Skip {model_name}: {me}", flush=True)

    if loaded_model is None:
        raise RuntimeError("No candidate model loaded")

    # single embed
    t0 = time.perf_counter()
    vec = loaded_model.encode(TEST_TEXT, normalize_embeddings=True)
    single_ms = round((time.perf_counter() - t0) * 1000, 1)
    backend["single_ms"] = single_ms
    backend["dims"] = len(vec)
    backend["first3"] = [round(float(v), 6) for v in vec[:3]]

    # batch embed
    t0 = time.perf_counter()
    vecs = loaded_model.encode(TEST_BATCH, normalize_embeddings=True, batch_size=10)
    batch_ms = round((time.perf_counter() - t0) * 1000, 1)
    backend["batch_10_ms"] = batch_ms
    backend["batch_per_item_ms"] = round(batch_ms / 10, 1)

    backend["available"] = True
    backend["status"] = "admitted"
    print(f"  ✅ dims={len(vec)} single={single_ms}ms batch10={batch_ms}ms device={device}", flush=True)
except Exception as e:
    backend["error"] = str(e)
    backend["status"] = "failed"
    print(f"  ❌ {e}", flush=True)
results["backends"]["sentence_transformers"] = backend


# ── Backend 2: Ollama HTTP API ────────────────────────────────────────────────
print("[P-11] Backend 2: Ollama HTTP API", flush=True)
backend = {"id": "ollama_http", "available": False}
try:
    import urllib.request

    OLLAMA_URL = "http://localhost:11434/api/embeddings"
    payload = json.dumps({"model": "nomic-embed-text", "prompt": TEST_TEXT}).encode()

    # warmup + single
    t0 = time.perf_counter()
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    single_ms = round((time.perf_counter() - t0) * 1000, 1)

    vec = data["embedding"]
    backend["dims"] = len(vec)
    backend["first3"] = [round(float(v), 6) for v in vec[:3]]
    backend["single_ms"] = single_ms
    backend["model"] = "nomic-embed-text:latest"

    # batch (sequential — Ollama has no batch endpoint)
    t0 = time.perf_counter()
    for text in TEST_BATCH:
        p = json.dumps({"model": "nomic-embed-text", "prompt": text}).encode()
        req = urllib.request.Request(OLLAMA_URL, data=p, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            json.loads(r.read())
    batch_ms = round((time.perf_counter() - t0) * 1000, 1)
    backend["batch_10_ms"] = batch_ms
    backend["batch_per_item_ms"] = round(batch_ms / 10, 1)
    backend["note"] = "sequential only — no native batch endpoint"

    backend["available"] = True
    backend["status"] = "admitted"
    print(f"  ✅ dims={len(vec)} single={single_ms}ms batch10={batch_ms}ms", flush=True)
except Exception as e:
    backend["error"] = str(e)
    backend["status"] = "failed"
    print(f"  ❌ {e}", flush=True)
results["backends"]["ollama_http"] = backend


# ── Backend 3: llama-cpp-python (CPU/GPU embeddings via GGUF) ────────────────
print("[P-11] Backend 3: llama-cpp-python", flush=True)
backend = {"id": "llama_cpp_python", "available": False}
try:
    from llama_cpp import Llama

    # Check if a GGUF embedding model is cached locally
    # Common HuggingFace cache locations
    hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
    gguf_candidates = list(hf_cache.glob("**/nomic*embed*.gguf")) + list(hf_cache.glob("**/mxbai*embed*.gguf"))

    if not gguf_candidates:
        backend["status"] = "skipped"
        backend["reason"] = "no GGUF embedding model found in HF cache — would require download"
        backend["checked_path"] = str(hf_cache)
        print("  ⏭  skipped — no GGUF embedding model cached locally", flush=True)
    else:
        gguf_path = str(gguf_candidates[0])
        backend["model_path"] = gguf_path

        t0 = time.perf_counter()
        llm = Llama(model_path=gguf_path, embedding=True, n_ctx=512, verbose=False, n_gpu_layers=-1)
        load_ms = round((time.perf_counter() - t0) * 1000, 1)
        backend["load_ms"] = load_ms

        t0 = time.perf_counter()
        vec = llm.create_embedding(TEST_TEXT)["data"][0]["embedding"]
        single_ms = round((time.perf_counter() - t0) * 1000, 1)
        backend["dims"] = len(vec)
        backend["first3"] = [round(float(v), 6) for v in vec[:3]]
        backend["single_ms"] = single_ms

        t0 = time.perf_counter()
        for text in TEST_BATCH:
            llm.create_embedding(text)
        batch_ms = round((time.perf_counter() - t0) * 1000, 1)
        backend["batch_10_ms"] = batch_ms
        backend["batch_per_item_ms"] = round(batch_ms / 10, 1)

        backend["available"] = True
        backend["status"] = "admitted"
        print(f"  ✅ dims={len(vec)} single={single_ms}ms batch10={batch_ms}ms", flush=True)
except Exception as e:
    backend["error"] = str(e)
    backend["status"] = "failed"
    print(f"  ❌ {e}", flush=True)
results["backends"]["llama_cpp_python"] = backend


# ── Backend 4: transformers AutoModel direct ─────────────────────────────────
print("[P-11] Backend 4: transformers AutoModel (direct, no sentence-transformers wrapper)", flush=True)
backend = {"id": "transformers_direct", "available": False}
try:
    import torch
    from transformers import AutoTokenizer, AutoModel

    model_name = "nomic-ai/nomic-embed-text-v1.5"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    backend["device"] = device

    tk_kwargs = {"token": HF_TOKEN} if HF_TOKEN else {}
    t0 = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(model_name, **tk_kwargs)
    model = AutoModel.from_pretrained(model_name, trust_remote_code=True, **tk_kwargs).to(device)
    model.eval()
    load_ms = round((time.perf_counter() - t0) * 1000, 1)
    backend["model"] = model_name
    backend["load_ms"] = load_ms

    def mean_pool(token_embeds, attention_mask):
        mask = attention_mask.unsqueeze(-1).expand(token_embeds.size()).float()
        return (token_embeds * mask).sum(1) / mask.sum(1).clamp(min=1e-9)

    # single embed
    t0 = time.perf_counter()
    enc = tokenizer(TEST_TEXT, return_tensors="pt", truncation=True, max_length=512).to(device)
    with torch.no_grad():
        out = model(**enc)
    vec_t = mean_pool(out.last_hidden_state, enc["attention_mask"])
    vec_t = torch.nn.functional.normalize(vec_t, p=2, dim=1)
    vec = vec_t[0].cpu().numpy()
    single_ms = round((time.perf_counter() - t0) * 1000, 1)
    backend["dims"] = len(vec)
    backend["first3"] = [round(float(v), 6) for v in vec[:3]]
    backend["single_ms"] = single_ms

    # batch
    t0 = time.perf_counter()
    enc = tokenizer(TEST_BATCH, return_tensors="pt", truncation=True, max_length=512, padding=True).to(device)
    with torch.no_grad():
        out = model(**enc)
    vecs = mean_pool(out.last_hidden_state, enc["attention_mask"])
    vecs = torch.nn.functional.normalize(vecs, p=2, dim=1).cpu().numpy()
    batch_ms = round((time.perf_counter() - t0) * 1000, 1)
    backend["batch_10_ms"] = batch_ms
    backend["batch_per_item_ms"] = round(batch_ms / 10, 1)

    backend["available"] = True
    backend["status"] = "admitted"
    print(f"  ✅ dims={len(vec)} single={single_ms}ms batch10={batch_ms}ms device={device}", flush=True)
except Exception as e:
    backend["error"] = str(e)
    backend["status"] = "failed"
    print(f"  ❌ {e}", flush=True)
results["backends"]["transformers_direct"] = backend


# ── sqlite-vec Python availability ───────────────────────────────────────────
print("[P-11] Checking sqlite-vec Python binding", flush=True)
sv = {"available": False}
try:
    import sqlite_vec  # pypi: sqlite-vec
    sv["available"] = True
    sv["version"] = getattr(sqlite_vec, "__version__", "unknown")
    sv["status"] = "admitted"
    print(f"  ✅ sqlite-vec Python binding available: {sv['version']}", flush=True)
except ImportError:
    sv["status"] = "not_installed"
    sv["install_cmd"] = "uv add sqlite-vec"
    print("  ⚠  sqlite-vec not installed — uv add sqlite-vec", flush=True)
results["sqlite_vec"] = sv


# ── Recommendation ────────────────────────────────────────────────────────────
admitted = {k: v for k, v in results["backends"].items() if v.get("status") == "admitted"}
if admitted:
    # rank by batch_per_item_ms ascending (lower = faster)
    ranked = sorted(admitted.items(), key=lambda x: x[1].get("batch_per_item_ms", 9999))
    winner_id, winner = ranked[0]

    # override preference: GPU-native > HTTP > CPU
    gpu_native = [k for k, v in admitted.items() if v.get("device") == "cuda"]
    if gpu_native:
        winner_id = gpu_native[0]
        winner = admitted[winner_id]

    results["recommendation"] = {
        "backend": winner_id,
        "reason": f"GPU-native CUDA backend — {winner.get('dims')}d, single={winner.get('single_ms')}ms, batch/item={winner.get('batch_per_item_ms')}ms",
        "g7_integration": "Bun.spawn(['uv', 'run', 'scripts/embed.py', '--text', '...']) → stdout float32 LE bytes",
        "alternatives": [k for k in admitted if k != winner_id],
    }
    print(f"\n[P-11] Recommendation: {winner_id}", flush=True)
else:
    results["recommendation"] = {"backend": None, "reason": "no backends admitted"}
    print("\n[P-11] WARNING: no backends admitted", flush=True)


# ── Write manifest ────────────────────────────────────────────────────────────
MANIFEST_PATH.write_text(json.dumps(results, indent=2))
print(f"\n[P-11] Manifest written → {MANIFEST_PATH}", flush=True)

# Exit code: 0 if at least one GPU-native backend admitted
gpu_admitted = any(
    v.get("status") == "admitted" and v.get("device") == "cuda"
    for v in results["backends"].values()
)
sys.exit(0 if gpu_admitted else 2)
