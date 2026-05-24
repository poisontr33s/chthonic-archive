#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: hf_gemma_probe.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Hugging Face Gemma Probe (TATRAGRAMMATRON lane).

Purpose:
- Query the Hugging Face Hub API for Gemma-3 related repos (fine-tunes, merges, quantizations).
- Emit a deterministic shortlist JSON and a compact markdown report for mailbox ingestion.

Invocation:
- uv run scripts/hf_gemma_probe.py --search gemma-3 --limit 200 --out-json codex/mailbox/hf_gemma_probe.json --out-md codex/mailbox/HF_GEMMA_PROBE.md

Notes:
- Uses HF auth from env var `HF_TOKEN` if present.
- Does not write tokens anywhere.

@SID:           TOOL_HF_GEMMA_PROBE_V1
@Shabti:        CLI Script
@Purpose:       Hugging Face Gemma Probe (TATRAGRAMMATRON lane).
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from huggingface_hub import HfApi


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_get(d: Any, key: str, default=None):
    try:
        return d.get(key, default)
    except AttributeError:
        return default


@dataclass(frozen=True)
class ModelRow:
    repo_id: str
    author: str | None
    likes: int | None
    downloads: int | None
    gated: bool | None
    private: bool | None
    last_modified: str | None
    pipeline_tag: str | None
    library_name: str | None
    tags: list[str]
    inference: Any
    inference_provider_mapping: Any

    @staticmethod
    def from_model_info(mi: Any) -> "ModelRow":
        # huggingface_hub types are stable-ish but not strict; keep permissive extraction.
        return ModelRow(
            repo_id=getattr(mi, "id", None) or getattr(mi, "modelId", None) or "",
            author=getattr(mi, "author", None),
            likes=getattr(mi, "likes", None),
            downloads=getattr(mi, "downloads", None),
            gated=getattr(mi, "gated", None),
            private=getattr(mi, "private", None),
            last_modified=str(getattr(mi, "lastModified", None) or getattr(mi, "last_modified", None) or ""),
            pipeline_tag=getattr(mi, "pipeline_tag", None),
            library_name=getattr(mi, "library_name", None),
            tags=list(getattr(mi, "tags", None) or []),
            inference=getattr(mi, "inference", None),
            inference_provider_mapping=getattr(mi, "inferenceProviderMapping", None)
            or getattr(mi, "inference_provider_mapping", None),
        )


def score_row(row: ModelRow) -> float:
    # Deterministic scoring: prefer public + ungated, recent, high downloads/likes.
    score = 0.0
    if row.private:
        score -= 100.0
    if row.gated:
        score -= 10.0
    if row.downloads is not None:
        score += min(50.0, (row.downloads ** 0.5) / 10.0)
    if row.likes is not None:
        score += min(20.0, (row.likes ** 0.5) / 2.0)
    # Prefer repos explicitly tagged with gemma-3
    tags_lower = {t.lower() for t in row.tags}
    if any("gemma-3" in t for t in tags_lower):
        score += 5.0
    if any("gguf" in t for t in tags_lower):
        score += 2.0
    return round(score, 3)


def list_models(api: HfApi, search: str, limit: int) -> Iterable[Any]:
    # Expand inference info so we can see if hosted inference exists.
    return api.list_models(
        search=search,
        sort="downloads",
        limit=limit,
        expand=["author", "downloads", "likes", "gated", "private", "lastModified", "tags", "pipeline_tag", "library_name", "inference", "inferenceProviderMapping"],
    )


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_md(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = payload["top"]
    lines = [
        "# HF Gemma Probe",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Search: `{payload['search']}`",
        f"- Total fetched: `{payload['fetched']}`",
        f"- Top emitted: `{len(rows)}`",
        "",
        "## Top Candidates",
        "",
        "| Repo | Score | Downloads | Likes | Gated | Private | Last Modified | Tags |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in rows:
        tags = ", ".join(r["tags"][:8])
        lines.append(
            f"| `{r['repo_id']}` | `{r['score']}` | `{r.get('downloads')}` | `{r.get('likes')}` | `{r.get('gated')}` | `{r.get('private')}` | `{r.get('last_modified')}` | `{tags}` |"
        )
    lines += [
        "",
        "## Notes",
        "",
        "- This is Hub metadata only (not a benchmark).",
        "- If `gated=true`, you may need to accept model terms on the Hub UI before downloads/inference.",
        "- `inference_provider_mapping` presence indicates the model may be routable via Inference Providers; absence does not mean unusable.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    # Prefer API-pool env var when present; HF_TOKEN can be stale and overrides other auth.
    if os.getenv("HUGGINGFACE_HUB_TOKEN") and os.getenv("HF_TOKEN"):
        os.environ.pop("HF_TOKEN", None)

    ap = argparse.ArgumentParser()
    ap.add_argument("--search", default="gemma-3", help="Hub search query (default: gemma-3).")
    ap.add_argument("--limit", type=int, default=200, help="Max models to fetch.")
    ap.add_argument("--top", type=int, default=25, help="Top rows to emit.")
    ap.add_argument("--out-json", default="codex/mailbox/hf_gemma_probe.json")
    ap.add_argument("--out-md", default="codex/mailbox/HF_GEMMA_PROBE.md")
    args = ap.parse_args()

    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN") or None
    api = HfApi(token=token)

    fetched: list[ModelRow] = []
    for mi in list_models(api, args.search, args.limit):
        row = ModelRow.from_model_info(mi)
        if not row.repo_id:
            continue
        fetched.append(row)

    scored = []
    for r in fetched:
        scored.append({**asdict(r), "score": score_row(r)})
    scored.sort(key=lambda x: x["score"], reverse=True)

    payload = {
        "generated_at": utc_now_iso(),
        "search": args.search,
        "fetched": len(scored),
        "top": scored[: args.top],
    }

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    write_json(out_json, payload)
    write_md(out_md, payload)
    print(f"Wrote: {out_json.as_posix()}")
    print(f"Wrote: {out_md.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
