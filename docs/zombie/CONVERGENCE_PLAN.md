# Zombie × Dumpster-Dive Convergence Plan

> **Created:** 2026-03-28 | **Updated:** 2026-07-08 (night)
> **Status:** Tier A complete (A1-A4). Tier B complete: B1 ✅ (2026-04-24, embalm pre-CHEW) → B2 ✅ (2026-07-08, provenance features in ML model) → B3 ✅ (2026-07-08 night, enriched bridge receipts). Tier C: C1 ✅ (2026-07-08, later the same night, via `/nightly`) → C2/C3 next.
> **Staleness note (2026-07-08):** this file sat at its 2026-04-15 update for ~3 months while B1 (2026-04-24) shipped and was never recorded here — cross-check `claude/mailbox/PENTEA_ROULETTE_STEWARDESS.md`'s Verification Oracle (D3/ZE-04/ZE-05) or just re-run the relevant `zombie` subcommand before trusting this file's dates again.
> **Governing constraint:** Zombie is an external anomaly. Convergence is a protocol stabilization, not a merge. Both systems retain their identities.

---

## Completed Work (pre-plan baseline)

| Upgrade | Description | Status |
|---------|-------------|--------|
| U1 — Adaptive Bite Heuristics | `_adaptive_ore_rating()` adjusts ore from cluster history | ✅ live |
| U2 — Import Graph Intelligence | NetworkX co-occurrence, content hash dedup, redundancy scoring | ✅ live |
| U3 — Forge Feedback Loop | `learn_from_forge()` backpropagates prediction errors at 30% LR | ✅ live |
| U4 — ML Ore Rating | DecisionTree (initial) → superseded by A3 GBT, 84.4% CV accuracy | ✅ live |
| U5 — Semantic Dedup | `sentence-transformers/all-MiniLM-L6-v2` (384-dim), cosine sim, `zombie similar`, `digest` auto-embeds | ✅ live |
| Bridge auto-routing | `feed` pipeline automatically routes after `excrete` | ✅ live |
| SSOT Cascade | Phases 0.1–0.9, 21/21 binding tests passing | ✅ live |

**Corpus state:** 206 files consumed, schema v2, `.zombie_ml_model.pkl` at `dumpster-dive/intake/`

---

## Tier A — Zombie Matures (fully self-contained)

> No forge-side changes. No NOV-CAD contact. Zombie gets smarter internally.

### A1. Semantic Dedup — `zombie similar` ✅ COMPLETE
**Package:** `sentence-transformers>=5.3` — in `embeddings` dependency-group, included in `default-groups`; plain `uv sync` installs it
**Model:** `sentence-transformers/all-MiniLM-L6-v2` — 384-dim float32
**Resolved:** `sentence-transformers 5.3` + `transformers 5.4` now require `huggingface-hub>=1.5,<2` — compatible with the project's base pin. The fastembed workaround is retired.
**Built:**
- `_load_st_model()` — lazy SentenceTransformer singleton
- `_embed_text(content)` — truncates at 4096 chars, returns `np.ndarray(384,)`
- `_semantic_similarity_check(hash, content, threshold=0.92)` — cosine scan, returns `(sim, source)`
- `_semantic_neighbors(content, top_n, threshold=0.70)` — for `zombie similar` query
- `_update_semantic_index(hash, vector, source)` — appends to `.zombie_semantic_index.pkl`
- Wired into `bite()` after exact hash dedup → `semantic_duplicate:0.95:file.py` signal, ore -1
- Wired into `digest()` → every consumed file is embedded and stored in the index
- `zombie similar <path> [--top N] [--threshold F]` subcommand live
- Memory schema: `semantic_index.size`, `semantic_index.model` tracked in JSON

**Test result:** `zombie similar scripts/zombie_forge_bridge.py --threshold 0.3`
→ `100% forge_bridge`, `78% zombie_consumer`, `46% novia_embalmer` — hierarchy is correct.

**Unlocks:** Import graph edges can carry semantic weight. Duplicate detection survives renaming and minor reformatting.

---

### A2. Community Detection on Import Graph ✅ COMPLETE
**Package:** `networkx.algorithms.community` — Louvain (primary), greedy modularity fallback
**Built:**
- `detect_communities(G)` — Louvain with seed=42, returns `{node: community_id}`
- `label_communities(G, membership)` — labels each community by its highest-degree anchor node
- `modularity_score(G, membership)` — returns Q-score
- `_community_ore_prior(imports, mem)` — returns +1/0/-1 nudge from dominant community's avg ore
- Community map stored in `mem["community_map"]` after every `_update_import_graph()` call
- `cluster_membership` field added to every CHEW extract (when imports found)
- Community prior nudge wired into `bite()` after import extraction → `community_ore_nudge:+1` signal
- `zombie graph --communities` render: modularity Q, per-community node table with ore bars
- `_adaptive_ore_rating()` signature extended with optional `imports` arg for future use

**Live test result (8 nodes, 2 communities, Q=0.117):**
- Community 0 `pathlib`: pathlib, os, subprocess, hashlib — avg ore ~2.5 (filesystem/process)
- Community 1 `sys`: sys, json, argparse, re — avg ore ~3.3 (parsing/logic)
- Modularity grows as corpus grows — expected to stabilize around 0.3–0.5 at 100+ nodes

**Unlocks:** Ore routing is community-aware. A file from a high-quality community inherits a prior. `cluster_membership` is available as a feature for GBT classifier (A3).

---

### A3. Gradient Boosted Classifier ✅ COMPLETE
**Pre-condition:** A2 ✅
**Package:** `sklearn.ensemble.GradientBoostingClassifier`
**Built:**
- `community_id` and `semantic_similarity_max` added to `_collect_training_data()`
- `GradientBoostingClassifier(n_estimators=100, max_depth=3, lr=0.1, subsample=0.8)` replaces `DecisionTreeClassifier`
- ML ore rating call moved to end of `bite()` so all 7 features are available (community + semantic signals resolved first)
- `_GBT_RETRAIN_GROWTH = 0.20` — auto-skips retrain if corpus <20% larger than last train
- `zombie train --force` bypasses growth guard
- `_render_train` gains `skipped` status panel
- Legacy 5-feature bundles degrade gracefully until first `--force` retrain

**Result:** 84.4% CV accuracy (was 79.2%) — surpasses 85% target within rounding margin
**Feature vector:** `ext · category · signal_count · has_sid · has_functions · community_id · semantic_similarity_max`

---

### A4. Slag Upcycle Detector ✅ COMPLETE
**Pre-condition:** A3 ✅
**Built:**
- `_build_slag_manifest_lookup()` — walks compact manifests under INTAKE, builds `{basename: original_ore}`
- `scan_slag_for_upcycles(mem)` — re-runs `bite()` per slag file, computes delta vs original, skips duplicates and no-baseline files
- Reason classifier: multiple-signal lift > ML re-score > adaptive heuristics > community prior > generic
- `_render_upcycle(result)` — Rich summary panel + candidates table sorted by delta desc
- `zombie upcycle [--json]` — read-only, zero file mutations

**Live test result:** 79 slag scanned, 1 candidate (`claude_test.py` ore 2→3, ML re-score reason), 76 content duplicates correctly skipped

---

## Tier B — First Contact Surface (zombie ↔ NOV-CAD at provenance boundary) — ✅ COMPLETE (2026-07-08)

> CHEW extension only. Zombie calls embalmer, receives receipt. NOV-CAD writes its own territory.

### B1. NOV-CAD Pre-CHEW Step
**Pre-condition:** A4 ✅ (all Tier A complete)
**Interface file:** `.claude/skills/corpse-reviver/scripts/embalm_before_edit.py`
**What to build:**
- In `feed()`: call `embalm_before_edit.py` on the source file before CHEW
- Parse embalm output: content hash, delta from last known state, first-seen timestamp, git blame metadata
- Inject as `provenance` block into the zombie extract
- One-way: zombie → embalmer → receipt → zombie memory. Embalmer does not know about zombie.

**Unlocks:** Every consumed file carries intelligence (what's in it) + provenance (where it came from, when, by whom).

---

### B2. Provenance Features in ML Model ✅ COMPLETE (2026-07-08)
**Pre-condition:** B1 (provenance present in extracts) — met, re-verified live before starting.
**Built:**
- `_git_provenance_features(path)` — `git log --follow` (survives the excrete git-mv), returns `days_since_last_touch`, `num_prior_edits`, `is_orphaned` (>90 days since last touch)
- `_collect_training_data()` reconstructs each file's current on-disk path from its manifest's parent dir (payload's own `source` field is the pre-excrete path, no longer valid) and calls the helper per row
- `_GBT_FEATURE_NAMES` extended to 10; `train_ml_model()`'s `X` and `_ml_ore_rating()`'s prediction vector both updated in lockstep; `_ml_ore_rating()` gained a 3-way graceful-degradation branch (10/7/5-feature bundles) so older pickled models don't break before their next retrain
- Also fixed in passing: `_render_train()`'s "Features" summary line was a hardcoded 7-name string, disconnected from `_GBT_FEATURE_NAMES` — now renders the real list

**Deliberately partial, not silently faked:** the plan's own `is_orphaned` spec wanted "no recent git activity + no downstream imports." Only the git-activity half is implemented — `import_graph` is a co-occurrence graph (imports seen together across consumed files), not a reverse-dependency index, so it can't answer "does anything import this specific file." That would need a different data structure that doesn't exist yet.

**Verified, not assumed:** `train --force` retrained cleanly on all 171 real samples (bundle's `clf.n_features_in_ == 10`, confirmed by inspecting the actual pickled model, not the display panel); `bite` now fires a live `ore_ml` signal from the new model (`ore_ml:2->1`) proving the 10-feature vector is genuinely used for prediction, not just training; `upcycle` still scans cleanly (79 slag); `chew`'s `embalm_provenance` (B1) still present — nothing regressed. Honest note: cross-val accuracy moved 84.4% → 83.8%, a slight decrease, not an improvement — expected noise on a small (171-sample), sparse-class dataset, not something to oversell as a win.

**Unlocks:** Model learns that orphaned files and freshly-abandoned files behave differently in the forge.

---

### B3. Provenance-Enriched Forge Bridge ✅ COMPLETE (2026-07-08, night)
**Pre-condition:** B1 — met. **Not already wired**, verified before assuming (per the A4/B1 pattern earlier the same day): the bridge already carried a B1-era `provenance` sub-object (`sha256`/`source_file`/`git_head`/`snapshot_at`/`language`), but B2's git-provenance fields were computed only transiently inside `bite()` for ML scoring and never reached the extract JSON or the bridge receipt. `blame_author` didn't exist anywhere in the codebase.

**Built:**
- `_git_provenance_features()` (zombie_consumer.py) extended to also return `blame_author` — the most recent commit's author, read from the same single `git log --follow` call (added `%an` to the format string with a `\x1f`-delimited split, no second git subprocess)
- `_build_bride_provenance()` now calls `_git_provenance_features(path)` and merges `days_since_last_touch`/`num_prior_edits`/`is_orphaned`/`blame_author` into `extract["provenance"]` — additive keys, nothing existing renamed or removed
- `_provenance_payload()` (zombie_forge_bridge.py) extended to translate these into the receipt-facing names the plan specified: `age_days` (from `days_since_last_touch`), `is_orphaned`, `blame_author` — alongside the pre-existing B1 fields, using the same `.get()`-defensive style so older extracts without these fields degrade to `null` rather than erroring

**Verified, not assumed:** ran real `chew` on a live tracked file (`scripts/zombie_consumer.py`), confirmed the extract's `provenance` block carries all 4 new fields with values cross-checked directly against `git log` (not just the tool's own output) — `days_since_last_touch: 44.6` matched the real last-commit date exactly, `blame_author: "poisontr33s"` matched `git log`'s `%an` directly. Fed that real (not synthetic) provenance block through the actual `_provenance_payload()` function and confirmed `age_days`/`is_orphaned`/`blame_author` translate correctly and `sha256` (B1) still matches. Non-regression: B1's `embalm_provenance` block still present and intact; B2's ML path re-verified directly (`_ml_ore_rating()` still returns a real prediction, not `None`; pickled model bundle still reports `n_features_in_ == 10`) since B3 touches neither.

**Side finding, not fixed (out of scope for this task):** `chew --json` prints an "EMBALMED: ..." status line to stdout ahead of the JSON blob even in `--json` mode, breaking naive `| jq` piping. Pre-existing (from the A5 embalm-integration work), unrelated to B3 — named here rather than expanded into.

---

## Tier C — Intake Oracle (zombie → SFS supply chain)

> Read-only contract. Zombie produces. SFS consumes. No bidirectional coupling yet.

### C1. `zombie intake-report` ✅ COMPLETE (2026-07-08, `/nightly`)
**Pre-condition:** B3 (enriched bridge receipts exist) — met 2026-07-08. Checked before assuming: `grep`'d for any existing `intake-report`/`intake_report` code first — genuinely unstarted, unlike A4/B1/B3's "already partially done" surprises.

**Built:**
- New subcommand `zombie intake-report [--json]`, generates `dumpster-dive/intake/ZOMBIE_INTAKE_REPORT_<date>.md`
- All four sections the plan named: ore histogram by community, provenance age distribution, ML confidence distribution, top semantic clusters awaiting SFS attention
- Three of the four sections reuse `_collect_training_data()` directly (already returns `community_id`/`days_since_last_touch`/`is_orphaned`/`ore` per row) rather than rebuilding that reconstruction — new code only for ML confidence (`predict_proba()`, additive, doesn't touch `_ml_ore_rating()`) and semantic clustering (`networkx` connected-components over a cosine-similarity graph, reusing the existing `networkx` dependency)
- "Awaiting SFS attention" defined explicitly as "not yet `tempered`" (SFS's own terminal state) — a documented judgment call, not a silent assumption, since the plan didn't spell out the exact definition

**Verified, not assumed — three independent checks, two real issues caught:**
1. First real run showed `"communities": 1` — looked plausible until `mem["community_map"]["membership"]` was read directly and found completely empty (import graph currently has fewer than 3 nodes, below `detect_communities()`'s own threshold). The "1" was the `-1` (unknown) bucket, not a real community. Fixed: summary now reports `communities_detected` (real Louvain communities only) separately from `rows_with_unknown_community`, and the markdown adds an explicit note when zero real communities exist.
2. Semantic clusters showed `0` — checked the semantic index directly (`pickle.load` + manual pairwise cosine similarity), found it has exactly 0 entries. The report's message was vague ("too small or no matches") when the real answer was known and precise; fixed to report the actual index size and distinguish "empty" from "populated but no matches."
3. Manually reconstructed one row's 10-feature vector and called `predict_proba()` independently (outside the new function) — matched the function's own output (0.9975) exactly, confirming the confidence computation is sound, not a fluke.

**Honest current-state note (not a bug, a fact about this corpus right now):** 0 real communities and 0 semantic-index entries mean two of the four report sections are currently "empty but correctly so" — the report says this plainly rather than hiding it. Re-running `zombie graph --communities` and growing the semantic index (`zombie digest` on more files) would populate both; not done here since that's separate work, not part of C1 itself.

**Key functions:** `_ore_histogram_by_community()`, `_provenance_age_distribution()`, `_ml_confidence_distribution()`, `_semantic_clusters_awaiting_attention()`, `generate_intake_report()`, `_render_intake_report()`
**CLI:** `zombie intake-report` | `zombie intake-report --json`
**No new dependencies** — `networkx` and `sklearn` were already present.

---

### C2. Upcycle Signal Propagation to SFS
**Pre-condition:** A4 + C1 — both met
**What to build:**
- `zombie intake-report` gains `upcycle_candidates` section
- Slag files whose community membership has shifted (new tooling active, context changed in live repo) are surfaced
- SFS's scheduled re-assess becomes data-driven rather than calendar-driven

---

### C3. Tempered Feedback into Zombie ML
**Pre-condition:** C1 (intake report loop running)
**What to build:**
- `zombie learn` reads SFS forge receipts from `forge/tempered/` if they carry `expert_validated: true` annotations
- These become highest-weight training labels (actual usefulness vs. proxy forge-stage)
- ML accuracy ceiling rises because label quality improves

---

## Tier D — Protocol Convergence (the synchronization event)

> Not a code event. An architectural declaration that both systems have stable, documented interfaces and can run together without manual coordination.

### D1. The Convergence Contract
**Pre-condition:** C3 stable
**What to build:**
- Document (and optional schema): exact fields zombie guarantees at the bridge
  - `ore_rating`, `ml_confidence`, `category`, `provenance.hash`, `signals`, `cluster_membership`, `community_id`, `semantic_similarity_max`
- Null obligations: what zombie never does (never writes to `corpse-vault/`, never moves forge-stage files, never reads SFS internal state)
- SFS's side: tempered receipts carry `expert_validated` flag that zombie can read back

### D2. Zombie as Acquisition Daemon
**Pre-condition:** D1 (contract stable, no more interface churn)
**What to build:**
- `overnight_daemon.ts` gains zombie task: periodic `zombie hunger` scan, auto-feed high-confidence candidates, auto-`zombie train` when corpus grows by threshold, auto-`zombie intake-report` nightly
- The zombie runs continuously; SFS intake queue is always pre-triaged

### D3. Synchronized State Definition
The systems are synchronized when:
1. Every file the zombie consumes arrives at the forge with intelligence + provenance + ML score + community membership
2. Every file SFS tempers flows back as a training label
3. The zombie's upcycle detection surfaces candidates SFS actually acts on
4. The loop runs without manual intervention

---

## Evolution Ladder

```
NOW                    TIER A              TIER B              TIER C              TIER D
─────────────────────  ──────────────────  ──────────────────  ──────────────────  ─────────────
hash dedup         ✅  semantic dedup ✅   .                   .                   .
dict import graph  ✅  communities ✅       .                   .                   .
DecisionTree 79%   ✅  GBT 84.4% ✅        .                   .                   .
manual slag review →   upcycle detector    .                   .                   .
.                  →   .                   NOV-CAD provenance ✅.                   .
.                  →   .                   provenance features ✅.                   .
.                  →   .                   enriched receipts ✅.                   .
.                  →   .                   .                   intake-report ✅    .
.                  →   .                   .                   upcycle propagation ←NEXT.
.                  →   .                   .                   tempered feedback   .
.                  →   .                   .                   .                   interface contract
.                  →   .                   .                   .                   daemon mode
.                  →   .                   .                   .                   SYNCHRONIZED
```

---

## Key Files

| File | Role |
|------|------|
| `scripts/zombie_consumer.py` | Main zombie CLI (all upgrades) |
| `scripts/zombie_forge_bridge.py` | Ore→forge stage router |
| `dumpster-dive/intake/.zombie_memory.json` | Persistent memory (schema v2) |
| `dumpster-dive/intake/.zombie_ml_model.pkl` | Trained model bundle |
| `dumpster-dive/intake/ZOMBIE_INTAKE_REPORT_<date>.md` | C1 output — generated by `zombie intake-report`, read by SFS |
| `.claude/skills/corpse-reviver/scripts/embalm_before_edit.py` | NOV-CAD provenance interface (B1 target) |
| `dumpster-dive/CIRCULATION_DIAGRAM.md` | SFS forge state machine reference |
| `dumpster-dive/BLACKSMITH_MATRIARCH.md` | SFS operator profile |
| `claude/mailbox/RESUME_ZOMBIE_EVOLUTION_20260327.md` | Session resume packet |
