# Session Overview — 2026-03-20/21

> Birds-eye: what was built, what exists now, what to do next

---

## What Was Built This Session

### 1. Skill Tensor Parity State

Inventoried all three agent skill directories and documented the gap.

| Agent | Skills | Shared Core |
|-------|-------:|:-----------:|
| Claude | 33 | 27 |
| Codex | 28 | 27 |
| Gemini | 28 | 27 |

**Gap:** 7 skills not shared. 6 Claude-only, 1 Gemini-only.

**File:** [`SKILL_PARITY_STATE_20260320.md`](SKILL_PARITY_STATE_20260320.md)

### 2. Skill Tensor File Inventory

Mapped all tensor-related files across 5 layers: monolith → probes → config → artifacts → matrix files.

**File:** [`SKILL_TENSOR_FILE_INVENTORY_20260320.md`](SKILL_TENSOR_FILE_INVENTORY_20260320.md)

### 3. Ghost Shim Upcycle

10 dead 8-line shim files converted into live diagnostic probes. Each reads [`SKILL_TENSOR_CYCLE_LATEST.json`](../../codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json) and reports on its specific stage.

| Probe | What It Reports |
|-------|-----------------|
| [`skill_tensor_common.py`](../../scripts/skill_tensor_common.py) | Hub — shared reader for all probes |
| [`skill_tensor_inventory.py`](../../scripts/skill_tensor_inventory.py) | Skill count per lane, live parity gaps |
| [`skill_tensor_pool.py`](../../scripts/skill_tensor_pool.py) | Pool size, legal/degraded/blocked |
| [`skill_tensor_roulette.py`](../../scripts/skill_tensor_roulette.py) | Last sampled chain, diversity score |
| [`skill_tensor_weights.py`](../../scripts/skill_tensor_weights.py) | Pruning stats, effective pool |
| [`skill_tensor_execute.py`](../../scripts/skill_tensor_execute.py) | Execution status, failure details |
| [`skill_tensor_feedback.py`](../../scripts/skill_tensor_feedback.py) | Feedback loop health, capacity |
| [`skill_tensor_ledger.py`](../../scripts/skill_tensor_ledger.py) | Run history, ledger state |
| [`skill_tensor_plan.py`](../../scripts/skill_tensor_plan.py) | Planned chain detail |
| [`skill_tensor_render_spec.py`](../../scripts/skill_tensor_render_spec.py) | Spec drift detection vs LATEST.json |

### 4. Zombie Consumer

New tool: [`zombie_consumer.py`](../../scripts/zombie_consumer.py) — feeds on dead codebase files, extracts intelligence (imports, SIDs, docstrings, patterns), routes remains to [`dumpster-dive/intake/`](../../dumpster-dive/intake/).

Grows a persistent memory at `dumpster-dive/intake/.zombie_memory.json`.

Current hunger scan: **20 candidates** ready to consume (10 backups, 6 root strays, 3 recovered, 1 legacy).

### 5. Link Audit Hardening

Two fixes to [`link_audit.py`](../../scripts/link_audit.py):

- **Directory link detection** — `[DIR]` status when target resolves to a directory without trailing `/`. Intentional directory references (trailing `/` or `/` in label) pass clean.
- **Path-disambiguated collision suppression** — Links with directory components in the target (`../../AGENT_COMMON.md`) no longer trigger false "unlabeled collision" warnings.

### 6. Scripts Restructure Plan

6-phase plan for reorganizing ~306 files in [`scripts/`](../../scripts/):

**File:** [`SCRIPTS_RESTRUCTURE_PLAN_20260320.md`](SCRIPTS_RESTRUCTURE_PLAN_20260320.md)

---

## Current Anchor Documents

| File | Purpose | Links |
|------|---------|------:|
| [`SKILL_PARITY_STATE_20260320.md`](SKILL_PARITY_STATE_20260320.md) | Tensor system explanation + parity table | 1 |
| [`SKILL_TENSOR_FILE_INVENTORY_20260320.md`](SKILL_TENSOR_FILE_INVENTORY_20260320.md) | 5-layer tensor file map | 25 |
| [`SCRIPTS_RESTRUCTURE_PLAN_20260320.md`](SCRIPTS_RESTRUCTURE_PLAN_20260320.md) | 6-phase restructure plan | 13 |
| This file | Session overview + next steps | — |

All links audited clean via `uv run scripts/link_audit.py check`.

---

## What To Do Next (High-Level) changes are required for steps 3-6. Each depends on the previous, so skip none.

1. **Feed the Zombie** — 20 dead files, zero risk, clears noise
2. **Freeze Baseline** — snapshot link/collision state before restructure
3. **Skill Parity** — equalize 27→34 shared skills across all three agents
4. **Directory Structure** — move clusters one commit at a time
5. **Tensor Execution** — re-run the cycle once the pool is clean

*Reference:* `uv run` — [scripts/link_audit.py](../../scripts/link_audit.py) — *Checks to validate links in all docs after edits.* `uv run` — **scripts/skill_tensor_*.py** — *Per-stage diagnostics of tensor state.* `uv run` — **[scripts/skill_tensor_cycle.py](../../scripts/skill_tensor_cycle.py)** — *Full tensor generation + execution.* 
- *Checks to validate links in all docs after edits.*
Each step depends on the one before it. Skip none.

---

## What To Do Next (Hierarchical)

### Priority 1: Feed the Zombie (Phase 0)

The lowest-risk, highest-cleanup-value step. No code changes, no path breaks.

```
uv run scripts/zombie_consumer.py hunger          # see candidates
uv run scripts/zombie_consumer.py feed <path>     # consume one at a time
```

**20 files to consume:**
- 10 `.bak` backup corpses (ore rating 2-3)
- 6 root-level stray `.py` files (ore rating 2-3)
- 3 `recovered_*` salvage files (ore rating 3)
- 1 `wpth_repeatable_cycle_LEGACY` (ore rating 3)

After: collision index is cleaner, `scripts/` root is lighter.

### Priority 2: Freeze Reference Map (Phase 1)

```
uv run scripts/link_audit.py scan --json > claude/mailbox/LINK_AUDIT_BASELINE.json
uv run scripts/link_audit.py collisions --json > claude/mailbox/COLLISION_INDEX_BASELINE.json
```

This creates the "before" snapshot so restructure progress is measurable.

### Priority 3: Skill Parity Equalization

Promote missing skills across agents:

- **Codex needs 5:** git-snapshot, handoff-loop, overnight-archaeology, sfa, theme-system
- **Gemini needs 6:** above + link-path-guard
- **All three need:** triad-velocity-lane (currently Gemini-only)

After: tensor pool becomes a clean `N × 9` grid with zero legality holes.

### Priority 4: Scripts Directory Structure (Phase 2-3)

Define target layout, then move one cluster per commit:
1. `icons/` (8 files, standalone)
2. `poe/` (4 files, self-contained)
3. `decorator/` (4 files, internal)
4. ...through to `tensor/` (11 files, most connected — last)

### Priority 5: Tensor Cycle Execution

The cycle currently fails at the `execute` stage (rc=2, 3 critical freshness issues). Once parity is equalized and the pool is clean, re-run:

```
uv run scripts/skill_tensor_cycle.py cycle
```

---

## Tools Available Now

| Tool | Command | Purpose |
|------|---------|---------|
| Zombie | `uv run scripts/zombie_consumer.py` | Consume dead files with intelligence extraction |
| Link Audit | `uv run scripts/link_audit.py` | Validate/fix markdown links and backtick refs |
| Tensor Probes | `uv run scripts/skill_tensor_*.py` | Per-stage diagnostics of tensor state |
| Tensor Cycle | `uv run scripts/skill_tensor_cycle.py` | Full tensor generation + execution |
| Hunger Scan | `uv run scripts/zombie_consumer.py hunger` | Find consumable candidates |
| Parity Check | `uv run scripts/skill_tensor_inventory.py` | Live parity gap report |
