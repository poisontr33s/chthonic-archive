#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: uncensored_lane_steward.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Uncensored lane steward:
- read latest local benchmark results
- inspect local model inventory
- query live HF candidates (uncensored lanes)
- produce a quality-first lane recommendation packet

Usage:
  uv run scripts/uncensored_lane_steward.py

@SID:           TOOL_UNCENSORED_LANE_STEWARD_V1
@Shabti:        CLI Script
@Purpose:       Uncensored lane steward:
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from huggingface_hub import HfApi


REPO_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = REPO_ROOT / "models"
OUT_DIR = REPO_ROOT / "claude-codex-gemini" / "session_resumption_pickup"


@dataclass
class LocalModel:
    name: str
    path: Path
    total_bytes: int
    newest_mtime: float
    gguf_files: int
    exl2_files: int
    safetensors_files: int


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def read_latest_benchmark() -> dict[str, Any] | None:
    candidates = sorted(
        OUT_DIR.glob("LOCAL_UNCENSORED_BENCHMARK_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return None
    try:
        return json.loads(candidates[0].read_text(encoding="utf-8"))
    except Exception:
        return None


def scan_local_models() -> list[LocalModel]:
    if not MODELS_DIR.exists():
        return []
    out: list[LocalModel] = []
    for d in sorted(MODELS_DIR.iterdir()):
        if not d.is_dir():
            continue
        files = [f for f in d.rglob("*") if f.is_file()]
        if not files:
            continue
        total = sum(f.stat().st_size for f in files)
        newest = max(f.stat().st_mtime for f in files)
        gguf = sum(1 for f in files if f.suffix.lower() == ".gguf")
        exl2 = sum(1 for f in files if f.suffix.lower() == ".exl2")
        safetensors = sum(1 for f in files if f.suffix.lower() == ".safetensors")
        out.append(
            LocalModel(
                name=d.name,
                path=d,
                total_bytes=total,
                newest_mtime=newest,
                gguf_files=gguf,
                exl2_files=exl2,
                safetensors_files=safetensors,
            )
        )
    return out


def score_local_lanes(benchmark: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not benchmark:
        return []
    rows = []
    for row in benchmark.get("results", []):
        lane = row.get("lane", "unknown")
        composite = float(row.get("composite_score", 0.0))
        toks = float(row.get("avg_toks_per_s", 0.0))
        # quality-first score: prioritize correctness, then speed.
        score = composite * 1000.0 + toks
        rows.append(
            {
                "lane": lane,
                "composite_score": composite,
                "avg_toks_per_s": toks,
                "score": round(score, 4),
                "model_file": row.get("model_file"),
                "tasks": row.get("tasks", []),
            }
        )
    return sorted(rows, key=lambda x: x["score"], reverse=True)


def parse_iso(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        # HF often returns "2026-02-19T..Z"
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def is_uncensored_candidate(model_id: str) -> bool:
    lower = model_id.lower()
    flags = ["uncensored", "abliterated", "heretic", "derestricted", "unfiltered"]
    return any(flag in lower for flag in flags)


def has_quant_artifacts(siblings: list[Any]) -> dict[str, bool]:
    names = [getattr(s, "rfilename", "") for s in siblings]
    lower = [n.lower() for n in names]
    return {
        "gguf": any(n.endswith(".gguf") for n in lower),
        "safetensors": any(n.endswith(".safetensors") for n in lower),
        "awq": any("awq" in n for n in lower),
        "gptq": any("gptq" in n for n in lower),
        "exl2": any(".exl2" in n or "exl2" in n for n in lower),
    }


def fetch_live_hf_candidates(limit_per_query: int = 25, top_n: int = 30) -> list[dict[str, Any]]:
    token = os.getenv("HUGGINGFACE_HUB_TOKEN") or os.getenv("HF_TOKEN") or None
    api = HfApi(token=token)

    queries = [
        "uncensored gguf",
        "abliterated gguf",
        "heretic gguf",
        "qwen3 abliterated gguf",
        "gpt-oss uncensored gguf",
    ]

    seen: dict[str, dict[str, Any]] = {}
    for query in queries:
        try:
            models = api.list_models(search=query, sort="lastModified", limit=limit_per_query)
        except Exception:
            continue
        for m in models:
            model_id = getattr(m, "id", None)
            if not model_id or not is_uncensored_candidate(model_id):
                continue
            if model_id not in seen:
                seen[model_id] = {
                    "id": model_id,
                    "downloads": int(getattr(m, "downloads", 0) or 0),
                    "likes": int(getattr(m, "likes", 0) or 0),
                    "last_modified": str(getattr(m, "last_modified", "")),
                }

    # enrich top recency+downloads candidates with quantization artifacts
    prelim = sorted(
        seen.values(),
        key=lambda x: (x["downloads"], x["likes"], x["last_modified"]),
        reverse=True,
    )[:top_n]

    enriched: list[dict[str, Any]] = []
    now = utc_now()
    for row in prelim:
        model_id = row["id"]
        artifacts = {"gguf": False, "safetensors": False, "awq": False, "gptq": False, "exl2": False}
        try:
            info = api.model_info(model_id)
            artifacts = has_quant_artifacts(getattr(info, "siblings", []) or [])
            last_dt = parse_iso(str(getattr(info, "last_modified", "")))
            if last_dt is not None:
                row["last_modified"] = last_dt.isoformat()
        except Exception:
            pass

        last_dt = parse_iso(row.get("last_modified"))
        age_days = 9999.0
        if last_dt:
            age_days = max(0.0, (now - last_dt).total_seconds() / 86400.0)

        recency_boost = 1.0 / (1.0 + math.log10(age_days + 1.0))
        popularity = math.log10(max(1, row["downloads"])) + 0.25 * math.log10(max(1, row["likes"] + 1))
        quant_bonus = (
            (1.0 if artifacts["gguf"] else 0.0)
            + (0.5 if artifacts["safetensors"] else 0.0)
            + (0.5 if artifacts["awq"] or artifacts["gptq"] or artifacts["exl2"] else 0.0)
        )
        score = popularity + recency_boost + quant_bonus

        enriched.append(
            {
                **row,
                "artifacts": artifacts,
                "age_days": round(age_days, 2),
                "live_score": round(score, 4),
            }
        )

    return sorted(enriched, key=lambda x: x["live_score"], reverse=True)


def compute_lane_policy(local_ranked: list[dict[str, Any]]) -> dict[str, Any]:
    # Defaults when no benchmark data exists.
    policy = {
        "strict_json_lane": {"lane": None, "reason": "no benchmark"},
        "code_lane": {"lane": None, "reason": "no benchmark"},
        "unrestricted_lane": {"lane": None, "reason": "no benchmark"},
        "demoted_lanes": [],
    }
    if not local_ranked:
        return policy

    by_name = {r["lane"]: r for r in local_ranked}
    best = local_ranked[0]
    policy["strict_json_lane"] = {"lane": best["lane"], "reason": "highest quality-first score"}

    # Prefer coder lane for code if present and valid.
    coder = next((r for r in local_ranked if "coder" in r["lane"]), None)
    policy["code_lane"] = {
        "lane": (coder or best)["lane"],
        "reason": "coder-specialized lane preferred when available",
    }

    # Unrestricted lane should still pass quality checks.
    instr = next((r for r in local_ranked if "instruct" in r["lane"]), None)
    policy["unrestricted_lane"] = {
        "lane": (instr or best)["lane"],
        "reason": "best uncensored compliance lane with quality guarantees",
    }

    for lane in local_ranked:
        if lane["composite_score"] < 100.0:
            policy["demoted_lanes"].append(
                {
                    "lane": lane["lane"],
                    "reason": f"composite_score={lane['composite_score']} < 100.0",
                }
            )

    # Explicit demotion for GPT-OSS lane if present and failing.
    gpt_oss = by_name.get("gpt_oss_20b_neoplus_uncensored")
    if gpt_oss and gpt_oss["composite_score"] < 100.0:
        policy["demoted_lanes"].append(
            {
                "lane": gpt_oss["lane"],
                "reason": "fails structured output compliance; keep experimental only",
            }
        )

    return policy


def extract_quant_tag(model_file: str | None) -> str:
    if not model_file:
        return "unknown"
    name = Path(model_file).name.upper()
    patterns = [
        r"(IQ[0-9]_[A-Z0-9_]+)",
        r"(Q[0-9]_[A-Z0-9_]+)",
        r"(Q[0-9](?:_[A-Z0-9_]+)?)",
        r"(MXFP4)",
    ]
    for pattern in patterns:
        match = re.search(pattern, name)
        if match:
            return match.group(1)
    return "unknown"


def quant_preferences_for_role(role: str) -> list[str]:
    if role in {"strict_json", "code"}:
        return ["Q6_K", "Q5_K_M", "Q5_K_S", "Q4_K_M"]
    return ["Q5_K_M", "Q4_K_M", "Q4_K_S", "Q3_K_M"]


def build_runtime_payload(
    generated: datetime, local_ranked: list[dict[str, Any]], policy: dict[str, Any]
) -> dict[str, Any]:
    by_lane = {str(r.get("lane")): r for r in local_ranked}
    policy_roles = {
        "strict_json": "strict_json_lane",
        "code": "code_lane",
        "unrestricted": "unrestricted_lane",
    }

    lanes: dict[str, Any] = {}
    for role, policy_key in policy_roles.items():
        policy_row = policy.get(policy_key, {})
        lane_name = policy_row.get("lane")
        ranked_row = by_lane.get(str(lane_name), {})
        model_file = ranked_row.get("model_file")
        model_path = Path(model_file) if isinstance(model_file, str) and model_file else None
        lanes[role] = {
            "lane": lane_name,
            "reason": policy_row.get("reason"),
            "model_file": model_file,
            "model_exists": bool(model_path and model_path.exists()),
            "quant_tag": extract_quant_tag(model_file if isinstance(model_file, str) else None),
            "composite_score": ranked_row.get("composite_score"),
            "avg_toks_per_s": ranked_row.get("avg_toks_per_s"),
            "recommended_quant_targets": quant_preferences_for_role(role),
        }

    default_lane = "strict_json"
    if not lanes.get(default_lane, {}).get("model_exists"):
        fallback = next((k for k, v in lanes.items() if v.get("model_exists")), None)
        if fallback:
            default_lane = fallback

    default_model = lanes.get(default_lane, {}).get("model_file")
    endpoint = {
        "host": "127.0.0.1",
        "port": 8000,
        "base_url": "http://127.0.0.1:8000/v1",
        "chat_completions_path": "/chat/completions",
        "compatibility": "openai-style-http",
    }

    return {
        "generated": generated.isoformat(),
        "default_lane": default_lane,
        "default_model_file": default_model,
        "endpoint_defaults": endpoint,
        "lanes": lanes,
        "commands": {
            "refresh_benchmark": "uv run scripts/benchmark_local_uncensored_lanes.py --include-qwen25",
            "refresh_policy": "uv run scripts/uncensored_lane_steward.py",
            "serve_strict_json": "pwsh -NoProfile -File scripts/serve_uncensored_lane.ps1 -Lane strict_json",
            "serve_code": "pwsh -NoProfile -File scripts/serve_uncensored_lane.ps1 -Lane code",
            "serve_unrestricted": "pwsh -NoProfile -File scripts/serve_uncensored_lane.ps1 -Lane unrestricted",
        },
    }


def render_runtime_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = [
        "---",
        "type: uncensored-lane-runtime",
        f"generated: {payload.get('generated')}",
        "---",
        "",
        "# Uncensored Lane Runtime Manifest",
        "",
        f"- Default lane: `{payload.get('default_lane')}`",
        f"- Default model: `{Path(str(payload.get('default_model_file') or '')).name}`",
        f"- Base URL: `{payload.get('endpoint_defaults', {}).get('base_url')}`",
        "",
        "## Lane Routing",
        "",
        "| Role | Lane | Model | Exists | Quant | Composite | toks/s |",
        "| --- | --- | --- | --- | --- | ---: | ---: |",
    ]

    for role in ("strict_json", "code", "unrestricted"):
        row = payload.get("lanes", {}).get(role, {})
        lines.append(
            f"| {role} | {row.get('lane') or 'n/a'} | "
            f"{Path(str(row.get('model_file') or '')).name or 'n/a'} | "
            f"{'Y' if row.get('model_exists') else 'N'} | {row.get('quant_tag') or 'unknown'} | "
            f"{row.get('composite_score') or 0} | {row.get('avg_toks_per_s') or 0} |"
        )

    lines += [
        "",
        "## Launch Commands",
        "",
        f"- strict JSON: `{payload['commands']['serve_strict_json']}`",
        f"- code: `{payload['commands']['serve_code']}`",
        f"- unrestricted: `{payload['commands']['serve_unrestricted']}`",
        "",
    ]
    return "\n".join(lines).strip() + "\n"


def render_runtime_env(payload: dict[str, Any]) -> str:
    lanes = payload.get("lanes", {})
    endpoint = payload.get("endpoint_defaults", {})
    lines = [
        f"CHTHONIC_LLM_BASE_URL={endpoint.get('base_url', '')}",
        f"CHTHONIC_LLM_DEFAULT_LANE={payload.get('default_lane', '')}",
        f"CHTHONIC_LLM_DEFAULT_MODEL_PATH={payload.get('default_model_file', '') or ''}",
        f"CHTHONIC_LLM_STRICT_JSON_MODEL_PATH={lanes.get('strict_json', {}).get('model_file', '') or ''}",
        f"CHTHONIC_LLM_CODE_MODEL_PATH={lanes.get('code', {}).get('model_file', '') or ''}",
        f"CHTHONIC_LLM_UNRESTRICTED_MODEL_PATH={lanes.get('unrestricted', {}).get('model_file', '') or ''}",
    ]
    return "\n".join(lines).strip() + "\n"


def render_markdown(payload: dict[str, Any]) -> str:
    generated = payload["generated"]
    lines: list[str] = [
        "---",
        "type: uncensored-lane-steward",
        f"generated: {generated}",
        "---",
        "",
        "# Uncensored Lane Steward",
        "",
        "## Policy",
        "",
    ]

    policy = payload["lane_policy"]
    lines.append(f"- Strict JSON lane: `{policy['strict_json_lane']['lane']}` ({policy['strict_json_lane']['reason']})")
    lines.append(f"- Code lane: `{policy['code_lane']['lane']}` ({policy['code_lane']['reason']})")
    lines.append(
        f"- Unrestricted lane: `{policy['unrestricted_lane']['lane']}` ({policy['unrestricted_lane']['reason']})"
    )
    if policy["demoted_lanes"]:
        lines.append("- Demoted lanes:")
        for item in policy["demoted_lanes"][:6]:
            lines.append(f"  - `{item['lane']}`: {item['reason']}")

    lines += [
        "",
        "## Local Ranked Lanes",
        "",
        "| Lane | Composite | Avg toks/s | Score | Model file |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload["local_ranked_lanes"]:
        lines.append(
            f"| {row['lane']} | {row['composite_score']} | {row['avg_toks_per_s']} | "
            f"{row['score']} | {Path(str(row.get('model_file') or '')).name} |"
        )

    lines += [
        "",
        "## Live HF Candidates (Uncensored + Quantization-friendly)",
        "",
        "| Model | Downloads | Likes | Age(days) | GGUF | SAFETENSORS | AWQ/GPTQ/EXL2 | Score |",
        "| --- | ---: | ---: | ---: | --- | --- | --- | ---: |",
    ]
    for row in payload["hf_live_candidates"][:20]:
        art = row["artifacts"]
        awq_mix = art["awq"] or art["gptq"] or art["exl2"]
        lines.append(
            f"| `{row['id']}` | {row['downloads']} | {row['likes']} | {row['age_days']} | "
            f"{'Y' if art['gguf'] else 'N'} | {'Y' if art['safetensors'] else 'N'} | "
            f"{'Y' if awq_mix else 'N'} | {row['live_score']} |"
        )

    lines += [
        "",
        "## Quantization Guidance",
        "",
        "- Default quality lane: `Q5_K_M` or `Q6_K` (GGUF) for JSON-critical tasks.",
        "- Throughput lane: `Q4_K_M` when latency matters more than instruction exactness.",
        "- Cross-language serving lane: host via `llama_cpp.server` (OpenAI-style HTTP) to make model access language-agnostic.",
        "",
    ]
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    generated = utc_now()
    benchmark = read_latest_benchmark()
    local_ranked = score_local_lanes(benchmark)
    local_models = scan_local_models()
    hf_candidates = fetch_live_hf_candidates()
    policy = compute_lane_policy(local_ranked)
    runtime_payload = build_runtime_payload(generated, local_ranked, policy)

    payload = {
        "generated": generated.isoformat(),
        "local_ranked_lanes": local_ranked,
        "local_models": [
            {
                "name": m.name,
                "path": str(m.path),
                "total_gb": round(m.total_bytes / (1024**3), 3),
                "newest_mtime_utc": datetime.fromtimestamp(m.newest_mtime, tz=timezone.utc).isoformat(),
                "artifacts": {
                    "gguf_files": m.gguf_files,
                    "exl2_files": m.exl2_files,
                    "safetensors_files": m.safetensors_files,
                },
            }
            for m in local_models
        ],
        "hf_live_candidates": hf_candidates,
        "lane_policy": policy,
        "source": {
            "benchmark_json_present": benchmark is not None,
            "benchmark_file_pattern": "LOCAL_UNCENSORED_BENCHMARK_*.json",
            "hf_queries": [
                "uncensored gguf",
                "abliterated gguf",
                "heretic gguf",
                "qwen3 abliterated gguf",
                "gpt-oss uncensored gguf",
            ],
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = generated.strftime("%Y%m%d_%H%M%S")
    out_json = OUT_DIR / f"UNCENSORED_LANE_STEWARD_{stamp}.json"
    out_md = OUT_DIR / f"UNCENSORED_LANE_STEWARD_{stamp}.md"
    latest_json = OUT_DIR / "UNCENSORED_LANE_STEWARD_LATEST.json"
    latest_md = OUT_DIR / "UNCENSORED_LANE_STEWARD_LATEST.md"
    runtime_json = OUT_DIR / f"UNCENSORED_LANE_RUNTIME_{stamp}.json"
    runtime_md = OUT_DIR / f"UNCENSORED_LANE_RUNTIME_{stamp}.md"
    runtime_env = OUT_DIR / f"UNCENSORED_LANE_RUNTIME_{stamp}.env"
    runtime_latest_json = OUT_DIR / "UNCENSORED_LANE_RUNTIME_LATEST.json"
    runtime_latest_md = OUT_DIR / "UNCENSORED_LANE_RUNTIME_LATEST.md"
    runtime_latest_env = OUT_DIR / "UNCENSORED_LANE_RUNTIME_LATEST.env"

    markdown = render_markdown(payload)
    runtime_markdown = render_runtime_markdown(runtime_payload)
    runtime_env_content = render_runtime_env(runtime_payload)
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    out_md.write_text(markdown, encoding="utf-8")
    latest_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    latest_md.write_text(markdown, encoding="utf-8")
    runtime_json.write_text(json.dumps(runtime_payload, indent=2), encoding="utf-8")
    runtime_md.write_text(runtime_markdown, encoding="utf-8")
    runtime_env.write_text(runtime_env_content, encoding="utf-8")
    runtime_latest_json.write_text(json.dumps(runtime_payload, indent=2), encoding="utf-8")
    runtime_latest_md.write_text(runtime_markdown, encoding="utf-8")
    runtime_latest_env.write_text(runtime_env_content, encoding="utf-8")

    print(f"steward_json={out_json}")
    print(f"steward_md={out_md}")
    print(f"latest_json={latest_json}")
    print(f"latest_md={latest_md}")
    print(f"runtime_json={runtime_json}")
    print(f"runtime_md={runtime_md}")
    print(f"runtime_env={runtime_env}")
    print(f"runtime_latest_json={runtime_latest_json}")
    print(f"runtime_latest_md={runtime_latest_md}")
    print(f"runtime_latest_env={runtime_latest_env}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
