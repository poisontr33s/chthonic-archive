#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: skill_tensor_common.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Skill Tensor Probe Hub — reads LATEST.json and dispatches stage diagnostics.

Upcycled from the shim-ghost era. This is the shared reader for all 9 probes.
Each probe imports `load_latest` and `section` from here, then slices its view.

@SID:           TOOL_SKILL_TENSOR_COMMON_V1
@Shabti:        CLI Script
@Purpose:       Skill Tensor Probe Hub — reads LATEST.json and dispatches stage diagnostics.
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import json
import sys
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    cur = (start or Path(__file__)).resolve()
    for p in [cur, *cur.parents]:
        if (p / "AGENTS.md").exists() and (p / "pyproject.toml").exists():
            return p
    return Path.cwd()


ROOT = find_repo_root()
LATEST = ROOT / "codex" / "mailbox" / "SKILL_TENSOR_CYCLE_LATEST.json"


def load_latest(path: Path | None = None) -> dict:
    """Load the cycle LATEST.json or raise FileNotFoundError with a clear message."""
    target = path or LATEST
    if not target.exists():
        raise FileNotFoundError(
            f"{target.relative_to(ROOT) if target.is_absolute() and ROOT in target.parents else target} "
            f"not found — run skill_tensor_cycle.py first."
        )
    return json.loads(target.read_text(encoding="utf-8"))


def section(data: dict, key: str) -> dict:
    """Extract a named section from the cycle data."""
    return data.get("sections", {}).get(key, {})


def step_by_name(data: dict, name: str) -> dict | None:
    """Find a step entry by stage name."""
    for s in data.get("steps", []):
        if s.get("name") == name:
            return s
    return None


def status_badge(status: str) -> str:
    ok = {"passed", "done", "success"}
    return "[PASS]" if status.lower() in ok else "[FAIL]"


def print_kv(label: str, value, indent: int = 0) -> None:
    pad = "  " * indent
    print(f"{pad}{label}: {value}")


def probe_header(name: str, data: dict) -> None:
    overall = data.get("overall_status", "unknown")
    print(f"=== {name.upper()} PROBE === {status_badge(overall)} overall")
    print()


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Skill Tensor probe hub — summary view")
    ap.add_argument(
        "--latest-path",
        default=None,
        metavar="PATH",
        help="Override path to SKILL_TENSOR_CYCLE_LATEST.json (default: codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json)",
    )
    _args = ap.parse_args()
    try:
        data = load_latest(Path(_args.latest_path) if _args.latest_path else None)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Cycle status: {data.get('overall_status')}")
    print(f"Stages: {data.get('queue_length')}")
    print(f"Sections available: {', '.join(data.get('sections', {}).keys())}")
    steps = data.get("steps", [])
    passed = sum(1 for s in steps if s.get("status") == "passed")
    failed = sum(1 for s in steps if s.get("status") == "failed")
    print(f"Steps: {passed} passed, {failed} failed, {len(steps)} total")
