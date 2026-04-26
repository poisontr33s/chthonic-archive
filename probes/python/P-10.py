"""
P-10 — tabby_modern / model_load_gate
Gate 10: validates ModelState.load() succeeds against a real exl2 model.

Run with model mounted read-only at /models/test-model:
  podman run --rm ... \
    -v /path/to/Llama-3.1-8B-Instruct-exl2-8.0bpw:/models/test-model:ro \
    <IMAGE> python /ext-probes/P-10.py

Emits: /workspace/manifest/tabby_model_load_gate.json
Exit 0 = admitted. Exit 1 = failed.
"""

from __future__ import annotations

import asyncio
import json
import os
import pathlib
import sys
import time

MODEL_DIR = pathlib.Path("/models/test-model")
MANIFEST_DIR = pathlib.Path("/workspace/manifest")
MANIFEST_PATH = MANIFEST_DIR / "tabby_model_load_gate.json"


def _verify_model_dir() -> dict:
    if not MODEL_DIR.exists():
        return {"check": "model_dir_exists", "status": "FAIL", "detail": f"{MODEL_DIR} not mounted"}
    files = list(MODEL_DIR.iterdir())
    names = [f.name for f in files]
    has_config = "config.json" in names
    has_tokenizer = "tokenizer.json" in names or "tokenizer_config.json" in names
    has_weights = any(n.endswith(".safetensors") for n in names)
    return {
        "check": "model_dir_contents",
        "status": "OK" if (has_config and has_tokenizer and has_weights) else "FAIL",
        "files_found": sorted(names),
        "has_config_json": has_config,
        "has_tokenizer": has_tokenizer,
        "has_safetensors": has_weights,
    }


async def _run_load() -> dict:
    from tabby_modern.state import ModelState

    state = ModelState()
    t0 = time.perf_counter()
    await state.load(MODEL_DIR)
    elapsed = time.perf_counter() - t0

    return {
        "check": "model_load",
        "status": "OK" if state.loaded else "FAIL",
        "state_loaded": state.loaded,
        "model_name": state.model_name,
        "load_time_s": round(elapsed, 2),
    }


def main() -> int:
    results: list[dict] = []
    verdict = "ADMITTED"

    # Step 1: model directory check
    dir_check = _verify_model_dir()
    results.append(dir_check)
    if dir_check["status"] != "OK":
        verdict = "FAILED_MODEL_DIR"

    # Step 2: tabby_modern import check
    if verdict == "ADMITTED":
        try:
            import tabby_modern  # noqa: F401
            results.append({"check": "tabby_modern_import", "status": "OK"})
        except Exception as exc:
            results.append({"check": "tabby_modern_import", "status": "FAIL", "detail": str(exc)})
            verdict = "FAILED_IMPORT"

    # Step 3: model load
    if verdict == "ADMITTED":
        try:
            load_result = asyncio.run(_run_load())
            results.append(load_result)
            if load_result["status"] != "OK":
                verdict = "FAILED_LOAD"
        except Exception as exc:
            results.append({"check": "model_load", "status": "FAIL", "detail": str(exc)})
            verdict = "FAILED_LOAD"

    # Emit manifest
    manifest = {
        "gate": "tabby_model_load_gate",
        "probe": "P-10",
        "level": "L2" if verdict == "ADMITTED" else "L0",
        "status": "admitted_model_load_gate" if verdict == "ADMITTED" else "failed",
        "verdict": verdict,
        "model_dir": str(MODEL_DIR),
        "checks": results,
    }

    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))

    return 0 if verdict == "ADMITTED" else 1


if __name__ == "__main__":
    sys.exit(main())
