#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: skill_tensor_ledger.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
LEDGER PROBE — Ledger entries, run history, capacity status.
The memory of what the tensor has done.

@SID:           TOOL_SKILL_TENSOR_LEDGER_V1
@Shabti:        CLI Script
@Purpose:       LEDGER PROBE — Ledger entries, run history, capacity status.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from skill_tensor_common import ROOT, load_latest, print_kv, probe_header, section, step_by_name

LEDGER_PATH = ROOT / "codex" / "mailbox" / ".tmp_tensor_cycle" / "SKILL_TENSOR_LEDGER.json"


def main() -> None:
    data = load_latest()
    probe_header("ledger", data)

    step = step_by_name(data, "ledger")
    if step:
        print_kv("Stage status", step["status"])
        print_kv("Duration", f"{step['seconds']:.3f}s")

    sec = section(data, "ledger")
    print_kv("Mode", sec.get("ledger_mode", "?"))
    print_kv("Max runs", sec.get("max_runs", "?"))
    print_kv("Run count", sec.get("run_count", "?"))
    print_kv("Latest status", sec.get("latest_execution_status", "?"))

    # Try to read the actual ledger for history detail
    if LEDGER_PATH.exists():
        ledger_data = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        runs = ledger_data.get("runs", [])
        print()
        print(f"--- Run History (last 5 of {len(runs)}) ---")
        for run in runs[-5:]:
            status = run.get("execution_status", run.get("status", "?"))
            seed = run.get("seed_text", "?")
            chain = run.get("chain_length", "?")
            ts = run.get("timestamp", "?")
            print(f"  [{status}] chain={chain} seed={seed} @ {ts}")
    else:
        print()
        print(f"  (Ledger file not found at {LEDGER_PATH.relative_to(ROOT)})")


if __name__ == "__main__":
    main()
