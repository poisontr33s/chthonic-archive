#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Deterministic sampler for skill tensor roulette chains.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "AGENTS.md").exists() and (p / "pyproject.toml").exists():
            return p
    return start.resolve()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def deterministic_seed(seed_text: str) -> int:
    digest = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def weight_cell(cell: dict, rules: dict, weights: dict | None = None) -> tuple[float, list[str]]:
    reasons: list[str] = []
    weight = 1.0

    operator_modes = rules.get("operator_modes", {})
    mode = operator_modes.get(cell["operator_skill"], "meta")
    if mode == "mutating":
        weight *= 1.4
        reasons.append("mutating_operator:+0.4x")
    elif mode == "read_only":
        weight *= 1.1
        reasons.append("read_only_operator:+0.1x")
    else:
        weight *= 1.2
        reasons.append("meta_operator:+0.2x")

    if cell["executor_flavor"] != cell["target_skill_lane"]:
        weight *= 1.5
        reasons.append("cross_lane:+0.5x")
    else:
        weight *= 1.1
        reasons.append("self_lane:+0.1x")

    if cell["target_flavor_mode"] != cell["target_skill_lane"]:
        weight *= 1.25
        reasons.append("cross_flavor_interp:+0.25x")

    if cell["operator_skill"] == "trainstop-orchestrator":
        weight *= 0.85
        reasons.append("meta_heavy_penalty:-0.15x")

    if weights:
        key = f"{cell['target_root']}::{cell['target_skill']}"
        delta = weights.get("per_skill_weight_adjustments", {}).get(key)
        if isinstance(delta, (int, float)):
            weight *= float(delta)
            reasons.append(f"adaptive_weight:{delta}x")
        op_delta = weights.get("per_operator_weight_adjustments", {}).get(cell["operator_skill"])
        if isinstance(op_delta, (int, float)):
            weight *= float(op_delta)
            reasons.append(f"operator_weight:{op_delta}x")

    return weight, reasons


def cell_identity(cell: dict) -> tuple[str, str, str, str, str, str]:
    return (
        cell["executor_flavor"],
        cell["operator_skill"],
        cell["source_root"],
        cell["target_root"],
        cell["target_skill"],
        cell["target_flavor_mode"],
    )


def transition_allowed(candidate: dict, previous: dict | None, chain: list[dict], rules: dict) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    tr = rules.get("transition_rules", {})

    if tr.get("disallow_duplicate_cells_in_chain", False):
        seen = {cell_identity(step["cell"]) for step in chain}
        if cell_identity(candidate) in seen:
            return False, ["duplicate_cell_blocked"]

    if tr.get("disallow_same_target_skill_repeat", False):
        seen_skills = {(step["cell"]["target_root"], step["cell"]["target_skill"]) for step in chain}
        if (candidate["target_root"], candidate["target_skill"]) in seen_skills:
            return False, ["repeated_target_skill_blocked"]

    if previous and tr.get("disallow_same_operator_consecutive", False):
        if candidate["operator_skill"] == previous["cell"]["operator_skill"]:
            return False, ["same_operator_consecutive_blocked"]

    return True, reasons


def pruned_by_history(candidate: dict, weights: dict | None) -> bool:
    if not weights:
        return False
    ident = [
        candidate["executor_flavor"],
        candidate["operator_skill"],
        candidate["source_root"],
        candidate["target_root"],
        candidate["target_skill"],
        candidate["target_flavor_mode"],
    ]
    return ident in weights.get("pruned_exact_cells", [])


def transition_weight(candidate: dict, previous: dict | None, rules: dict) -> tuple[float, list[str]]:
    if previous is None:
        return 1.0, ["initial_step"]

    tr = rules.get("transition_rules", {})
    weight = 1.0
    reasons: list[str] = []

    if tr.get("prefer_target_lane_to_next_executor", False):
        if previous["cell"]["target_skill_lane"] == candidate["executor_flavor"]:
            weight *= 1.8
            reasons.append("handoff_continuity:+0.8x")

    if tr.get("prefer_root_continuity", False):
        if previous["cell"]["target_root"] == candidate["source_root"]:
            weight *= 1.25
            reasons.append("root_continuity:+0.25x")

    return weight, reasons


def transition_artifact(candidate: dict, previous: dict | None, chain: list[dict], rules: dict, filtered_out: list[str]) -> dict:
    allowed, _ = transition_allowed(candidate, previous, chain, rules)
    weight_mult, weight_reasons = transition_weight(candidate, previous, rules)
    return {
        "allowed": allowed,
        "previous_target_lane": None if previous is None else previous["cell"]["target_skill_lane"],
        "previous_operator": None if previous is None else previous["cell"]["operator_skill"],
        "transition_weight_multiplier": round(weight_mult, 6),
        "transition_weight_reasons": weight_reasons,
        "filtered_out_rules": filtered_out,
    }


def summarize_chain(chain: list[dict]) -> dict:
    if not chain:
        return {
            "diversity_score": 0.0,
            "cross_lane_coverage": 0.0,
            "operator_spread": 0.0,
            "target_spread": 0.0,
        }

    executors = {step["cell"]["executor_flavor"] for step in chain}
    operator_skills = {step["cell"]["operator_skill"] for step in chain}
    targets = {(step["cell"]["target_root"], step["cell"]["target_skill"]) for step in chain}
    cross_lane_steps = [
        step for step in chain
        if step["cell"]["executor_flavor"] != step["cell"]["target_skill_lane"]
    ]

    diversity_score = round((len(executors) + len(operator_skills) + len(targets)) / (3 + 4 + len(chain)), 4)
    cross_lane_coverage = round(len(cross_lane_steps) / len(chain), 4)
    operator_spread = round(len(operator_skills) / len(chain), 4)
    target_spread = round(len(targets) / len(chain), 4)

    return {
        "diversity_score": diversity_score,
        "cross_lane_coverage": cross_lane_coverage,
        "operator_spread": operator_spread,
        "target_spread": target_spread,
        "executor_flavors_seen": sorted(executors),
        "operator_skills_seen": sorted(operator_skills),
        "distinct_targets_seen": len(targets),
    }


def meets_diversity_minimums(summary: dict, rules: dict) -> bool:
    mins = rules.get("diversity_minimums", {})
    if len(summary.get("executor_flavors_seen", [])) < mins.get("min_executor_flavors", 1):
        return False
    if len(summary.get("operator_skills_seen", [])) < mins.get("min_operator_skills", 1):
        return False
    if summary.get("cross_lane_coverage", 0.0) < mins.get("min_cross_lane_coverage", 0.0):
        return False
    return True


def write_markdown_summary(path: Path, payload: dict) -> None:
    summary = payload.get("summary", {})
    lines = [
        "# Skill Tensor Roulette",
        "",
        f"- Seed: `{payload.get('seed_text')}`",
        f"- Seed Value: `{payload.get('seed_value')}`",
        f"- Chain Length: `{payload.get('chain_length_actual')}`",
        f"- Pool Size: `{payload.get('pool_size')}`",
        f"- Diversity Score: `{summary.get('diversity_score')}`",
        f"- Cross-Lane Coverage: `{summary.get('cross_lane_coverage')}`",
        "",
        "## Steps",
    ]
    for step in payload.get("selected", []):
        cell = step["cell"]
        lines += [
            f"### Step {step['step']}",
            f"- Executor: `{cell['executor_flavor']}`",
            f"- Operator: `{cell['operator_skill']}`",
            f"- Target: `{cell['target_root']}::{cell['target_skill']}`",
            f"- Flavor: `{cell['target_flavor_mode']}`",
            f"- Weight: `{step['weight']}`",
            "",
        ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sample_chain(pool: list[dict], rules: dict, weights: dict | None, rng: random.Random, chain_length: int) -> list[dict]:
    chain: list[dict] = []
    previous: dict | None = None

    for step_index in range(chain_length):
        available: list[tuple[dict, float, list[str]]] = []
        filtered_summary: dict[str, int] = {}
        for cell in pool:
            if pruned_by_history(cell, weights):
                filtered_summary["history_pruned"] = filtered_summary.get("history_pruned", 0) + 1
                continue
            allowed, blocked_reasons = transition_allowed(cell, previous, chain, rules)
            if not allowed:
                for reason in blocked_reasons:
                    filtered_summary[reason] = filtered_summary.get(reason, 0) + 1
                continue
            base_weight, base_reasons = weight_cell(cell, rules, weights)
            trans_weight, trans_reasons = transition_weight(cell, previous, rules)
            available.append((cell, base_weight * trans_weight, base_reasons + trans_reasons))

        if not available:
            break

        total = sum(w for _, w, _ in available)
        pick = rng.uniform(0, total)
        upto = 0.0
        chosen_index = 0
        for i, (_, weight, _) in enumerate(available):
            upto += weight
            if upto >= pick:
                chosen_index = i
                break

        cell, weight, reasons = available[chosen_index]
        chain.append(
            {
                "step": step_index + 1,
                "cell": cell,
                "weight": round(weight, 6),
                "reasons": reasons,
                "transition": transition_artifact(
                    cell,
                    previous,
                    chain,
                    rules,
                    [f"{k}:{v}" for k, v in sorted(filtered_summary.items())],
                ),
            }
        )
        previous = chain[-1]

    return chain


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic skill tensor roulette sampler")
    parser.add_argument("--rules", default="config/skill_tensor_rules.json")
    parser.add_argument("--pool", default="codex/mailbox/SKILL_TENSOR_POOL.json")
    parser.add_argument("--weights", default="codex/mailbox/SKILL_TENSOR_WEIGHTS_LATEST.json")
    parser.add_argument("--output", default="codex/mailbox/SKILL_TENSOR_ROULETTE_LATEST.json")
    parser.add_argument("--seed", default="trainstop-default-seed")
    parser.add_argument("--chain-length", type=int, default=4)
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    rules = load_json(repo_root / args.rules)
    pool_payload = load_json(repo_root / args.pool)
    weights_path = repo_root / args.weights
    weights = load_json(weights_path) if weights_path.exists() else None
    pool = list(pool_payload.get("pool", []))

    seed_value = deterministic_seed(args.seed)
    rng = random.Random(seed_value)
    chain = []
    for _ in range(12):
        chain = sample_chain(pool, rules, weights, rng, args.chain_length)
        if meets_diversity_minimums(summarize_chain(chain), rules):
            break

    summary = summarize_chain(chain)
    payload = {
        "schema_version": 1,
        "seed_text": args.seed,
        "seed_value": seed_value,
        "chain_length_requested": args.chain_length,
        "chain_length_actual": len(chain),
        "pool_size": pool_payload.get("pool_size"),
        "weights_source": args.weights if weights is not None else None,
        "selected": chain,
        "summary": summary,
    }

    out = repo_root / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_markdown_summary(out.with_suffix(".md"), payload)
    print(out.relative_to(repo_root).as_posix())
    print(f"seed_value={seed_value}")
    print(f"chain_length={len(chain)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
