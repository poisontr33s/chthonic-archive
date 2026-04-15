# Zombie Consumer — Project Home

> Cold-start orientation. Read this first if context is lost.
>
> For the full build history: [`UPGRADE_LOG.md`](UPGRADE_LOG.md)
> For the 4-tier convergence plan: [`CONVERGENCE_PLAN.md`](CONVERGENCE_PLAN.md)
> For the operational state snapshot: [`../../claude/mailbox/RESUME_ZOMBIE_EVOLUTION_20260327.md`](../../claude/mailbox/RESUME_ZOMBIE_EVOLUTION_20260327.md)

---

## What Is Zombie

The zombie consumer is an external anomaly operator that reads files from `dumpster-dive/` and produces structured intelligence about them. It is **not** part of the forge. It never writes to `corpse-vault/`. It never moves forge-stage files. It never reads SFS internal state.

Its output surfaces at the `dumpster-dive/intake/` boundary, where Sister Ferrum Scoriae's forge can read it. The zombie eats. The forge decides what to do with the meal.

**Pipeline:** `BITE → CHEW → DIGEST → EXCRETE`

| Stage | What happens |
|-------|-------------|
| `bite()` | Assess a file — ore rating, signals, import scan, dedup checks, ML inference |
| `chew()` | Extract intelligence — SIDs, shabti refs, imports, function defs, docstrings |
| `digest()` | Persist to memory — update profiles, graph, semantic index |
| `excrete()` | Write compact manifest to `dumpster-dive/intake/`, route to forge bridge |

---

## Current State (as of 2026-04-15)

**8 upgrades live.** All fire on every `bite()` in this order:

1. **Adaptive Bite Heuristics** — ore adjusted from cluster category history
2. **Import Graph Intelligence** — co-occurrence graph, content hash dedup, redundancy scoring
3. **Forge Feedback Loop** — forge outcomes backpropagated at 30% LR into cluster profiles
4. **Content + Semantic Dedup** — SHA-256 exact dedup, then cosine similarity at threshold 0.92
5. **Community Detection prior** — import community membership → ore nudge (+1/0/−1)
6. **GBT Ore Rating** — 7-feature `GradientBoostingClassifier`, 84.4% CV accuracy, fires last

**Plus A4 — Slag Upcycle Detector** (post-processing): `zombie upcycle` re-assesses all slag-routed files against current ML scores and surfaces candidates with ore delta ≥ 1.

| Metric | Value |
|--------|-------|
| Files consumed | 206 |
| ML model | GBT, 171 samples, 84.4% CV |
| Import graph | 8 nodes, 2 communities, Q=0.117 |
| Semantic index | 384-dim float32 (all-MiniLM-L6-v2) |
| Bridge | wired, 0 unrouted |

---

## Install & Run

```powershell
# Install (all groups in default-groups — no flags needed)
uv sync

# Assess a file
uv run scripts/zombie_consumer.py bite <path>

# Full pipeline — assess + extract + persist + route
uv run scripts/zombie_consumer.py feed <path>

# View all intelligence layers
uv run scripts/zombie_consumer.py memory

# Find semantic neighbors
uv run scripts/zombie_consumer.py similar <path> [--top 5] [--threshold 0.7]

# View import graph + community structure
uv run scripts/zombie_consumer.py graph --communities

# Retrain ML model (auto-skips if corpus <20% growth since last train)
uv run scripts/zombie_consumer.py train
uv run scripts/zombie_consumer.py train --force   # bypass growth guard

# Absorb forge feedback
uv run scripts/zombie_consumer.py learn

# View cluster profiles
uv run scripts/zombie_consumer.py profiles

# Hunger scan — find consumable candidates
uv run scripts/zombie_consumer.py hunger

# Slag upcycle detector — surface slag files whose ore has risen since routing (read-only)
uv run scripts/zombie_consumer.py upcycle
uv run scripts/zombie_consumer.py upcycle --json   # structured output
```

---

## Key Files

| File | Role | Move? |
|------|------|-------|
| `scripts/zombie_consumer.py` | Main CLI — all 7 upgrades | Never |
| `scripts/zombie_forge_bridge.py` | Ore → forge stage router | Never |
| `dumpster-dive/intake/.zombie_memory.json` | Persistent memory (brain) | Never |
| `dumpster-dive/intake/.zombie_ml_model.pkl` | GBT bundle (le_ext, le_cat, clf) | Never |
| `dumpster-dive/intake/.zombie_semantic_index.pkl` | Semantic embedding index | Never |
| `docs/zombie/UPGRADE_LOG.md` | Chronological build history | Here |
| `docs/zombie/CONVERGENCE_PLAN.md` | 4-tier plan to SFS synchronization | Here |
| `docs/DEPENDENCY_POLICY.md` | Repo-wide dependency rules | docs/ |
| `claude/mailbox/RESUME_ZOMBIE_EVOLUTION_20260327.md` | Operational state snapshot | mailbox |
| `memory/project_zombie_evolution.md` | Cross-session memory anchor | memory/ |

**Hard constraint:** `.zombie_*.pkl` and `.zombie_memory.json` paths are hardcoded. Do not move them.

---

## Architecture Invariants

```
Zombie (external anomaly)
    ↓  reads from
dumpster-dive/intake/          ← zombie writes compact manifests here
    ↓  forge bridge routes to
dumpster-dive/forge/<stage>/   ← SFS owns this territory
    ↓  zombie reads forge outcomes back via
zombie learn                   ← closes the feedback loop
```

**What zombie NEVER does:**
- Writes to `corpse-vault/`
- Moves or deletes forge-stage files
- Reads SFS internal state
- Talks to NOV-CAD directly (B1 provenance step is next, but will be one-way)

---

## Convergence Trajectory

The zombie evolves toward synchronized operation with SFS and NOV-CAD across 4 tiers:

- **Tier A** — zombie matures internally (A1–A4): A1 ✅ A2 ✅ A3 ✅ → **A4 next** (slag upcycle detector)
- **Tier B** — first contact with NOV-CAD at provenance boundary
- **Tier C** — intake oracle (`zombie intake-report` for SFS supply chain)
- **Tier D** — protocol convergence (interface contract + daemon mode)

Full plan: [`CONVERGENCE_PLAN.md`](CONVERGENCE_PLAN.md)

---

## Recovery Path (zombie apocalypse protocol)

Context fully lost? Start here, in order:

1. This file — reestablish what zombie is and its current state
2. [`UPGRADE_LOG.md`](UPGRADE_LOG.md) — how the code got to this state, step by step
3. [`CONVERGENCE_PLAN.md`](CONVERGENCE_PLAN.md) — what is complete, what is next
4. `claude/mailbox/RESUME_ZOMBIE_EVOLUTION_20260327.md` — operational details, exact next task
5. `memory/project_zombie_evolution.md` — cross-session memory (loaded by harness automatically)
6. `uv run scripts/zombie_consumer.py memory` — verify live state in the JSON brain

If the ML model is missing: `zombie train --force` rebuilds it from the compact manifests.
If the semantic index is empty: `zombie feed` on any file to re-seed it.
