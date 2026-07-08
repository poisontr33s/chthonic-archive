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

## A4 — Slag Upcycle Detector (2026-04-15)

**Session:** Tessara/Copilot, 2026-04-15

**What:** `zombie upcycle` subcommand — scans all files in `forge/slag/`, re-runs `bite()` on each, compares current ML/adaptive ore score against original ore from compact manifests. Surfaces candidates where `delta >= 1`. Read-only — zero file mutations.

**Logic:**
- `_build_slag_manifest_lookup()` — walks `INTAKE.rglob(".zombie_compact_manifest.json")`, builds `{basename: original_ore}` from stored extracts
- `scan_slag_for_upcycles(mem)` — iterates slag files, skips exact duplicates (`content_duplicate` signal), skips files with no baseline, calls `bite()` per file, fires delta check
- Reason classification (deterministic priority): multiple-signal lift > ML re-score > adaptive heuristics > community prior > generic
- `_render_upcycle(result)` — Rich panel summary + sortable candidates table (`Ore Now · Orig · Delta · Name · Category · Reason`)
- CLI: `zombie upcycle [--json]`

**Live test result (2026-04-15):**
- Slag files scanned: 79
- Upcycle candidates: 1 (`claude_test.py` — ore 2 → 3, delta +1, reason: ML model re-scores ore higher than original slag routing)
- No baseline (skipped): 1
- Content duplicates (skipped): 76

**Key functions:** `_build_slag_manifest_lookup()`, `scan_slag_for_upcycles()`, `_render_upcycle()`
**CLI:** `zombie upcycle` | `zombie upcycle --json`
**No new dependencies** — reuses existing `bite()`, ML bundle, Rich.

---

## B1/"ZE-05" — NOV-CAD Pre-CHEW Embalm Wiring (2026-04-24)

**Added retroactively 2026-07-08** — this upgrade shipped and was verified 2026-04-24 (`61574546`, "feat(zombie): A5 NOV-CAD pre-CHEW embalm wiring — ZE-05") but was never recorded in this file, only in the git commit message and `claude/mailbox/PENTEA_ROULETTE_STEWARDESS.md`'s Domain Queue Tables. That gap is why this file, `CONVERGENCE_PLAN.md`, and `memory/project_zombie_evolution.md` all independently drifted into claiming Tier B1 was still "next" as late as 2026-07-08, three months after it actually shipped.

**What:** `chew()` now snapshots a file via `embalm_before_edit.py` (the corpse-reviver skill) before extracting intelligence, and stores the result in `extract["embalm_provenance"]`.

**Built:**
- `_load_embalm_module()` — dynamic import from `.codex/skills/corpse-reviver/scripts/embalm_before_edit.py`
- `_embalm_pre_chew(path)` — snapshots before `bite()`, graceful fallback to `{}` on any failure so a broken embalm never blocks `chew()`
- `chew()` calls `_embalm_pre_chew()` first, stores the result in `extract["embalm_provenance"]`

**Live test result (2026-04-24):** `zombie chew slag/claude_test.py --json` → embalmed to `python/7feeab51c64ff52a_claude_test.py.snapshot` (27L, 712B), session `2026-04-24T02-25-48Z_zombie_chew` created, `embalm_provenance` key present in JSON output.

**Re-verified live, 2026-07-08 (2.5 months later, unmaintained):** ran `zombie chew` fresh — still produces a real `embalm_provenance` block (`hash`, `source_file`, `language`, `byte_size`, `line_count`, `snapshot_at`, `head_commit`, `git_status`, `landmarks`, `snapshot_path`) via a genuinely new, today-timestamped session dir. Still works.

**No new dependencies** — corpse-reviver skill already existed.

---

## B2 — Provenance Features in ML Model (2026-07-08)

**Session:** Claude, 2026-07-08

**What:** the GBT classifier now trains on 3 additional git-derived features, not just structural/semantic signals.

**Built:**
- `_git_provenance_features(path)` — `git log --follow --format=%at` per file (`--follow` survives the `excrete()` git-mv into `dumpster-dive/intake/`); returns `days_since_last_touch`, `num_prior_edits`, `is_orphaned` (>90 days since last touch, no git history at all defaults to maximally-orphaned rather than raising)
- `_collect_training_data()` reconstructs each file's real current on-disk path as `manifest_path.parent / Path(payload["source"]).name` — the payload's own `source` field is the pre-`excrete` path and no longer points at a real file — then calls the helper per training row
- `_GBT_FEATURE_NAMES` extended from 7 to 10; `train_ml_model()`'s `X` and `_ml_ore_rating()`'s prediction-time vector updated in lockstep; `_ml_ore_rating()` gained a third degradation branch (10 / 7 / 5-feature bundles) so an un-retrained pickle from before this change keeps predicting correctly instead of erroring
- Also fixed in passing: `_render_train()`'s "Features" summary line was a hardcoded 7-name string that had already gone stale once (didn't reflect the 7-feature A3 upgrade's real names either) — now renders `_GBT_FEATURE_NAMES` directly so it can't drift again

**Deliberately partial — named, not hidden:** the plan's original B2 spec wanted `is_orphaned` to mean "no recent git activity + no downstream imports." Only the git-activity half is built. `import_graph` (`mem["import_graph"]`) is a co-occurrence graph — which import names tend to appear together across consumed files — not a reverse-dependency index, so it cannot answer "does anything else import this specific file." That would need a different data structure that doesn't exist yet in this codebase.

**Live test result (2026-07-08):** `zombie train --force` retrained on all 171 real samples. Verified against the actual pickled bundle, not just the display panel: `clf.n_features_in_ == 10`, `feature_names` list matches exactly. `zombie bite` on a real slag file now fires a live `ore_ml:2->1` signal, proving the 10-feature vector is genuinely used for prediction, not just training. `zombie upcycle` still scans cleanly (79 slag). `zombie chew`'s `embalm_provenance` (B1, above) still present — nothing regressed.

**Honest result, not oversold:** cross-val accuracy moved 84.4% → 83.8% — a slight decrease. Expected noise on a small (171-sample), sparse-class dataset (sklearn's own CV warning: "least populated class has only 1 member"), not evidence the new features are wrong, but not a win to claim either.

**Key functions:** `_git_provenance_features()`, updated `_collect_training_data()`, `train_ml_model()`, `_ml_ore_rating()`, `_render_train()`
**CLI:** `zombie train --force` (retrain on enriched corpus); `zombie bite`/`zombie chew` (prediction path, unchanged interface)
**No new dependencies** — `subprocess` and `datetime` were already imported.

---

## B3 — Provenance-Enriched Forge Bridge (2026-07-08, night)

**Session:** Claude, `/nightly` autonomous continuation, 2026-07-08 (user asleep)

**What:** the forge bridge receipt JSON (`scripts/zombie_forge_bridge.py`) now carries B2's git-provenance signal plus a new `blame_author` field — available for SFS to optionally read at anvil/furnace, no schema requirement on the forge side.

**Not already wired — verified before assuming, per the A4/B1 pattern from earlier the same day:** the bridge already had a `provenance` sub-object in its receipts (B1-era: `sha256`/`source_file`/`git_head`/`snapshot_at`/`language`, via `_extract_provenance()`/`_provenance_payload()`), but B2's three git-derived fields were computed only inside `bite()` for ML scoring and discarded afterward — never written into the extract JSON, so the bridge had nothing to read. `blame_author` existed nowhere in either script.

**Built:**
- `_git_provenance_features()` extended to also return `blame_author` (the most recent commit's author) — read from the *same* `git log --follow` subprocess call already in place for the other three fields, by widening the format string to `%at\x1f%an` and splitting on the delimiter; no second git invocation added
- `_build_bride_provenance()` (builds `extract["provenance"]`, the dict the bridge reads) now calls `_git_provenance_features(path)` and merges `days_since_last_touch`/`num_prior_edits`/`is_orphaned`/`blame_author` in — purely additive, no existing key touched
- `_provenance_payload()` (in `zombie_forge_bridge.py`) extended to translate these into the plan's named receipt fields — `age_days` (from `days_since_last_touch`), `is_orphaned`, `blame_author` — using the same defensive `.get()` style as the existing B1 fields, so a receipt built from an older, pre-B3 extract just gets `null` for the new keys rather than erroring

**Deliberately minimal, no second subprocess in the hot ML path:** `bite()` (called by `chew()` internally) still computes its own `_git_provenance_features()` call for ML scoring, unchanged; `_build_bride_provenance()` calls it again independently rather than threading a value through `bite()`'s return dict — a small redundant `git log` per `chew()` (not per `bite()` alone), traded for keeping both functions fully self-contained and `bite()`'s already-shipped B2 body untouched.

**Verified, not assumed:** ran real `zombie chew scripts/zombie_consumer.py --json` and confirmed the extract's `provenance` block carries all 4 new fields — cross-checked directly against raw `git log` output (not the tool's own claim): `days_since_last_touch: 44.6` matched the file's actual last-commit date (2026-05-24, a `patch_utf8` fix) exactly, `blame_author: "poisontr33s"` matched `git log --format=%an` directly. Fed that real provenance block through the actual `_provenance_payload()` function (dynamic import, no filesystem mutation) and confirmed `age_days`/`is_orphaned`/`blame_author` translate correctly and `sha256` (B1) is unchanged. Non-regression, both re-checked directly rather than assumed: B1's `embalm_provenance` block still present and intact in the same extract; B2's ML path still returns a real prediction (not `None`) from `_ml_ore_rating()`, and the pickled bundle still reports `n_features_in_ == 10` — B3 touches neither code path.

**Side finding, named not fixed (out of scope for this task):** `zombie chew --json` prints an "EMBALMED: ..." status line (and a "Session manifest: ..." line) to stdout ahead of the JSON blob, even in `--json` mode — breaks naive `| jq` piping on the raw output. Pre-existing, from the A5 embalm-integration work (B1, above), unrelated to B3. Worth a follow-up: route that print through the same `--json` conditional the rest of the CLI already uses.

**Also surfaced, not acted on:** while verifying git history for this file, found the entire session's accumulated work (TAA fix, camera input, README, `ci/checks/glsl-lint.ts`, `NEW_PROVIDENCE` coordinate consolidation, corpse-reviver's UTF-8 patch, this B2/B3 zombie work, and more) is sitting uncommitted in the working tree — the last real commit to `scripts/zombie_consumer.py` predates all of it (2026-05-24). This nightly's own commit (below) is scoped to only the zombie B2+B3 files; the rest is named in the landing doc for the user's own call, not committed autonomously.

**Key functions:** `_git_provenance_features()` (extended), `_build_bride_provenance()` (extended), `_provenance_payload()` (extended, in `zombie_forge_bridge.py`)
**CLI:** no new subcommand — `zombie chew`/`zombie feed` (extract provenance, unchanged interface) and `zombie_forge_bridge.py route` (receipt provenance, unchanged interface) both just carry more data now
**No new dependencies.**

---

## C1 — Zombie Intake Report (2026-07-08, later the same night)

**Session:** Claude, `/nightly` (second invocation of the same night — first was B3), user genuinely asleep for the first time this skill ran fully unattended.

**What:** new `zombie intake-report [--json]` subcommand generates `dumpster-dive/intake/ZOMBIE_INTAKE_REPORT_<date>.md` — the four sections the plan named: ore histogram by community, provenance age distribution, ML confidence distribution, top semantic clusters awaiting SFS attention.

**Built:**
- `_ore_histogram_by_community()`, `_provenance_age_distribution()` — both pure aggregation over `_collect_training_data()`'s existing rows, no new data collection
- `_ml_confidence_distribution()` — new, additive: reconstructs the same 10-feature vector `_ml_ore_rating()` builds, calls `predict_proba()` instead of `predict()`, buckets the max class probability. Does not touch `_ml_ore_rating()`. Only supports the current 10-feature bundle shape — reports unavailable with a clear reason for older 7/5-feature bundles rather than replicating the full 3-way degradation, a deliberate scope limit
- `_semantic_clusters_awaiting_attention()` — new: connected-components over a cosine-similarity graph built with `networkx` (already a dependency), threshold 0.75 (tighter than `zombie similar`'s 0.70 default). "Awaiting attention" defined as "at least one member not yet `tempered`" — a documented judgment call, since the plan didn't specify the exact definition
- `generate_intake_report()` orchestrates all four, writes the markdown file; `_render_intake_report()` is the Rich console summary

**Verified, not assumed — real run, three independent checks, two real issues caught and fixed before calling this done:**
1. First run's JSON summary said `"communities": 1` — read `mem["community_map"]["membership"]` directly (bypassing the new code entirely) and found it completely empty: the import graph currently has fewer than 3 nodes, below `detect_communities()`'s own threshold. The "1" was the `-1`/unknown bucket, not a real community — a misleading top-line number even though the markdown table itself was already honestly labeled. Fixed: summary now reports `communities_detected` (real Louvain communities only, currently 0) separately from `rows_with_unknown_community` (171), and the markdown adds an explicit sentence when zero real communities exist.
2. Semantic clusters showed `0` — independently unpickled `.zombie_semantic_index.pkl` and computed every pairwise cosine similarity by hand; the index has exactly 0 entries, so `0` is correct, but the report's original wording ("too small, or no matches") was vague when the true answer was known and precise. Fixed to report the actual index size and distinguish "empty" from "populated but nothing clusters."
3. Manually rebuilt one row's 10-feature vector and called `clf.predict_proba()` independently, outside `_ml_confidence_distribution()` — matched its own output (0.9975) exactly, confirming the confidence computation is sound rather than a fluke that happened to look plausible.

**Honest current-state note, not a bug:** with 0 real communities and an empty semantic index right now, two of the four report sections are correctly-empty rather than broken — the report says so plainly. Growing the semantic index (`zombie digest` on more files) and letting the import graph pass 3 nodes would populate both; that's separate future work, not part of C1.

**Key functions:** `_ore_histogram_by_community()`, `_provenance_age_distribution()`, `_ml_confidence_distribution()`, `_semantic_clusters_awaiting_attention()`, `generate_intake_report()`, `_render_intake_report()`
**CLI:** `zombie intake-report` | `zombie intake-report --json`
**No new dependencies** — `networkx` and `sklearn` were already present.

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
