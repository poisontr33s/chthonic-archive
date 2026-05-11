#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: embed_model_discover.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
embed_model_discover.py — Script logic for embed_model_discover.py.

@SID:           embed_model_discover
@Shabti:        CLI Script
@Purpose:       Script logic for embed_model_discover.py.
"""

# @SID: embed_model_discover — HF Hub embedding model discovery + gating classification
#
# Scans HF Hub for top feature-extraction / sentence-similarity models, classifies gating
# type (open / auto / form / org), cross-references a curated MTEB score table, and outputs
# a ranked candidate list of models not yet in the registry — or all models if
# --include-registered is set.
#
# Output:
#   stdout     — human-readable ranked table + gating summary
#   manifest/embed_model_candidates.json — full structured output for downstream tooling
#
# Usage:
#   uv run scripts/embed_model_discover.py                   # top 20 candidates
#   uv run scripts/embed_model_discover.py --filter-gated    # only gated models
#   uv run scripts/embed_model_discover.py --filter-open     # only openly accessible
#   uv run scripts/embed_model_discover.py --min-mteb 64.0   # MTEB floor
#   uv run scripts/embed_model_discover.py --limit 50 --include-registered
#
# Gating classification (from HF API `gated` field):
#   open   — gated:false  — download freely
#   auto   — gated:"auto" — HF agree-terms API works (Tier-1 accept OK)
#   form   — gated:"manual" — web form / org-controlled (Tier-3 Playwright or manual)
#
# HF API reference: https://huggingface.co/docs/hub/api#get-apimodelsmodel_id

import math
import os
import sys
import json
import argparse
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone

# ── Paths ─────────────────────────────────────────────────────────────────────
_SCRIPTS = Path(__file__).parent
_ROOT = _SCRIPTS.parent
REGISTRY_PATH = _SCRIPTS / "embed_model_registry.json"
MANIFEST_DIR = _ROOT / "manifest"

# ── MTEB curated score table (English average, MTEB leaderboard 2026-05) ──────
# Source: https://huggingface.co/spaces/mteb/leaderboard
# Models marked "est." are extrapolated from tech reports / model cards.
# Models marked "multi" are multilingual — English score is lower than their primary metric.
MTEB_SCORES: dict[str, tuple[float, str]] = {
    # (score, source_note)
    "NVIDIA/NV-Embed-v2":                        (69.32, "leaderboard"),
    "Qwen/Qwen3-Embedding-8B":                   (68.26, "Qwen3 tech report"),
    "BAAI/bge-en-icl":                           (68.09, "leaderboard"),
    "Alibaba-NLP/gte-Qwen2-7B-instruct":         (67.48, "leaderboard"),
    "Qwen/Qwen3-Embedding-4B":                   (67.03, "Qwen3 tech report"),
    "intfloat/e5-mistral-7b-instruct":           (66.63, "leaderboard"),
    "mistralai/Mistral-Embed":                   (66.08, "est. model card"),
    "Qwen/Qwen3-Embedding-0.6B":                 (65.70, "Qwen3 tech report"),
    "Alibaba-NLP/gte-large-en-v1.5":             (65.39, "leaderboard"),
    "Salesforce/SFR-Embedding-2_R":              (65.38, "leaderboard"),
    "dunzhang/stella_en_1.5B_v5":               (65.37, "leaderboard"),
    "Alibaba-NLP/gte-Qwen2-1.5B-instruct":      (65.01, "leaderboard"),
    "jinaai/jina-embeddings-v3":                 (64.56, "leaderboard"),
    "Cohere/Cohere-embed-english-v3.0":          (64.52, "est. Cohere blog"),
    "mixedbread-ai/mxbai-embed-large-v1":        (64.68, "leaderboard"),
    "Salesforce/SFR-Embedding-Mistral":          (64.41, "leaderboard"),
    "intfloat/multilingual-e5-large-instruct":   (64.42, "leaderboard"),
    "intfloat/e5-large-v2":                      (62.25, "leaderboard"),
    "BAAI/bge-large-en-v1.5":                    (63.98, "leaderboard"),
    "nomic-ai/nomic-embed-text-v1.5":            (62.28, "leaderboard"),
    "Cohere/Cohere-embed-multilingual-v3.0":     (62.40, "est. multi — Cohere blog"),
    "ibm-granite/granite-embedding-small-english-r2": (62.10, "est. model card"),
    "BAAI/bge-base-en-v1.5":                     (63.55, "leaderboard"),
    "BAAI/bge-m3":                               (57.10, "leaderboard (multi)"),
    "sentence-transformers/all-MiniLM-L6-v2":    (56.26, "leaderboard"),
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2": (53.75, "leaderboard"),
    "google/embeddinggemma-300m":                (60.12, "est. model card"),
    "nvidia/llama-nemotron-embed-1b-v2":         (62.50, "est. NVIDIA blog"),
    # Emerging 2026 candidates
    "Alibaba-NLP/gte-multilingual-base":         (63.80, "leaderboard"),
    "WhereIsAI/UAE-Large-V1":                    (64.64, "leaderboard"),
    "infgrad/stella-base-en-v2":                 (62.61, "leaderboard"),
    "llmrails/ember-v1":                         (63.54, "leaderboard"),
    "BAAI/bge-small-en-v1.5":                    (62.17, "leaderboard"),
    "thenlper/gte-large":                        (63.13, "leaderboard"),
    "thenlper/gte-base":                         (62.39, "leaderboard"),
    "hkunlp/instructor-xl":                      (61.79, "leaderboard"),
    "hkunlp/instructor-large":                   (61.59, "leaderboard"),
}

# VRAM estimate helper (FP16 + 30% overhead)
def _vram_gb(params_m: int | None) -> float | None:
    if params_m is None:
        return None
    return round((params_m * 2e6 * 1.3) / 1e9, 1)

# ── HF API helpers ─────────────────────────────────────────────────────────────
def _get_hf_token() -> str | None:
    for env in ("HF_TOKEN", "HUGGINGFACE_HUB_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        t = os.getenv(env)
        if t:
            return t.strip()
    p = Path.home() / ".huggingface" / "token"
    return p.read_text().strip() if p.exists() else None


def _hf_get(url: str, token: str | None) -> dict | list | None:
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode(errors="replace"))
    except urllib.error.HTTPError as e:
        print(f"  [warn] {url} → HTTP {e.code}", file=sys.stderr)
        return None
    except Exception as ex:
        print(f"  [warn] {url} → {ex}", file=sys.stderr)
        return None


def _search(pipeline_tag: str, sort: str, limit: int, token: str | None) -> list[dict]:
    params = urllib.parse.urlencode({
        "pipeline_tag": pipeline_tag,
        "sort": sort,
        "direction": "-1",
        "limit": str(limit),
        "full": "true",
    })
    url = f"https://huggingface.co/api/models?{params}"
    result = _hf_get(url, token)
    return result if isinstance(result, list) else []


def _classify_gate(raw_gated) -> str:
    if raw_gated is False or raw_gated == "false" or raw_gated is None:
        return "open"
    if raw_gated == "auto" or raw_gated is True or raw_gated == "true":
        return "auto"
    if raw_gated == "manual":
        return "form"
    return str(raw_gated)


def _build_candidate(m: dict, registered: set[str]) -> dict:
    """Build a normalised candidate record from HF model list entry."""
    model_id = m.get("id") or m.get("modelId") or ""
    mteb_entry = MTEB_SCORES.get(model_id)
    mteb_score = mteb_entry[0] if mteb_entry else None
    mteb_src = mteb_entry[1] if mteb_entry else "unknown"

    downloads = m.get("downloads") or 0
    likes = m.get("likes") or 0
    gate_raw = m.get("gated", False)
    gate_type = _classify_gate(gate_raw)

    # Rank score: MTEB (primary signal) + log scale downloads + likes noise
    rank = (mteb_score or 50.0) + math.log10(max(downloads, 1)) * 0.5 + min(likes, 500) * 0.005

    return {
        "model_id": model_id,
        "mteb_avg": mteb_score,
        "mteb_source": mteb_src,
        "dims": None,           # filled by --enrich if needed
        "gated": gate_raw,
        "gate_type": gate_type, # open / auto / form
        "downloads": downloads,
        "likes": likes,
        "pipeline_tag": m.get("pipeline_tag"),
        "tags": [t for t in (m.get("tags") or []) if not t.startswith("arxiv")],
        "last_modified": m.get("lastModified"),
        "in_registry": model_id in registered,
        "rank_score": round(rank, 3),
    }


def _load_registry() -> dict:
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {"models": {}}


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser(
        description="Discover top HF embedding models and classify their gating status.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--limit", type=int, default=20,
                    help="Max candidates to include in output (default: 20)")
    ap.add_argument("--fetch-limit", type=int, default=300,
                    help="Max models to fetch from HF API before filtering (default: 300)")
    ap.add_argument("--filter-gated", action="store_true",
                    help="Only show models with gated != false (auto + form)")
    ap.add_argument("--filter-open", action="store_true",
                    help="Only show models that are openly accessible")
    ap.add_argument("--min-mteb", type=float, default=None,
                    help="Minimum MTEB average score (filters unknown-score models if strict)")
    ap.add_argument("--min-downloads", type=int, default=10_000,
                    help="Minimum HF download count (default: 10000)")
    ap.add_argument("--include-registered", action="store_true",
                    help="Include models already in registry (marked in_registry:true)")
    ap.add_argument("--sort-by", choices=["rank", "mteb", "downloads", "likes"],
                    default="rank", help="Sort order (default: rank)")
    ap.add_argument("--output", type=Path,
                    default=MANIFEST_DIR / "embed_model_candidates.json",
                    help="Output JSON path (default: manifest/embed_model_candidates.json)")
    ap.add_argument("--json", action="store_true",
                    help="Print JSON to stdout instead of table")
    args = ap.parse_args()

    if args.filter_gated and args.filter_open:
        print("[error] --filter-gated and --filter-open are mutually exclusive", file=sys.stderr)
        sys.exit(1)

    registry = _load_registry()
    registered: set[str] = set(registry.get("models", {}).keys())
    active_model = registry.get("active_model_id", "")
    token = _get_hf_token()

    print(f"[discover] fetching HF Hub models (limit={args.fetch_limit})…", file=sys.stderr)

    # Fetch from both pipeline tags to maximise coverage
    raw: list[dict] = []
    for tag in ("feature-extraction", "sentence-similarity"):
        batch = _search(tag, sort="downloads", limit=args.fetch_limit // 2, token=token)
        raw.extend(batch)

    # Deduplicate by model_id
    seen: set[str] = set()
    deduped: list[dict] = []
    for m in raw:
        mid = m.get("id") or m.get("modelId") or ""
        if mid and mid not in seen:
            seen.add(mid)
            deduped.append(m)

    print(f"[discover] {len(deduped)} unique models from HF API", file=sys.stderr)

    # Build candidate records
    candidates: list[dict] = []
    for m in deduped:
        c = _build_candidate(m, registered)
        if not c["model_id"]:
            continue

        # Gating filter
        if args.filter_gated and c["gate_type"] == "open":
            continue
        if args.filter_open and c["gate_type"] != "open":
            continue

        # Download floor
        if c["downloads"] < args.min_downloads:
            continue

        # MTEB floor (only filter if score is known when min_mteb is set)
        if args.min_mteb is not None and c["mteb_avg"] is not None:
            if c["mteb_avg"] < args.min_mteb:
                continue

        # Registry filter
        if not args.include_registered and c["in_registry"]:
            continue

        candidates.append(c)

    # Sort
    sort_key = {
        "rank":      lambda x: x["rank_score"],
        "mteb":      lambda x: (x["mteb_avg"] or 0.0),
        "downloads": lambda x: x["downloads"],
        "likes":     lambda x: x["likes"],
    }[args.sort_by]
    candidates.sort(key=sort_key, reverse=True)
    candidates = candidates[: args.limit]

    # Gate type breakdown
    gate_counts: dict[str, int] = {}
    for c in candidates:
        gate_counts[c["gate_type"]] = gate_counts.get(c["gate_type"], 0) + 1

    output = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "active_model": active_model,
        "registered_count": len(registered),
        "fetched_total": len(deduped),
        "candidates_returned": len(candidates),
        "gate_breakdown": gate_counts,
        "filters": {
            "filter_gated": args.filter_gated,
            "filter_open": args.filter_open,
            "min_mteb": args.min_mteb,
            "min_downloads": args.min_downloads,
            "include_registered": args.include_registered,
            "sort_by": args.sort_by,
        },
        "candidates": candidates,
    }

    # Write manifest
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[discover] wrote {args.output}", file=sys.stderr)

    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    # ── Human-readable table ──────────────────────────────────────────────────
    print(f"\n{'─'*100}")
    print(f"  HF EMBEDDING MODEL DISCOVERY  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  active: {active_model}")
    print(f"  fetched={len(deduped)}  registered={len(registered)}  candidates={len(candidates)}  gate_breakdown={gate_counts}")
    print(f"{'─'*100}")

    header = f"{'#':>3}  {'MODEL ID':<52}  {'MTEB':>6}  {'GATE':>5}  {'DL':>8}  {'RANK':>6}  {'IN_REG':>6}"
    print(header)
    print("─" * 100)
    for i, c in enumerate(candidates, 1):
        mteb = f"{c['mteb_avg']:.2f}" if c["mteb_avg"] else "  ?"
        gate = {"open": "OPEN", "auto": "AUTO", "form": "FORM"}.get(c["gate_type"], c["gate_type"])
        dl = f"{c['downloads']:,}"
        reg = "★" if c["in_registry"] else ""
        active_marker = "◄" if c["model_id"] == active_model else ""
        print(f"{i:>3}  {c['model_id']:<52}  {mteb:>6}  {gate:>5}  {dl:>8}  {c['rank_score']:>6.2f}  {reg+active_marker:>6}")

    print(f"{'─'*100}")
    print()

    # Gate classification guide
    print("  GATE TYPES:")
    print("  OPEN  — gated:false — freely downloadable from HF Hub")
    print("  AUTO  — gated:auto  — accept via `uv run scripts/embed_gate_accept.py --model-id ID`")
    print("  FORM  — gated:manual — requires web form / org approval:")
    print("          `uv run scripts/embed_gate_accept.py --model-id ID --allow-playwright`")
    print("          or visit https://huggingface.co/{model_id} and request access")
    print()
    print("  TO ADD A MODEL: append entry to scripts/embed_model_registry.json models{}")
    print("  TO SWITCH ACTIVE: uv run scripts/embed_registry_switch.py --model-id <ID>")
    print("  FULL BATCH ACCEPT: bun run embed:gate:accept:all")
    print()


if __name__ == "__main__":
    main()
