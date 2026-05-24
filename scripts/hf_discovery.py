#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: hf_discovery.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Hugging Face Discovery (local, token-aware).

Goal: provide "intermediate assistance" without MCP by emitting deterministic artifacts
that the trainstop orchestrator can validate.

Artifacts:
  - artifacts/hf_discovery_<kind>_<timestamp>.json
  - artifacts/hf_discovery_<kind>_<timestamp>.md

Notes:
  - Uses HF token from env (HF_TOKEN or HUGGINGFACE_HUB_TOKEN); does not print it.
  - Intended to be run via the canonical API manager loader:
      pwsh -NoProfile -Command ".\\.codex\\skills\\api-manager\\scripts\\api_manager.ps1 -Load | Out-Null; uv run scripts/hf_discovery.py ..."

@SID:           TOOL_HF_DISCOVERY_V1
@Shabti:        CLI Script
@Purpose:       Hugging Face Discovery (local, token-aware).
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from huggingface_hub import HfApi


REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = REPO_ROOT / "artifacts"


def _now_stamp() -> str:
    # Avoid ":" for Windows filenames.
    return time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime())


def _get_token() -> str | None:
    return os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN") or None


@dataclass(frozen=True)
class HFResult:
    kind: str
    id: str
    url: str | None
    likes: int | None
    downloads: int | None
    last_modified: str | None
    tags: list[str]


def _to_result(kind: str, obj: Any) -> HFResult:
    # huggingface_hub uses different info objects; normalize safely.
    rid = getattr(obj, "id", None) or getattr(obj, "modelId", None) or getattr(obj, "repo_id", None) or ""
    likes = getattr(obj, "likes", None)
    downloads = getattr(obj, "downloads", None)
    last_modified = getattr(obj, "lastModified", None) or getattr(obj, "last_modified", None)
    tags = getattr(obj, "tags", None)
    if not isinstance(tags, list):
        tags = []
    url = None
    if isinstance(rid, str) and rid:
        if kind == "models":
            url = f"https://huggingface.co/{rid}"
        elif kind == "datasets":
            url = f"https://huggingface.co/datasets/{rid}"
        elif kind == "spaces":
            url = f"https://huggingface.co/spaces/{rid}"
    return HFResult(
        kind=kind,
        id=str(rid),
        url=url,
        likes=int(likes) if isinstance(likes, int) else None,
        downloads=int(downloads) if isinstance(downloads, int) else None,
        last_modified=str(last_modified) if last_modified is not None else None,
        tags=[str(t) for t in tags if isinstance(t, (str, int, float))],
    )


def write_artifacts(kind: str, query: str, limit: int, results: list[HFResult]) -> tuple[Path, Path]:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = _now_stamp()
    base = ARTIFACTS_DIR / f"hf_discovery_{kind}_{stamp}"

    payload = {
        "schema_version": 1,
        "generated_on": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "kind": kind,
        "query": query,
        "limit": limit,
        "result_count": len(results),
        "results": [asdict(r) for r in results],
    }
    json_path = base.with_suffix(".json")
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")

    md_lines: list[str] = []
    md_lines.append(f"# HF Discovery ({kind})")
    md_lines.append("")
    md_lines.append(f"- Generated: `{payload['generated_on']}`")
    md_lines.append(f"- Query: `{query}`")
    md_lines.append(f"- Limit: `{limit}`")
    md_lines.append(f"- Results: `{len(results)}`")
    md_lines.append("")
    for r in results:
        md_lines.append(f"## `{r.id}`")
        if r.url:
            md_lines.append(f"- URL: `{r.url}`")
        if r.likes is not None:
            md_lines.append(f"- Likes: `{r.likes}`")
        if r.downloads is not None:
            md_lines.append(f"- Downloads: `{r.downloads}`")
        if r.last_modified:
            md_lines.append(f"- Last modified: `{r.last_modified}`")
        if r.tags:
            md_lines.append(f"- Tags: `{', '.join(r.tags[:30])}`")
        md_lines.append("")

    md_path = base.with_suffix(".md")
    md_path.write_text("\n".join(md_lines).rstrip() + "\n", encoding="utf-8", newline="\n")
    return json_path, md_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["models", "datasets", "spaces"], default="spaces")
    ap.add_argument("--q", required=True, help="Natural language query (HF search).")
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()

    token = _get_token()
    api = HfApi(token=token)

    # Auth check at startup: fail fast with a clear error if unauthenticated.
    try:
        api.whoami()
    except Exception as e:
        print(f"error: HF authentication failed — {type(e).__name__}: {e}", file=sys.stderr)
        print("Hint: set HF_TOKEN or HUGGINGFACE_HUB_TOKEN in your environment.", file=sys.stderr)
        return 1

    q = args.q.strip()
    limit = max(1, min(50, int(args.limit)))

    # Keep calls bounded and reliable; sort is HF-side best-effort.
    if args.kind == "models":
        items = list(api.list_models(search=q, limit=limit, full=False, sort="downloads"))
    elif args.kind == "datasets":
        items = list(api.list_datasets(search=q, limit=limit, full=False, sort="downloads"))
    else:
        items = list(api.list_spaces(search=q, limit=limit, full=False, sort="likes"))

    results = [_to_result(args.kind, it) for it in items if getattr(it, "id", None) or getattr(it, "modelId", None) or getattr(it, "repo_id", None)]
    json_path, md_path = write_artifacts(args.kind, q, limit, results)

    # Write LATEST alias (overwrites each run — always points at most recent output).
    for src_path, alias_name in [
        (json_path, f"hf_discovery_{args.kind}_LATEST.json"),
        (md_path, f"hf_discovery_{args.kind}_LATEST.md"),
    ]:
        alias_path = ARTIFACTS_DIR / alias_name
        alias_path.write_bytes(src_path.read_bytes())

    # Print only artifact paths (no secrets, minimal noise).
    print(f"Wrote: {json_path.as_posix()}")
    print(f"Wrote: {md_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
