#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: skill_tensor_weights.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
WEIGHTS PROBE — Weight distribution, pruning stats, recent-touch penalties.
How the roulette is biased before selection.

@SID:           TOOL_SKILL_TENSOR_WEIGHTS_V1
@Shabti:        CLI Script
@Purpose:       WEIGHTS PROBE — Weight distribution, pruning stats, recent-touch penalties.
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from skill_tensor_common import load_latest, print_kv, probe_header, section, step_by_name


def main() -> None:
    data = load_latest()
    probe_header("weights", data)

    step = step_by_name(data, "weights")
    if step:
        print_kv("Stage status", step["status"])
        print_kv("Duration", f"{step['seconds']:.3f}s")

    sec = section(data, "weights")
    print_kv("Recent ledger entries used", sec.get("recent_entry_count", "?"))
    print_kv("Pruned action keys", sec.get("pruned_action_key_count", "?"))
    print_kv("Pruned exact cells", sec.get("pruned_exact_cell_count", "?"))

    # Cross-ref with pool for coverage
    pool = section(data, "pool")
    if pool:
        pool_size = pool.get("pool_size", 0)
        pruned = sec.get("pruned_exact_cell_count", 0)
        effective = pool_size - pruned
        print()
        print("--- Effective Pool After Pruning ---")
        print_kv("Pool before pruning", pool_size)
        print_kv("Cells pruned by history", pruned)
        print_kv("Effective pool", effective)
        if pool_size > 0:
            print_kv("Pruning rate", f"{pruned / pool_size * 100:.2f}%")


if __name__ == "__main__":
    main()
