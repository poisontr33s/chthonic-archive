# Zombie Consumer — Upgrade Log

> Chronological build trail. Each entry records what was built, when, what session produced it,
> and what the verified state was at close. Reproducibility anchor — if context is lost, read
> this file first to reestablish where the code is and how it got there.
>
> Runtime: `scripts/zombie_consumer.py` | Bridge: `scripts/zombie_forge_bridge.py`
> Memory: `dumpster-dive/intake/.zombie_memory.json`

---

## Origin — Schema v1 → v2 (2026-03-21)

**Session:** Claude, 2026-03-21
**Corpus at start:** ~20 files consumed (Phase 0)
**Source pattern:** Architecture stolen from `skill_tensor_cycle.py` feedback chain (weights → roulette → ledger → feedback), applied to file consumption instead of skill execution.

**Memory migration: v1 → v2** — zero data loss. New fields added:

| Field | Purpose |
|-------|---------|
| `cluster_profiles` | Running stats per category — avg_ore, avg_extractable, yield_rate |
| `import_graph` | Co-occurrence map with ore correlation per import |
| `content_hashes_seen` | Exact dedup registry |
| `forge_feedback` | Tempered/slag counts + prediction error log |

---

## U1 — Adaptive Bite Heuristics (2026-03-21)

**What:** After every `digest()`, zombie updates a running profile per category (backup, legacy, recovered, test, candidate). Tracks `avg_ore`, `avg_extractable`, `yield_rate`. `bite()` consults these on the next assessment: auto-enables `--deep` if `yield_rate > 0.6`, downgrades ore if `avg_extractable < 0.3` and count ≥ 5.

**Activation threshold:** 3 samples per category.
**CLI:** `zombie profiles`
**Key function:** `_adaptive_ore_rating()`

---

## U2 — Import Graph Intelligence (2026-03-21)

**What:** Three mechanisms:
- **Import co-occurrence graph** — every Python import tracked as a node with `seen`, `ore_avg`, `co_occurs`. Predictive prior: "files importing boto3 avg ore 1.5."
- **Content hash dedup** — SHA-256 prefix stored per consumed file. Duplicates flagged, ore downgraded.
- **Redundancy scoring** — `_import_redundancy_score()`: 0.0 (novel) → 1.0 (fully redundant). Score > 0.8 → downgrade + signal.
- **NetworkX graph engine** — `build_nx_graph()`, `graph_centrality()`, `export_dot()` (Graphviz DOT with ore-colored nodes).

**CLI:** `zombie imports` | `zombie graph` | `zombie graph --dot <file>`

---

## U3 — Forge Feedback Loop (2026-03-21)

**What:** Closes the loop between zombie consumption and Sister Ferrum Scoriae's forge. `zombie learn` reads forge stage directories, maps stage → ore (tempered=5 … slag=1), backpropagates prediction errors at 30% learning rate into `cluster_profiles.avg_ore`. `avg_ore` clamped to 1.0–5.0 (bug fixed 2026-03-23: learning rate had overcorrected `candidate` to -5.33).

**Prediction errors logged** in `forge_feedback.ore_prediction_errors` with full audit trail.
**CLI:** `zombie learn`

---

## A5/A6 — Forge Bridge + Batch Feed (2026-03-23)

**Session:** Codex, delegated via `HANDOFF_SFS_QML_BRIDE_SYNC_20260323.md`

**A5 — Forge Bridge built** (`scripts/zombie_forge_bridge.py`):
- Ore → forge stage routing table: ore 5 → quench/anvil, 4 → anvil, 3 → furnace, 2 → slag, 1 → slag + upcycle tag
- Wired into `feed` pipeline — automatic routing fires after every `excrete`
- **49 files routed, 0 unrouted**

**A6 — Batch Feed:**
- 37 deprecated/legacy/bak files consumed
- **57 total files consumed** post-A6
- 38 prediction errors logged, cluster profiles corrected
- 4 cluster profiles active: recovered (3.03, auto-deep), legacy (1.36), backup (1.20), candidate (1.0)
- Forge stage populations at close: anvil=29, furnace=27, slag=8, tempered=24, quench=1

---

## U4 — ML Ore Rating / DecisionTree (2026-03-27)

**Session:** Claude, 2026-03-27
**Corpus at start:** 206 files consumed

**What:** `_ml_ore_rating()` via `sklearn.tree.DecisionTreeClassifier`. Sources ALL matched forge outcomes via `_scan_forge_outcomes()` × compact manifests (not just prediction errors — key fix). 171 training samples. 5-feature vector: `ext`, `category`, `signal_count`, `has_sid`, `has_functions`.

**Result:** 79.2% CV accuracy.
**CLI:** `zombie train`
**Artifact:** `dumpster-dive/intake/.zombie_ml_model.pkl`
**Key functions:** `_collect_training_data()`, `train_ml_model()`, `_ml_ore_rating()`

> Note: DecisionTree superseded by GBT in A3 below. This entry preserved as origin record.

---

## U5 — Semantic Dedup (2026-03-28)

**Session:** Claude, 2026-03-28

**What:** Embedding-based duplicate detection using `sentence-transformers/all-MiniLM-L6-v2` (384-dim float32). Cosine similarity threshold 0.92 for dedup, 0.70 for neighbors. Every `digest()` auto-embeds and stores in `.zombie_semantic_index.pkl`. `bite()` fires semantic check after exact hash dedup.

**Dependency resolution:** fastembed (initial workaround) retired. `sentence-transformers 5.3.0` + `transformers 5.4.0` + `huggingface-hub>=1.5` now compatible — cleanly locked via `dependency-groups.embeddings`. `uv sync` installs the full stack (embeddings is in `default-groups`).

**CLI:** `zombie similar <path> [--top N] [--threshold F]`
**Artifact:** `dumpster-dive/intake/.zombie_semantic_index.pkl`
**Key functions:** `_load_st_model()`, `_embed_text()`, `_semantic_similarity_check()`, `_semantic_neighbors()`, `_update_semantic_index()`

---

## A1 — Semantic Dedup stabilized as plan entry (2026-03-28)

This is U5 formalized as the entry point of the 4-tier convergence plan (`docs/zombie/CONVERGENCE_PLAN.md`). No new code — the plan retroactively named U5 as A1.

---

## A2 — Community Detection on Import Graph (2026-04-15)

**Session:** Claude, 2026-04-15

**What:** Louvain community detection (`nx.algorithms.community.louvain_communities(seed=42)`) on the import co-occurrence graph, with `greedy_modularity_communities` fallback. Community ore prior nudge (+1/0/-1) fired in `bite()` after imports are extracted. `cluster_membership` added to every CHEW extract. Community map stored and refreshed in `mem["community_map"]` after every graph mutation.

**Live test result:** 8 nodes, 2 communities, Q=0.117
- Community 0 `pathlib`: pathlib, os, subprocess, hashlib — avg ore ~2.5
- Community 1 `sys`: sys, json, argparse, re — avg ore ~3.3

**CLI:** `zombie graph --communities`
**Memory fields:** `community_map.{membership, labels, modularity, n_communities}`
**Key functions:** `detect_communities()`, `label_communities()`, `modularity_score()`, `_community_ore_prior()`

---

## A3 — Gradient Boosted Classifier (2026-04-15)

**Session:** Claude, 2026-04-15

**What:** `GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, subsample=0.8)` replaces `DecisionTreeClassifier`. Feature vector extended to 7: adds `community_id` (dominant import community, −1 if unknown) and `semantic_similarity_max` (highest cosine sim signal from BITE). ML ore rating call moved to end of `bite()` so all 7 features are resolved before inference.

**Auto-retrain guard:** `_GBT_RETRAIN_GROWTH = 0.20` — `zombie train` silently skips if corpus hasn't grown ≥20% since last train. `zombie train --force` bypasses. Legacy 5-feature bundles degrade gracefully until first `--force` retrain.

**Result:** 84.4% CV accuracy (was 79.2% DecisionTree).
**Feature vector:** `ext · category · signal_count · has_sid · has_functions · community_id · semantic_similarity_max`
**CLI:** `zombie train` | `zombie train --force`
**Artifact:** `dumpster-dive/intake/.zombie_ml_model.pkl` (GBT bundle: `le_ext`, `le_cat`, `clf`, `feature_names`)

---

## Current State (as of 2026-04-15)

| Metric | Value |
|--------|-------|
| Files consumed | 206 |
| Memory schema | v2 |
| Cluster profiles | 4 active |
| Import graph | 8 nodes, ~36 edges |
| Communities | 2, Q=0.117 |
| ML accuracy | 84.4% (GBT, 171 samples) |
| Semantic index | `.zombie_semantic_index.pkl` |
| Bridge routing | wired, 0 unrouted |
| Forge feedback | 38 prediction errors absorbed |

**Install:** `uv sync` (all groups in `default-groups`)
**Retrain:** `uv run scripts/zombie_consumer.py train --force`
**Feed a file:** `uv run scripts/zombie_consumer.py feed <path>`
**Find semantic neighbors:** `uv run scripts/zombie_consumer.py similar <path>`
**Graph communities:** `uv run scripts/zombie_consumer.py graph --communities`

---

## Recovery Checklist (zombie apocalypse protocol)

If context is fully lost and you need to re-establish:

1. Read this file (`docs/zombie/UPGRADE_LOG.md`) — understand the build history
2. Read `docs/zombie/README.md` — cold-start orientation and current command reference
3. Read `docs/zombie/CONVERGENCE_PLAN.md` — what is done, what is next
4. Read `memory/project_zombie_evolution.md` — cross-session memory (loaded by harness)
5. Read `claude/mailbox/RESUME_ZOMBIE_EVOLUTION_20260327.md` — operational state snapshot
6. Run `uv run scripts/zombie_consumer.py memory` — verify live memory state
7. Run `uv run scripts/zombie_consumer.py train` — check if retrain is needed (skipped = OK, insufficient = corpus shrank)

**Do not:** move `.zombie_*.pkl` or `.zombie_memory.json` — these are the zombie's brain. Paths are hardcoded to `dumpster-dive/intake/`.

**Do not:** `uv pip install` anything — fix `pyproject.toml` and `uv lock` instead.
