#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: local_refiner.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Overnight Archaeology Refiner — Local ExLlamaV2 Edition

Same interface as hf_refiner.py but runs inference locally on the GPU
via ExLlamaV2. Zero API cost, zero network dependency, fully air-gapped.

Reads L1 ore (from the local scavenge daemon) and classifies files as
PROMOTE/FLAG/SKIP using a quantized Llama model on the RTX 4090.

@SID:           TOOL_LOCAL_REFINER_V1
@Shabti:          Synthesis
@Purpose:       Overnight Archaeology Refiner — Local ExLlamaV2 Edition

Usage:
  uv run scripts/local_refiner.py                          # auto-find latest L1 ore
  uv run scripts/local_refiner.py --ore path/to/L1-ore.json
  uv run scripts/local_refiner.py --model-dir path/to/exl2/model
  uv run scripts/local_refiner.py --dry-run                # show what would be sent
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import json
import os
import re
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore", category=UserWarning)

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MAILBOX = REPO_ROOT / "claude" / "mailbox"
ORE_BASE = REPO_ROOT / "dumpster-dive" / "intake" / "overnight-intelligence"
DEFAULT_MODEL_DIR = REPO_ROOT / "models" / "Llama-3.1-8B-Instruct-exl2-6.0bpw"

MAX_SEQ_LEN = 4096
MAX_NEW_TOKENS = 512
MAX_INPUT_CHARS = 4000
TEMPERATURE = 0.1

# Reuse ore/digest functions from hf_refiner
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hf_refiner import find_latest_ore, load_ore, load_prior_digest, build_domain_prompt


class LocalLLM:
    """ExLlamaV2 local inference wrapper."""

    def __init__(self, model_dir: str, max_seq_len: int = MAX_SEQ_LEN):
        from exllamav2 import ExLlamaV2, ExLlamaV2Config, ExLlamaV2Cache, ExLlamaV2Tokenizer
        from exllamav2.generator import ExLlamaV2BaseGenerator

        print(f"  Loading model from: {model_dir}")
        t0 = time.time()

        config = ExLlamaV2Config(model_dir)
        config.max_seq_len = max_seq_len
        config.max_batch_size = 1
        config.no_flash_attn = True

        self.model = ExLlamaV2(config)
        print(f"    Loading weights to GPU...", end="", flush=True)
        self.model.load()
        print(f" done ({time.time() - t0:.1f}s)")

        self.tokenizer = ExLlamaV2Tokenizer(config)
        self.cache = ExLlamaV2Cache(self.model, max_seq_len=max_seq_len)
        self.generator = ExLlamaV2BaseGenerator(
            model=self.model,
            cache=self.cache,
            tokenizer=self.tokenizer,
        )
        self._model_dir = model_dir

    def generate(self, prompt: str, max_tokens: int = MAX_NEW_TOKENS, temperature: float = TEMPERATURE) -> str:
        """Generate a response for a single prompt."""
        from exllamav2.generator import ExLlamaV2Sampler

        # Format as Llama 3.1 chat template
        formatted = (
            "<|begin_of_text|>"
            "<|start_header_id|>user<|end_header_id|>\n\n"
            f"{prompt}"
            "<|eot_id|>"
            "<|start_header_id|>assistant<|end_header_id|>\n\n"
        )

        settings = ExLlamaV2Sampler.Settings()
        settings.temperature = temperature
        settings.top_p = 0.9
        settings.top_k = 40
        settings.token_repetition_penalty = 1.1

        output = self.generator.generate_simple(
            formatted,
            settings,
            max_tokens,
            encode_special_tokens=True,
            decode_special_tokens=False,
            token_healing=False,
            completion_only=True,
            stop_token=128009,  # <|eot_id|>
        )

        # Trim at any continuation markers (model sometimes generates more turns)
        for marker in ["\nFILES:", "\nassistant", "\nuser", "\n---"]:
            idx = output.find(marker)
            if idx > 0:
                output = output[:idx]

        return output.strip()

    def vram_usage(self) -> str:
        """Report current VRAM usage."""
        import torch
        allocated = torch.cuda.memory_allocated() / 1024**3
        reserved = torch.cuda.memory_reserved() / 1024**3
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        return f"{allocated:.1f}GB allocated, {reserved:.1f}GB reserved, {total:.1f}GB total"


def build_local_prompt(domain: str, entries: list[dict], prior: dict | None) -> str:
    """Build a concise classification prompt optimized for smaller local models."""
    ore_lines = []
    for e in entries[:30]:
        line = (
            f"- {e['path']} | {e.get('ext', '?')} | {e.get('lines', '?')}L | "
            f"age:{e.get('age_days', '?')}d | tier:{e.get('gold', {}).get('tier', '?')}"
        )
        ore_lines.append(line)

    ore_text = "\n".join(ore_lines)
    if len(ore_text) > MAX_INPUT_CHARS:
        ore_text = ore_text[:MAX_INPUT_CHARS] + "\n..."

    return (
        f'Classify these files from "{domain}/" as PROMOTE, FLAG, or SKIP.\n'
        "Respond ONLY with lines in this exact format:\n"
        "[PROMOTE] path - reason (max 15 words)\n"
        "[FLAG] path - reason (max 15 words)\n"
        "Do NOT list SKIP files. Do NOT add extra text.\n\n"
        f"FILES:\n{ore_text}"
    )


def refine_ore_local(ore: list[dict], llm: LocalLLM, prior: dict | None, dry_run: bool = False):
    """Group ore by domain and classify each using local LLM."""
    by_domain: dict[str, list[dict]] = {}
    for entry in ore:
        path = entry.get("path", "")
        parts = path.replace("\\", "/").split("/")
        domain = parts[0] if len(parts) > 1 else "."
        by_domain.setdefault(domain, []).append(entry)

    domains = sorted(by_domain.items(), key=lambda x: len(x[1]), reverse=True)

    all_findings = []
    all_raw = []
    processed = 0
    total_tokens_est = 0

    for domain, entries in domains:
        if len(entries) < 3:
            continue

        prompt = build_local_prompt(domain, entries, prior)

        if dry_run:
            print(f"  [DRY] {domain}: {len(entries)} files, prompt {len(prompt)} chars")
            continue

        print(f"  L2: Refining \"{domain}\" ({len(entries)} files)...", end="", flush=True)

        try:
            t0 = time.time()
            response = llm.generate(prompt)
            elapsed = time.time() - t0
            total_tokens_est += len(response.split())
            print(f" {elapsed:.1f}s")

            all_raw.append(f"## {domain}\n{response}")

            for line in response.split("\n"):
                line = line.strip()
                match = re.match(r"^\[?(PROMOTE|FLAG)\]?\s*(.+?)\s*[—–\-]\s*(.+)$", line)
                if match:
                    extracted_path = match.group(2).strip()
                    # Filter hallucinated template entries
                    if extracted_path.lower() in ("path", "error", "file", "reason"):
                        continue
                    if "max 15 words" in match.group(3).lower():
                        continue
                    all_findings.append({
                        "domain": domain,
                        "verdict": match.group(1),
                        "path": extracted_path,
                        "reason": match.group(3).strip(),
                    })

            processed += 1

        except Exception as e:
            print(f" ⚠ failed: {e}")
            all_raw.append(f"## {domain}\nERROR: {e}")

    return all_findings, all_raw, processed


def write_digest(findings: list[dict], raw_responses: list[str], model_dir: str, prior: dict | None, domains_processed: int):
    """Write the L2 digest to claude/mailbox/."""
    CLAUDE_MAILBOX.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y_%m_%d")
    filename = f"ARCHAEOLOGY_DIGEST_{date_str}.md"

    promotes = [f for f in findings if f["verdict"] == "PROMOTE"]
    flags = [f for f in findings if f["verdict"] == "FLAG"]

    model_name = Path(model_dir).name
    prior_line = f"{prior['date']} ({len(prior['promotes'])}P/{len(prior['flags'])}F)" if prior else "none (first run)"

    lines = [
        "---",
        "type: archaeology-digest",
        "from: local-refiner-daemon",
        "to: claude",
        f"created: {now.isoformat()}",
        "priority: low",
        "scope: repo-wide",
        f"model: {model_name} (local ExLlamaV2)",
        f"loop-level: L1 (fed by L0 from {prior['date']})" if prior else "loop-level: L1 (first run, no L0 prior)",
        "api-cost: $0 (fully local, air-gapped)",
        "---",
        "",
        f"# ☥ Archaeology Digest — {now.strftime('%Y-%m-%d')}",
        "",
        f"**Generated by:** local_refiner.py (ExLlamaV2, GPU inference)",
        f"**Model:** {model_name}",
        f"**Domains scanned:** {domains_processed}",
        f"**Promotions:** {len(promotes)} | **Flags:** {len(flags)}",
        f"**Prior digest (L0 newsfeed):** {prior_line}",
        f"**API cost:** $0 (fully local, zero network)",
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

    lines += [
        "",
        "## 🚩 Flagged for Attention",
        "",
    ]

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


def main():
    import argparse
    from scripts.lib.shared import configure_utf8_output
    configure_utf8_output()

    parser = argparse.ArgumentParser(description="Refine L1 ore using local ExLlamaV2 inference")
    parser.add_argument("--ore", type=str, help="Path to L1-ore.json (auto-detects latest if omitted)")
    parser.add_argument("--model-dir", type=str, default=str(DEFAULT_MODEL_DIR),
                        help=f"Path to ExLlamaV2 model directory (default: {DEFAULT_MODEL_DIR.name})")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be sent without running inference")
    parser.add_argument("--no-digest", action="store_true", help="Don't write digest to mailbox")
    parser.add_argument("--max-seq-len", type=int, default=MAX_SEQ_LEN, help="Max sequence length (default: 4096)")
    args = parser.parse_args()

    print("☥ Local Archaeology Refiner starting")
    print(f"  Model dir: {args.model_dir}")

    # Verify model exists
    model_path = Path(args.model_dir)
    if not model_path.exists():
        print(f"ERROR: Model directory not found: {args.model_dir}")
        print("  Download with: uv run python -c \"from huggingface_hub import snapshot_download; "
              "snapshot_download('turboderp/Llama-3.1-8B-Instruct-exl2', revision='6.0bpw', "
              "local_dir='models/Llama-3.1-8B-Instruct-exl2-6.0bpw')\"")
        sys.exit(1)

    # Find ore
    if args.ore:
        ore_path = Path(args.ore)
    else:
        ore_path = find_latest_ore()

    if not ore_path or not ore_path.exists():
        print("ERROR: No L1 ore found. Run the nightly scavenge first:")
        print("  .\\scripts\\run_archaeology.ps1 -SkipDaemon")
        sys.exit(1)

    print(f"  Ore: {ore_path}")

    # Load ore
    ore = load_ore(ore_path)
    print(f"  Ore entries: {len(ore)}")

    # Load prior digest
    prior = load_prior_digest()
    if prior:
        print(f"  L0 newsfeed: {prior['date']} ({len(prior['promotes'])}P/{len(prior['flags'])}F)")
    else:
        print("  L0 newsfeed: none (first run)")

    if args.dry_run:
        print("\n── DRY RUN ──")
        _, _, _ = refine_ore_local(ore, None, prior, dry_run=True)
        return

    # Load model to GPU
    llm = LocalLLM(args.model_dir, max_seq_len=args.max_seq_len)
    print(f"  VRAM: {llm.vram_usage()}")

    # Refine
    print()
    t0 = time.time()
    findings, raw, processed = refine_ore_local(ore, llm, prior)
    total_time = time.time() - t0

    promotes = [f for f in findings if f["verdict"] == "PROMOTE"]
    flags = [f for f in findings if f["verdict"] == "FLAG"]
    print(f"\n  L2 complete: {processed} domains, {len(promotes)} promotions, {len(flags)} flags")
    print(f"  Total inference time: {total_time:.1f}s ({total_time / max(processed, 1):.1f}s/domain)")

    # Write digest
    if not args.no_digest:
        write_digest(findings, raw, args.model_dir, prior, processed)

    print(f"\n☥ Refinement complete (fully local, $0 cost).")


if __name__ == "__main__":
    main()
