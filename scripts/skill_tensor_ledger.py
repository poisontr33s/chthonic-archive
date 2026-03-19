#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Append the latest roulette + plan state into a historical skill tensor ledger.
"""

from __future__ import annotations

import argparse
import json
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


def write_markdown_summary(path: Path, ledger: dict) -> None:
    entries = ledger.get("entries", [])
    latest = entries[-1] if entries else {}
    lines = [
        "# Skill Tensor Ledger",
        "",
        f"- Entries: `{len(entries)}`",
        f"- Latest Status: `{latest.get('execution_status')}`",
        f"- Latest Seed: `{latest.get('seed_text')}`",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Append latest roulette state to tensor ledger")
    parser.add_argument("--roulette", default="codex/mailbox/SKILL_TENSOR_ROULETTE_LATEST.json")
    parser.add_argument("--plan", default="codex/mailbox/SKILL_TENSOR_PLAN_LATEST.json")
    parser.add_argument("--output", default="codex/mailbox/SKILL_TENSOR_LEDGER.json")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    roulette = load_json(repo_root / args.roulette)
    plan = load_json(repo_root / args.plan)

    out = repo_root / args.output
    if out.exists():
        ledger = load_json(out)
    else:
        ledger = {"schema_version": 1, "entries": []}

    steps = plan.get("steps", [])
    touched = [
        {
            "lane": step["cell"]["target_skill_lane"],
            "root": step["cell"]["target_root"],
            "skill": step["cell"]["target_skill"],
        }
        for step in steps
    ]

    entry = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "seed_text": roulette.get("seed_text"),
        "seed_value": roulette.get("seed_value"),
        "chain_length": roulette.get("chain_length_actual"),
        "summary": roulette.get("summary", {}),
        "sampled_steps": roulette.get("selected", []),
        "planned_steps": steps,
        "execution_status": "planned",
        "failure_classes": [],
        "touched": touched,
    }

    ledger.setdefault("entries", []).append(entry)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    write_markdown_summary(out.with_suffix(".md"), ledger)
    print(out.relative_to(repo_root).as_posix())
    print(f"entries={len(ledger['entries'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
