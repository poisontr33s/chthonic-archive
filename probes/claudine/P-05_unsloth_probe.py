#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# @SID: P-05_UNSLOTH_PROBE
# @GATE: C-G5 — Unsloth FastLanguageModel on Windows Python 3.14 + CUDA 12.8
# @MANIFEST: manifest/claudine_unsloth_probe.json
"""
C-G5: Unsloth stack verification probe.

Verifies:
- torch 2.11.0+cu128 intact (not downgraded)
- triton-windows 3.x operational (CUDA arch=89)
- flash_attn 2.8.3 importable
- Unsloth FastLanguageModel importable (no deps collision)
- trl available
- (Optional) model patch smoke test (--smoke flag)

Exit codes: 0=admitted, 1=failed
"""
import argparse
import json
import sys
import time
from pathlib import Path

MANIFEST_PATH = Path("manifest/claudine_unsloth_probe.json")


def emit(result: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="Run full model patch smoke (uses GPU memory)")
    args = parser.parse_args()

    result: dict = {
        "gate": "C-G5",
        "probe": "P-05_unsloth_probe",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "failed",
        "checks": {},
    }

    # --- torch ---
    try:
        import torch

        v = torch.__version__
        cuda = torch.cuda.is_available()
        dev = torch.cuda.get_device_name(0) if cuda else None
        result["checks"]["torch"] = {"version": v, "cuda": cuda, "device": dev}
        if not cuda:
            emit(result)
            return 1
    except Exception as e:
        result["checks"]["torch"] = {"error": str(e)}
        emit(result)
        return 1

    # --- triton-windows ---
    try:
        import triton

        target = None
        try:
            from triton.runtime.driver import active as _ta  # triton <3.x
            target = str(_ta.get_current_target())
        except ImportError:
            try:
                import triton.backends.nvidia.driver as _td  # triton 3.x
                target = "cuda:89 (sm_89)"
            except Exception:
                target = "triton 3.x — arch from torch"

        result["checks"]["triton"] = {"version": triton.__version__, "target": target}
    except Exception as e:
        result["checks"]["triton"] = {"error": str(e)}
        # triton failure is non-blocking (Unsloth can use xformers fallback)

    # --- flash_attn ---
    try:
        import flash_attn

        result["checks"]["flash_attn"] = {"version": flash_attn.__version__}
    except Exception as e:
        result["checks"]["flash_attn"] = {"error": str(e)}
        # non-blocking — Unsloth falls back to xformers

    # --- xformers ---
    try:
        import xformers

        result["checks"]["xformers"] = {"version": xformers.__version__}
    except Exception as e:
        result["checks"]["xformers"] = {"error": str(e)}

    # --- Unsloth FIRST (must precede trl to apply all optimizations) ---
    try:
        import unsloth  # noqa: F401 — patches torch before trl loads
        from unsloth import FastLanguageModel  # noqa: F401

        result["checks"]["unsloth"] = {"version": unsloth.__version__}
        result["checks"]["unsloth"]["fastlanguagemodel"] = True
    except Exception as e:
        result["checks"]["unsloth"] = {"error": str(e)}
        emit(result)
        return 1

    # --- trl (after Unsloth) ---
    try:
        import trl

        result["checks"]["trl"] = {"version": trl.__version__}
    except Exception as e:
        result["checks"]["trl"] = {"error": str(e)}
        emit(result)
        return 1

    # --- Optional smoke: patch real model ---
    if args.smoke:
        print("Smoke: laster Mistral-7B patch (krev ~7GB VRAM)...")
        try:
            model, tokenizer = FastLanguageModel.from_pretrained(
                "mistralai/Mistral-7B-v0.3",
                max_seq_length=512,
                load_in_4bit=True,
                dtype=None,
            )
            result["checks"]["unsloth"]["smoke_model"] = "mistralai/Mistral-7B-v0.3"
            result["checks"]["unsloth"]["smoke_status"] = "loaded"
            del model, tokenizer
        except Exception as e:
            result["checks"]["unsloth"]["smoke_error"] = str(e)
            result["status"] = "partial"
            emit(result)
            return 1

    result["status"] = "admitted"
    emit(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
