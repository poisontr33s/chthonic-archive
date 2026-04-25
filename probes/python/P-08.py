#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @SID: PROBE_EXLLAMAV2_SOURCE_BUILD_V1
# P-08.py — exllamav2 source build validation on Linux cp314
#
# FAF Gate 4: exllamav2/cp314_source_build_linux
# Platform-stratification reframe (FAF v0.4):
#   The wheel ceiling (cp313) is a publishing constraint, not a code barrier.
#   On Linux with CUDA dev + GCC + cmake, `pip install .` builds from source.
#   The exllamav2 source has no Python 3.14 incompatibility.
#
# Run AFTER: build/tabby-modern-gpu/Containerfile G4 layer executes
#   (git clone turboderp-org/exllamav2 v0.3.2 && uv pip install . --no-build-isolation)
#
# Emits: manifest/exllamav2_source_gate.json
# Exit 0: admitted (source build succeeded, import works)
# Exit 1: source build failed or import error

import datetime
import importlib.metadata
import json
import pathlib
import sys

result: dict = {
    "probe_id": "P-08",
    "gate": "exllamav2/cp314_source_build_linux",
    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    "substrate": "linux",
    "note": (
        "Wall is the wheel, not the code. "
        "Source build on Linux CUDA dev environment (CUDA 12.8, GCC, cmake)."
    ),
}

# --- Step 1: package import ---
try:
    import exllamav2  # noqa: F401

    try:
        result["exllamav2_version"] = importlib.metadata.version("exllamav2")
    except importlib.metadata.PackageNotFoundError:
        result["exllamav2_version"] = "unknown (metadata absent — source install)"

    result["import_result"] = "SUCCESS"
    result["level"] = "L1_installed"
    result["status"] = "admitted_L1_source_linux"

    # --- Step 2: config class import (L2 — interrogable) ---
    try:
        from exllamav2 import ExLlamaV2Config  # noqa: F401

        result["config_import"] = "SUCCESS"
        result["level"] = "L2_interrogable"
        result["status"] = "admitted_L2_source_linux"
    except Exception as cfg_err:
        result["config_import"] = f"PARTIAL: {cfg_err}"

except ImportError as e:
    result["import_result"] = f"FAILED: {e}"
    result["level"] = "L0_blocked"
    result["status"] = "source_build_failed"
    result["error"] = str(e)
    result["minimum_condition_to_reopen"] = (
        "exllamav2 source build succeeds in CUDA dev container "
        "(git clone v0.3.2 + uv pip install . --no-build-isolation)"
    )

result["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"

manifest = pathlib.Path("/workspace/manifest/exllamav2_source_gate.json")
manifest.parent.mkdir(parents=True, exist_ok=True)
manifest.write_text(json.dumps(result, indent=2), encoding="utf-8")

print(json.dumps(result, indent=2))
sys.exit(0 if result.get("status", "").startswith("admitted") else 1)
