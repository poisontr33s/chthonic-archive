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
- Full move count: `76176`
- Legal moves: `5580`
- Degraded moves: `65709`
- Blocked moves: `4887`
- Pool size: `11214`
- Unique action-key groups: `891`
- Excluded cells: `64962`
- Current chain length: `4`
- Current diversity score: `0.9091`
- Current cross-lane coverage: `1.0`
- Current distinct sampled action keys: `4`
- Current history-pruned exact cells: `4`
- Current history-pruned action keys: `4`

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

Any inventoried skill can appear as a symbolic operator in the tensor universe.

Current native adapter-backed operator families include:

- `trainstop-orchestrator`
- `skill-polisher`
- `skill-audit`
- `link-path-guard`
- `mailbox-handoff`
- `python-header-canon`

### Target Skill

Any skill entry discovered under a skill root.

### Target Flavor Mode

- `codex`
- `claude`
- `gemini`

## Universe

The full tensor is generated across:

- `executor_flavor`
- `operator_flavor`
- `operator_skill`
- `target_flavor`
- `target_skill`
- `interpretation_flavor`

## Tensor Axes

A minimal run cell is:

`(executor_flavor, operator_skill, source_root, target_root, target_skill, target_flavor_mode)`

Extended chains add:

`(previous_state, chain_depth, seed, weighting_profile)`

## Action Identity

Each symbolic cell now resolves to a normalized execution identity:

`action_key = (operator, scope, actionable-target...)`

Current execution scopes:

- `skill`
- `lane`

## Current Artifact Policy

- `LATEST.json` and `LATEST.md` companions are regenerated in place.
- No timestamp duplication is required for normal iteration.
- The loop state should be read from the latest artifacts, not reconstructed manually.

## Canonical Current Artifacts

- `docs/ops/SKILL_TENSOR_ROULETTE_SPEC.md`
- `codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json`
- `codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.md`

## Debug / Compatibility Exports

- Stage exports exist only as explicit debug outputs under `codex/mailbox/.tensor_debug/`
- The cycle JSON embeds the summarized state needed for repo-facing review

## Phases

### Phase 0: Anchors

Status: `DONE`

### Phase 1: Plan Layer

Status: `DONE`

Outputs:

- Embedded in `codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json`

### Phase 2: Historical Memory

Status: `DONE`

Outputs:

- Embedded in `codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json`

### Phase 3: Adaptive Weighting

Status: `DONE`

Current refinements:

- recent-touch penalties
- failed-target promotion
- operator-level adjustments
- exact successful recent-cell pruning

Outputs:

- Embedded in `codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json`

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

- Embedded in `codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json`

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
