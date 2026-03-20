#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Feed latest execution outcomes back into the tensor ledger and refresh weights.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "AGENTS.md").exists() and (p / "pyproject.toml").exists():
            return p
    return start.resolve()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_current_cycle_entry(ledger: dict, roulette: dict, plan: dict) -> dict:
    entries = ledger.setdefault("entries", [])
    latest = entries[-1] if entries else None

    sampled = roulette.get("selected", [])
    latest_sampled = latest.get("sampled_steps", []) if latest else None

    if latest is None or latest_sampled != sampled:
        touched = [
            {
                "lane": step["cell"]["target_skill_lane"],
                "root": step["cell"]["target_root"],
                "skill": step["cell"]["target_skill"],
            }
            for step in plan.get("steps", [])
        ]
        latest = {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "seed_text": roulette.get("seed_text"),
            "seed_value": roulette.get("seed_value"),
            "chain_length": roulette.get("chain_length_actual"),
            "summary": roulette.get("summary", {}),
            "sampled_steps": sampled,
            "planned_steps": plan.get("steps", []),
            "execution_status": "planned",
            "failure_classes": [],
            "touched": touched,
        }
        entries.append(latest)

    return latest


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply latest execution results back into the tensor ledger")
    parser.add_argument("--ledger", default="codex/mailbox/SKILL_TENSOR_LEDGER.json")
    parser.add_argument("--execution", default="codex/mailbox/SKILL_TENSOR_EXECUTION_LATEST.json")
    parser.add_argument("--roulette", default="codex/mailbox/SKILL_TENSOR_ROULETTE_LATEST.json")
    parser.add_argument("--plan", default="codex/mailbox/SKILL_TENSOR_PLAN_LATEST.json")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    ledger_path = repo_root / args.ledger
    execution_path = repo_root / args.execution
    roulette_path = repo_root / args.roulette
    plan_path = repo_root / args.plan

    ledger = load_json(ledger_path)
    execution = load_json(execution_path)
    roulette = load_json(roulette_path)
    plan = load_json(plan_path)

    latest = ensure_current_cycle_entry(ledger, roulette, plan)
    latest["execution_status"] = execution.get("overall_status", "unknown")

    failure_classes = []
    for result in execution.get("results", []):
        if result.get("status") != "passed":
            kind = "generic_failure"
            command = result.get("command") or []
            if any("trainstop-orchestrator/scripts/orchestrate.py" in str(x) for x in command):
                kind = "trainstop_gate_failure"
            elif any("skill_path_guard.py" in str(x) for x in command):
                kind = "path_guard_failure"
            elif any("skill_audit.py" in str(x) for x in command):
                kind = "skill_audit_failure"
            elif any("polish_skill.py" in str(x) for x in command):
                kind = "skill_polisher_failure"
            failure_classes.append(
                {
                    "step": result.get("step"),
                    "kind": kind,
                    "status": result.get("status"),
                    "command": result.get("command"),
                    "rc": result.get("rc"),
                }
            )
    latest["failure_classes"] = failure_classes
    latest["execution_results"] = execution.get("results", [])

    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")

    # Refresh weights from the new ledger state.
    subprocess.run(
        ["uv", "run", "scripts/skill_tensor_weights.py"],
        cwd=repo_root,
        check=False,
    )
    subprocess.run(
        ["uv", "run", "scripts/skill_tensor_render_spec.py"],
        cwd=repo_root,
        check=False,
    )

    print(ledger_path.relative_to(repo_root).as_posix())
    print(f"execution_status={latest['execution_status']}")
    print(f"failure_classes={len(failure_classes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
