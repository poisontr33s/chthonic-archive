#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Build an execution plan artifact from a sampled skill tensor roulette chain.
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


def command_for_step(cell: dict) -> list[str]:
    operator = cell["operator_skill"]
    target_root = cell["target_root"]
    flavor = cell["target_flavor_mode"]
    target_skill = cell["target_skill"]

    if operator == "skill-audit":
        return [
            "uv",
            "run",
            "scripts/skill_audit.py",
            "--flavor",
            flavor,
            "--root",
            target_root,
            "--skill",
            target_skill,
        ]

    if operator == "skill-polisher":
        return [
            "uv",
            "run",
            ".codex/skills/skill-polisher/scripts/polish_skill.py",
            str(Path(target_root) / target_skill),
            "--mode",
            "verify",
            "--target-flavor",
            flavor,
            "--no-require-assets",
        ]

    if operator == "link-path-guard":
        return [
            "uv",
            "run",
            "scripts/skill_path_guard.py",
            str(Path(target_root) / target_skill / "SKILL.md"),
        ]

    if operator == "trainstop-orchestrator":
        return [
            "uv",
            "run",
            ".codex/skills/trainstop-orchestrator/scripts/orchestrate.py",
            "--target",
            cell["target_skill_lane"],
            "--lane",
            "maintenance",
        ]

    return ["echo", f"NO_COMMAND_MAPPING:{operator}"]


def expected_artifacts(cell: dict) -> list[str]:
    operator = cell["operator_skill"]

    if operator == "skill-audit":
        return []
    if operator == "skill-polisher":
        return []
    if operator == "link-path-guard":
        return [f"logs/skill_path_guard.log"]
    if operator == "trainstop-orchestrator":
        return ["codex/mailbox/TRAINSTOP_ORCHESTRATOR_LATEST.json"]
    return []


def expected_artifact_class(cell: dict) -> str:
    operator = cell["operator_skill"]
    if operator == "skill-audit":
        return "machine_report"
    if operator == "skill-polisher":
        return "verification_report"
    if operator == "link-path-guard":
        return "log"
    if operator == "trainstop-orchestrator":
        return "orchestration_report"
    return "unspecified"


def safety_class(cell: dict, rules: dict) -> str:
    mode = rules.get("operator_modes", {}).get(cell["operator_skill"], "meta")
    if mode == "read_only":
        return "read_only"
    if mode == "mutating":
        if cell["executor_flavor"] == cell["target_skill_lane"]:
            return "local_mutation"
        return "cross_lane_mutation"
    return "meta_orchestration"


def stop_condition(step: dict) -> str:
    safety = step["safety_class"]
    if safety in {"cross_lane_mutation", "meta_orchestration"}:
        return "stop_on_nonzero_or_missing_artifact"
    return "stop_on_nonzero"


def capability_for(cell: dict, capabilities: dict) -> dict:
    return capabilities.get("operators", {}).get(cell["operator_skill"], {})


def write_markdown_summary(path: Path, payload: dict) -> None:
    lines = [
        "# Skill Tensor Plan",
        "",
        f"- Seed: `{payload.get('seed_text')}`",
        f"- Seed Value: `{payload.get('seed_value')}`",
        f"- Chain Length: `{payload.get('chain_length')}`",
        "",
        "## Steps",
    ]
    for step in payload.get("steps", []):
        cell = step["cell"]
        lines += [
            f"### Step {step['step']}",
            f"- Executor: `{cell['executor_flavor']}`",
            f"- Operator: `{cell['operator_skill']}`",
            f"- Target: `{cell['target_root']}::{cell['target_skill']}`",
            f"- Flavor: `{cell['target_flavor_mode']}`",
            f"- Safety: `{step['safety_class']}`",
            f"- Artifact Class: `{step['expected_artifact_class']}`",
            f"- Command: `{' '.join(step['command'])}`",
            "",
        ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a plan artifact from sampled skill roulette")
    parser.add_argument("--rules", default="config/skill_tensor_rules.json")
    parser.add_argument("--capabilities", default="config/skill_operator_capabilities.json")
    parser.add_argument("--input", default="codex/mailbox/SKILL_TENSOR_ROULETTE_LATEST.json")
    parser.add_argument("--output", default="codex/mailbox/SKILL_TENSOR_PLAN_LATEST.json")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    rules = load_json(repo_root / args.rules)
    capabilities = load_json(repo_root / args.capabilities)
    sampled = load_json(repo_root / args.input)

    plan_steps = []
    for selected in sampled.get("selected", []):
        cell = selected["cell"]
        step_plan = {
            "step": selected["step"],
            "cell": cell,
            "command": command_for_step(cell),
            "expected_artifacts": expected_artifacts(cell),
            "expected_artifact_class": expected_artifact_class(cell),
            "operator_mode": rules.get("operator_modes", {}).get(cell["operator_skill"], "meta"),
            "operator_capabilities": capability_for(cell, capabilities),
            "safety_class": safety_class(cell, rules),
            "weight": selected.get("weight"),
            "weight_reasons": selected.get("reasons", []),
            "transition": selected.get("transition", {}),
        }
        step_plan["stop_condition"] = stop_condition(step_plan)
        plan_steps.append(step_plan)

    payload = {
        "schema_version": 1,
        "roulette_source": args.input,
        "capabilities_source": args.capabilities,
        "seed_text": sampled.get("seed_text"),
        "seed_value": sampled.get("seed_value"),
        "chain_length": sampled.get("chain_length_actual"),
        "steps": plan_steps,
    }

    out = repo_root / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_markdown_summary(out.with_suffix(".md"), payload)
    print(out.relative_to(repo_root).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
