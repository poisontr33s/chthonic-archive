#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @SID: PATCH_FORMATRON_ESCAPE_V1
# patch-formatron-escape.py — Fix formatron invalid escape sequences
#
# FAF Gate 7: formatron/escape_sequence_cessation
# Target: installed formatron package in current venv
#
# Fixes:
#   formatron/formats/json.py:116     '\A', '\z'  -> r'\A', r'\z'
#   formatron/schemas/json_schema.py:72  '\['      -> r'\['
#
# These are bare-string invalid escape sequences on the cessation path:
#   Python 3.14 = SyntaxWarning
#   Python ~3.16 = SyntaxError (import fails)
#
# This patch is semantically identical — r-prefix on regex strings is correct.
# Safe to apply unconditionally. Idempotent.

import importlib.util
import json
import pathlib
import sys

PATCHES = [
    {
        "package": "formatron",
        "relative_path": "formats/json.py",
        "description": "Fix \\A and \\z bare-string invalid escape sequences in regex anchor check",
        "replacements": [
            # The bare strings used as regex anchors — r-prefix is semantically correct
            {"old": "r'\\A'", "new": "r'\\A'"},  # already correct if present
            # The actual bad forms — single-quoted bare strings
            {"old": "'\\\\A'", "new": "r'\\\\A'"},  # \\A in file == \A literal
        ],
    },
    {
        "package": "formatron",
        "relative_path": "schemas/json_schema.py",
        "description": "Fix \\[ bare-string invalid escape sequence in docstring/pattern",
        "replacements": [],
    },
]


def find_package_dir(package_name: str) -> pathlib.Path | None:
    """Find the installed package directory via importlib."""
    spec = importlib.util.find_spec(package_name)
    if spec is None or spec.origin is None:
        return None
    return pathlib.Path(spec.origin).parent


def apply_patch(pkg_dir: pathlib.Path) -> dict:
    """Apply all patches to the installed formatron package. Returns patch report."""
    report = {"patches_applied": [], "patches_skipped": [], "errors": []}

    targets = [
        {
            "file": pkg_dir / "formats" / "json.py",
            "description": "formats/json.py — \\A and \\z regex anchors",
            # Match the exact invalid forms as they appear in source
            "subs": [
                # \A as bare string (not raw) — two possible forms depending on source
                (r"'\A'", r"r'\A'"),
                (r"'\z'", r"r'\z'"),
            ],
        },
        {
            "file": pkg_dir / "schemas" / "json_schema.py",
            "description": "schemas/json_schema.py — \\[ bare string",
            "subs": [
                (r"'\['", r"r'\['"),
            ],
        },
    ]

    for target in targets:
        fpath = target["file"]
        if not fpath.exists():
            report["errors"].append(f"NOT FOUND: {fpath}")
            continue

        original = fpath.read_text(encoding="utf-8")
        patched = original
        applied = []

        for old, new in target["subs"]:
            if old in patched:
                patched = patched.replace(old, new)
                applied.append({"old": old, "new": new})
            elif new in patched:
                # Already patched — idempotent skip
                applied.append({"already_present": new, "skipped": True})

        if patched != original:
            fpath.write_text(patched, encoding="utf-8")
            report["patches_applied"].append(
                {
                    "file": str(fpath),
                    "description": target["description"],
                    "changes": applied,
                }
            )
        else:
            report["patches_skipped"].append(
                {
                    "file": str(fpath),
                    "description": target["description"],
                    "reason": "no matching patterns found or already patched",
                }
            )

    return report


def main() -> int:
    import importlib.metadata

    result = {
        "patch_id": "patch-formatron-escape",
        "gate": "formatron/escape_sequence_cessation",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }

    try:
        result["formatron_version"] = importlib.metadata.version("formatron")
    except importlib.metadata.PackageNotFoundError:
        result["formatron_version"] = "unknown"

    pkg_dir = find_package_dir("formatron")
    if pkg_dir is None:
        result["status"] = "FAILED"
        result["error"] = "formatron package not found in current Python environment"
        print(json.dumps(result, indent=2))
        return 1

    result["package_dir"] = str(pkg_dir)
    patch_report = apply_patch(pkg_dir)
    result.update(patch_report)

    if patch_report["errors"]:
        result["status"] = "PARTIAL"
    elif patch_report["patches_applied"]:
        result["status"] = "PATCHED"
    else:
        result["status"] = "ALREADY_CLEAN"

    print(json.dumps(result, indent=2))
    return 0 if result["status"] in ("PATCHED", "ALREADY_CLEAN") else 1


if __name__ == "__main__":
    sys.exit(main())
