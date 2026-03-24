# Handoff A5 — COMPLETE: `zombie_forge_bridge.py`

**Date:** 2026-03-23
**From:** Claude (A5 execution session)
**To:** Next Claude / Codex session
**Status:** ✅ A5 DONE — forge feedback loop is live
**Prerequisite chain:** A1-A4 ✅ → **A5 ✅** → A6, A7, A8

> This is the post-completion receipt for [HANDOFF_A5_FORGE_BRIDGE_20260323.md](HANDOFF_A5_FORGE_BRIDGE_20260323.md).
> Read that file for the original spec. Read this file for actual outcome + next-session entry point.

---

## What Was Delivered

[scripts/zombie_forge_bridge.py](../../scripts/zombie_forge_bridge.py) — new file, 360 lines.

Routes `.zombie_extract_*.json` files from `dumpster-dive/intake/` into `dumpster-dive/forge/` stages by `ore_rating`, writes forge receipt sidecars, appends `PATHWAY_REGISTRY.json`, and closes the `zombie learn` feedback loop.

### Verification results (all four checks passed)

```
uv run scripts/zombie_forge_bridge.py route --dry-run  →  12 files previewed, 0 errors
uv run scripts/zombie_forge_bridge.py route            →  12 routed, 0 already done, 0 errors
uv run scripts/zombie_forge_bridge.py status           →  12/12 routed, 0 unrouted
uv run scripts/zombie_consumer.py learn                →  34 scanned, 12 matched, 2 new lessons
```

The critical test (`zombie learn` returning >0 matched) passed at 12 matched. Forge feedback loop is live.

---

## File Cross-Reference (full affected set)

### New file

| File | Type | Role |
|---|---|---|
| [scripts/zombie_forge_bridge.py](../../scripts/zombie_forge_bridge.py) | `.py` | The bridge — built this session. Entry: `uv run scripts/zombie_forge_bridge.py` |

### Modified files

| File | Type | Change |
|---|---|---|
| [dumpster-dive/forge/PATHWAY_REGISTRY.json](../../dumpster-dive/forge/PATHWAY_REGISTRY.json) | `.json` | 12 entries appended (was N, now N+12). Array format preserved, append-only |
| [dumpster-dive/intake/.zombie_memory.json](../../dumpster-dive/intake/.zombie_memory.json) | `.json` | Updated by `zombie learn` — 2 prediction errors logged, cluster profiles adjusted |

### Read-only sources (not modified)

| File | Type | Why it was read |
|---|---|---|
| [scripts/zombie_consumer.py](../../scripts/zombie_consumer.py) | `.py` | Pattern source — `find_repo_root`, `safe_relative`, `FORGE_STATES`, `_ore_bar`, Rich rendering, argparse style |
| [dumpster-dive/forge/PROCESS_FLOW.md](../../dumpster-dive/forge/PROCESS_FLOW.md) | `.md` | Canonical routing table + stage definitions |
| [dumpster-dive/forge/PATHWAY_REGISTRY.json](../../dumpster-dive/forge/PATHWAY_REGISTRY.json) | `.json` | Pre-route schema + existing entries |
| [claude/mailbox/HANDOFF_A5_FORGE_BRIDGE_20260323.md](HANDOFF_A5_FORGE_BRIDGE_20260323.md) | `.md` | Original spec (authoritative) |
| [claude/mailbox/ZOMBIE_EVOLUTION_PROJECT_20260321.md](ZOMBIE_EVOLUTION_PROJECT_20260321.md) | `.md` | Full system architecture, A5-A8 backlog |

### Forge receipts written (12 new `.json` sidecars)

All receipts written to forge stage dirs alongside the routed files:

| Receipt file | Stage | Input type |
|---|---|---|
| `dumpster-dive/forge/furnace/.forge_receipt_chthonic.ps1.bak-20260316-193628.json` | furnace | `.bak` |
| `dumpster-dive/forge/furnace/.forge_receipt_probe_toolchain_path.ps1.bak-20260316-193439.json` | furnace | `.bak` |
| `dumpster-dive/forge/furnace/.forge_receipt_wpth_repeatable_cycle_LEGACY.json` | furnace | (no ext) |
| `dumpster-dive/forge/furnace/.forge_receipt_recovered_batch_transliteration.ps1.json` | furnace | `.ps1` |
| `dumpster-dive/forge/furnace/.forge_receipt_recovered_shell_recipe_cli.go.json` | furnace | `.go` |
| `dumpster-dive/forge/furnace/.forge_receipt_get_hash.py.json` | furnace | `.py` |
| `dumpster-dive/forge/furnace/.forge_receipt_purify_ssot.py.json` | furnace | `.py` |
| `dumpster-dive/forge/furnace/.forge_receipt_strip_post_ssot.py.json` | furnace | `.py` |
| `dumpster-dive/forge/furnace/.forge_receipt_strip_ssot.py.json` | furnace | `.py` |
| `dumpster-dive/forge/furnace/.forge_receipt_strip_ssot_v2.py.json` | furnace | `.py` |
| `dumpster-dive/forge/anvil/.forge_receipt_recovered_python_cluster_registry.py.json` | anvil | `.py` |
| `dumpster-dive/forge/slag/.forge_receipt_claude_test.py.json` | slag | `.py` |

### Forge stage populations (post-route, verified)

```json
{
  "anvil":     { "files": 4,  "bridge_routed": 1  },
  "furnace":   { "files": 22, "bridge_routed": 10 },
  "quench":    { "files": 1,  "bridge_routed": 0  },
  "slag":      { "files": 2,  "bridge_routed": 1  },
  "tea-vault": { "files": 1,  "bridge_routed": 0  },
  "tempered":  { "files": 24, "bridge_routed": 0  }
}
```

Non-bridge files in those stages pre-existed. `bridge_routed` = files added this session.

---

## Routed Files by Batch

### `scripts-restructure-2026-03-20/bak/` → furnace (ore 3, backup)

- `chthonic.ps1.bak-20260316-193628`
- `probe_toolchain_path.ps1.bak-20260316-193439`

> Note: bak/ contains 10 backup files total but only 2 `.zombie_extract_*.json` existed — bridge routes what's extracted, not raw content. 8 bak files have no extract yet.

### `scripts-restructure-2026-03-20/legacy/` → furnace (ore 3, legacy)

- `wpth_repeatable_cycle_LEGACY`

### `scripts-restructure-2026-03-20/recovered/` → furnace/anvil

- `recovered_batch_transliteration.ps1` → furnace (ore 3)
- `recovered_python_cluster_registry.py` → anvil (ore 4) ← prediction error (actual: anvil/3)
- `recovered_shell_recipe_cli.go` → furnace (ore 3)

### `scripts-restructure-2026-03-20/root-strays/` → furnace/slag

- `get_hash.py` → furnace (ore 3)
- `purify_ssot.py` → furnace (ore 3)
- `strip_post_ssot.py` → furnace (ore 3)
- `strip_ssot.py` → furnace (ore 3)
- `strip_ssot_v2.py` → furnace (ore 3)
- `claude_test.py` → slag (ore 2) ← prediction error (actual: slag/1)

---

## `zombie learn` Output — First Real Feedback Cycle

```json
{
  "outcomes_scanned": 34,
  "consumed_matched": 12,
  "new_lessons": 0,
  "total_errors": 2
}
```

> `new_lessons: 0` on second run (idempotent — lessons already applied). First run logged 2 new lessons.

### Prediction errors logged

| File | Predicted ore | Forge verdict | Error | Direction |
|---|---|---|---|---|
| `claude_test.py` | 2 | slag (→ 1) | −1 | too high |
| `recovered_python_cluster_registry.py` | 4 | anvil (→ 3) | −1 | too high |

**System response:** `cluster_profiles` adjusted for `test` and `recovered` categories. Next `bite()` on test files will adjust ore downward. This is expected behaviour for first-cycle feedback — the zombie was predicting slightly optimistically.

---

## PATHWAY_REGISTRY.json — Filetypes Now Registered (by bridge session)

Before this session the registry contained: `.log`, `.env`, `.off`, `.vsconfig`, `.bat` (pre-existing non-bridge entries).

New filetypes added by the bridge:

| Input type | Count | Forge stage |
|---|---|---|
| `.bak` (`.ps1.bak-*`) | 2 | furnace |
| `.ps1` | 1 | furnace |
| `.go` | 1 | furnace |
| `.py` | 7 | furnace (5), anvil (1), slag (1) |
| (no ext) — legacy | 1 | furnace |

All entries use pathway `"zombie extract -> ore routing -> forge stage"` and `"novel": true`.

---

## Bridge API Reference

```
uv run scripts/zombie_forge_bridge.py route
uv run scripts/zombie_forge_bridge.py route --dry-run
uv run scripts/zombie_forge_bridge.py route --batch <subdir-name>
uv run scripts/zombie_forge_bridge.py route --json
uv run scripts/zombie_forge_bridge.py status
uv run scripts/zombie_forge_bridge.py status --json
```

### Idempotency

Routing is hash-gated. Re-running `route` on the same intake is safe — existing receipts are detected by `content_hash`, files are skipped. The check uses `.forge_receipt_*.json` sidecars in each stage dir, not the registry.

### Name-preservation invariant

Companion files are copied preserving the original filename. `zombie learn` matches by `Path(e["consumed"]).name` — if filename changes, the match breaks. This invariant is a hard constraint in the bridge (`target_path = stage_dir / companion_name`).

### EMBALM integration (future-proof, passive)

The bridge checks for `.embalm_provenance_{name}.json` adjacent to each companion file. If found, the path is written into the forge receipt under `provenance_sidecar`. If absent, `"provenance_sidecar": null`. No failure, no hard dependency. Novia Cadaveris EMBALM can be activated later and receipts will auto-populate.

---

## Open Items (A6, A7, A8)

From [ZOMBIE_EVOLUTION_PROJECT_20260321.md § Next steps](ZOMBIE_EVOLUTION_PROJECT_20260321.md):

| Item | Description | Dependency |
|---|---|---|
| **A6** | Feed new files into zombie — populate profiles with real data beyond the 20-file seed | A5 ✅ (done) |
| **A7** | Bounded consumption log — apply `max_runs` pattern to keep last N meals | none |
| **A8** | Activate Novia PROWL — `git diff --cached` gating, WIP label removal | independent |

**A6 next action:** Identify the next candidate files via `uv run scripts/zombie_consumer.py hunger`, then `feed` them. The adaptive bite heuristics will now produce real corrections on next cycle because `learn` has logged 2 prediction errors.

---

## Do Not

- Do not modify the intake `.zombie_extract_*.json` files — they are the intelligence record and also the bridge's input
- Do not renumber or rename files in forge stages — `zombie learn` matches by filename
- Do not add a `tea-vault/` route by default — only `superposition` signal triggers it (currently no intake files carry this signal)
- Do not delete forge receipts — they are the idempotency gate

---

## Quick-Start for Next Session

```sh
# Verify current state
uv run scripts/zombie_forge_bridge.py status

# Check what the zombie wants to eat next
uv run scripts/zombie_consumer.py hunger

# Full pipeline on a new file
uv run scripts/zombie_consumer.py feed <path> --batch a6-intake-2026-03-23

# After feeding, route the new batch
uv run scripts/zombie_forge_bridge.py route --batch a6-intake-2026-03-23

# Close the loop
uv run scripts/zombie_consumer.py learn
```
