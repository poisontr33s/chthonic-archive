---
type: design-spec
category: operations
created: 2026-03-19
description: Ontology and execution model for trainstop skill tensor roulette
---

# Skill Tensor Roulette Spec

This spec is regenerated from the live tensor artifacts. It is the canonical anchor for current state, not a manually-maintained note.

## Live Cycle State

- Latest execution status: `passed`
- Inventory skill count: `92`
- Pool size: `2028`
- Excluded cells: `168`
- Current chain length: `4`
- Current diversity score: `0.9091`
- Current cross-lane coverage: `1.0`
- Current history-pruned exact cells: `4`

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

Status: `DONE`

### Phase 1: Plan Layer

Status: `DONE`

Outputs:

- `codex/mailbox/SKILL_TENSOR_PLAN_LATEST.json`
- `codex/mailbox/SKILL_TENSOR_PLAN_LATEST.md`

### Phase 2: Historical Memory

Status: `DONE`

Outputs:

- `codex/mailbox/SKILL_TENSOR_LEDGER.json`
- `codex/mailbox/SKILL_TENSOR_LEDGER.md`

### Phase 3: Adaptive Weighting

Status: `DONE`

Current refinements:

- recent-touch penalties
- failed-target promotion
- operator-level adjustments
- exact successful recent-cell pruning

Outputs:

- `codex/mailbox/SKILL_TENSOR_WEIGHTS_LATEST.json`
- `codex/mailbox/SKILL_TENSOR_WEIGHTS_LATEST.md`

### Phase 4: Operator Capability Manifest

Status: `DONE`

Outputs:

- `config/skill_operator_capabilities.json`

### Phase 5: Sampled-Chain Executor

Status: `DONE`

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

Status: `DONE`

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
