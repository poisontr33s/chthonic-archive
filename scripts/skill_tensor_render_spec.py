#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Render the skill tensor roulette spec from current live artifact state.
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
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def exists(repo_root: Path, rel: str) -> bool:
    return (repo_root / rel).exists()


def phase_status(repo_root: Path) -> dict[str, str]:
    exec_payload = load_json(repo_root / "codex/mailbox/SKILL_TENSOR_EXECUTION_LATEST.json")
    ledger_exists = exists(repo_root, "codex/mailbox/SKILL_TENSOR_LEDGER.json")
    weights_exists = exists(repo_root, "codex/mailbox/SKILL_TENSOR_WEIGHTS_LATEST.json")
    capabilities_exists = exists(repo_root, "config/skill_operator_capabilities.json")
    plan_exists = exists(repo_root, "codex/mailbox/SKILL_TENSOR_PLAN_LATEST.json")
    roulette_exists = exists(repo_root, "codex/mailbox/SKILL_TENSOR_ROULETTE_LATEST.json")
    pool_exists = exists(repo_root, "codex/mailbox/SKILL_TENSOR_POOL.json")
    inventory_exists = exists(repo_root, "codex/mailbox/SKILL_TENSOR_INVENTORY.json")

    return {
        "phase0": "DONE" if inventory_exists and pool_exists and roulette_exists else "IN PROGRESS",
        "phase1": "DONE" if plan_exists else "IN PROGRESS",
        "phase2": "DONE" if ledger_exists else "IN PROGRESS",
        "phase3": "DONE" if weights_exists else "IN PROGRESS",
        "phase4": "DONE" if capabilities_exists else "IN PROGRESS",
        "phase5": "DONE" if exec_payload.get("overall_status") == "passed" else ("IN PROGRESS" if exec_payload else "PENDING"),
        "phase6": "DONE" if ledger_exists and weights_exists and roulette_exists else "IN PROGRESS",
        "execution_status": exec_payload.get("overall_status", "unknown"),
    }


def render(repo_root: Path) -> str:
    statuses = phase_status(repo_root)
    inventory = load_json(repo_root / "codex/mailbox/SKILL_TENSOR_INVENTORY.json")
    pool = load_json(repo_root / "codex/mailbox/SKILL_TENSOR_POOL.json")
    roulette = load_json(repo_root / "codex/mailbox/SKILL_TENSOR_ROULETTE_LATEST.json")
    weights = load_json(repo_root / "codex/mailbox/SKILL_TENSOR_WEIGHTS_LATEST.json")

    skill_count = len(inventory.get("skills", []))
    pool_size = pool.get("pool_size", 0)
    excluded_size = pool.get("excluded_size", 0)
    chain_length = roulette.get("chain_length_actual", 0)
    diversity_score = roulette.get("summary", {}).get("diversity_score", 0)
    cross_lane_coverage = roulette.get("summary", {}).get("cross_lane_coverage", 0)
    pruned = len(weights.get("pruned_exact_cells", []))

    return f"""---
type: design-spec
category: operations
created: 2026-03-19
description: Ontology and execution model for trainstop skill tensor roulette
---

# Skill Tensor Roulette Spec

This spec is regenerated from the live tensor artifacts. It is the canonical anchor for current state, not a manually-maintained note.

## Live Cycle State

- Latest execution status: `{statuses["execution_status"]}`
- Inventory skill count: `{skill_count}`
- Pool size: `{pool_size}`
- Excluded cells: `{excluded_size}`
- Current chain length: `{chain_length}`
- Current diversity score: `{diversity_score}`
- Current cross-lane coverage: `{cross_lane_coverage}`
- Current history-pruned exact cells: `{pruned}`

## Core Objects

### Agent Flavor

- `codex`
- `claude`
- `gemini`

### Skill Root

- `.codex/skills`
- `.claude/skills`
- `.gemini/extensions/chthonic-archive-sync/skills`

### Operator Skill

- `trainstop-orchestrator`
- `skill-polisher`
- `skill-audit`
- `link-path-guard`

### Target Skill

Any skill entry discovered under a skill root.

### Target Flavor Mode

- `codex`
- `claude`
- `gemini`

## Tensor Axes

A minimal run cell is:

`(executor_flavor, operator_skill, source_root, target_root, target_skill, target_flavor_mode)`

Extended chains add:

`(previous_state, chain_depth, seed, weighting_profile)`

## Current Artifact Policy

- `LATEST.json` and `LATEST.md` companions are regenerated in place.
- No timestamp duplication is required for normal iteration.
- The loop state should be read from the latest artifacts, not reconstructed manually.

## Canonical Current Artifacts

- `docs/ops/SKILL_TENSOR_ROULETTE_SPEC.md`
- `config/skill_tensor_rules.json`
- `config/skill_operator_capabilities.json`
- `codex/mailbox/SKILL_TENSOR_INVENTORY.json`
- `codex/mailbox/SKILL_TENSOR_POOL.json`
- `codex/mailbox/SKILL_TENSOR_ROULETTE_LATEST.json`
- `codex/mailbox/SKILL_TENSOR_PLAN_LATEST.json`
- `codex/mailbox/SKILL_TENSOR_EXECUTION_LATEST.json`
- `codex/mailbox/SKILL_TENSOR_LEDGER.json`
- `codex/mailbox/SKILL_TENSOR_WEIGHTS_LATEST.json`

## Phases

### Phase 0: Anchors

Status: `{statuses["phase0"]}`

### Phase 1: Plan Layer

Status: `{statuses["phase1"]}`

Outputs:

- `codex/mailbox/SKILL_TENSOR_PLAN_LATEST.json`
- `codex/mailbox/SKILL_TENSOR_PLAN_LATEST.md`

### Phase 2: Historical Memory

Status: `{statuses["phase2"]}`

Outputs:

- `codex/mailbox/SKILL_TENSOR_LEDGER.json`
- `codex/mailbox/SKILL_TENSOR_LEDGER.md`

### Phase 3: Adaptive Weighting

Status: `{statuses["phase3"]}`

Current refinements:

- recent-touch penalties
- failed-target promotion
- operator-level adjustments
- exact successful recent-cell pruning

Outputs:

- `codex/mailbox/SKILL_TENSOR_WEIGHTS_LATEST.json`
- `codex/mailbox/SKILL_TENSOR_WEIGHTS_LATEST.md`

### Phase 4: Operator Capability Manifest

Status: `{statuses["phase4"]}`

Outputs:

- `config/skill_operator_capabilities.json`

### Phase 5: Sampled-Chain Executor

Status: `{statuses["phase5"]}`

Current refinements:

- capability enforcement
- artifact verification
- explicit failure kinds
- advisory trainstop freshness gate
- operator-specific command templates beyond root-wide defaults

Outputs:

- `codex/mailbox/SKILL_TENSOR_EXECUTION_LATEST.json`
- `codex/mailbox/SKILL_TENSOR_EXECUTION_LATEST.md`

### Phase 6: Feedback Loop

Status: `{statuses["phase6"]}`

Current refinements:

- execution -> ledger writeback
- ledger -> weight refresh
- weights -> next roulette sample
- stronger history-driven pruning
- richer diversity constraints

## Next Frontier

- stronger history-driven pruning
- more sophisticated weight formulas
- richer roulette diversity constraints
- operator-specific execution semantics
- better pruning of low-value chains
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the tensor spec from live artifacts")
    parser.add_argument("--output", default="docs/ops/SKILL_TENSOR_ROULETTE_SPEC.md")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    out = repo_root / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(repo_root), encoding="utf-8")
    print(out.relative_to(repo_root).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
