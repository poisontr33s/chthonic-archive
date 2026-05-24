#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: skill_tensor_roulette.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
ROULETTE PROBE — Last sampled chain, diversity score, operator/target spread.
This is what the RNG actually picked from the pool.

@SID:           TOOL_SKILL_TENSOR_ROULETTE_V1
@Shabti:        CLI Script
@Purpose:       ROULETTE PROBE — Last sampled chain, diversity score, operator/target spread.
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
    probe_header("roulette", data)

    step = step_by_name(data, "roulette")
    if step:
        print_kv("Stage status", step["status"])
        print_kv("Duration", f"{step['seconds']:.3f}s")

    sec = section(data, "roulette")
    print_kv("Chain length", sec.get("chain_length", "?"))

    summary = sec.get("summary", {})
    if summary:
        print()
        print("--- Diversity ---")
        print_kv("Diversity score", summary.get("diversity_score", "?"))
        print_kv("Cross-lane coverage", summary.get("cross_lane_coverage", "?"))
        print_kv("Operator spread", summary.get("operator_spread", "?"))
        print_kv("Target spread", summary.get("target_spread", "?"))
        print()
        print("--- Coverage ---")
        print_kv("Executor flavors", ", ".join(summary.get("executor_flavors_seen", [])))
        print_kv("Operator skills", ", ".join(summary.get("operator_skills_seen", [])))
        print_kv("Distinct targets", summary.get("distinct_targets_seen", "?"))
        print_kv("Distinct action keys", summary.get("distinct_action_keys_seen", "?"))
        print_kv("Action scopes", ", ".join(summary.get("action_scopes_seen", [])))

    # Action model collisions
    am = data.get("action_model", {})
    if am:
        print()
        print("--- Action Model ---")
        print_kv("Unique action keys", am.get("unique_action_key_count", "?"))
        print_kv("Collapsed groups", am.get("collapsed_group_count", "?"))
        print_kv("Largest collision", am.get("largest_collision_group", "?"))
        print_kv("Sampled has collisions", am.get("sampled_has_action_collisions", "?"))


if __name__ == "__main__":
    main()
