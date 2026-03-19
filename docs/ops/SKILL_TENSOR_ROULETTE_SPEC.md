---
type: design-spec
category: operations
created: 2026-03-19
description: Ontology and execution model for trainstop skill tensor roulette
---

# Skill Tensor Roulette Spec

This spec defines the first-stage architecture for the Train Stop tensor challenge.

The immediate goal is not to run every combination. The immediate goal is to define the legal state space and produce a deterministic inventory from which roulette chains can be sampled later.

## Stage 1 Scope

Stage 1 produces three artifacts:

1. Ontology spec (this file)
2. Legality manifest (`config/skill_tensor_rules.json`)
3. Inventory generator (`scripts/skill_tensor_inventory.py`)

No roulette execution happens in Stage 1.

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

A skill that can operate on other skills or roots.

Initial intended operator set:

- `trainstop-orchestrator`
- `skill-polisher`
- `skill-audit`
- `link-path-guard`

### Target Skill

Any skill entry discovered under a skill root.

### Target Flavor Mode

Interpretation mode used by the operator:

- `codex`
- `claude`
- `gemini`

### Chain Depth

Ordered position of a step in a roulette chain.

## Tensor Axes

A minimal run cell is:

`(executor_flavor, operator_skill, source_root, target_root, target_skill, target_flavor_mode)`

Extended chains add:

`(previous_state, chain_depth, seed, weighting_profile)`

## Stage 1 Legality Rules

The legality manifest decides what enters the pool.

Initial rule classes:

1. Operator eligibility
2. Target eligibility
3. Lane/flavor compatibility
4. Self-target restrictions
5. Redirect/stub exclusion
6. Read-only vs mutating operator behavior

## Pool vs Execution

Stage 1 only creates the pool candidate space.

The pool is:

- all legal run cells
- annotated with metadata
- not executed

Later stages can:

- sample one run
- sample `k` runs
- generate deterministic chains from a seed

## Required Success Artifacts

Every future roulette run should emit:

1. sampled chain
2. legality proof / reasons included
3. executor + operator + target tuple per hop
4. pass/fail state per hop
5. resulting artifacts / diffs / reports

Current `LATEST` artifact policy:

- JSON and Markdown companions are regenerated in place.
- The tensor loop does not create timestamp-spam artifacts by default.
- Canonical `LATEST` files act as the live anchor surface for the current cycle.

## Initial Constraints

The first implementation should exclude:

- redirect-only skills
- stub/system-only folders
- skills with no `SKILL.md`

The first implementation should classify but not yet auto-execute:

- lane-specific skills
- cross-flavor drift
- stale mirrored copies

## Phases

### Phase 0: Anchors

Status: `DONE`

Artifacts:

1. `DONE` ontology spec
2. `DONE` legality manifest
3. `DONE` inventory artifact
4. `DONE` legal run-cell pool
5. `DONE` deterministic roulette sample

Current canonical anchors:

- `docs/ops/SKILL_TENSOR_ROULETTE_SPEC.md`
- `config/skill_tensor_rules.json`
- `codex/mailbox/SKILL_TENSOR_INVENTORY.json`
- `codex/mailbox/SKILL_TENSOR_POOL.json`
- `codex/mailbox/SKILL_TENSOR_ROULETTE_LATEST.json`

### Phase 1: Plan Layer

Goal:

Convert a sampled roulette chain into an executable but non-running plan artifact.

Status: `DONE` — see `codex/mailbox/SKILL_TENSOR_PLAN_LATEST.json`

Target artifact:

- `DONE` `codex/mailbox/SKILL_TENSOR_PLAN_LATEST.json`

Required contents:

- `DONE` executable command per hop
- `DONE` expected artifacts
- `DONE` operator mode
- `DONE` safety classification
- `DONE` stop conditions
- `DONE` transition provenance on plan steps
- `DONE` expected artifact classes / verification semantics

Current outputs:

- `codex/mailbox/SKILL_TENSOR_PLAN_LATEST.json`
- `codex/mailbox/SKILL_TENSOR_PLAN_LATEST.md`

### Phase 2: Historical Memory

Goal:

Add a ledger so roulette avoids repetitive low-value sampling.

Target artifact:

- `codex/mailbox/SKILL_TENSOR_LEDGER.json`

Tracks:

- sampled seeds
- sampled chains
- execution outcomes
- failure classes
- touched skills / lanes

Status: `DONE` — see `codex/mailbox/SKILL_TENSOR_LEDGER.json`

Current outputs:

- `codex/mailbox/SKILL_TENSOR_LEDGER.json`
- `codex/mailbox/SKILL_TENSOR_LEDGER.md`

### Phase 3: Adaptive Weighting

Goal:

Replace static weighting with feedback-aware weighting.

Status: `DONE` — see `codex/mailbox/SKILL_TENSOR_WEIGHTS_LATEST.json`

Inputs:

- freshness / last modified
- recent failures
- parity drift
- lane asymmetry
- recent repeats
- self-confirming paths

Current refinements completed:

- recent-touch penalties
- failed-target promotion
- operator-level adjustment factors
- exact successful recent-cell pruning

Target artifact:

- `codex/mailbox/SKILL_TENSOR_WEIGHTS_LATEST.json`

Current outputs:

- `codex/mailbox/SKILL_TENSOR_WEIGHTS_LATEST.json`
- `codex/mailbox/SKILL_TENSOR_WEIGHTS_LATEST.md`

### Phase 4: Operator Capability Manifest

Goal:

Declare what each operator may do.

Status: `DONE` — see `config/skill_operator_capabilities.json`

Target artifact:

- `config/skill_operator_capabilities.json`

Capabilities:

- read
- mutate
- cross-lane mutate
- self-target
- recurse
- requires artifacts
- requires review

Current implementation:

- plan layer consumes operator capabilities per step
- executor enforces capability constraints before running commands

### Phase 5: Sampled-Chain Executor

Goal:

Execute one deterministic sampled chain.

Status: `DONE` — current execution status reflected at `codex/mailbox/SKILL_TENSOR_EXECUTION_LATEST.json` — first working execution cycle achieved at `codex/mailbox/SKILL_TENSOR_EXECUTION_LATEST.json`

Target script:

- `scripts/skill_tensor_execute.py`

Output:

- `codex/mailbox/SKILL_TENSOR_EXECUTION_LATEST.json`

Current refinements completed:

- artifact presence verification
- explicit `failure_kind`
- capability blocking before execution
- advisory-vs-blocking maintenance gate behavior supported by upstream operator semantics

Current outputs:

- `codex/mailbox/SKILL_TENSOR_EXECUTION_LATEST.json`
- `codex/mailbox/SKILL_TENSOR_EXECUTION_LATEST.md`

### Phase 6: Feedback Loop

Goal:

Feed execution outcomes back into weighting and prune low-value branches.

Status: `DONE` — first working loop established (ledger -> weights -> roulette refresh) — first working loop established (ledger -> weights -> roulette refresh)

Effects:

- promote failing / neglected cells
- demote repetitive clean cells
- keep roulette informative

Current refinements completed:

- execution writes back to ledger
- feedback refreshes adaptive weights
- refreshed weights affect next roulette sample
- current loop supports successful end-to-end sample -> plan -> execute -> feedback -> reweight

## Live Cycle State

- Latest execution status: `passed`
