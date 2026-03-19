#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Build the legal run-cell pool for skill tensor roulette.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "AGENTS.md").exists() and (p / "pyproject.toml").exists():
            return p
    return start.resolve()


@dataclass
class RunCell:
    executor_flavor: str
    operator_skill: str
    source_root: str
    target_root: str
    target_skill: str
    target_skill_lane: str
    target_flavor_mode: str


@dataclass
class ExcludedCell:
    executor_flavor: str
    operator_skill: str
    target_root: str
    target_skill: str
    target_skill_lane: str
    target_flavor_mode: str
    reason: str


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_markdown_summary(path: Path, payload: dict) -> None:
    lines = [
        "# Skill Tensor Pool",
        "",
        f"- Pool Size: `{payload.get('pool_size')}`",
        f"- Excluded Size: `{payload.get('excluded_size')}`",
        "",
        "## Notes",
        "- Pool contains legal run-cells only.",
        "- Excluded cells include reasons in the JSON artifact.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build legal skill tensor run-cell pool")
    parser.add_argument("--rules", default="config/skill_tensor_rules.json")
    parser.add_argument("--inventory", default="codex/mailbox/SKILL_TENSOR_INVENTORY.json")
    parser.add_argument("--output", default="codex/mailbox/SKILL_TENSOR_POOL.json")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    rules = load_json(repo_root / args.rules)
    inventory = load_json(repo_root / args.inventory)

    agent_flavors = list(rules["agent_flavors"])
    skill_roots = dict(rules["skill_roots"])
    operator_skills = list(rules["operator_skills"])
    target_flavor_modes = list(rules["target_flavor_modes"])
    excluded_targets = set(rules.get("excluded_targets", []))
    lane_specific = {k: set(v) for k, v in rules.get("lane_specific_targets", {}).items()}

    skills = [row for row in inventory.get("skills", []) if isinstance(row, dict)]
    target_rows = [row for row in skills if row.get("classification") == "candidate" and row.get("skill") not in excluded_targets]

    pool: list[RunCell] = []
    excluded: list[ExcludedCell] = []

    for executor in agent_flavors:
        source_root = skill_roots[executor]
        for operator in operator_skills:
            for target in target_rows:
                target_skill = str(target["skill"])
                target_root = str(target["root"])
                target_lane = str(target["lane"])
                for target_flavor in target_flavor_modes:
                    reason = None

                    # Lane-specific targets can always run on themselves, but cross-lane
                    # use should be explicitly allowed later. Stage 1 excludes them.
                    if target_skill in lane_specific.get(target_lane, set()) and executor != target_lane:
                        reason = f"lane_specific_target_for_{target_lane}"

                    if reason:
                        excluded.append(
                            ExcludedCell(
                                executor_flavor=executor,
                                operator_skill=operator,
                                target_root=target_root,
                                target_skill=target_skill,
                                target_skill_lane=target_lane,
                                target_flavor_mode=target_flavor,
                                reason=reason,
                            )
                        )
                    else:
                        pool.append(
                            RunCell(
                                executor_flavor=executor,
                                operator_skill=operator,
                                source_root=source_root,
                                target_root=target_root,
                                target_skill=target_skill,
                                target_skill_lane=target_lane,
                                target_flavor_mode=target_flavor,
                            )
                        )

    payload = {
        "schema_version": 1,
        "rules_source": args.rules,
        "inventory_source": args.inventory,
        "pool_size": len(pool),
        "excluded_size": len(excluded),
        "pool": [asdict(cell) for cell in pool],
        "excluded": [asdict(cell) for cell in excluded],
    }

    out = repo_root / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_markdown_summary(out.with_suffix(".md"), payload)
    print(out.relative_to(repo_root).as_posix())
    print(f"pool_size={len(pool)}")
    print(f"excluded_size={len(excluded)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
