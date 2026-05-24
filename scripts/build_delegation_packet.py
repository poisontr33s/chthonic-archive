#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: build_delegation_packet.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Build a high-context delegation packet from live local state plus curated
evidence snapshots for impossible-on-paper tasks.

Usage:
  uv run scripts/build_delegation_packet.py --preset gemma4-local-delegation
  uv run scripts/build_delegation_packet.py --preset gemma4-local-delegation --mission "..."

@SID:           TOOL_BUILD_DELEGATION_PACKET_V1
@Shabti:        CLI Script
@Purpose:       Build a live delegation packet for high-context agent tasks.
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = REPO_ROOT / "models"
OUT_DIR = REPO_ROOT / "codex" / "artifacts"
RESIDUE_REF = OUT_DIR / "ANKH_LOGICAL_RESIDUE_REFERENCE.toml"
EQUIVALENCE_REF = OUT_DIR / "INVARIANT_EQUIVALENCE_REGISTRY.toml"
DEFAULT_JSON_OUT = OUT_DIR / "DELEGATION_PACKET_CANONICAL.json"
DEFAULT_MD_OUT = OUT_DIR / "DELEGATION_PACKET_CANONICAL.md"


@dataclass
class LocalModel:
    name: str
    path: str
    artifact_type: str
    total_gb: float


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def run_output(cmd: list[str]) -> str | None:
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    except Exception:
        return None
    text = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    return text or None


def run_json(cmd: list[str]) -> dict[str, Any] | None:
    text = run_output(cmd)
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def powershell_value(command: str) -> str | None:
    return run_output(["powershell", "-NoProfile", "-Command", command])


def detect_cpu() -> dict[str, str]:
    output = powershell_value(
        "(Get-CimInstance Win32_Processor | "
        "Select-Object -First 1 Name,NumberOfCores,NumberOfLogicalProcessors | "
        "ConvertTo-Json -Compress)"
    )
    if not output:
        return {}
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return {}
    return {
        "name": str(data.get("Name", "")),
        "cores": str(data.get("NumberOfCores", "")),
        "threads": str(data.get("NumberOfLogicalProcessors", "")),
    }


def detect_ram_gb() -> float | None:
    output = powershell_value(
        "[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)"
    )
    if not output:
        return None
    try:
        value = output.strip().splitlines()[-1].replace(",", ".")
        return float(value)
    except ValueError:
        return None


def detect_gpu() -> dict[str, str]:
    output = run_output(
        ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"]
    )
    if not output:
        return {}
    first = output.splitlines()[0]
    parts = [p.strip() for p in first.split(",")]
    if len(parts) < 3:
        return {"raw": first}
    return {
        "name": parts[0],
        "memory_total": parts[1],
        "driver_version": parts[2],
    }


def scan_local_models() -> list[LocalModel]:
    if not MODELS_DIR.exists():
        return []
    rows: list[LocalModel] = []
    for path in sorted(MODELS_DIR.iterdir()):
        if not path.is_dir():
            continue
        files = [p for p in path.rglob("*") if p.is_file()]
        if not files:
            continue
        total_bytes = sum(p.stat().st_size for p in files)
        gguf = any(p.suffix.lower() == ".gguf" for p in files)
        exl2 = any(".exl2" in p.name.lower() for p in files) or "exl2" in path.name.lower()
        safetensors = any(p.suffix.lower() == ".safetensors" for p in files)
        artifact_type = "gguf" if gguf else "exl2" if exl2 else "safetensors" if safetensors else "mixed"
        rows.append(
            LocalModel(
                name=path.name,
                path=str(path),
                artifact_type=artifact_type,
                total_gb=round(total_bytes / (1024**3), 3),
            )
        )
    return rows


def mistralrs_status() -> dict[str, Any]:
    text = run_output([sys.executable, str(REPO_ROOT / "scripts" / "mistralrs_model_manager.py"), "status"])
    if not text:
        return {"status": "unknown"}
    status = {"status": "unknown", "raw": text}
    if "Server: OFFLINE" in text:
        status["status"] = "offline"
    elif "Server: ONLINE" in text:
        status["status"] = "online"
    gpu_match = re.search(r"GPU:\s*(.+)", text)
    if gpu_match:
        status["gpu"] = gpu_match.group(1).strip()
    return status


def scout_candidates(vram_gb: float) -> list[dict[str, Any]]:
    payload = run_json(
        [
            "uv",
            "run",
            "scripts/hf_model_scout.py",
            "--vram",
            str(int(vram_gb)),
            "--top",
            "6",
            "--verify",
            "--json",
        ]
    )
    if not payload:
        return []
    return list(payload.get("models", []))


def local_readiness_summary() -> dict[str, Any]:
    path = REPO_ROOT / "codex" / "mailbox" / "LOCAL_AI_READINESS_LATEST.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    summary = payload.get("summary", {})
    return {
        "runtime_ready": summary.get("runtime_ready"),
        "cpp_toolchain_ready": summary.get("cpp_toolchain_ready"),
        "local_refiner_ready": summary.get("local_refiner_ready"),
        "hf_stack_ready": summary.get("hf_stack_ready"),
        "ready_for_skill_integration": summary.get("ready_for_skill_integration"),
    }


def load_residue_reference() -> dict[str, Any]:
    if not RESIDUE_REF.exists():
        return {}
    try:
        return tomllib.loads(RESIDUE_REF.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_equivalence_reference() -> dict[str, Any]:
    if not EQUIVALENCE_REF.exists():
        return {}
    try:
        return tomllib.loads(EQUIVALENCE_REF.read_text(encoding="utf-8"))
    except Exception:
        return {}


def preset_gemma4_local_delegation() -> dict[str, Any]:
    checked = "2026-04-15"
    return {
        "id": "gemma4-local-delegation",
        "checked_on": checked,
        "default_mission": (
            "Determine the strongest local delegation worker this desktop can sustain, "
            "starting with Gemma 4 31B as a hypothesis and replacing it the moment evidence "
            "shows a better model-runtime pair."
        ),
        "impossible_core": (
            "Plain Gemma 4 31B BF16 is not a natural single-GPU fit on 24 GB VRAM, "
            "so the delegated run must either prove a quantized path or pivot fast."
        ),
        "ankh_bridge": [
            "ANKH is the Egyptological/Andean 50/50 abstraction of the archive: vertical command plus horizontal reciprocal memory, acting as a bridge between human and digital cognition.",
            "Do not flatten ANKH into governance vocabulary, carrier-language, or a prompt wrapper. Treat it as a bridge abstraction for how pressure, memory, and reciprocity are organized.",
            "Use the bridge explicitly: authoritative bottleneck naming on one side, reciprocal multi-tier memory choreography on the other.",
        ],
        "remote_evidence": [
            {
                "date_checked": checked,
                "claim": "google/gemma-4-31B-it is a 30.7B dense Gemma 4 model with 256K context, system-role support, thinking mode, and native tool calling.",
                "source": "https://huggingface.co/google/gemma-4-31B-it",
            },
            {
                "date_checked": checked,
                "claim": "The vLLM Gemma 4 recipe documents Gemma 4 reasoning parsing, tool-call parsing, structured outputs, and lists Gemma 4 31B IT at 1x80 GB BF16.",
                "source": "https://docs.vllm.ai/projects/recipes/en/latest/Google/Gemma4.html",
            },
            {
                "date_checked": checked,
                "claim": "RedHatAI/gemma-4-31B-it-NVFP4 is a Gemma 4 31B quantized variant for vLLM and states roughly 75 percent lower memory requirements than the unquantized model.",
                "source": "https://huggingface.co/RedHatAI/gemma-4-31B-it-NVFP4",
            },
            {
                "date_checked": checked,
                "claim": "The current mistral.rs supported-model page lists Gemma 3, Gemma 3n, Qwen 3, Llama 4, and GPT-OSS but does not list Gemma 4.",
                "source": "https://ericlbuehler.github.io/mistral.rs/SUPPORTED_MODELS.html",
            },
            {
                "date_checked": checked,
                "claim": "NVIDIA's current NIM support matrix for Gemma 4 31B requires compute capability >= 9.0 and more than 110 GB total BF16 memory in the generic configuration.",
                "source": "https://docs.nvidia.com/nim/vision-language-models/latest/support-matrix.html",
            },
            {
                "date_checked": checked,
                "claim": "Unsloth hosts a Gemma 4 31B GGUF conversion, which keeps a GGUF path in play even if it is not the first-choice runtime.",
                "source": "https://huggingface.co/unsloth/gemma-4-31B-it-GGUF",
            },
        ],
        "benchmark_requirements": [
            "tight JSON schema compliance",
            "task decomposition under ambiguity",
            "tool-call shaped output or native tool calling",
            "patch-plan quality from noisy repo context",
            "long-context synthesis across multiple snippets",
            "self-correction after updated evidence",
            "latency, throughput, and VRAM notes",
        ],
        "decision_rules": [
            "Prefer documented runtime support over wishcasting.",
            "Prefer reusable server runtimes over per-script model loads.",
            "If Gemma 4 survives, test vLLM before any experimental mistral.rs path.",
            "If quantization is the only way forward, say that explicitly.",
            "If Gemma 4 remains unstable or memory-bound, switch to the strongest practical local contender.",
        ],
        "refusal_transmutation": [
            "When the task feels impossible, do not suppress that reaction. Convert it into a named physical law.",
            "For each impossibility claim, split it into the law itself and the implementation habit masquerading as the law.",
            "Generate loophole classes against the habit, not the law.",
            "For each loophole, state memory effect, bandwidth effect, latency effect, fidelity risk, and cheapest falsification test.",
            "If a path dies, feed the failure back as a tighter constraint and recurse instead of stopping.",
        ],
    }


def build_task_body(
    mission: str,
    preset: dict[str, Any],
    hardware: dict[str, Any],
    models: list[LocalModel],
    scout: list[dict[str, Any]],
    readiness: dict[str, Any],
    mistral_status: dict[str, Any],
    residue: dict[str, Any],
    equivalence: dict[str, Any],
) -> str:
    cpu = hardware.get("cpu", {})
    gpu = hardware.get("gpu", {})
    ram_gb = hardware.get("ram_gb")
    model_lines = [f"- {m.name} [{m.artifact_type}, {m.total_gb} GB]" for m in models[:8]]
    if not model_lines:
        model_lines = ["- (no local model directories found)"]

    fallback_lines: list[str] = []
    for row in scout[:4]:
        rec = row.get("recommended_format", {})
        fallback_lines.append(
            f"- {row.get('id')} -> {rec.get('format', 'unknown')} / {rec.get('cmd', 'n/a')}"
        )
    if not fallback_lines:
        fallback_lines = ["- (no scout data available)"]

    evidence_lines = [
        f"- {item['claim']} [{item['date_checked']}] ({item['source']})"
        for item in preset["remote_evidence"]
    ]
    ankh_lines = [f"- {line}" for line in preset["ankh_bridge"]]
    refusal_lines = [f"- {line}" for line in preset["refusal_transmutation"]]
    residue_style = residue.get("style", {})
    residue_reasoning = residue.get("reasoning", {})
    residue_prefers = [f"- {line}" for line in residue_style.get("prefer", [])[:5]]
    residue_avoids = [f"- {line}" for line in residue_style.get("avoid", [])[:5]]
    residue_loop = [f"- {line}" for line in residue_reasoning.get("transmutation_loop", [])]
    equivalence_lines = []
    for family in equivalence.get("family", [])[:4]:
        invariant = family.get("invariant", "")
        preserve_as = "; ".join(family.get("preserve_as", [])[:3])
        avoid = ", ".join(family.get("avoid_reduction_to", [])[:4])
        equivalence_lines.append(f"- {invariant} | preserve: {preserve_as} | avoid: {avoid}")

    readiness_lines = [
        f"- runtime_ready={readiness.get('runtime_ready')}",
        f"- cpp_toolchain_ready={readiness.get('cpp_toolchain_ready')}",
        f"- local_refiner_ready={readiness.get('local_refiner_ready')}",
        f"- hf_stack_ready={readiness.get('hf_stack_ready')}",
        f"- ready_for_skill_integration={readiness.get('ready_for_skill_integration')}",
        f"- mistralrs_status={mistral_status.get('status')}",
    ]

    sections = [
        "You are here to compress the search space, not to narrate impossibility.",
        "",
        "Mission",
        mission,
        "",
        "Impossible Core",
        preset["impossible_core"],
        "",
        "Machine Envelope",
        f"- CPU: {cpu.get('name', 'unknown')} ({cpu.get('cores', '?')} cores / {cpu.get('threads', '?')} threads)",
        f"- GPU: {gpu.get('name', 'unknown')} / {gpu.get('memory_total', 'unknown')} / driver {gpu.get('driver_version', 'unknown')}",
        f"- RAM: {ram_gb if ram_gb is not None else 'unknown'} GB",
        "",
        "Local Model Inventory",
        *model_lines,
        "",
        "Local Runtime Signals",
        *readiness_lines,
        "",
        "Current External Evidence",
        *evidence_lines,
        "",
        "ANKH Bridge Premise",
        *ankh_lines,
        "",
        "Refusal Transmutation Loop",
        *refusal_lines,
        "",
        "Residue Style Preferences",
        *residue_prefers,
        "",
        "Residue Style Avoidances",
        *residue_avoids,
        "",
        "Residue Logic Loop",
        *residue_loop,
        "",
        "Invariant Equivalence Families",
        *equivalence_lines,
        "",
        "Fallback Candidates From Local Scout",
        *fallback_lines,
        "",
        "Execution Ladder",
        "1. Reconfirm the machine envelope and which runtimes are already healthy.",
        "2. Build a compatibility matrix for Gemma 4 31B, Gemma 4 31B NVFP4, Gemma 4 26B A4B, the strongest local candidate already on disk, and one additional fallback if current evidence reveals a stronger 24 GB fit.",
        "3. Pick the runtime path for each serious candidate. Favor documented support, reusable servers, and OpenAI-compatible APIs.",
        "4. Prove or kill the Gemma 4 path quickly. Do not romanticize it.",
        "5. Benchmark delegation behavior, not generic prose quality.",
        "6. If Gemma 4 fails, switch to the strongest practical contender and continue the benchmark instead of stopping.",
        "7. Produce a winning operating contract that makes future delegation runs stronger than default.",
        "",
        "Benchmark Requirements",
        *[f"- {item}" for item in preset["benchmark_requirements"]],
        "",
        "Decision Rules",
        *[f"- {item}" for item in preset["decision_rules"]],
        "",
        "Deliverables",
        "- compatibility_matrix",
        "- runtime_decision_log",
        "- delegation_benchmark_results",
        "- winning_runtime_and_model",
        "- winning_prompt_contract",
        "- next_action_if_blocked",
        "",
        "Failure Discipline",
        "- If a path fails, state exactly what failed: VRAM, runtime support, tool calling, structured outputs, throughput, or stability.",
        "- Leave behind the strongest remaining path instead of a narrative about difficulty.",
        "- Keep the final answer evidence-first and explicit about tradeoffs.",
        "- Every impossibility statement must be translated into a law, a masquerading habit, and a falsifiable loophole path.",
        "- Keep the language in-house, specific, and free of decorative dominance signals.",
    ]
    return "\n".join(sections).strip() + "\n"


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "---",
        "type: delegation-packet",
        f"generated: {payload['generated']}",
        f"preset: {payload['preset']}",
        "---",
        "",
        "# Delegation Packet",
        "",
        f"- Mission: {payload['mission']}",
        f"- Checked on: `{payload['checked_on']}`",
        "",
        "## Machine",
        f"- CPU: `{payload['hardware'].get('cpu', {}).get('name', 'unknown')}`",
        f"- GPU: `{payload['hardware'].get('gpu', {}).get('name', 'unknown')}`",
        f"- VRAM: `{payload['hardware'].get('gpu', {}).get('memory_total', 'unknown')}`",
        f"- RAM: `{payload['hardware'].get('ram_gb', 'unknown')}` GB",
        "",
        "## Local Models",
    ]
    for row in payload["local_models"]:
        lines.append(
            f"- `{row['name']}` [{row['artifact_type']}] `{row['total_gb']} GB`"
        )

    lines += [
        "",
        "## External Evidence Snapshot",
    ]
    for item in payload["remote_evidence"]:
        lines.append(f"- {item['claim']} ([source]({item['source']}), checked `{item['date_checked']}`)")

    lines += [
        "",
        "## Task Body",
        "",
        "```text",
        payload["task_body"].rstrip(),
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a live delegation packet.")
    parser.add_argument(
        "--preset",
        required=True,
        choices=["gemma4-local-delegation"],
        help="Delegation preset to build.",
    )
    parser.add_argument("--mission", help="Override the default mission text.")
    parser.add_argument("--out", help="Markdown output path.")
    parser.add_argument("--json-out", help="JSON output path.")
    parser.add_argument("--write-md", action="store_true", help="Write a human-readable markdown mirror.")
    args = parser.parse_args()

    preset = preset_gemma4_local_delegation()
    mission = args.mission or preset["default_mission"]
    residue = load_residue_reference()
    equivalence = load_equivalence_reference()

    hardware = {
        "cpu": detect_cpu(),
        "gpu": detect_gpu(),
        "ram_gb": detect_ram_gb(),
    }
    local_models = scan_local_models()
    scout = scout_candidates(vram_gb=24.0)
    readiness = local_readiness_summary()
    mistral_status = mistralrs_status()
    task_body = build_task_body(
        mission=mission,
        preset=preset,
        hardware=hardware,
        models=local_models,
        scout=scout,
        readiness=readiness,
        mistral_status=mistral_status,
        residue=residue,
        equivalence=equivalence,
    )

    payload = {
        "generated": utc_now().isoformat(),
        "preset": preset["id"],
        "checked_on": preset["checked_on"],
        "mission": mission,
        "impossible_core": preset["impossible_core"],
        "hardware": hardware,
        "local_models": [m.__dict__ for m in local_models],
        "mistralrs_status": mistral_status,
        "readiness": readiness,
        "scout_candidates": scout,
        "remote_evidence": preset["remote_evidence"],
        "ankh_bridge": preset["ankh_bridge"],
        "residue_reference_path": str(RESIDUE_REF) if RESIDUE_REF.exists() else None,
        "residue_reference": residue,
        "equivalence_reference_path": str(EQUIVALENCE_REF) if EQUIVALENCE_REF.exists() else None,
        "equivalence_reference": equivalence,
        "benchmark_requirements": preset["benchmark_requirements"],
        "decision_rules": preset["decision_rules"],
        "refusal_transmutation": preset["refusal_transmutation"],
        "task_body": task_body,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_json = Path(args.json_out) if args.json_out else DEFAULT_JSON_OUT
    write_md = bool(args.write_md or args.out)
    out_md = Path(args.out) if args.out else DEFAULT_MD_OUT if write_md else None

    markdown = render_markdown(payload)
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if out_md is not None:
        out_md.write_text(markdown, encoding="utf-8")

    print(f"packet_json={out_json}")
    if out_md is not None:
        print(f"packet_md={out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
