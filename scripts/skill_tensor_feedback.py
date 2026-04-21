#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: skill_tensor_feedback.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
FEEDBACK PROBE — Feedback loop health, ledger writeback status.
The closed loop: execution -> ledger -> weights -> next roulette.

@SID:           TOOL_SKILL_TENSOR_FEEDBACK_V1
@Shabti:        CLI Script
@Purpose:       FEEDBACK PROBE — Feedback loop health, ledger writeback status.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from skill_tensor_common import load_latest, print_kv, probe_header, section, status_badge, step_by_name


def main() -> None:
    data = load_latest()
    probe_header("feedback", data)

    step = step_by_name(data, "feedback")
    if step:
        print_kv("Stage status", f"{step['status']} {status_badge(step['status'])}")
        print_kv("Duration", f"{step['seconds']:.3f}s")

    # Ledger state (the feedback target)
    ledger = section(data, "ledger")
    if ledger:
        print()
        print("--- Ledger State ---")
        print_kv("Mode", ledger.get("ledger_mode", "?"))
        print_kv("Max runs", ledger.get("max_runs", "?"))
        print_kv("Run count", ledger.get("run_count", "?"))
        print_kv("Latest execution status", ledger.get("latest_execution_status", "?"))
        print_kv("Latest seed", ledger.get("latest_seed_text", "?"))
        at_cap = ledger.get("run_count", 0) >= ledger.get("max_runs", float("inf"))
        print_kv("At capacity", at_cap)

    # Bootstrap info
    boot = data.get("bootstrap", {})
    if boot:
        print()
        print("--- Bootstrap ---")
        print_kv("Ledger existed", boot.get("ledger_existed", "?"))
        print_kv("Ledger initialized this run", boot.get("ledger_initialized", "?"))
        print_kv("Entries before run", boot.get("entries_before_run", "?"))


if __name__ == "__main__":
    main()
