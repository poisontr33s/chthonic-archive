#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SID: PROBE_PRE_G10A_API_FIDELITY
# Gate: pre-G10a — exllamav3 API symbol fidelity check
# Validates that symbols assumed by apps/tabby-modern/src/tabby_modern/state.py
# _load_blocking() actually exist in the installed exllamav3 0.0.30.
# Run inside container e5b8a003e9d1 (or any tabby-modern-gpu image).
# No model file required — import-only probe.
import json, sys, importlib.metadata

result = {
    "probe_id": "pre-G10a",
    "gate": "exllamav3/api_fidelity",
    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    "symbols": {},
    "config_attrs": [],
    "state_py_assumptions": {
        "Config": None,
        "Model": None,
        "Tokenizer": None,
        "cfg.model_dir": None,
        "model.load()": None,
    },
    "verdict": None,
}

try:
    import exllamav3
    result["exllamav3_version"] = importlib.metadata.version("exllamav3")
    tops = [x for x in dir(exllamav3) if not x.startswith("_")]
    result["top_level_exports"] = tops

    # Check each assumed symbol
    for sym in ["Config", "Model", "Tokenizer",
                "ExLlamaV3Config", "ExLlamaV3Model", "ExLlamaV3Tokenizer"]:
        present = hasattr(exllamav3, sym)
        result["symbols"][sym] = "FOUND" if present else "ABSENT"

    # Validate Config instantiation + attribute names
    try:
        from exllamav3 import Config
        result["state_py_assumptions"]["Config"] = "FOUND"
        c = Config()
        all_attrs = [a for a in dir(c) if not a.startswith("_")]
        result["config_attrs"] = all_attrs
        result["state_py_assumptions"]["cfg.model_dir"] = (
            "FOUND" if hasattr(c, "model_dir") else "ABSENT"
        )
        # Also check alternative attribute names
        for alt in ["model_path", "model_directory", "directory", "path"]:
            if hasattr(c, alt):
                result[f"alt_model_attr_{alt}"] = "FOUND"
    except Exception as e:
        result["state_py_assumptions"]["Config"] = f"ERROR: {e}"

    # Validate Model
    try:
        from exllamav3 import Model
        result["state_py_assumptions"]["Model"] = "FOUND"
        result["state_py_assumptions"]["model.load()"] = (
            "FOUND" if hasattr(Model, "load") else "ABSENT — check instance method"
        )
        # Check instance method too
        try:
            m = Model.__new__(Model)
            result["model_instance_has_load"] = hasattr(m, "load")
        except Exception:
            result["model_instance_has_load"] = "could not instantiate without config"
    except Exception as e:
        result["state_py_assumptions"]["Model"] = f"ERROR: {e}"

    # Validate Tokenizer
    try:
        from exllamav3 import Tokenizer
        result["state_py_assumptions"]["Tokenizer"] = "FOUND"
    except Exception as e:
        result["state_py_assumptions"]["Tokenizer"] = f"ERROR: {e}"

    # Verdict
    core_ok = all(
        result["state_py_assumptions"][k] in ("FOUND", None)
        or str(result["state_py_assumptions"][k]).startswith("FOUND")
        for k in ["Config", "Model", "Tokenizer"]
    )
    model_dir_ok = result["state_py_assumptions"]["cfg.model_dir"] == "FOUND"
    result["verdict"] = "CLEAN" if (core_ok and model_dir_ok) else "MISMATCH_DETECTED"

except ImportError as e:
    result["verdict"] = f"IMPORT_FAILED: {e}"

print(json.dumps(result, indent=2))
sys.exit(0 if result.get("verdict") == "CLEAN" else 1)
