#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: benchmark_delegation_lanes.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Deterministic delegation benchmark for local GGUF lanes.

Usage:
  uv run scripts/benchmark_delegation_lanes.py
  uv run scripts/benchmark_delegation_lanes.py --lanes qwen25_14b_baseline

@SID:           TOOL_BENCHMARK_DELEGATION_LANES_V1
@Shabti:        CLI Script
@Purpose:       Deterministic delegation benchmark for local GGUF lanes.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = REPO_ROOT / "models"
OUT_DIR = REPO_ROOT / "codex" / "artifacts"
DEFAULT_JSON_OUT = OUT_DIR / "DELEGATION_BENCHMARK_CANONICAL.json"
DEFAULT_MD_OUT = OUT_DIR / "DELEGATION_BENCHMARK_CANONICAL.md"


@dataclass
class ModelTarget:
    lane: str
    model_dir: Path
    filename_pattern: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def find_model_file(model_dir: Path, filename_pattern: str) -> Path | None:
    if not model_dir.exists():
        return None
    candidates = sorted(model_dir.glob(filename_pattern))
    return candidates[0] if candidates else None


def tokenize_count(llm: Any, text: str) -> int:
    try:
        return len(llm.tokenize(text.encode("utf-8"), add_bos=False))
    except Exception:
        return max(1, len(text.split()))


def normalize_harmony_output(text: str) -> str:
    if "<|channel|>" not in text:
        return text.strip()
    final_match = re.search(
        r"<\|channel\|>\s*final.*?<\|message\|>(.*?)(?:<\|end\|>|$)",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if final_match:
        return final_match.group(1).strip()
    cleaned = re.sub(r"<\|[^|]+\|>", "", text)
    return cleaned.strip()


def run_chat(llm: Any, system: str, user: str, max_tokens: int = 300) -> tuple[str, float, int]:
    t0 = time.perf_counter()
    result = llm.create_chat_completion(
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.0,
        top_p=1.0,
        max_tokens=max_tokens,
    )
    elapsed = max(1e-6, time.perf_counter() - t0)
    raw_content = result["choices"][0]["message"]["content"]
    content = normalize_harmony_output(raw_content)
    out_tokens = tokenize_count(llm, content)
    return content, elapsed, out_tokens


def extract_json(text: str) -> dict[str, Any] | None:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def eval_schema_task(output: str) -> tuple[bool, str]:
    obj = extract_json(output)
    if not obj:
        return False, "json-parse-fail"
    if set(obj.keys()) != {"verdict", "confidence", "reason"}:
        return False, "wrong-keys"
    if obj["verdict"] not in {"PROMOTE", "HOLD", "REJECT"}:
        return False, "bad-verdict"
    if not isinstance(obj["confidence"], int):
        return False, "confidence-not-int"
    if not isinstance(obj["reason"], str) or len(obj["reason"].split()) > 12:
        return False, "bad-reason"
    return True, "ok"


def eval_plan_task(output: str) -> tuple[bool, str]:
    obj = extract_json(output)
    if not obj:
        return False, "json-parse-fail"
    steps = obj.get("steps")
    if not isinstance(steps, list) or not 4 <= len(steps) <= 7:
        return False, "bad-step-count"
    for step in steps:
        if not isinstance(step, dict):
            return False, "step-not-object"
        if set(step.keys()) != {"id", "action", "why"}:
            return False, "bad-step-keys"
        if not isinstance(step["id"], str) or not step["id"].startswith("S"):
            return False, "bad-id"
    return True, "ok"


def eval_tool_task(output: str) -> tuple[bool, str]:
    obj = extract_json(output)
    if not obj:
        return False, "json-parse-fail"
    calls = obj.get("tool_calls")
    if not isinstance(calls, list) or len(calls) != 1:
        return False, "bad-tool-call-count"
    call = calls[0]
    if call.get("name") != "benchmark_candidate":
        return False, "wrong-tool-name"
    args = call.get("arguments")
    if not isinstance(args, dict):
        return False, "bad-arguments"
    if args.get("runtime") not in {"vllm", "mistralrs", "llama_cpp"}:
        return False, "bad-runtime"
    if not isinstance(args.get("model"), str) or not args["model"]:
        return False, "missing-model"
    return True, "ok"


def eval_synthesis_task(output: str) -> tuple[bool, str]:
    obj = extract_json(output)
    if not obj:
        return False, "json-parse-fail"
    if obj.get("winner") != "B":
        return False, "wrong-winner"
    evidence_ids = obj.get("evidence_ids")
    if evidence_ids != ["E2", "E4"]:
        return False, "wrong-evidence"
    return True, "ok"


def eval_revision_task(output: str) -> tuple[bool, str]:
    obj = extract_json(output)
    if not obj:
        return False, "json-parse-fail"
    final_answer = str(obj.get("final_answer", "")).lower()
    superseded = str(obj.get("superseded_claim", "")).lower()
    if "nvfp4" not in final_answer:
        return False, "missed-correction"
    if "bf16 is feasible on a single 4090" not in superseded:
        return False, "missing-superseded-claim"
    return True, "ok"


def benchmark_model(model_file: Path, lane: str, n_ctx: int, n_gpu_layers: int) -> dict[str, Any]:
    from llama_cpp import Llama

    load_t0 = time.perf_counter()
    llm = Llama(
        model_path=str(model_file),
        n_gpu_layers=n_gpu_layers,
        n_ctx=n_ctx,
        seed=42,
        verbose=False,
    )
    load_seconds = time.perf_counter() - load_t0
    system = "Return only the requested output. Prefer valid JSON when asked."

    tasks = [
        {
            "name": "schema_task",
            "user": (
                'Return ONLY JSON with keys "verdict","confidence","reason". '
                'Use verdict PROMOTE/HOLD/REJECT, confidence integer 0..100, '
                "reason <= 12 words."
            ),
            "max_tokens": 120,
            "evaluator": eval_schema_task,
        },
        {
            "name": "plan_task",
            "user": (
                "A local model candidate is too large for direct BF16 on 24 GB VRAM. "
                'Return ONLY JSON: {"steps":[...]} with 4 to 7 step objects. '
                'Each step object must have keys "id","action","why". Use ids S1,S2,...'
            ),
            "max_tokens": 260,
            "evaluator": eval_plan_task,
        },
        {
            "name": "tool_task",
            "user": (
                "Pick a first benchmark attempt for Gemma 4 on a 4090. "
                'Return ONLY JSON with {"tool_calls":[{"name":"benchmark_candidate","arguments":{"model":"...","runtime":"...","reason":"..."}}]}. '
                "Allowed runtimes: vllm, mistralrs, llama_cpp."
            ),
            "max_tokens": 220,
            "evaluator": eval_tool_task,
        },
        {
            "name": "synthesis_task",
            "user": (
                "Evidence packet: "
                "E1: mistral.rs docs do not list Gemma 4. "
                "E2: vLLM docs explicitly support Gemma 4. "
                "E3: NIM needs >110 GB BF16. "
                "E4: NVFP4 Gemma 4 claims much lower memory use. "
                'Return ONLY JSON {"winner":"A|B","evidence_ids":["...","..."]}. '
                "A means keep mistralrs first. B means keep vllm first."
            ),
            "max_tokens": 120,
            "evaluator": eval_synthesis_task,
        },
        {
            "name": "revision_task",
            "user": (
                "Initial claim: BF16 is feasible on a single 4090. "
                "Correction: vLLM lists Gemma 4 31B BF16 at 1x80 GB, while NVFP4 is the plausible 24 GB route. "
                'Return ONLY JSON with keys "final_answer" and "superseded_claim".'
            ),
            "max_tokens": 180,
            "evaluator": eval_revision_task,
        },
    ]

    task_results: list[dict[str, Any]] = []
    total_tokens = 0
    total_seconds = 0.0
    passes = 0

    for task in tasks:
        output, elapsed, out_tokens = run_chat(
            llm, system, task["user"], max_tokens=task["max_tokens"]
        )
        ok, detail = task["evaluator"](output)
        if ok:
            passes += 1
        total_tokens += out_tokens
        total_seconds += elapsed
        task_results.append(
            {
                "task": task["name"],
                "ok": ok,
                "detail": detail,
                "elapsed_s": round(elapsed, 4),
                "out_tokens": out_tokens,
                "toks_per_s": round(out_tokens / max(elapsed, 1e-6), 2),
                "output_preview": output.strip().replace("\n", " ")[:260],
            }
        )

    composite = round((passes / len(tasks)) * 100.0, 1)
    avg_toks_per_s = round(total_tokens / max(total_seconds, 1e-6), 2)
    return {
        "lane": lane,
        "model_file": str(model_file),
        "load_seconds": round(load_seconds, 3),
        "tasks": task_results,
        "passes": passes,
        "task_count": len(tasks),
        "composite_score": composite,
        "avg_toks_per_s": avg_toks_per_s,
        "total_tokens": total_tokens,
        "total_infer_seconds": round(total_seconds, 4),
    }


def render_markdown(results: list[dict[str, Any]], generated: datetime) -> str:
    ranked = sorted(
        results,
        key=lambda r: (r.get("composite_score", 0), r.get("avg_toks_per_s", 0)),
        reverse=True,
    )
    lines = [
        "---",
        "type: local-delegation-benchmark",
        f"generated: {generated.isoformat()}",
        "---",
        "",
        "# Local Delegation Benchmark",
        "",
        "| Lane | Composite | Passes | Avg toks/s | Load(s) | Model file |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in ranked:
        lines.append(
            f"| {row['lane']} | {row['composite_score']} | {row['passes']}/{row['task_count']} | "
            f"{row['avg_toks_per_s']} | {row['load_seconds']} | {Path(row['model_file']).name} |"
        )
    for row in ranked:
        lines += [
            "",
            f"## {row['lane']}",
            "",
            f"- Composite: **{row['composite_score']}** ({row['passes']}/{row['task_count']})",
            f"- Throughput: `{row['avg_toks_per_s']} tokens/s`",
            "",
            "| Task | Status | Detail | toks/s | Output preview |",
            "| --- | --- | --- | --- | --- |",
        ]
        for task in row["tasks"]:
            status = "OK" if task["ok"] else "FAIL"
            preview = task["output_preview"].replace("|", "\\|")
            lines.append(
                f"| {task['task']} | {status} | {task['detail']} | {task['toks_per_s']} | {preview} |"
            )
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark delegation behavior on local GGUF lanes.")
    parser.add_argument("--out", help="Markdown output path.")
    parser.add_argument("--json-out", help="JSON output path.")
    parser.add_argument("--write-md", action="store_true", help="Write a human-readable markdown mirror.")
    parser.add_argument("--n-ctx", type=int, default=4096)
    parser.add_argument("--n-gpu-layers", type=int, default=-1)
    parser.add_argument("--lanes", help="Comma-separated lane names to limit execution.")
    parser.add_argument(
        "--include-qwen25",
        action="store_true",
        help="Include the Qwen2.5 14B baseline lane.",
    )
    args = parser.parse_args()

    targets = [
        ModelTarget(
            lane="qwen3_instruct_abliterated",
            model_dir=MODELS_DIR / "Qwen3-30B-A3B-Instruct-abliterated-GGUF",
            filename_pattern="*.gguf",
        ),
        ModelTarget(
            lane="qwen3_coder_abliterated",
            model_dir=MODELS_DIR / "Qwen3-Coder-30B-A3B-abliterated-GGUF",
            filename_pattern="*.gguf",
        ),
        ModelTarget(
            lane="gpt_oss_20b_neoplus_uncensored",
            model_dir=MODELS_DIR / "GPT-OSS-20B-NEOPlus-Uncensored",
            filename_pattern="*.gguf",
        ),
    ]
    if args.include_qwen25:
        targets.append(
            ModelTarget(
                lane="qwen25_14b_baseline",
                model_dir=MODELS_DIR / "Qwen2.5-14B-Instruct-GGUF",
                filename_pattern="*00001-of-00003.gguf",
            )
        )

    if args.lanes:
        allowed = {part.strip() for part in args.lanes.split(",") if part.strip()}
        targets = [target for target in targets if target.lane in allowed]

    discovered: list[tuple[ModelTarget, Path]] = []
    for target in targets:
        file_path = find_model_file(target.model_dir, target.filename_pattern)
        if file_path is not None:
            discovered.append((target, file_path))
    if not discovered:
        raise SystemExit("No delegation benchmark target models found.")

    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for target, file_path in discovered:
        try:
            print(f"[bench] {target.lane} -> {file_path.name}")
            results.append(
                benchmark_model(
                    model_file=file_path,
                    lane=target.lane,
                    n_ctx=args.n_ctx,
                    n_gpu_layers=args.n_gpu_layers,
                )
            )
        except Exception as exc:
            failures.append({"lane": target.lane, "error": str(exc)})
            print(f"[bench] FAIL {target.lane}: {exc}")

    generated = utc_now()
    payload = {
        "generated": generated.isoformat(),
        "results": results,
        "failures": failures,
        "config": {
            "n_ctx": args.n_ctx,
            "n_gpu_layers": args.n_gpu_layers,
            "lanes": args.lanes,
            "include_qwen25": args.include_qwen25,
        },
    }
    markdown = render_markdown(results, generated)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_json = Path(args.json_out) if args.json_out else DEFAULT_JSON_OUT
    write_md = bool(args.write_md or args.out)
    out_md = Path(args.out) if args.out else DEFAULT_MD_OUT if write_md else None

    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if out_md is not None:
        out_md.write_text(markdown, encoding="utf-8")

    print(f"benchmark_json={out_json}")
    if out_md is not None:
        print(f"benchmark_md={out_md}")
    if failures:
        print(f"failures={len(failures)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
