#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@SID: HF_MODEL_SCOUT_2026_02_27
@Purpose: Format-aware HuggingFace model discovery for mistral.rs v0.7.0
@Backend: HuggingFace API → arch filter → format detect → VRAM fit → ranked output

Discovers compatible models and recommends the OPTIMAL loading format per model:
  UQFF  — Pre-quantized, instant load, best of all worlds (if available)
  GPTQ  — Trained quantization, Marlin 4-bit kernels on CUDA (if available)
  ISQ   — Quantize-on-load from safetensors; use `--isq 4` for auto-best
  GGUF  — Pre-quantized ecosystem files (limited arch support in mistral.rs)

Format hierarchy (quality × speed × convenience):
  UQFF > GPTQ-4bit > ISQ-with-imatrix > ISQ-auto > GGUF

Usage:
  python scripts/hf_model_scout.py                   # Full scan, 16GB VRAM
  python scripts/hf_model_scout.py --vram 24          # Custom VRAM target
  python scripts/hf_model_scout.py --family qwen3     # Single family
  python scripts/hf_model_scout.py --json             # JSON output
  python scripts/hf_model_scout.py --top 5            # Top N results
  python scripts/hf_model_scout.py --new-only         # Last 30 days
  python scripts/hf_model_scout.py --verify           # Deep verify (HF API)

Post-scout:
  mistralrs tune -m "<model_id>" --json               # Exact VRAM + quant rec
  python scripts/mistralrs_model_manager.py swap "<id>"  # Load it
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# ── mistral.rs v0.7.0 Architecture Registry ─────────────────────────────────
# Source: `mistralrs serve -m test -a bogus` error output
# Dense architectures work reliably with ISQ. MoE has known issues.

DENSE_ARCHS = {
    "llama", "qwen2", "qwen3", "phi3", "phi2", "mistral",
    "gemma", "gemma2", "starcoder2", "glm4", "smollm3", "gpt_oss",
}

MOE_ARCHS = {
    "mixtral", "phi3.5moe", "deepseekv2", "deepseekv3",
    "qwen3moe", "glm4moe", "glm4moelite", "granitemoehybrid",
}

ALL_ARCHS = DENSE_ARCHS | MOE_ARCHS

# Architecture detection: regex patterns matched against model ID + tags.
# Order matters — more specific patterns first.
ARCH_PATTERNS: list[tuple[str, str]] = [
    (r"qwen[-/._]?3(?!.*moe)", "qwen3"),
    (r"qwen[-/._]?2", "qwen2"),
    (r"gemma[-._]?2(?![-._]?\d)", "gemma2"),
    (r"gemma[-._]?(?:1(?:\.\d)?|1)(?![-._]?\d)\b", "gemma"),
    (r"phi[-._]?[34](?!.*moe)", "phi3"),
    (r"phi[-._]?2\b", "phi2"),
    (r"smollm[-._]?3", "smollm3"),
    (r"starcoder[-._]?2", "starcoder2"),
    (r"glm[-._]?4(?!.*moe)", "glm4"),
    (r"gpt[-._]?oss", "gpt_oss"),
    (r"mixtral", "mixtral"),
    (r"deepseek[-._]?v?3", "deepseekv3"),
    (r"deepseek[-._]?v?2", "deepseekv2"),
    (r"(?:^|[/._-])mistral(?![-._]?mix)", "mistral"),
    (r"llama", "llama"),
]

# HF config.json architectures → mistral.rs arch (for --verify)
HF_CONFIG_ARCH_MAP: dict[str, str] = {
    "LlamaForCausalLM": "llama",
    "MistralForCausalLM": "mistral",
    "MixtralForCausalLM": "mixtral",
    "GemmaForCausalLM": "gemma",
    "Gemma2ForCausalLM": "gemma2",
    "Qwen2ForCausalLM": "qwen2",
    "Qwen3ForCausalLM": "qwen3",
    "Phi3ForCausalLM": "phi3",
    "PhiForCausalLM": "phi2",
    "Starcoder2ForCausalLM": "starcoder2",
    "DeepseekV2ForCausalLM": "deepseekv2",
    "DeepseekV3ForCausalLM": "deepseekv3",
    "ChatGLMModel": "glm4",
}

# Targeted search queries per architecture family
FAMILY_SEARCHES: list[tuple[str, str]] = [
    ("qwen3", "qwen3 instruct"),
    ("qwen2", "qwen2.5 instruct"),
    ("llama", "llama 3 instruct"),
    ("phi3", "phi-4"),
    ("gemma2", "gemma-2 it"),
    ("mistral", "mistral instruct"),
    ("smollm3", "smollm3"),
    ("glm4", "glm-4 chat"),
]

# VRAM estimation per quantization format (bytes per parameter)
QUANT_PROFILES: dict[str, dict] = {
    "Q4K":  {"bpp": 0.5625, "label": "ISQ Q4K",  "bits": 4.5},
    "Q6K":  {"bpp": 0.75,   "label": "ISQ Q6K",  "bits": 6.0},
    "Q8_0": {"bpp": 1.0,    "label": "ISQ Q8",   "bits": 8.0},
    "FP8":  {"bpp": 1.0,    "label": "FP8",      "bits": 8.0},
    "GPTQ4":{"bpp": 0.5,    "label": "GPTQ 4-bit","bits": 4.0},
    "FP16": {"bpp": 2.0,    "label": "FP16",     "bits": 16.0},
}
VRAM_OVERHEAD_GB = 2.0              # KV cache + CUDA + PagedAttention
VRAM_SAFETY_MARGIN = 1.1            # 10% headroom

DEFAULT_VRAM_GB = 16
DEFAULT_TOP_N = 20
HF_API = "https://huggingface.co/api/models"

# Known UQFF repos (EricB collection — checked 2026-02-27)
KNOWN_UQFF: dict[str, str] = {
    "microsoft/Phi-3.5-mini-instruct": "EricB/Phi-3.5-mini-instruct-UQFF",
    "google/gemma-2-9b-it": "EricB/gemma-2-9b-it-UQFF",
    "google/gemma-2-2b-it": "EricB/gemma-2-2b-it-UQFF",
    "google/gemma-2-27b-it": "EricB/gemma-2-27b-it-UQFF",
    "meta-llama/Llama-3.2-3B-Instruct": "EricB/Llama-3.2-3B-Instruct-UQFF",
    "meta-llama/Llama-3.2-1B-Instruct": "EricB/Llama-3.2-1B-Instruct-UQFF",
    "meta-llama/Llama-3.1-8B-Instruct": "EricB/Llama-3.1-8B-Instruct-UQFF",
    "mistralai/Mistral-7B-Instruct-v0.3": "EricB/Mistral-7B-Instruct-v0.3-UQFF",
    "mistralai/Mistral-Nemo-Instruct-2407": "EricB/Mistral-Nemo-Instruct-2407-UQFF",
}


# ── HTTP ─────────────────────────────────────────────────────────────────────

def http_get(url: str, timeout: int = 15) -> dict | list | None:
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "chthonic-hf-scout/1.0",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


# ── Detection ────────────────────────────────────────────────────────────────

def detect_arch(model_id: str, tags: list[str] | None = None) -> str | None:
    """Heuristic architecture detection from model ID and tags."""
    corpus = model_id.lower()
    if tags:
        corpus += " " + " ".join(t.lower() for t in tags)
    for pattern, arch in ARCH_PATTERNS:
        if re.search(pattern, corpus, re.IGNORECASE):
            return arch
    return None


def detect_params_b(model_id: str) -> float | None:
    """Extract parameter count in billions from model ID."""
    match = re.search(r"(\d+(?:\.\d+)?)\s*[bB]\b", model_id)
    if match:
        val = float(match.group(1))
        if 0.1 <= val <= 1000:
            return val
    # Models without param count in ID
    specials = {
        "phi-4-mini": 3.8, "phi-4": 14.0,
        "phi-3-mini": 3.8, "phi-3-small": 7.0, "phi-3-medium": 14.0,
    }
    lower = model_id.lower()
    for needle, params in specials.items():
        if needle in lower:
            return params
    return None


def estimate_vram(params_b: float, quant: str = "Q4K") -> float:
    """Estimate total VRAM in GB for model at given quantization."""
    bpp = QUANT_PROFILES.get(quant, QUANT_PROFILES["Q4K"])["bpp"]
    weights_gb = params_b * 1e9 * bpp / (1024 ** 3)
    return round((weights_gb + VRAM_OVERHEAD_GB) * VRAM_SAFETY_MARGIN, 1)


def best_quant_for_vram(params_b: float, vram_gb: float) -> str:
    """Pick the highest-quality quant that fits in VRAM."""
    # Prefer higher quality when it fits
    for q in ("FP8", "Q6K", "Q4K"):
        if estimate_vram(params_b, q) <= vram_gb:
            return q
    return "Q4K"  # Fallback — it's the smallest practical quant


def recommend_format(model_id: str, params_b: float | None, vram_gb: float,
                     verified: dict | None = None) -> dict:
    """Recommend best loading format + serve command for a model."""
    rec: dict = {"format": "isq", "quant": "4", "reason": "auto-select"}

    # 1. Check for UQFF (instant load, pre-quantized, best experience)
    uqff_id = KNOWN_UQFF.get(model_id)
    if uqff_id:
        rec = {
            "format": "uqff",
            "quant": "q4k",
            "reason": "pre-quantized UQFF, instant load",
            "uqff_repo": uqff_id,
            "cmd": f'mistralrs serve -m "{uqff_id}" --from-uqff q4k-0.uqff -p 8080 --ui',
        }
        return rec

    # 2. Check for GPTQ (trained quant, Marlin kernels on CUDA)
    if verified and verified.get("has_gptq"):
        gptq_id = verified["gptq_id"]
        rec = {
            "format": "gptq",
            "quant": "4-bit",
            "reason": "GPTQ Marlin kernels (fastest 4-bit on CUDA)",
            "gptq_repo": gptq_id,
            "cmd": f'mistralrs serve -m "{gptq_id}" -p 8080 --ui',
        }
        return rec

    # 3. ISQ (quantize safetensors on load)
    has_st = True
    if verified:
        has_st = verified.get("has_safetensors", False)

    if has_st:
        if params_b:
            q = best_quant_for_vram(params_b, vram_gb)
            label = QUANT_PROFILES[q]["label"]
            rec = {
                "format": "isq",
                "quant": "4",  # auto-select; mistral.rs picks best for platform
                "specific_quant": q,
                "reason": f"{label} fits {vram_gb:.0f}G VRAM" if q != "Q4K"
                          else "auto-select (Q4K on CUDA)",
                "cmd": f'mistralrs serve -m "{model_id}" --isq 4 -p 8080 --ui',
            }
        else:
            rec["cmd"] = f'mistralrs serve -m "{model_id}" --isq 4 -p 8080 --ui'
    else:
        rec = {
            "format": "unknown",
            "quant": "?",
            "reason": "no safetensors detected — may need GGUF",
            "cmd": f'mistralrs serve -m "{model_id}" --isq 4 -p 8080 --ui',
        }

    return rec


def is_instruct(model_id: str, tags: list[str] | None = None) -> bool:
    """Check if model is instruction-tuned."""
    corpus = (model_id + " " + " ".join(tags or [])).lower()
    return any(ind in corpus for ind in ("instruct", "chat", "-it\b", "conversational"))


def days_ago(iso: str | None) -> int | None:
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return max(0, (datetime.now(timezone.utc) - dt).days)
    except (ValueError, TypeError):
        return None


def age_label(days: int | None) -> str:
    if days is None:
        return "?"
    if days == 0:
        return "today"
    if days < 30:
        return f"{days}d"
    if days < 365:
        return f"{days // 30}mo"
    return f"{days // 365}y"


# ── Scoring ──────────────────────────────────────────────────────────────────

def score_model(m: dict, vram_gb: float) -> float:
    """Composite score: trending × recency × VRAM fit × arch reliability."""
    trend = min((m.get("trendingScore") or 0) / 500, 1.0)

    dl = m.get("downloads") or 0
    dl_s = min((dl ** 0.3) / 40, 1.0) if dl > 0 else 0

    likes = m.get("likes") or 0
    like_s = min((likes ** 0.4) / 20, 1.0) if likes > 0 else 0

    days = days_ago(m.get("createdAt"))
    if days is None:
        recency = 0.3
    elif days <= 7:
        recency = 1.0
    elif days <= 30:
        recency = 0.85
    elif days <= 90:
        recency = 0.6
    elif days <= 365:
        recency = 0.35
    else:
        recency = 0.15

    params = m.get("_params_b")
    if params:
        est = estimate_vram(params)
        fit = 1.0 if est <= vram_gb else (0.5 if est <= vram_gb * 1.2 else 0.0)
        # Sweet spot: 7-14B gives best quality/speed on 16GB
        size_q = 0.08 if 7 <= params <= 14 else (0.04 if 3 <= params < 7 else 0.0)
    else:
        fit = 0.2  # Unknown params = uncertain, penalize
        size_q = 0.0

    arch = m.get("_arch")
    dense = 0.10 if arch and arch in DENSE_ARCHS else 0.0
    instruct = 0.12 if is_instruct(m["id"], m.get("tags")) else 0.0

    # UQFF availability bonus — instant load, no quant overhead
    uqff_bonus = 0.06 if m["id"] in KNOWN_UQFF else 0.0

    # GGUF repos typically lack safetensors for ISQ
    gguf_penalty = -0.08 if "gguf" in m["id"].lower() else 0.0

    return max(0.0,
        trend * 0.18
        + dl_s * 0.14
        + like_s * 0.10
        + recency * 0.10
        + fit * 0.15
        + size_q
        + dense
        + instruct
        + uqff_bonus
        + gguf_penalty
    )


# ── HF API ───────────────────────────────────────────────────────────────────

def build_queries(families: list[str] | None, limit: int) -> list[tuple[str, str]]:
    """Build (label, url) tuples for parallel HF API fetch."""
    qs: list[tuple[str, str]] = [
        ("trending", f"{HF_API}?filter=text-generation&sort=trendingScore&direction=-1&limit={limit}"),
        ("newest", f"{HF_API}?filter=text-generation&sort=lastModified&direction=-1&limit={limit}"),
        ("popular", f"{HF_API}?filter=text-generation&sort=downloads&direction=-1&limit={min(limit, 50)}"),
    ]

    targets = FAMILY_SEARCHES
    if families:
        targets = [(f, q) for f, q in FAMILY_SEARCHES if f in families]
        for fam in families:
            if not any(f == fam for f, _ in targets):
                targets.append((fam, fam))

    for _, term in targets:
        enc = urllib.parse.quote(term)
        qs.append((
            f"family:{term}",
            f"{HF_API}?search={enc}&filter=text-generation&sort=trendingScore&direction=-1&limit={min(limit, 50)}",
        ))

    return qs


def fetch_all(queries: list[tuple[str, str]]) -> dict[str, dict]:
    """Parallel fetch, merge, deduplicate."""
    models: dict[str, dict] = {}

    def fetch_one(label_url: tuple[str, str]) -> tuple[str, list]:
        label, url = label_url
        data = http_get(url)
        return (label, data if isinstance(data, list) else [])

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for label, results in pool.map(fetch_one, queries):
            for m in results:
                mid = m.get("id") or m.get("modelId")
                if not mid or m.get("private"):
                    continue
                if mid not in models:
                    models[mid] = m
                else:
                    existing = models[mid]
                    for key in ("trendingScore", "downloads", "likes"):
                        if (m.get(key) or 0) > (existing.get(key) or 0):
                            existing[key] = m[key]
                    if m.get("tags") and not existing.get("tags"):
                        existing["tags"] = m["tags"]

    return models


def verify_config(model_id: str) -> dict | None:
    """Fetch model metadata from HF to verify architecture, safetensors, GPTQ."""
    data = http_get(f"{HF_API}/{urllib.parse.quote(model_id, safe='/')}", timeout=10)
    if not data or not isinstance(data, dict):
        return None

    result: dict = {"verified": True}

    config = data.get("config") or {}
    archs = config.get("architectures") or []
    result["hf_architectures"] = archs
    result["mistralrs_arch"] = None
    for a in archs:
        if a in HF_CONFIG_ARCH_MAP:
            result["mistralrs_arch"] = HF_CONFIG_ARCH_MAP[a]
            break

    safetensors = data.get("safetensors")
    result["has_safetensors"] = safetensors is not None
    if isinstance(safetensors, dict):
        total = safetensors.get("total")
        if isinstance(total, (int, float)) and total > 0:
            result["exact_params_b"] = round(total / 1e9, 2)

    # Fallback: check siblings for .safetensors files
    if not result["has_safetensors"]:
        siblings = data.get("siblings") or []
        for s in siblings:
            if s.get("rfilename", "").endswith(".safetensors"):
                result["has_safetensors"] = True
                break

    result["gated"] = bool(data.get("gated"))

    # Check for GPTQ variant (common naming pattern)
    result["has_gptq"] = False
    result["has_uqff"] = model_id in KNOWN_UQFF
    tags = data.get("tags") or []
    if "gptq" in " ".join(tags).lower():
        result["has_gptq"] = True
        result["gptq_id"] = model_id
    else:
        # Quick probe for common GPTQ naming
        base = model_id.rstrip("/")
        for suffix in ("-gptq-4bit", "-GPTQ-4bit", "-gptq", "-GPTQ"):
            probe = http_get(f"{HF_API}/{urllib.parse.quote(base + suffix, safe='/')}", timeout=5)
            if probe and isinstance(probe, dict) and not probe.get("error"):
                result["has_gptq"] = True
                result["gptq_id"] = base + suffix
                break

    return result


# ── Output ───────────────────────────────────────────────────────────────────

def format_table(ranked: list[dict], vram_gb: float, elapsed: float) -> str:
    lines: list[str] = []
    lines.append("")
    lines.append(f"  HF Model Scout for mistral.rs — {vram_gb:.0f} GB VRAM target")
    lines.append(f"  Format priority: UQFF > GPTQ > ISQ-auto > GGUF")
    lines.append(f"  {'=' * 72}")
    lines.append("")
    lines.append(f"  {'#':>2}  {'Model':<42} {'Params':>6} {'VRAM':>6} {'Score':>5} {'Age':>5} {'Fmt'}")
    lines.append(f"  {'--':>2}  {'─' * 42} {'─' * 6} {'─' * 6} {'─' * 5} {'─' * 5} {'─' * 7}")

    for i, m in enumerate(ranked, 1):
        mid = m["id"]
        params = m.get("_params_b")
        vram = m.get("_vram_est")
        score = m.get("_score", 0)
        age = age_label(days_ago(m.get("createdAt")))
        arch = m.get("_arch") or "?"

        rec = recommend_format(mid, params, vram_gb, m.get("_verified"))
        fmt_tag = rec["format"].upper()

        params_s = f"{params:.1f}B" if params else "?"
        vram_s = f"{vram:.0f}G" if vram else "?"
        warn = " !" if vram and vram > vram_gb else ""
        display = mid if len(mid) <= 42 else mid[:39] + "..."

        lines.append(f"  {i:2d}  {display:<42} {params_s:>6} {vram_s:>5}{warn} {score:>5.2f} {age:>5} {fmt_tag}")
        lines.append(f"      > {rec.get('cmd', '?')}")
        lines.append(f"      [{arch}] {rec['reason']}")

        if m.get("_verified"):
            v = m["_verified"]
            flags = []
            if v.get("has_safetensors"):
                flags.append("safetensors")
            if v.get("has_gptq"):
                flags.append(f"GPTQ: {v.get('gptq_id', '?')}")
            if v.get("has_uqff"):
                flags.append(f"UQFF: {KNOWN_UQFF.get(mid, '?')}")
            if v.get("gated"):
                flags.append("GATED")
            if v.get("exact_params_b"):
                flags.append(f"exact: {v['exact_params_b']}B")
            if flags:
                lines.append(f"      [{' | '.join(flags)}]")

        lines.append("")

    return "\n".join(lines)


def format_json(ranked: list[dict], vram_gb: float) -> str:
    out = []
    for m in ranked:
        rec = recommend_format(m["id"], m.get("_params_b"), vram_gb, m.get("_verified"))
        entry = {
            "id": m["id"],
            "arch": m.get("_arch"),
            "params_b": m.get("_params_b"),
            "vram_q4k_gb": m.get("_vram_est"),
            "fits_vram": (m.get("_vram_est") or 999) <= vram_gb,
            "score": round(m.get("_score", 0), 4),
            "downloads": m.get("downloads", 0),
            "likes": m.get("likes", 0),
            "trending": m.get("trendingScore", 0),
            "created": m.get("createdAt"),
            "instruction_tuned": is_instruct(m["id"], m.get("tags")),
            "recommended_format": rec,
        }
        if m.get("_verified"):
            entry["verified"] = m["_verified"]
        out.append(entry)
    return json.dumps({"vram_gb": vram_gb, "format_priority": "UQFF > GPTQ > ISQ > GGUF", "models": out}, indent=2)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Architecture-aware HuggingFace model discovery for mistral.rs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Post-scout: mistralrs tune -m <id> --json  |  "
               "python scripts/mistralrs_model_manager.py swap <id>",
    )
    parser.add_argument("--vram", type=float, default=DEFAULT_VRAM_GB,
                        help=f"Target GPU VRAM in GB (default: {DEFAULT_VRAM_GB})")
    parser.add_argument("--top", type=int, default=DEFAULT_TOP_N,
                        help=f"Show top N results (default: {DEFAULT_TOP_N})")
    parser.add_argument("--family", type=str, default=None,
                        help="Comma-separated families (e.g., qwen3,llama,phi3)")
    parser.add_argument("--new-only", action="store_true",
                        help="Only models from last 30 days")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="JSON output")
    parser.add_argument("--verify", action="store_true",
                        help="Verify top results via HF config.json")
    parser.add_argument("--include-moe", action="store_true",
                        help="Include MoE architectures (risky on v0.7.0)")
    parser.add_argument("--limit", type=int, default=80,
                        help="Models per HF query (default: 80)")
    args = parser.parse_args()

    families = [f.strip() for f in args.family.split(",")] if args.family else None
    t0 = time.time()

    # Check if server is already running
    if not args.json_output:
        server = http_get("http://localhost:8080/v1/models", timeout=3)
        if server:
            loaded = [m["id"] for m in (server.get("data") or []) if m.get("status") == "loaded"]
            if loaded:
                print(f"  Currently loaded: {loaded[0]}")
                print()

    # 1. Fetch from HuggingFace
    queries = build_queries(families, args.limit)
    if not args.json_output:
        print(f"  Scanning HuggingFace ({len(queries)} queries)...", flush=True)

    raw = fetch_all(queries)

    # 2. Filter: architecture + VRAM
    candidates = []
    for mid, m in raw.items():
        m["id"] = mid
        arch = detect_arch(mid, m.get("tags"))
        if not arch:
            continue
        if not args.include_moe and arch in MOE_ARCHS:
            continue
        m["_arch"] = arch

        params = detect_params_b(mid)
        m["_params_b"] = params

        if params:
            vram = estimate_vram(params)
            m["_vram_est"] = vram
            if vram > args.vram * 1.3:
                continue
        else:
            m["_vram_est"] = None

        if args.new_only:
            age = days_ago(m.get("createdAt"))
            if age is None or age > 30:
                continue

        m["_score"] = score_model(m, args.vram)
        candidates.append(m)

    # 3. Rank
    candidates.sort(key=lambda x: x.get("_score", 0), reverse=True)
    top = candidates[: args.top]

    # 4. Optional verification
    if args.verify and top:
        if not args.json_output:
            print(f"  Verifying top {len(top)} configs...", flush=True)

        def verify_one(m: dict) -> dict:
            m["_verified"] = verify_config(m["id"])
            return m

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(verify_one, top))

    elapsed = time.time() - t0

    # 5. Output
    if args.json_output:
        print(format_json(top, args.vram))
    else:
        print(format_table(top, args.vram, elapsed))
        print(f"  Scanned: {len(raw)} | Compatible: {len(candidates)} | Shown: {len(top)} | {elapsed:.1f}s")
        if not args.verify and top:
            print(f"  Tip: --verify to check safetensors + GPTQ/UQFF availability")
        print(f"  Tip: mistralrs tune -m \"<model>\" --json for exact VRAM estimate")
        print(f"  Tip: mistralrs quantize to save as UQFF for instant future loads")
        print()


if __name__ == "__main__":
    main()
