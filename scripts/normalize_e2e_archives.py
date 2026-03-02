#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: normalize_e2e_archives.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Normalize archived e2e_matrix JSON artifacts for cross-platform consumption.

Targets:
- claude/mailbox/archive/**/e2e_matrix_*.json

Edits (in-place):
- Add schema_version (1) if missing
- Normalize root to POSIX and preserve original as root_native

Invocation:
- uv run scripts/normalize_e2e_archives.py

@SID:           TOOL_NORMALIZE_E2E_ARCHIVES_V1
@Shabti:        CLI Script
@Purpose:       Normalize archived e2e_matrix JSON artifacts for cross-platform consumption.
"""

from __future__ import annotations

import json
from pathlib import Path


def normalize_root(val: str) -> tuple[str, str]:
    native = val
    posix = val.replace("\\", "/")
    return posix, native


def main() -> int:
    root = Path("claude/mailbox/archive")
    if not root.exists():
        return 0

    changed = 0
    for p in sorted(root.rglob("e2e_matrix_*.json")):
        raw_in = json.loads(p.read_text(encoding="utf-8"))

        # Normalize with a consistent field order for readability.
        out: dict[str, object] = {}
        out["schema_version"] = int(raw_in.get("schema_version", 1))
        out["flavor"] = raw_in.get("flavor")

        if "root" in raw_in:
            posix, native = normalize_root(str(raw_in["root"]))
            out["root"] = posix
            out["root_native"] = raw_in.get("root_native", native)
        else:
            # Preserve if absent.
            if "root_native" in raw_in:
                out["root_native"] = raw_in.get("root_native")

        out["results"] = raw_in.get("results", [])

        # Preserve any other fields (stable order: append at end).
        for k in sorted(raw_in.keys()):
            if k in out:
                continue
            out[k] = raw_in[k]

        p.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8", newline="\n")
        changed += 1

    print(f"Normalized {changed} archived e2e_matrix JSON file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
