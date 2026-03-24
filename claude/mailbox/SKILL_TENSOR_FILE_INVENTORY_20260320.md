# Skill Tensor File Inventory

> Generated: 2026-03-20
> Updated: 2026-03-20 — ghost shims upcycled into diagnostic probes

---

## Layer 1: The Monolith (authority)

| File | Lines | Role |
|------|------:|------|
| [`scripts/skill_tensor_cycle.py`](../../scripts/skill_tensor_cycle.py) | 2,727 | Everything — 12 stages, CLI, all generation logic |

The monolith **generates** the tensor. Everything below **reads** it.

---

## Layer 2: The Probe Toolkit (upcycled from ghost shims)

Each former shim is now a standalone diagnostic that reads [`SKILL_TENSOR_CYCLE_LATEST.json`](../../codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json) and reports on its slice. Run any probe with `uv run scripts/skill_tensor_{name}.py`.

| File | Probe | What It Reports |
|------|-------|-----------------|
| [`scripts/skill_tensor_common.py`](../../scripts/skill_tensor_common.py) | Hub | Shared reader, `load_latest()`, status helpers — imported by all probes |
| [`scripts/skill_tensor_inventory.py`](../../scripts/skill_tensor_inventory.py) | Inventory | Skill count per lane, live parity gaps, filesystem vs last cycle delta |
| [`scripts/skill_tensor_pool.py`](../../scripts/skill_tensor_pool.py) | Pool | Pool size, legal/degraded/blocked, inclusion rate, universe breakdown |
| [`scripts/skill_tensor_roulette.py`](../../scripts/skill_tensor_roulette.py) | Roulette | Last sampled chain, diversity score, operator/target spread, collisions |
| [`scripts/skill_tensor_weights.py`](../../scripts/skill_tensor_weights.py) | Weights | Pruning stats, effective pool after history penalties |
| [`scripts/skill_tensor_execute.py`](../../scripts/skill_tensor_execute.py) | Execute | Last execution status, return code, failure details, freshness gate |
| [`scripts/skill_tensor_feedback.py`](../../scripts/skill_tensor_feedback.py) | Feedback | Ledger writeback health, capacity status, bootstrap state |
| [`scripts/skill_tensor_ledger.py`](../../scripts/skill_tensor_ledger.py) | Ledger | Run history (last 5), mode, capacity, reads actual ledger file |
| [`scripts/skill_tensor_plan.py`](../../scripts/skill_tensor_plan.py) | Plan | Planned chain detail — who runs what on whom, with mode |
| [`scripts/skill_tensor_render_spec.py`](../../scripts/skill_tensor_render_spec.py) | Render-Spec | Drift detection: spec markdown vs LATEST.json, phase status |

---

## Layer 3: Config

| File | Purpose |
|------|---------|
| [`config/skill_tensor_rules.json`](../../config/skill_tensor_rules.json) | Rules: flavors, roots, exclusions, transition rules, diversity minimums |
| [`config/skill_operator_capabilities.json`](../../config/skill_operator_capabilities.json) | 4 operator capability manifests (mode, mutate, cross-lane, recurse) |

---

## Layer 4: Output Artifacts (live state)

| File | Purpose |
|------|---------|
| [`codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json`](../../codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json) | Full cycle state dump — the single source the probes read |
| [`codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.md`](../../codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.md) | Human-readable cycle summary |
| [`docs/ops/SKILL_TENSOR_ROULETTE_SPEC.md`](../../docs/ops/SKILL_TENSOR_ROULETTE_SPEC.md) | Design spec (auto-regenerated from artifacts) |

---

## Layer 5: Matrix Files (codex/mailbox/)

The `skill_matrix_{A}_on_{B}.json` files (3×3 = 9) — the literal tensor cells per executor×target pair:

| File | Cell |
|------|------|
| [`skill_matrix_claude_on_claude.json`](../../codex/mailbox/skill_matrix_claude_on_claude.json) | Claude → Claude |
| [`skill_matrix_claude_on_codex.json`](../../codex/mailbox/skill_matrix_claude_on_codex.json) | Claude → Codex |
| [`skill_matrix_claude_on_gemini.json`](../../codex/mailbox/skill_matrix_claude_on_gemini.json) | Claude → Gemini |
| [`skill_matrix_codex_on_claude.json`](../../codex/mailbox/skill_matrix_codex_on_claude.json) | Codex → Claude |
| [`skill_matrix_codex_on_codex.json`](../../codex/mailbox/skill_matrix_codex_on_codex.json) | Codex → Codex |
| [`skill_matrix_codex_on_gemini.json`](../../codex/mailbox/skill_matrix_codex_on_gemini.json) | Codex → Gemini |
| [`skill_matrix_gemini_on_claude.json`](../../codex/mailbox/skill_matrix_gemini_on_claude.json) | Gemini → Claude |
| [`skill_matrix_gemini_on_codex.json`](../../codex/mailbox/skill_matrix_gemini_on_codex.json) | Gemini → Codex |
| [`skill_matrix_gemini_on_gemini.json`](../../codex/mailbox/skill_matrix_gemini_on_gemini.json) | Gemini → Gemini |

---

## Companion Anchors (separate from this inventory)

| File | Purpose |
|------|---------|
| [`claude/mailbox/SKILL_PARITY_STATE_20260320.md`](SKILL_PARITY_STATE_20260320.md) | Parity table + system explanation + equalization roadmap |

---

## Architecture Summary

```
skill_tensor_cycle.py  ──generates──►  LATEST.json  ◄──reads──  9 probes + common.py
         │                                  │
         │                                  ├──►  LATEST.md
         │                                  └──►  ROULETTE_SPEC.md
         │
         └──reads──►  config/*.json
                       skill_operator_capabilities.json
                       skill_tensor_rules.json
```

**Monolith writes. Probes read. Config configures. Artifacts persist. Anchors document.**
