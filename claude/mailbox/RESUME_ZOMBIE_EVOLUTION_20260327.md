# Resume Packet: Zombie Evolution + Dumpster-Dive Cascade

> **Date:** 2026-03-27 | **From:** Claude session (SSOT cascade + zombie audit)
> **Pick ONE and execute it. Do not summarize, do not re-audit.**

---

## Current State (verified running 2026-03-27)

### Zombie Consumer (`scripts/zombie_consumer.py` — 1340 lines)
- **178 files consumed**, schema v2, 4 cluster profiles active
- **165 extract files** across intake + forge stages
- **Three upgrades implemented and live:**
  1. **Adaptive Bite Heuristics** — `_adaptive_ore_rating()` adjusts ore from cluster history. `candidate` learned avg_ore=1.0 (29 samples), `recovered` avg_ore=3.03 (yield_rate=1.0, auto-deep)
  2. **Import Graph Intelligence** — 8 nodes, 36 edges, content hash dedup, redundancy scoring. `pathlib`/`sys`/`json` are hubs (degree 0.857)
  3. **Forge Feedback Loop** — `learn_from_forge()` scanned 72 forge outcomes, matched 54, absorbed 38 prediction errors at 30% learning rate. 1 tempered, 8 slag in feedback memory

### Forge Pipeline (dumpster-dive/forge/)
| Stage | Files | Purpose |
|-------|-------|---------|
| intake | 3 | Waiting for routing |
| anvil | 58 | Under analysis |
| furnace | 75 | Heat refinement |
| quench | 1 | Validated |
| tempered | 33 | Successfully processed |
| slag | 15 | Low-value archival |

**Bridge:** `scripts/zombie_forge_bridge.py` routes ore_rating 5→quench, 4→anvil, 3→furnace, 2→slag, 1→slag+upcycle, superposition→tea-vault.

### SSOT Cascade (Phases 0.1-0.9 complete)
- 28 cascade register entries in `mas_mcp/logic/ssot_manifest.py`
- Bridges: Python + TypeScript + PowerShell + Extension (all wired, all consumers importing)
- `.ankhrc` at repo root (47 paths, TOML hub)
- 21/21 binding tests passing
- 12 root artifacts relocated to `dumpster-dive/intake/root-hygiene-0.7/`

---

## Execution Menu (next steps from the original evolution path)

### 1. Feed to 200 threshold — unlock polars aggregation
The zombie is at 178/200 consumed files. Run `zombie hunger` to find ~22 more candidates, feed them, then wire polars frame aggregation on the consumption_log. The design spec says:
- `polars` for instant group-by on consumption_log (already in pyproject.toml)
- Replace dict-based cluster_profiles with polars DataFrame for richer queries
- Add `zombie stats` subcommand with polars-powered analytics

### 2. Wire scikit-learn DecisionTree on signals→ore_rating
At 178 files with 38 forge prediction errors, there's enough data to train a basic classifier. The design spec:
- Features: file extension, size_lines, signal count, import_redundancy, category one-hot
- Target: forge_ore (from forge outcome, not predicted ore)
- Replace static heuristics with `_ml_ore_rating()` fallback when tree has >50 training samples
- Add `zombie train` subcommand

### 3. Forge pipeline gap — automate intake→ANVIL routing
Currently `zombie_forge_bridge.py route` must be run manually. Wire it into the `feed` pipeline so `zombie feed <path>` automatically routes the extract to the correct forge stage after excrete. This closes the zombie→forge automation gap identified in the SFS×QML handoff.

### 4. Semantic dedup via sentence-transformers (GPU path)
User has 4090 24GB VRAM + i9-13900 + 64GB RAM. At 200+ files:
- Embed file contents with `sentence-transformers` for near-duplicate detection
- Replace content_hash exact-match dedup with cosine similarity threshold
- Add `zombie similar <path>` subcommand showing semantic neighbors

### 5. Novia Cadaveris × Zombie CHEW composition
From the SFS×QML handoff findings: zombie extracts *intelligence* (imports, patterns, SIDs), embalmer extracts *provenance* (who wrote it, when, why). These compose — wire `embalm_before_edit.py` as a pre-CHEW step so every consumed file gets both intelligence AND provenance extraction before routing to forge.

---

## Key Files
| File | Purpose |
|------|---------|
| `scripts/zombie_consumer.py` | Main zombie CLI (1340 lines, all 3 upgrades) |
| `scripts/zombie_forge_bridge.py` | Ore→forge stage router |
| `dumpster-dive/intake/.zombie_memory.json` | Persistent memory (schema v2, 178 files) |
| `.ankhrc` | SSOT navigation hub (47 paths) |
| `mas_mcp/logic/ssot_manifest.py` | Cascade register (28 entries) |
| `mas_mcp/tests/test_ssot_binding.py` | 21 cascade validation tests |
| `docs/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md` | Blueprint (Phases 0.1-0.8 done) |
| `claude/mailbox/HANDOFF_SFS_QML_BRIDE_SYNC_20260323.md` | SFS×QML cross-system investigation |
| `codex/mailbox/SFS_QML_BRIDE_SYNC_FINDINGS_20260323.md` | Codex response to above |

## Hardware Context
4090 24GB VRAM, i9-13900, 64GB RAM — unlocks GPU-accelerated clustering (cuml/RAPIDS), local LLM summarization (13B+ models), and sentence-transformers semantic dedup.

## Evolution Path (from original design)
```
NOW (n=178)         200 files            500+ files
rich tables    ->   polars frames   ->   polars + plotly dashboards
dict graph     ->   networkx (done) ->   networkx + community detection
manual rules   ->   decision tree   ->   gradient boosted classifier
hash dedup     ->   hash (done)     ->   semantic embedding dedup
no feedback    ->   learn() (done)  ->   continuous backprop
```
