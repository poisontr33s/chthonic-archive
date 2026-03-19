#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Derive adaptive weighting signals for skill tensor roulette.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "AGENTS.md").exists() and (p / "pyproject.toml").exists():
            return p
    return start.resolve()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_markdown_summary(path: Path, payload: dict) -> None:
    lines = [
        "# Skill Tensor Weights",
        "",
        f"- Pool Size: `{payload.get('pool_size')}`",
        f"- Ledger Entries: `{payload.get('recent_entry_count')}`",
        f"- Pruned Exact Cells: `{len(payload.get('pruned_exact_cells', []))}`",
        "",
        "## Operator Adjustments",
    ]
    for op, val in sorted(payload.get("per_operator_weight_adjustments", {}).items()):
        lines.append(f"- `{op}`: `{val}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build adaptive weights for skill tensor roulette")
    parser.add_argument("--rules", default="config/skill_tensor_rules.json")
    parser.add_argument("--inventory", default="codex/mailbox/SKILL_TENSOR_INVENTORY.json")
    parser.add_argument("--pool", default="codex/mailbox/SKILL_TENSOR_POOL.json")
    parser.add_argument("--ledger", default="codex/mailbox/SKILL_TENSOR_LEDGER.json")
    parser.add_argument("--output", default="codex/mailbox/SKILL_TENSOR_WEIGHTS_LATEST.json")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    rules = load_json(repo_root / args.rules)
    inventory = load_json(repo_root / args.inventory)
    pool = load_json(repo_root / args.pool)
    ledger = load_json(repo_root / args.ledger)

    skills = inventory.get("skills", [])
    pool_cells = pool.get("pool", [])
    entries = ledger.get("entries", [])

    recent_targets = set()
    failed_targets = set()
    recent_success_cells = set()
    operator_counts: dict[str, int] = {}
    success_window = int(rules.get("history_pruning", {}).get("recent_success_window", 5))
    for entry in entries[-10:]:
        for touched in entry.get("touched", []):
            recent_targets.add((touched.get("root"), touched.get("skill")))
        for sampled in entry.get("sampled_steps", []):
            cell = sampled.get("cell", {})
            op = cell.get("operator_skill")
            if op:
                operator_counts[op] = operator_counts.get(op, 0) + 1
        if entry.get("execution_status") in {"failed", "blocked"}:
            for touched in entry.get("touched", []):
                failed_targets.add((touched.get("root"), touched.get("skill")))
        if entry.get("execution_status") == "passed":
            for sampled in entry.get("sampled_steps", []):
                cell = sampled.get("cell", {})
                ident = (
                    cell.get("executor_flavor"),
                    cell.get("operator_skill"),
                    cell.get("source_root"),
                    cell.get("target_root"),
                    cell.get("target_skill"),
                    cell.get("target_flavor_mode"),
                )
                recent_success_cells.add(ident)

    per_skill = {}
    for row in skills:
        lane = row["lane"]
        root = row["root"]
        skill = row["skill"]
        stale_bonus = 1.0
        if row.get("classification") == "candidate":
            stale_bonus += 0.25
        if (root, skill) in recent_targets:
            stale_bonus -= 0.2
        if (root, skill) in failed_targets:
            stale_bonus += 0.35
        if skill in rules.get("lane_specific_targets", {}).get(lane, []):
            stale_bonus += 0.15
        per_skill[f"{root}::{skill}"] = round(stale_bonus, 4)

    per_operator = {}
    total_operator_hits = sum(operator_counts.values()) or 1
    for op in sorted({cell.get("operator_skill") for cell in pool_cells if isinstance(cell, dict)}):
        count = operator_counts.get(op, 0)
        ratio = count / total_operator_hits
        adj = 1.0 - min(0.25, ratio * 0.5)
        per_operator[op] = round(adj, 4)

    pruned_exact_cells = []
    if rules.get("history_pruning", {}).get("prune_exact_success_cells", False):
        for ident in list(recent_success_cells)[: success_window * 8]:
            pruned_exact_cells.append(list(ident))

    payload = {
        "schema_version": 1,
        "sources": {
            "rules": args.rules,
            "inventory": args.inventory,
            "pool": args.pool,
            "ledger": args.ledger,
        },
        "pool_size": pool.get("pool_size"),
        "recent_entry_count": len(entries),
        "per_skill_weight_adjustments": per_skill,
        "per_operator_weight_adjustments": per_operator,
        "pruned_exact_cells": pruned_exact_cells,
    }

    out = repo_root / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_markdown_summary(out.with_suffix(".md"), payload)
    print(out.relative_to(repo_root).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
