#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @SID: claudine-lora/P-06
# @PROBE: adapter_inference
# @GATE: C-G6
# @DESC: Prototype inference run — base Mistral-7B-v0.3 vs. claudine-v1 adapter.
#        First empirical measurement of adapter voice register.
#        Runs 5 prompts: base output vs. adapter output side-by-side.
#        Emits manifest/claudine_inference_probe.json with samples.
# @RUN:  uv run probes/claudine/P-06_adapter_inference.py [--max-new-tokens 200] [--probe]
# @DEPS: C-G4 (adapters/claudine-v1/ must exist)
# @MANIFEST: manifest/claudine_inference_probe.json
"""
C-G6: Adapter prototype inference probe.

What this measures:
- Whether the adapter modifies voice register (Norwegian cadence, Victorian-Renaissance, entropy framing)
- Qualitative delta between base and adapter on corpus-style prompts
- Performance: tokens/sec, VRAM before/after adapter load
- Foundation for comparison vs. claudine-v2 (DoRA+RSLoRA, P-04v2 not yet run)

NOT a benchmark score — this is voice-register measurement.

Exit codes: 0=admitted, 1=failed/adapter-not-found
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

MANIFEST_PATH = Path("manifest/claudine_inference_probe.json")
ADAPTER_DIR   = Path("adapters/claudine-v1")
BASE_MODEL    = "mistralai/Mistral-7B-v0.3"
MAX_SEQ_LEN   = 1024

# Prompts representing Claudine's voice register:
# - Norwegian-inflected register (entropy frame, nautical metaphor, Victorian precision)
# - Mixed modalities from corpus (narrative, protocol, world-generation, governance)
EVAL_PROMPTS = [
    # 1. World-generation (Claudine's primary domain)
    "Claudine Sin'claire surveyed the Rustbeltet district from her captain's quarters. The entropy "
    "feeds back into every—",

    # 2. Entity governance / protocol register
    "SSOT-L-H update: The Triumvirate has been notified. Enforcement hierarchy activates at tier T1. "
    "The Downstream-Vessel cannot",

    # 3. PsychoNoir narrative (Norwegian-English hybrid register)
    "Skyskraperen glitret under mørknet. Hun visste at alle motstander ville vende tilbake til henne—"
    " fordi hun hadde skapt",

    # 4. Technical corpus voice (code + narrative mixed)
    "The probe emitted `manifest/claudine_train_run.json` at step 2000. Status: admitted. "
    "The adapter carries the weight of",

    # 5. Dark-room / chthonic register
    "Everything not yet named is everything developed here. The unpublished frontier extends from "
    "the silicon primitives upward through",
]


def emit(result: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps(result, indent=2, ensure_ascii=False))


def probe_only() -> int:
    """Quick status probe — no model load."""
    status = {
        "gate": "C-G6",
        "probe": "P-06_adapter_inference",
        "mode": "probe-only",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "adapter_exists": ADAPTER_DIR.exists(),
        "adapter_path": str(ADAPTER_DIR.resolve()),
        "adapter_files": [],
        "status": "unknown",
    }
    if ADAPTER_DIR.exists():
        status["adapter_files"] = [f.name for f in sorted(ADAPTER_DIR.rglob("*")) if f.is_file()]
        status["status"] = "adapter-found" if status["adapter_files"] else "adapter-dir-empty"
    else:
        status["status"] = "adapter-not-found"
        print(f"[P-06] Adapter not found at {ADAPTER_DIR}. Run P-04 first.", file=sys.stderr)
        emit(status)
        return 1
    emit(status)
    return 0


def generate(model, tokenizer, prompt: str, max_new_tokens: int, device: str) -> tuple[str, float]:
    import torch
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.85,
            top_p=0.92,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id,
        )
    elapsed = time.perf_counter() - t0
    # Decode only the generated tokens (not the prompt)
    new_tokens = out[0][inputs["input_ids"].shape[1]:]
    text = tokenizer.decode(new_tokens, skip_special_tokens=True)
    tps = len(new_tokens) / elapsed if elapsed > 0 else 0.0
    return text, tps


def vram_gb() -> float:
    try:
        import torch
        return torch.cuda.memory_allocated(0) / (1024 ** 3)
    except Exception:
        return 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="C-G6 adapter inference probe")
    parser.add_argument("--probe", action="store_true", help="Status check only — no model load")
    parser.add_argument("--max-new-tokens", type=int, default=150, help="Tokens to generate per prompt")
    parser.add_argument("--base-only", action="store_true", help="Skip adapter, run base model only")
    args = parser.parse_args()

    if args.probe:
        return probe_only()

    if not ADAPTER_DIR.exists():
        print(f"[P-06] Adapter not found at {ADAPTER_DIR}. Run P-04 to completion first.", file=sys.stderr)
        emit({"gate": "C-G6", "status": "failed", "reason": "adapter-not-found"})
        return 1

    result: dict = {
        "gate": "C-G6",
        "probe": "P-06_adapter_inference",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "base_model": BASE_MODEL,
        "adapter_path": str(ADAPTER_DIR.resolve()),
        "status": "failed",
        "hardware": {},
        "base_samples": [],
        "adapter_samples": [],
        "comparison": [],
        "performance": {},
    }

    # --- hardware probe ---
    try:
        import torch
        result["hardware"] = {
            "torch": torch.__version__,
            "cuda": torch.cuda.is_available(),
            "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "vram_total_gb": round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
                if torch.cuda.is_available() else None,
        }
        if not torch.cuda.is_available():
            result["reason"] = "no-CUDA"
            emit(result)
            return 1
        device = "cuda"
    except ImportError as e:
        result["reason"] = f"torch-import-failed: {e}"
        emit(result)
        return 1

    # --- load base model (4-bit NF4, same config as training) ---
    print("[P-06] Loading base model (4-bit NF4)...", flush=True)
    t_load_start = time.perf_counter()
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        bnb_cfg = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            quantization_config=bnb_cfg,
            device_map="auto",
            torch_dtype=torch.bfloat16,
        )
        base_model.eval()
        t_base_loaded = time.perf_counter() - t_load_start
        result["performance"]["base_load_seconds"] = round(t_base_loaded, 1)
        result["performance"]["vram_after_base_gb"] = round(vram_gb(), 2)
        print(f"[P-06] Base model loaded in {t_base_loaded:.1f}s, VRAM: {vram_gb():.2f}GB", flush=True)
    except Exception as e:
        result["reason"] = f"base-model-load-failed: {e}"
        emit(result)
        return 1

    # --- base model inference ---
    print("[P-06] Running base model inference...", flush=True)
    base_tps_list: list[float] = []
    for i, prompt in enumerate(EVAL_PROMPTS):
        print(f"  [base] prompt {i+1}/{len(EVAL_PROMPTS)}...", flush=True)
        out, tps = generate(base_model, tokenizer, prompt, args.max_new_tokens, device)
        result["base_samples"].append({
            "prompt_id": i + 1,
            "prompt": prompt,
            "completion": out,
            "tokens_per_sec": round(tps, 1),
        })
        base_tps_list.append(tps)
        print(f"    → {repr(out[:80])}... ({tps:.1f} tok/s)")

    result["performance"]["base_avg_tps"] = round(sum(base_tps_list) / len(base_tps_list), 1)

    if args.base_only:
        result["status"] = "partial-base-only"
        emit(result)
        return 0

    # --- apply adapter ---
    print("[P-06] Applying claudine-v1 adapter...", flush=True)
    t_adapter_start = time.perf_counter()
    try:
        from peft import PeftModel
        adapter_model = PeftModel.from_pretrained(base_model, str(ADAPTER_DIR))
        adapter_model.eval()
        t_adapter_loaded = time.perf_counter() - t_adapter_start
        result["performance"]["adapter_load_seconds"] = round(t_adapter_loaded, 1)
        result["performance"]["vram_after_adapter_gb"] = round(vram_gb(), 2)
        print(f"[P-06] Adapter applied in {t_adapter_loaded:.1f}s, VRAM: {vram_gb():.2f}GB", flush=True)
    except Exception as e:
        result["reason"] = f"adapter-load-failed: {e}"
        emit(result)
        return 1

    # --- adapter inference ---
    print("[P-06] Running adapter model inference...", flush=True)
    adapter_tps_list: list[float] = []
    for i, prompt in enumerate(EVAL_PROMPTS):
        print(f"  [adapter] prompt {i+1}/{len(EVAL_PROMPTS)}...", flush=True)
        out, tps = generate(adapter_model, tokenizer, prompt, args.max_new_tokens, device)
        result["adapter_samples"].append({
            "prompt_id": i + 1,
            "prompt": prompt,
            "completion": out,
            "tokens_per_sec": round(tps, 1),
        })
        adapter_tps_list.append(tps)
        print(f"    → {repr(out[:80])}... ({tps:.1f} tok/s)")

    result["performance"]["adapter_avg_tps"] = round(sum(adapter_tps_list) / len(adapter_tps_list), 1)

    # --- side-by-side comparison ---
    for i in range(len(EVAL_PROMPTS)):
        base_out = result["base_samples"][i]["completion"]
        adapter_out = result["adapter_samples"][i]["completion"]
        result["comparison"].append({
            "prompt_id": i + 1,
            "prompt": EVAL_PROMPTS[i],
            "base": base_out,
            "adapter": adapter_out,
            "delta_note": "",  # Analyst fills in after review
        })

    result["status"] = "admitted"
    emit(result)
    print(f"\n[P-06] C-G6 admitted. Manifest: {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
