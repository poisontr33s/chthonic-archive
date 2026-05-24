#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: skill_tensor_pool.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
POOL PROBE — Pool size, legal vs degraded vs blocked, exclusion ratio.
The pool is the set of cells eligible for roulette selection.

@SID:           TOOL_SKILL_TENSOR_POOL_V1
@Shabti:        CLI Script
@Purpose:       POOL PROBE — Pool size, legal vs degraded vs blocked, exclusion ratio.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from skill_tensor_common import load_latest, print_kv, probe_header, section, step_by_name


def main() -> None:
    data = load_latest()
    probe_header("pool", data)

    step = step_by_name(data, "pool")
    if step:
        print_kv("Stage status", step["status"])
        print_kv("Duration", f"{step['seconds']:.3f}s")

    sec = section(data, "pool")
    pool_size = sec.get("pool_size", 0)
    excluded = sec.get("excluded_size", 0)
    groups = sec.get("action_group_count", 0)
    total = pool_size + excluded

    print_kv("Pool size (legal)", pool_size)
    print_kv("Excluded cells", excluded)
    print_kv("Total universe cells", total)
    print_kv("Inclusion rate", f"{pool_size / total * 100:.1f}%" if total else "N/A")
    print_kv("Action key groups", groups)

    # Universe breakdown
    uni = section(data, "universe")
    if uni:
        print()
        print("--- Universe Breakdown ---")
        print_kv("Total moves", uni.get("move_count", "?"))
        for status, count in uni.get("status_counts", {}).items():
            print_kv(f"  {status}", count)
        print()
        print("--- Execution Kind ---")
        for kind, count in uni.get("execution_kind_counts", {}).items():
            print_kv(f"  {kind}", count)


if __name__ == "__main__":
    main()
