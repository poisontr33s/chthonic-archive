#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @SID: PROBE_FORMATRON_CESSATION_V1
# P-07 — formatron escape-sequence cessation gate
#
# Gate: formatron/escape_sequence_cessation
# FAF: docs/reference/FAF_TABBYAPI_PY314_GPU_INFERENCE_HOST.md §Gate 7
#
# Validates formatron import on the current Python version.
# Reports severity level relative to cessation trajectory:
#   3.12 = DeprecationWarning  (historical)
#   3.14 = SyntaxWarning       (you are here)
#   ~3.16 = SyntaxError        (cessation — import fails)
#
# Output: manifest/formatron_cessation_gate.json
# Exit code: 0 = clean or warning_degraded (survivable)
#            1 = FAILED_cessation_hit (SyntaxError — gate blocked)

import importlib.metadata
import json
import pathlib
import sys
import warnings

MANIFEST_DIR = pathlib.Path(__file__).parents[2] / "manifest"
MANIFEST_DIR.mkdir(exist_ok=True)
OUT_PATH = MANIFEST_DIR / "formatron_cessation_gate.json"

PY_VER = sys.version_info
result = {
    "gate": "formatron/escape_sequence_cessation",
    "probe_id": "P-07",
    "python_version": f"{PY_VER.major}.{PY_VER.minor}.{PY_VER.micro}",
    "python_executable": sys.executable,
    "cessation_timeline": {
        "3.12": "DeprecationWarning",
        "3.14": "SyntaxWarning (current horizon)",
        "~3.16": "SyntaxError (cessation — import fails)",
    },
}

try:
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        import formatron  # noqa: F401

    syntax_warnings = [
        {
            "category": w.category.__name__,
            "message": str(w.message),
            "filename": str(w.filename),
            "lineno": w.lineno,
        }
        for w in captured
        if issubclass(w.category, (SyntaxWarning, DeprecationWarning))
    ]

    try:
        result["formatron_version"] = importlib.metadata.version("formatron")
    except importlib.metadata.PackageNotFoundError:
        result["formatron_version"] = "not_found_in_metadata"

    if syntax_warnings:
        result["status"] = "warning_degraded"
        result["level"] = "L3_survivable"
        result["syntax_warnings"] = syntax_warnings
        result["warning_count"] = len(syntax_warnings)
        result["cessation_proximity"] = (
            "AT_BOUNDARY"
            if PY_VER >= (3, 14)
            else "APPROACHING"
        )
        result["membrane_required"] = (
            "Pin formatron to known-working version in apps/tabby-modern/pyproject.toml. "
            "Monitor upstream for fix. Cite FAF Gate 7."
        )
        result["upstream_fix"] = (
            "formatron/formats/json.py:116 — change '\\A','\\z' to r'\\A',r'\\z'; "
            "formatron/schemas/json_schema.py:72 — change '\\[' to r'\\['"
        )
    else:
        result["status"] = "clean"
        result["level"] = "L4_useful"
        result["syntax_warnings"] = []
        result["warning_count"] = 0

    exit_code = 0

except SyntaxError as e:
    result["status"] = "FAILED_cessation_hit"
    result["level"] = "L0_blocked"
    result["error"] = str(e)
    result["error_file"] = getattr(e, "filename", None)
    result["error_lineno"] = getattr(e, "lineno", None)
    result["minimum_condition_to_reopen"] = (
        "formatron upstream fixes invalid escape sequences "
        "OR dependency substituted with cessation-clean alternative"
    )
    result["syntax_warnings"] = []
    exit_code = 1

except ImportError as e:
    result["status"] = "FAILED_import_error"
    result["level"] = "L0_blocked"
    result["error"] = str(e)
    result["minimum_condition_to_reopen"] = "formatron installed in current venv"
    result["syntax_warnings"] = []
    exit_code = 1

OUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
sys.exit(exit_code)
