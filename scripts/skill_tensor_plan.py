#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: skill_tensor_plan.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
PLAN PROBE — Current execution plan, step count, capability enforcement.
What the roulette pick turned into before execution.

@SID:           TOOL_SKILL_TENSOR_PLAN_V1
@Shabti:        CLI Script
@Purpose:       PLAN PROBE — Current execution plan, step count, capability enforcement.
"""

import json

from skill_tensor_common import ROOT, load_latest, print_kv, probe_header, section, step_by_name

PLAN_PATH = ROOT / "codex" / "mailbox" / ".tmp_tensor_cycle" / "SKILL_TENSOR_PLAN_LATEST.json"


def main() -> None:
    data = load_latest()
    probe_header("plan", data)

    step = step_by_name(data, "plan")
    if step:
        print_kv("Stage status", step["status"])
        print_kv("Duration", f"{step['seconds']:.3f}s")

    sec = section(data, "plan")
    print_kv("Planned steps", sec.get("step_count", "?"))

    # Read actual plan for detail
    if PLAN_PATH.exists():
        plan_data = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        steps = plan_data.get("steps", plan_data.get("chain", []))
        if steps:
            print()
            print("--- Planned Chain ---")
            for i, s in enumerate(steps):
                op = s.get("operator_skill", s.get("operator", "?"))
                target = s.get("target_skill", s.get("target", "?"))
                lane = s.get("target_skill_lane", s.get("lane", "?"))
                executor = s.get("executor_flavor", "?")
                mode = s.get("adapter_mode", s.get("mode", "?"))
                print(f"  [{i+1}] {executor} runs {op} on {lane}::{target} (mode={mode})")
    else:
        print("  (Plan file not found)")


if __name__ == "__main__":
    main()
