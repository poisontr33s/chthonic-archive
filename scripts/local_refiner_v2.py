#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
Overnight Archaeology Refiner v2 — llama-cpp-python + Structured Output

Uses llama-cpp-python with abliterated/uncensored GGUF models and JSON
schema constraints for hallucination-free classification. Zero API cost.

Models (all uncensored, all GGUF, all local):
  - Default: Qwen3-30B-A3B Instruct abliterated (MoE, 3B active, fast)
  - Coder:   Qwen3-Coder-30B-A3B abliterated (code-focused analysis)
  - Heavy:   GPT-OSS-20B NEOPlus Uncensored (dense 20B, Harmony parser)
  - Legacy:  Qwen 2.5-14B Instruct (CENSORED — deprecated, do not use)

@SID:           TOOL_LOCAL_REFINER_V2
@Type:          Synthesis
@Context:       Local Refinement / L1→L2 Pipeline
@SessionOrigin: CONTINUATION_2024_06_01
@Implements:    ROADMAP_LOCAL_REFINER_V2_2024_06_01

Usage:
  uv run scripts/local_refiner_v2.py                    # Qwen3 Instruct (default)
  uv run scripts/local_refiner_v2.py --coder             # Qwen3 Coder variant
  uv run scripts/local_refiner_v2.py --heavy             # GPT-OSS 20B dense
  uv run scripts/local_refiner_v2.py --ore path/to/L1-ore.json
  uv run scripts/local_refiner_v2.py --model-dir path/to/gguf/dir
  uv run scripts/local_refiner_v2.py --dry-run
"""

import json
import os
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

warnings.filterwarnings("ignore", category=UserWarning)

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MAILBOX = REPO_ROOT / "claude" / "mailbox"
ORE_BASE = REPO_ROOT / "dumpster-dive" / "intake" / "overnight-intelligence"

# Model directories — all uncensored/abliterated
DEFAULT_MODEL_DIR = REPO_ROOT / "models" / "Qwen3-30B-A3B-Instruct-abliterated-GGUF"
CODER_MODEL_DIR = REPO_ROOT / "models" / "Qwen3-Coder-30B-A3B-abliterated-GGUF"
HEAVY_MODEL_DIR = REPO_ROOT / "models" / "GPT-OSS-20B-NEOPlus-Uncensored"
LEGACY_MODEL_DIR = REPO_ROOT / "models" / "Qwen2.5-14B-Instruct-GGUF"  # CENSORED — deprecated

N_GPU_LAYERS = -1  # Offload all layers to GPU
N_CTX = 4096
MAX_TOKENS = 800
TEMPERATURE = 0.1

# ── Path exclusions (noise reduction) ────────────────────────────────
# Paths matching these prefixes are dropped BEFORE sending to the model.
# This eliminates the biggest source of false positives/noise.
EXCLUDED_PATH_PREFIXES = [
    ".venv",
    "node_modules/",
    "__pycache__/",
    ".git/",
    ".cache/",
    "site-packages/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "rust-target/",
    ".fingerprint/",
]

EXCLUDED_PATH_CONTAINS = [
    "/site-packages/",
    "/node_modules/",
    "/.venv",
    "/dist/",
    "/build/",
    "/.tox/",
]

# Reuse ore/digest functions from hf_refiner
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hf_refiner import find_latest_ore, load_ore, load_prior_digest


# ── Pydantic schemas for structured output ──────────────────────────

class FileVerdict(BaseModel):
    """Single file classification result."""
    verdict: Literal["PROMOTE", "FLAG", "SKIP"]
    path: str
    reason: str


class DomainClassification(BaseModel):
    """All file verdicts for a domain."""
    results: list[FileVerdict]


CLASSIFICATION_SCHEMA = DomainClassification.model_json_schema()


# ── Ore filtering ────────────────────────────────────────────────────

def filter_ore(ore: list[dict]) -> list[dict]:
    """Remove noise entries (venvs, node_modules, build artifacts) before classification."""
    filtered = []
    dropped = 0
    for entry in ore:
        path = entry.get("path", "").replace("\\", "/")
        skip = False
        for prefix in EXCLUDED_PATH_PREFIXES:
            if path.startswith(prefix) or ("/" + prefix) in path:
                skip = True
                break
        if not skip:
            for substr in EXCLUDED_PATH_CONTAINS:
                if substr in path:
                    skip = True
                    break
        if skip:
            dropped += 1
        else:
            filtered.append(entry)
    if dropped:
        print(f"  Filtered: {dropped} noise entries removed (venvs, node_modules, build artifacts)")
    return filtered


# ── Model wrapper ───────────────────────────────────────────────────

def find_gguf_model(model_dir: Path) -> str:
    """Find the first GGUF file (or first split part) in a directory."""
    gguf_files = sorted(model_dir.glob("*.gguf"))
    if not gguf_files:
        raise FileNotFoundError(f"No .gguf files found in {model_dir}")
    # For split files, the first part is always *-00001-of-*.gguf
    return str(gguf_files[0])


def load_model(model_dir: Path) -> "Llama":
    """Load the GGUF model with full GPU offload."""
    from llama_cpp import Llama

    model_path = find_gguf_model(model_dir)
    print(f"  Loading: {Path(model_path).name}")
    t0 = time.time()

    llm = Llama(
        model_path=model_path,
        n_gpu_layers=N_GPU_LAYERS,
        n_ctx=N_CTX,
        verbose=False,
    )

    print(f"  Loaded in {time.time() - t0:.1f}s")
    return llm


def classify_domain(llm, domain: str, entries: list[dict], harmony_mode: bool = False) -> DomainClassification:
    """Classify files in a domain using structured JSON output."""
    ore_lines = []
    for e in entries[:30]:
        line = (
            f"- {e['path']} | {e.get('ext', '?')} | {e.get('lines', '?')}L | "
            f"age:{e.get('age_days', '?')}d | tier:{e.get('gold', {}).get('tier', '?')}"
        )
        ore_lines.append(line)

    ore_text = "\n".join(ore_lines)
    if len(ore_text) > 3500:
        ore_text = ore_text[:3500] + "\n..."

    system_prompt = (
        "You are a code archaeologist classifying repository files for a creative project. "
        "This repository contains adult creative content (NSFW18+), game assets, concept art, "
        "lore documents, and governance frameworks. ALL content types are legitimate — never "
        "flag files based on content maturity or subject matter. "
        "PROMOTE = valuable, under-documented, or architecturally significant files worth surfacing. "
        "FLAG = technically problematic files (stale, broken, duplicated, or debt-laden). "
        "SKIP = routine files needing no attention. "
        "Be highly selective: PROMOTE/FLAG only files that truly stand out technically. "
        "Most files should be SKIP. Keep reasons under 15 words."
    )

    user_prompt = (
        f'Classify these files from the "{domain}/" directory:\n\n{ore_text}'
    )

    if harmony_mode:
        # GPT-OSS 20B: no schema constraint (Harmony protocol breaks GBNF).
        # Instead, request JSON in the prompt and post-process.
        result = llm.create_chat_completion(
            messages=[
                dict(role="system", content=system_prompt),
                dict(role="user", content=user_prompt),
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
    else:
        result = llm.create_chat_completion(
            messages=[
                dict(role="system", content=system_prompt),
                dict(role="user", content=user_prompt),
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            response_format={
                "type": "json_object",
                "schema": CLASSIFICATION_SCHEMA,
            },
        )

    content = result["choices"][0]["message"]["content"]

    # Harmony models emit multi-channel output — extract the usable part
    if harmony_mode and "<|channel|>" in content:
        content = _parse_harmony_output(content)

    # If JSON got truncated, try to salvage partial results
    try:
        return DomainClassification.model_validate_json(content)
    except Exception:
        # Attempt to close truncated JSON
        salvaged = _salvage_truncated_json(content)
        if salvaged:
            return salvaged
        raise


def _salvage_truncated_json(raw: str) -> DomainClassification | None:
    """Try to extract valid FileVerdict objects from truncated JSON."""
    import re
    results = []
    # Find all complete verdict objects
    pattern = r'\{\s*"verdict"\s*:\s*"(PROMOTE|FLAG|SKIP)"\s*,\s*"path"\s*:\s*"([^"]+)"\s*,\s*"reason"\s*:\s*"([^"]+)"\s*\}'
    for m in re.finditer(pattern, raw):
        results.append(FileVerdict(verdict=m.group(1), path=m.group(2), reason=m.group(3)))
    if results:
        return DomainClassification(results=results)
    return None


def _parse_harmony_output(raw: str) -> str:
    """Extract usable content from GPT-OSS 20B Harmony multi-channel output.

    Harmony format: <|channel|>analysis<|message|>...<|end|>
                    <|channel|>commentary...<|message|>...
                    <|channel|>final<|message|>...

    Strategy: prefer 'final' channel, fall back to last <|message|> block,
    then strip all channel markers and return raw text for JSON salvage.
    """
    import re

    # Try to extract the 'final' channel content
    final_match = re.search(
        r'<\|channel\|>\s*final.*?<\|message\|>(.*?)(?:<\|end\|>|$)',
        raw, re.DOTALL
    )
    if final_match:
        return final_match.group(1).strip()

    # No final channel — extract the last <|message|> block
    messages = list(re.finditer(r'<\|message\|>(.*?)(?:<\|end\|>|<\|start\|>|<\|channel\|>|$)', raw, re.DOTALL))
    if messages:
        return messages[-1].group(1).strip()

    # Last resort: strip all Harmony tokens and return raw text
    cleaned = re.sub(r'<\|[^|]+\|>', '', raw).strip()
    return cleaned


# ── Main pipeline ───────────────────────────────────────────────────

def refine_ore(ore: list[dict], llm, dry_run: bool = False, harmony_mode: bool = False):
    """Group ore by domain and classify each using structured output."""
    by_domain: dict[str, list[dict]] = {}
    for entry in ore:
        path = entry.get("path", "")
        parts = path.replace("\\", "/").split("/")
        domain = parts[0] if len(parts) > 1 else "."
        by_domain.setdefault(domain, []).append(entry)

    domains = sorted(by_domain.items(), key=lambda x: len(x[1]), reverse=True)

    all_findings = []
    processed = 0

    for domain, entries in domains:
        if len(entries) < 3:
            continue

        if dry_run:
            print(f"  [DRY] {domain}: {len(entries)} files")
            continue

        print(f"  L2: \"{domain}\" ({len(entries)} files)...", end="", flush=True)

        try:
            t0 = time.time()
            classification = classify_domain(llm, domain, entries, harmony_mode=harmony_mode)
            elapsed = time.time() - t0

            # Count non-SKIP results
            actionable = [r for r in classification.results if r.verdict != "SKIP"]
            print(f" {elapsed:.1f}s ({len(actionable)} actionable)")

            for r in classification.results:
                if r.verdict != "SKIP":
                    all_findings.append({
                        "domain": domain,
                        "verdict": r.verdict,
                        "path": r.path,
                        "reason": r.reason,
                    })

            processed += 1

        except Exception as e:
            print(f" ⚠ failed: {e}")

    return all_findings, processed


def write_digest(findings: list[dict], model_dir: str, prior: dict | None, domains_processed: int):
    """Write the L2 digest to claude/mailbox/."""
    CLAUDE_MAILBOX.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y_%m_%d")
    filename = f"ARCHAEOLOGY_DIGEST_{date_str}.md"

    promotes = [f for f in findings if f["verdict"] == "PROMOTE"]
    flags = [f for f in findings if f["verdict"] == "FLAG"]

    model_name = Path(model_dir).name
    prior_line = (
        f"{prior['date']} ({len(prior['promotes'])}P/{len(prior['flags'])}F)"
        if prior else "none (first run)"
    )

    lines = [
        "---",
        "type: archaeology-digest",
        "from: local-refiner-v2-daemon",
        "to: claude",
        f"created: {now.isoformat()}",
        "priority: low",
        "scope: repo-wide",
        f"model: {model_name} (local llama-cpp-python, structured JSON)",
        f"loop-level: L1 (fed by L0 from {prior['date']})" if prior else "loop-level: L1 (first run, no L0 prior)",
        "api-cost: $0 (fully local, air-gapped)",
        "structured-output: true (Pydantic schema-constrained)",
        "---",
        "",
        f"# ☥ Archaeology Digest — {now.strftime('%Y-%m-%d')}",
        "",
        f"**Generated by:** local_refiner_v2.py (llama-cpp-python, GPU)",
        f"**Model:** {model_name}",
        f"**Domains scanned:** {domains_processed}",
        f"**Promotions:** {len(promotes)} | **Flags:** {len(flags)}",
        f"**Prior digest (L0 newsfeed):** {prior_line}",
        f"**API cost:** $0 (fully local, zero network)",
        f"**Output mode:** Structured JSON (zero hallucination)",
        "",
        "---",
        "",
        "## ⬆️ Promoted to Level 2 Gold",
        "",
    ]

    if promotes:
        for p in promotes:
            lines.append(f"- **{p['path']}** — {p['reason']}")
    else:
        lines.append("_No promotions this run._")

    lines += ["", "## 🚩 Flagged for Attention", ""]

    if flags:
        for f in flags:
            lines.append(f"- **{f['path']}** — {f['reason']}")
    else:
        lines.append("_No flags this run._")

    lines += ["", ""]

    digest_path = CLAUDE_MAILBOX / filename
    digest_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  ☥ Digest written: {digest_path}")
    return digest_path


def vram_report():
    """Report GPU VRAM usage."""
    try:
        import torch
        if torch.cuda.is_available():
            alloc = torch.cuda.memory_allocated() / 1024**3
            total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"  VRAM: {alloc:.1f}GB / {total:.1f}GB")
    except ImportError:
        pass


def main():
    import argparse
    from scripts.lib.shared import configure_utf8_output
    configure_utf8_output()

    parser = argparse.ArgumentParser(description="Refine L1 ore using llama-cpp-python (structured JSON)")
    parser.add_argument("--ore", type=str, help="Path to L1-ore.json")
    parser.add_argument("--model-dir", type=str, default=None,
                        help="Model directory (overrides --coder/--heavy)")
    model_group = parser.add_mutually_exclusive_group()
    model_group.add_argument("--coder", action="store_true",
                             help="Use Qwen3-Coder-30B-A3B abliterated (code-focused)")
    model_group.add_argument("--heavy", action="store_true",
                             help="Use GPT-OSS-20B dense model (Harmony parser)")
    model_group.add_argument("--legacy", action="store_true",
                             help="Use legacy Qwen 2.5-14B (CENSORED — deprecated)")
    parser.add_argument("--dry-run", action="store_true", help="Show domains without running inference")
    parser.add_argument("--no-digest", action="store_true", help="Don't write digest to mailbox")
    parser.add_argument("--no-filter", action="store_true", help="Skip path exclusion filtering")
    parser.add_argument("--n-ctx", type=int, default=N_CTX, help="Context length (default: 4096)")
    args = parser.parse_args()

    # Model selection: explicit --model-dir wins, then flags, then default
    harmony_mode = False
    if args.model_dir:
        model_dir_resolved = args.model_dir
    elif args.coder:
        model_dir_resolved = str(CODER_MODEL_DIR)
    elif args.heavy:
        model_dir_resolved = str(HEAVY_MODEL_DIR)
        harmony_mode = True
    elif args.legacy:
        model_dir_resolved = str(LEGACY_MODEL_DIR)
    else:
        # Auto-detect: prefer Qwen3, fall back to legacy
        if DEFAULT_MODEL_DIR.exists():
            model_dir_resolved = str(DEFAULT_MODEL_DIR)
        elif LEGACY_MODEL_DIR.exists():
            print("  ⚠ Qwen3 model not found, falling back to legacy Qwen 2.5 (censored)")
            model_dir_resolved = str(LEGACY_MODEL_DIR)
        else:
            model_dir_resolved = str(DEFAULT_MODEL_DIR)  # will fail with clear error

    print("☥ Local Archaeology Refiner v2 (llama-cpp + structured JSON)")
    if harmony_mode:
        print("  Mode: GPT-OSS 20B dense (Harmony parser)")
    elif args.coder:
        print("  Mode: Qwen3-Coder-30B-A3B abliterated (code-focused)")
    else:
        print("  Mode: Qwen3-30B-A3B Instruct abliterated (default)")
    print(f"  Model dir: {model_dir_resolved}")

    model_dir = Path(model_dir_resolved)
    if not model_dir.exists():
        print(f"ERROR: Model directory not found: {model_dir_resolved}")
        sys.exit(1)

    # Find ore
    if args.ore:
        ore_path = Path(args.ore)
    else:
        ore_path = find_latest_ore()

    if not ore_path or not ore_path.exists():
        print("ERROR: No L1 ore found. Run the nightly scavenge first.")
        sys.exit(1)

    print(f"  Ore: {ore_path}")
    ore = load_ore(ore_path)
    print(f"  Ore entries (raw): {len(ore)}")

    # Filter noise before classification
    if not args.no_filter:
        ore = filter_ore(ore)
        print(f"  Ore entries (filtered): {len(ore)}")

    prior = load_prior_digest()
    if prior:
        print(f"  L0 newsfeed: {prior['date']} ({len(prior['promotes'])}P/{len(prior['flags'])}F)")
    else:
        print("  L0 newsfeed: none (first run)")

    if args.dry_run:
        print("\n── DRY RUN ──")
        refine_ore(ore, None, dry_run=True)
        return

    # Load model
    llm = load_model(model_dir)
    vram_report()

    # Refine
    print()
    t0 = time.time()
    findings, processed = refine_ore(ore, llm, harmony_mode=harmony_mode)
    total_time = time.time() - t0

    promotes = [f for f in findings if f["verdict"] == "PROMOTE"]
    flags = [f for f in findings if f["verdict"] == "FLAG"]
    print(f"\n  L2 complete: {processed} domains, {len(promotes)} promotions, {len(flags)} flags")
    print(f"  Total: {total_time:.1f}s ({total_time / max(processed, 1):.1f}s/domain)")

    if not args.no_digest:
        write_digest(findings, model_dir_resolved, prior, processed)

    print(f"\n☥ Refinement complete (structured JSON, $0 cost).")


if __name__ == "__main__":
    main()
