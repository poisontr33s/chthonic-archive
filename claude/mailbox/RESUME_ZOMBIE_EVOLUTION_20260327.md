# Resume Packet: Zombie Evolution + Dumpster-Dive Cascade

> **Date:** 2026-03-28 | **From:** Claude session (A2 — community detection)
> **Pick ONE and execute it. Do not summarize, do not re-audit.**

---

## Current State (verified running 2026-03-28)

### Zombie Consumer (`scripts/zombie_consumer.py`)
- **206 files consumed**, schema v2, 4 cluster profiles active
- **Six upgrades implemented and live:**
  1. **Adaptive Bite Heuristics** — `_adaptive_ore_rating()` adjusts ore from cluster history
  2. **Import Graph Intelligence** — 8 nodes, 36 edges, content hash dedup, redundancy scoring
  3. **Forge Feedback Loop** — 38 prediction errors absorbed, 30% learning rate
  4. **ML Ore Rating** — `_ml_ore_rating()` via DecisionTree; **171 samples, 79.2% CV accuracy**, model at `dumpster-dive/intake/.zombie_ml_model.pkl`; activates in `bite()` after adaptive heuristics
  5. **Semantic Dedup** — `sentence-transformers/all-MiniLM-L6-v2` (384-dim float32); `zombie similar <path>`; cosine threshold 0.92 for dedup, 0.70 for neighbors; index at `dumpster-dive/intake/.zombie_semantic_index.pkl`; every `digest` auto-embeds
  6. **Community Detection** — Louvain on import graph; `detect_communities()`, `label_communities()`, `modularity_score()`; community ore prior nudge (+1/0/-1) in `bite()`; `cluster_membership` in CHEW extract; `zombie graph --communities`; `mem["community_map"]` updated after every graph mutation

### Semantic Index State
- Model: `sentence-transformers/all-MiniLM-L6-v2` via `SentenceTransformer.encode()` (float32)
- Install: `uv sync` (embeddings group is in `default-groups`; no flag needed)
- Index: `dumpster-dive/intake/.zombie_semantic_index.pkl`; `zombie memory` shows `Semantic embeddings` count
- `zombie similar <path> [--top N] [--threshold F]` live

### Community Detection State (A2 — live)
- Louvain (`louvain_communities(seed=42)`) with greedy_modularity fallback
- **Live test result (8 nodes, 2 communities, Q=0.117):**
  - Community 0 `pathlib`: pathlib, os, subprocess, hashlib — avg ore ~2.5
  - Community 1 `sys`: sys, json, argparse, re — avg ore ~3.3
- Modularity grows as corpus grows; expected ~0.3–0.5 at 100+ import nodes
- `mem["community_map"]` = `{membership, labels, modularity, n_communities}`
- `cluster_membership` field in every CHEW extract (when imports found)

### ML Model State
- Features: `ext`, `category`, `signal_count`, `has_sid`, `has_functions`
- Label: actual forge ore (tempered=5, quench=4, furnace/anvil=3, intake=2, slag=1)
- Source: all 177 matched forge outcomes × compact manifests (not just prediction errors)
- `zombie train` subcommand: re-trains and updates memory metadata
- Status in memory: `ml_model.n_samples=171`, `ml_model.accuracy=0.792`

### Forge Pipeline (dumpster-dive/forge/)
Bridge wired into `feed` pipeline — automatic routing fires after every `excrete`. `actionable_unrouted: 0`.

### SSOT Cascade (Phases 0.1-0.9 complete, 21/21 tests passing)

---

## Execution Menu (remaining evolution path)

### 1. GBT Classifier ← **NEXT** (A3)
Replace `DecisionTreeClassifier` in `train_ml_model()` with `GradientBoostingClassifier`.
- Add `community_id` and `semantic_similarity_max` to `_collect_training_data()`
- Auto-retrain when `n_samples` grows by 20%+ since last train
- `zombie train --force` to bypass threshold check
- Target: 85%+ CV accuracy (baseline: 79.2%)
- Pre-condition: A2 ✅

### 2. Novia Cadaveris × Zombie CHEW composition
Wire `embalm_before_edit.py` as a pre-CHEW step so every consumed file gets both intelligence AND provenance extraction before routing to forge. Canonical owners: SFS (Sister Ferrum Scoriae) and NOV-CAD (Novia Cadaveris) — touch only at intake/bridge/provenance surfaces.

### 3. Retrain ML on larger corpus
After more forge outcomes accumulate (currently 171/177 matched), re-run `zombie train` to refresh accuracy. The sklearn warning ("least populated class has only 1 member") means one ore class is underrepresented — feed more `quench`-rated files to balance classes.

### 4. SSOT filename refactor
`copilot-instructions.archive.md` → semantically accurate name. Deferred until structural ownership stabilized. Not a current task.

---

## Full Convergence Plan
`docs/ZOMBIE_CONVERGENCE_PLAN.md` — 4-tier plan from Tier A (zombie-internal) through Tier D (protocol convergence with SFS/NOV-CAD). A1 (semantic dedup) is the designated entry point.

## Key Files
| File | Purpose |
|------|---------|
| `scripts/zombie_consumer.py` | Main zombie CLI (1979 lines, all 4 upgrades) |
| `scripts/zombie_forge_bridge.py` | Ore→forge stage router (wired into feed) |
| `dumpster-dive/intake/.zombie_memory.json` | Persistent memory (schema v2, 206 files, ml_model metadata) |
| `dumpster-dive/intake/.zombie_ml_model.pkl` | Trained DecisionTree bundle (le_ext, le_cat, clf) |
| `.ankhrc` | SSOT navigation hub (47 paths) |
| `mas_mcp/logic/ssot_manifest.py` | Cascade register (28 entries) |
| `mas_mcp/tests/test_ssot_binding.py` | 21 cascade validation tests |

## Hardware Context
4090 24GB VRAM, i9-13900, 64GB RAM — unlocks GPU-accelerated clustering (cuml/RAPIDS), local LLM summarization (13B+ models), and sentence-transformers semantic dedup.

## Evolution Path (updated)
```
NOW (n=206)              NEXT                    500+ files
rich tables          ✅  polars frames       ->   polars + plotly dashboards
dict graph           ✅  networkx (done)     ->   networkx + community detection
manual rules         ✅  decision tree       ->   gradient boosted classifier
hash dedup               semantic embedding  ->   cosine sim + cluster index
no feedback          ✅  learn() (done)      ->   continuous backprop
```
