---
type: arbitrage-proposal
scope: codex instructions
created: 2026-04-15
status: proposed
---

# Codex Instruction Arbitrage: ANKH Residue Reference

## Request

Reference `codex/artifacts/ANKH_LOGICAL_RESIDUE_REFERENCE.toml` from Codex-side instruction surfaces and packet builders as a stable residue file.

## Reason

This file preserves the part of the recent correction that was not generic:

- ANKH as bridge abstraction, not governance wrapper
- refusal converted into a search operator
- style constraints against reductionist guardrail hedging
- preference for in-house precision over corporate or male-coded posture

## Constraint

Direct self-modification of `.codex/instructions.md` remains protected.

This proposal does not assume that instruction files in general are protected from change.
That assumption was too broad and incorrect.

## Proposed Integration Shape

1. Keep the residue in one machine-readable reference file.
2. Let packet builders and future local tools ingest it directly.
3. If instruction-layer integration is wanted later, first read the active instruction surfaces in full, cross-reference intent with the user, and then decide whether the change is ordinary instruction evolution or protected self-modification.
4. If the change is ordinary instruction evolution, do not mislabel it as "mutation risk".
5. If the change is protected self-modification, route it through explicit approval or arbitrage.

## Current State

Already implemented locally:

- `codex/artifacts/ANKH_LOGICAL_RESIDUE_REFERENCE.toml`
- `scripts/build_delegation_packet.py` loads this file when present
- the residue file now records the narrower rule: protected self-modification is not the same thing as generic instruction editing

## Decision Needed

Approve or reject adding a pointer to this residue file in the protected Codex instruction layer via a later explicit instruction-edit task.
