#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: skill_tensor_execute.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
EXECUTE PROBE — Last execution status, failure details, timing.
Where the rubber meets the road.

@SID:           TOOL_SKILL_TENSOR_EXECUTE_V1
@Shabti:        CLI Script
@Purpose:       EXECUTE PROBE — Last execution status, failure details, timing.
"""

from skill_tensor_common import load_latest, print_kv, probe_header, section, status_badge, step_by_name


def main() -> None:
    data = load_latest()
    probe_header("execute", data)

    step = step_by_name(data, "execute")
    if step:
        print_kv("Stage status", f"{step['status']} {status_badge(step['status'])}")
        print_kv("Return code", step.get("rc", "?"))
        print_kv("Duration", f"{step['seconds']:.3f}s")
        stderr = step.get("stderr_tail", "")
        if stderr:
            print_kv("Last error", stderr)

    sec = section(data, "execution")
    print_kv("Overall execution status", sec.get("overall_status", "?"))
    print_kv("Result count", sec.get("result_count", "?"))

    # Freshness gate
    fresh = data.get("freshness", {})
    if fresh:
        print()
        print(f"--- Freshness Gate --- {status_badge(fresh.get('status', 'unknown'))}")
        print_kv("Status", fresh.get("status", "?"))
        print_kv("Critical issues", fresh.get("critical_issues", 0))
        print_kv("Warnings", fresh.get("warnings", 0))


if __name__ == "__main__":
    main()
