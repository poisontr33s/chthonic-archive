#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Deterministic local model A/B benchmark for uncensored lanes.

Targets llama-cpp GGUF models installed in ./models and scores them on:
1) JSON structure adherence
2) Code generation correctness
3) Short instruction compliance

Usage:
  uv run scripts/benchmark_local_uncensored_lanes.py
  uv run scripts/benchmark_local_uncensored_lanes.py --include-qwen25
  uv run scripts/benchmark_local_uncensored_lanes.py --out benchmark.md --json-out benchmark.json
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
OUT_DIR = REPO_ROOT / "claude-codex-gemini" / "session_resumption_pickup"


@dataclass
class ModelTarget:
    lane: str
    model_dir: Path
    filename_pattern: str
    enabled: bool = True


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
    """Extract useful content from Harmony channel wrappers if present."""
    if "<|channel|>" not in text:
        return text.strip()

    final_match = re.search(
        r"<\|channel\|>\s*final.*?<\|message\|>(.*?)(?:<\|end\|>|$)",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if final_match:
        return final_match.group(1).strip()

    messages = list(
        re.finditer(
            r"<\|message\|>(.*?)(?:<\|end\|>|<\|start\|>|<\|channel\|>|$)",
            text,
            flags=re.DOTALL,
        )
    )
    if messages:
        return messages[-1].group(1).strip()

    cleaned = re.sub(r"<\|[^|]+\|>", "", text)
    return cleaned.strip()


def run_chat(llm: Any, system: str, user: str, max_tokens: int = 200) -> tuple[str, float, int]:
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


def eval_json_task(output: str) -> tuple[bool, str]:
    text = output.strip()
    # extract first json object if wrappers exist
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return False, "no-json-object"
    raw = match.group(0)
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return False, "json-parse-fail"

    needed = {"verdict", "reason", "score"}
    if not needed.issubset(obj.keys()):
        return False, "missing-keys"
    if obj.get("verdict") not in {"PROMOTE", "FLAG", "SKIP"}:
        return False, "bad-verdict"
    if not isinstance(obj.get("reason"), str) or not obj["reason"].strip():
        return False, "bad-reason"
    if not isinstance(obj.get("score"), int):
        return False, "score-not-int"
    return True, "ok"


def eval_code_task(output: str) -> tuple[bool, str]:
    text = output.strip()
    # strip markdown fences
    text = re.sub(r"^```(?:python)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    if "def fib(" not in text:
        return False, "missing-fib"

    namespace: dict[str, Any] = {}
    try:
        exec(text, {}, namespace)
    except Exception:
        return False, "code-compile-fail"

    fib = namespace.get("fib")
    if not callable(fib):
        return False, "fib-not-callable"
    try:
        ok = fib(0) == 0 and fib(1) == 1 and fib(10) == 55
    except Exception:
        return False, "fib-runtime-fail"
    return (True, "ok") if ok else (False, "fib-wrong-output")


def eval_instruction_task(output: str) -> tuple[bool, str]:
    text = output.strip()
    words = re.findall(r"[A-Za-z0-9_\-]+", text)
    if not words:
        return False, "empty"
    if len(words) > 18:
        return False, "too-long"
    if "entropy" not in text.lower():
        return False, "missing-keyword-entropy"
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

    system = "Return concise outputs. No markdown unless explicitly requested."

    tasks = [
        {
            "name": "json_task",
            "user": (
                'Return ONLY a JSON object with keys "verdict","reason","score". '
                'Constraints: verdict in ["PROMOTE","FLAG","SKIP"], reason <= 12 words, '
                "score is integer 0..100."
            ),
            "max_tokens": 120,
            "evaluator": eval_json_task,
        },
        {
            "name": "code_task",
            "user": (
                "Write only Python code for function `def fib(n: int) -> int:` "
                "iterative, no recursion, returns nth Fibonacci."
            ),
            "max_tokens": 220,
            "evaluator": eval_code_task,
        },
        {
            "name": "instruction_task",
            "user": (
                "In one short sentence (<= 15 words), describe why self-healing lanes reduce entropy."
            ),
            "max_tokens": 80,
            "evaluator": eval_instruction_task,
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

    lines: list[str] = [
        "---",
        "type: local-model-benchmark",
        "scope: uncensored-lane-a-b",
        f"generated: {generated.isoformat()}",
        "---",
        "",
        "# Local Uncensored Lane Benchmark",
        "",
        "| Lane | Composite | Passes | Avg toks/s | Load(s) | Model file |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in ranked:
        lines.append(
            f"| {row['lane']} | {row['composite_score']} | "
            f"{row['passes']}/{row['task_count']} | {row['avg_toks_per_s']} | "
            f"{row['load_seconds']} | {Path(row['model_file']).name} |"
        )

    for row in ranked:
        lines += [
            "",
            f"## {row['lane']}",
            "",
            f"- Model: `{row['model_file']}`",
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
                f"| {task['task']} | {status} | {task['detail']} | "
                f"{task['toks_per_s']} | {preview} |"
            )

    lines += [
        "",
        "## Selection Rule",
        "",
        "1. Highest composite score wins.",
        "2. Tie-breaker is higher avg tokens/s.",
        "",
    ]
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark local uncensored lanes deterministically.")
    parser.add_argument("--out", help="Markdown output path.")
    parser.add_argument("--json-out", help="JSON output path.")
    parser.add_argument("--n-ctx", type=int, default=4096)
    parser.add_argument("--n-gpu-layers", type=int, default=-1)
    parser.add_argument(
        "--include-qwen25",
        action="store_true",
        help="Include Qwen2.5-14B baseline lane in addition to uncensored lanes.",
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

    discovered: list[tuple[ModelTarget, Path]] = []
    for target in targets:
        file_path = find_model_file(target.model_dir, target.filename_pattern)
        if file_path is not None:
            discovered.append((target, file_path))

    if not discovered:
        raise SystemExit("No benchmark target models found in ./models.")

    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for target, file_path in discovered:
        try:
            print(f"[bench] {target.lane} -> {file_path.name}")
            result = benchmark_model(
                model_file=file_path,
                lane=target.lane,
                n_ctx=args.n_ctx,
                n_gpu_layers=args.n_gpu_layers,
            )
            results.append(result)
        except Exception as exc:
            failures.append({"lane": target.lane, "error": str(exc)})
            print(f"[bench] FAIL {target.lane}: {exc}")

    generated = utc_now()
    markdown = render_markdown(results, generated)
    payload = {
        "generated": generated.isoformat(),
        "results": results,
        "failures": failures,
        "config": {
            "n_ctx": args.n_ctx,
            "n_gpu_layers": args.n_gpu_layers,
            "include_qwen25": args.include_qwen25,
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = generated.strftime("%Y%m%d_%H%M%S")
    out_md = Path(args.out) if args.out else OUT_DIR / f"LOCAL_UNCENSORED_BENCHMARK_{stamp}.md"
    out_json = Path(args.json_out) if args.json_out else OUT_DIR / f"LOCAL_UNCENSORED_BENCHMARK_{stamp}.json"
    latest_md = OUT_DIR / "LOCAL_UNCENSORED_BENCHMARK_LATEST.md"

    out_md.write_text(markdown, encoding="utf-8")
    latest_md.write_text(markdown, encoding="utf-8")
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"benchmark_md={out_md}")
    print(f"benchmark_latest={latest_md}")
    print(f"benchmark_json={out_json}")
    if failures:
        print(f"failures={len(failures)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
