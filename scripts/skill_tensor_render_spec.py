#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: skill_tensor_render_spec.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
RENDER-SPEC PROBE — Spec freshness check, phase status, artifact coherence.
Validates that docs/ops/SKILL_TENSOR_ROULETTE_SPEC.md reflects current state.

@SID:           TOOL_SKILL_TENSOR_RENDER_SPEC_V1
@Shabti:        CLI Script
@Purpose:       RENDER-SPEC PROBE — Spec freshness check, phase status, artifact coherence.
"""

import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from skill_tensor_common import ROOT, load_latest, print_kv, probe_header, section

SPEC_PATH = ROOT / "docs" / "ops" / "SKILL_TENSOR_ROULETTE_SPEC.md"


def extract_spec_numbers(text: str) -> dict[str, str]:
    """Pull key numbers from the spec markdown for drift detection."""
    patterns = {
        "skill_count": r"Inventory skill count:\s*`(\d+)`",
        "full_move_count": r"Full move count:\s*`(\d+)`",
        "legal_moves": r"Legal moves:\s*`(\d+)`",
        "pool_size": r"Pool size:\s*`(\d+)`",
        "chain_length": r"Current chain length:\s*`(\d+)`",
        "status": r"Latest execution status:\s*`(\w+)`",
    }
    result = {}
    for key, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            result[key] = m.group(1)
    return result


def main() -> None:
    data = load_latest()
    probe_header("render-spec", data)

    if not SPEC_PATH.exists():
        print(f"  SPEC NOT FOUND: {SPEC_PATH.relative_to(ROOT)}")
        return

    spec_text = SPEC_PATH.read_text(encoding="utf-8")
    spec_nums = extract_spec_numbers(spec_text)

    # Compare spec numbers against LATEST.json
    inv = section(data, "inventory")
    uni = section(data, "universe")
    pool = section(data, "pool")
    roulette = section(data, "roulette")

    checks = [
        ("skill_count", str(inv.get("skill_count", "")), spec_nums.get("skill_count", "")),
        ("full_move_count", str(uni.get("move_count", "")), spec_nums.get("full_move_count", "")),
        ("legal_moves", str(uni.get("status_counts", {}).get("legal", "")), spec_nums.get("legal_moves", "")),
        ("pool_size", str(pool.get("pool_size", "")), spec_nums.get("pool_size", "")),
        ("chain_length", str(roulette.get("chain_length", "")), spec_nums.get("chain_length", "")),
        ("status", data.get("overall_status", ""), spec_nums.get("status", "")),
    ]

    print("--- Spec vs LATEST.json ---")
    drifted = 0
    for label, latest_val, spec_val in checks:
        match = latest_val == spec_val
        marker = "OK" if match else "DRIFT"
        if not match:
            drifted += 1
        print(f"  {label}: spec={spec_val or '?'} latest={latest_val or '?'} [{marker}]")

    print()
    if drifted == 0:
        print("Spec is in sync with LATEST.json.")
    else:
        print(f"{drifted} field(s) drifted — run `uv run skill_tensor_cycle.py render-spec` to resync.")

    # Phase status summary
    phases = re.findall(r"### Phase (\d+):.*?\nStatus:\s*`(\w[\w ]*)`", spec_text, re.DOTALL)
    if phases:
        print()
        print("--- Phase Status ---")
        for num, status in phases:
            print(f"  Phase {num}: {status}")


if __name__ == "__main__":
    main()
