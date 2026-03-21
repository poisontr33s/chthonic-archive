#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
INVENTORY PROBE — Skill count per lane, parity gaps, missing surfaces.
Reads from LATEST.json inventory section + live filesystem for delta detection.
"""

from __future__ import annotations

import json
from pathlib import Path

from skill_tensor_common import (
    ROOT,
    load_latest,
    print_kv,
    probe_header,
    section,
    step_by_name,
)

SKILL_ROOTS = {
    "claude": ROOT / ".claude" / "skills",
    "codex": ROOT / ".codex" / "skills",
    "gemini": ROOT / ".gemini" / "extensions" / "chthonic-archive-sync" / "skills",
}


def live_skills(root: Path) -> set[str]:
    if not root.exists():
        return set()
    return {d.name for d in root.iterdir() if d.is_dir() and not d.name.startswith(".")}


def main() -> None:
    data = load_latest()
    probe_header("inventory", data)

    step = step_by_name(data, "inventory")
    if step:
        print_kv("Stage status", step["status"])
        print_kv("Duration", f"{step['seconds']:.3f}s")

    sec = section(data, "inventory")
    print_kv("Inventoried skill count (last cycle)", sec.get("skill_count", "?"))
    print()

    # Live filesystem comparison
    print("--- Live Filesystem ---")
    lane_sets: dict[str, set[str]] = {}
    for lane, root in SKILL_ROOTS.items():
        skills = live_skills(root)
        lane_sets[lane] = skills
        print_kv(f"{lane}", f"{len(skills)} skills", indent=1)

    # Parity analysis
    all_skills = set()
    for s in lane_sets.values():
        all_skills |= s
    shared = lane_sets["claude"] & lane_sets["codex"] & lane_sets["gemini"]
    print()
    print("--- Parity ---")
    print_kv("Total unique skills", len(all_skills))
    print_kv("Shared by all three", len(shared))
    print_kv("Parity gap", len(all_skills) - len(shared))

    if len(all_skills) > len(shared):
        print()
        for lane, skills in lane_sets.items():
            only = skills - shared
            missing = all_skills - skills
            if only:
                print(f"  {lane}-only: {', '.join(sorted(only))}")
            if missing:
                print(f"  {lane}-missing: {', '.join(sorted(missing))}")


if __name__ == "__main__":
    main()
