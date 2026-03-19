#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Feed latest execution outcomes back into the tensor ledger and refresh weights.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "AGENTS.md").exists() and (p / "pyproject.toml").exists():
            return p
    return start.resolve()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply latest execution results back into the tensor ledger")
    parser.add_argument("--ledger", default="codex/mailbox/SKILL_TENSOR_LEDGER.json")
    parser.add_argument("--execution", default="codex/mailbox/SKILL_TENSOR_EXECUTION_LATEST.json")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    ledger_path = repo_root / args.ledger
    execution_path = repo_root / args.execution

    ledger = load_json(ledger_path)
    execution = load_json(execution_path)

    entries = ledger.get("entries", [])
    if not entries:
        raise SystemExit("No ledger entries to update.")

    latest = entries[-1]
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
        ["uv", "run", "scripts/skill_tensor_sync_spec.py"],
        cwd=repo_root,
        check=False,
    )

    print(ledger_path.relative_to(repo_root).as_posix())
    print(f"execution_status={latest['execution_status']}")
    print(f"failure_classes={len(failure_classes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
