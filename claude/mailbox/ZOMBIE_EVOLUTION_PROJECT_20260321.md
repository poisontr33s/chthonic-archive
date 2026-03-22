# Zombie Evolution Project — Iterative Intelligence Pipeline

> Lock-in document. Built from implementation results, not speculation.
> Date: 2026-03-21

## What Was Built

Three upgrades to [zombie_consumer.py](../../scripts/zombie_consumer.py) that make it learn iteratively — each meal changes how it approaches the next one. The architecture is stolen directly from the [Skill Tensor Cycle](../../scripts/skill_tensor_cycle.py)'s feedback chain (weights → roulette → ledger → feedback) but applied to file consumption instead of skill execution.

### Memory Schema: v1 → v2

The zombie's persistent memory at [.zombie_memory.json](../../dumpster-dive/intake/.zombie_memory.json) was forward-migrated from flat accumulation (schema v1) to adaptive intelligence (schema v2). Zero data loss — all 20 prior meals and their extraction logs preserved.

New fields added:

| Field | Purpose | Stolen From |
|---|---|---|
| `cluster_profiles` | Running stats per category — avg_ore, avg_extractable, yield_rate | Tensor `per_skill_weight_adjustments` |
| `import_graph` | Co-occurrence map with ore correlation per import | Tensor `pruned_action_keys` exclusion set |
| `content_hashes_seen` | Exact dedup registry | Tensor `pruned_exact_cells` |
| `forge_feedback` | Tempered/slag counts + prediction error log | Tensor `apply_feedback()` backprop |

---

## Upgrade 1: Adaptive Bite Heuristics

**Source pattern:** [skill_tensor_cycle.py:846-860](../../scripts/skill_tensor_cycle.py) — `per_skill_weight_adjustments`

**What it does:** After every `digest()`, the zombie updates a running profile for that file's category (backup, legacy, recovered, test, candidate). The profile tracks:

- `avg_ore` — mean ore rating across all files in that category
- `avg_extractable` — mean number of intelligence types extracted
- `yield_rate` — fraction of files that produced meaningful extraction

**How bite() uses it:** On the next `bite()`, the zombie consults cluster_profiles:

- If `yield_rate > 0.6` → auto-enable `--deep` extraction (don't wait for the caller to ask)
- If `avg_extractable < 0.3` and `count >= 5` → downgrade ore_rating by 1 (this category is consistently empty)
- If `count < 3` → fall back to static heuristics (not enough data to learn from)

**Activation threshold:** 3 samples per category. Below that, static ratings apply.

**CLI:** `uv run scripts/zombie_consumer.py profiles`

---

## Upgrade 2: Import Graph Intelligence

**Source pattern:** [skill_tensor_cycle.py:870-875](../../scripts/skill_tensor_cycle.py) — `pruned_action_keys` / `pruned_exact_cells`

**What it does:** Two mechanisms:

### 2a. Import Co-occurrence Graph

Every Python file's imports are tracked as a graph. Each node stores:
- `seen` — how many files imported this
- `ore_avg` — average ore rating of files that imported this
- `co_occurs` — which other imports always appear alongside this one

This builds a predictive model: "files importing `boto3` have ore_avg 1.5" means the zombie can pre-assess a file's likely value before deep scanning.

### 2b. Content Hash Dedup

Every consumed file's SHA-256 prefix is stored. On the next `bite()`, if the content hash matches a prior meal, the zombie flags `content_duplicate` and downgrades ore by 1. This prevents wasting extraction effort on identical copies (the `.bak` pattern — 10 nearly-identical backups of the same file).

### 2c. Redundancy Scoring

`_import_redundancy_score()` computes how many of a file's imports the zombie has already seen. Score ranges 0.0 (novel) to 1.0 (fully redundant). If redundancy > 0.8, ore is downgraded and `high_import_redundancy` signal is added.

**CLI:** `uv run scripts/zombie_consumer.py imports`

---

## Upgrade 3: Forge Feedback Loop

**Source pattern:** [skill_tensor_cycle.py:1679-1706](../../scripts/skill_tensor_cycle.py) — `apply_feedback()`

**What it does:** Closes the loop between zombie consumption and [Sister Ferrum Scoriae's Forge](../../dumpster-dive/DUMPSTER_DIVE_REGISTRY.json):

```
ZOMBIE feeds → dumpster-dive/intake/
                     ↓
        Sister Ferrum Scoriae processes
                     ↓
              forge outcome (TEMPERED / SLAG / ANVIL / ...)
                     ↓
        zombie learn ← reads forge state directories
                     ↓
        adjusts cluster_profiles.avg_ore
```

**Forge-to-ore mapping:**

| Forge State | Implied Ore | Meaning |
|---|---|---|
| tempered | 5 | High-value — successfully processed |
| quench | 4 | Validated, ready for use |
| furnace | 3 | In processing |
| anvil | 3 | Under analysis |
| intake | 2 | Waiting |
| slag | 1 | Low-value archival |

**Learning rate:** 30%. If a file predicted ore-2 reaches tempered (actual ore-5), the error is +3. The zombie adjusts that category's `avg_ore` by `+3 * 0.3 = +0.9`. Conservative enough to avoid overfit, aggressive enough to correct within 3-4 cycles.

**Prediction errors are logged** in `forge_feedback.ore_prediction_errors` with full audit trail: file, predicted, actual, forge state, error magnitude, category, timestamp.

**CLI:** `uv run scripts/zombie_consumer.py learn`

---

## Architecture: How the Three Upgrades Chain

```
                    ┌─────────────────────────────────┐
                    │     ZOMBIE MEMORY (schema v2)    │
                    │                                  │
                    │  cluster_profiles ←──── Upgrade 1│
                    │  import_graph    ←──── Upgrade 2 │
                    │  content_hashes  ←──── Upgrade 2 │
                    │  forge_feedback  ←──── Upgrade 3 │
                    └──────┬────────────────┬──────────┘
                           │                │
                    ┌──────▼──────┐  ┌──────▼──────┐
                    │   bite()    │  │  learn()    │
                    │             │  │             │
                    │ consults:   │  │ reads:      │
                    │ - profiles  │  │ - forge/    │
                    │ - graph     │  │ - extracts  │
                    │ - hashes    │  │             │
                    │             │  │ adjusts:    │
                    │ adapts:     │  │ - profiles  │
                    │ - ore_rating│  │ - feedback  │
                    │ - deep scan │  │             │
                    │ - redundancy│  │             │
                    └──────┬──────┘  └─────────────┘
                           │
                    ┌──────▼──────┐
                    │  digest()   │
                    │             │
                    │ updates:    │
                    │ - profiles  │
                    │ - graph     │
                    │ - hashes    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  excrete()  │
                    │             │
                    │ writes:     │
                    │ - receipt   │
                    │ - log entry │
                    └──────┬──────┘
                           │
                    ┌──────▼──────────────────┐
                    │  dumpster-dive/intake/   │
                    │         ↓                │
                    │  Sister Ferrum Scoriae   │
                    │  FORGE (7 states)        │
                    │         ↓                │
                    │  tempered / slag / ...   │
                    │         ↓                │
                    │  zombie learn ← reads    │
                    └─────────────────────────┘
```

---

## CLI Reference

| Command | Purpose | Source |
|---|---|---|
| `bite <path>` | Assess file — adapts ore from cluster history, flags dupes | Upgrade 1+2 |
| `feed <path>` | Full pipeline — builds profiles + graph per meal | Upgrade 1+2 |
| `profiles` | Rich table: cluster profiles with yield rate + auto-deep flag | Upgrade 1 + Wire 2 |
| `imports` | Rich table: import co-occurrence graph with ore correlation | Upgrade 2 + Wire 2 |
| `graph` | NetworkX centrality analysis — hub/connector/bridge/leaf roles | Wire 1 |
| `graph --dot F` | Export Graphviz DOT with ore-colored nodes + weighted edges | Wire 1 |
| `learn` | Read forge outcomes, backprop into ore predictions | Upgrade 3 |
| `memory` | Full Rich dashboard — all intelligence layers in one view | Wire 2 |
| `hunger` | Rich table of consumable candidates with adaptive ore ratings | Upgrade 1 + Wire 2 |

---

## Evolution Wiring (implemented)

### Wire 1: NetworkX Graph Engine

Dependencies: `networkx>=3.6` (already in pyproject.toml)

- `build_nx_graph(mem)` — converts the dict-based import_graph to a directed NetworkX graph
- `graph_centrality(G)` — computes degree + betweenness centrality, classifies nodes as hub/connector/bridge/leaf
- `export_dot(G)` — generates Graphviz DOT with ore-colored nodes (green=high, yellow=mid, red=low) and weighted edges
- Enables future: community detection, shortest path analysis, subgraph extraction at 50+ nodes

### Wire 2: Rich Terminal Rendering

Dependencies: `rich` (transitive, already available)

All CLI output upgraded from plain `print()` to Rich tables, panels, and color-coded ore bars:
- `_ore_bar()` — ASCII-safe `####-` bar with green/yellow/red coloring
- `_render_memory()` — full dashboard with stats panel, cluster signals, profiles, import graph, forge feedback, last meals
- `_render_profiles()` — table with auto-deep indicator column
- `_render_imports()` — table with co-occurrence counts
- `_render_graph()` — summary panel + centrality rankings with role classification
- `_render_learn()` — forge feedback panel + prediction error breakdown
- `_render_hunger()` — candidate table with ore bars
- `_render_bite()` — assessment panel with extractable type labels

All commands retain `--json` for machine-readable output.

---

## Current State

- **20 files consumed** (pre-upgrade) + synthetic seed data for profiles and graph
- **Schema v2 migrated** — backwards compatible, zero data loss
- **Forge scan operational** — 22 files across forge states, 0 matched (intake not yet processed by forge)
- **Graph engine live** — 8 nodes, 36 edges, 1 component, density 0.643
- **Cluster profiles seeded** — 3 categories with yield rates (backup=0%, candidate=100%, recovered=100%)
- **Rich rendering active** — all subcommands upgraded

## What Makes This Different From The Tensor

The tensor cycle operates on a **fixed combinatorial space** (N skills × 3 operators × 3 targets = 9N cells) and prunes by exclusion. The zombie operates on an **unbounded file space** and learns by *profile accumulation*. Both use the same feedback architecture:

| Tensor | Zombie |
|---|---|
| Ledger (bounded run history) | Consumption log + cluster profiles |
| Weights (penalty/bonus per skill) | Adaptive ore_rating per category |
| Pruning (exclude successful cells) | Content hash dedup + import redundancy |
| Feedback (execution → ledger stamp) | Forge outcome → ore prediction correction |

The tensor asks "what should I try next?" The zombie asks "is this worth eating?"

---

## Natural Evolution Path

```
NOW (n=20, seeded)       ~100 files              ~500+ files
──────────────────       ──────────              ───────────
rich tables         ->   polars frames      ->   polars + plotly dashboards
networkx graph      ->   community detect   ->   subgraph extraction
dict import_graph   ->   networkx native    ->   embedding similarity
manual ore rules    ->   decision tree      ->   gradient boosted classifier
synthetic profiles  ->   real meal data     ->   continuous backprop
```

### Next steps (hierarchical)

1. **Feed new files** to populate cluster_profiles and import_graph with real meal data
2. **Run `learn`** after the forge processes the 20 intake files — first real feedback cycle
3. **Bounded consumption log** — apply tensor's `max_runs` pattern to keep last N meals (currently unbounded)
4. **At ~100 files:** add `polars` aggregation (group-by category/month, trend analysis)
5. **At ~100 labeled forge outcomes:** train `DecisionTreeClassifier` on signals → ore_rating
6. **Cross-zombie dedup** — if multiple zombies run in parallel (triad velocity), share content_hashes_seen

### Polars integration point (ready, not yet needed)

`polars>=1` is already in pyproject.toml. When the consumption log hits ~100 entries:

```python
import polars as pl
df = pl.DataFrame(mem["consumption_log"])
df.group_by("batch").agg(pl.count(), pl.col("timestamp").min())
```

The memory schema stores exactly the columns polars needs. No structural changes required.

### Classifier integration point (needs labeled data)

Once `learn` produces 100+ prediction errors (zombie predicted X, forge said Y):

```python
from sklearn.tree import DecisionTreeClassifier
features = [size_lines, num_imports, has_sid, has_cli, has_main, category_encoded]
target = actual_forge_ore
```

The zombie's `bite()` already extracts all these features. The forge feedback loop already produces the labels. The training data accumulates automatically — no collection step needed.

---

*Stolen from the tensor. Grown by the zombie. Fed to the forge. Rendered by Rich. Graphed by NetworkX.*
