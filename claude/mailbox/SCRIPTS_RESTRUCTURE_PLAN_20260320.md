# Scripts Restructure Plan

> Generated: 2026-03-20 | Updated: 2026-03-23
> Sequence: Do Not Skip Steps

---

## Phase 0: Feed the Zombie (zero risk, zero reference breakage) — ✅ COMPLETE 2026-03-23

**Nothing is deleted. Everything is ore. The zombie eats first.**

> **Status:** 20/20 files consumed. Zombie sated. 12 routed to forge via [zombie_forge_bridge.py](../../scripts/zombie_forge_bridge.py). 2 prediction errors logged. Forge feedback loop live.
> See: [HANDOFF_A5_COMPLETE_20260323.md](HANDOFF_A5_COMPLETE_20260323.md) for full receipt.

The [`zombie_consumer.py`](../../scripts/zombie_consumer.py) sits above the [`dumpster-dive/`](../../dumpster-dive/README.md) forge:

```
  ZOMBIE (intelligence layer)
    │
    ├── BITE    scan file for ore signals
    ├── CHEW    extract imports, SIDs, docstrings, patterns
    ├── DIGEST  write intelligence extract (.zombie_extract_*.json)
    └── EXCRETE git mv to dumpster-dive/intake/ with receipt
                │
                └──► Sister Ferrum Scoriae's FORGE (existing pipeline)
                     INTAKE → ANVIL → FURNACE → QUENCH → TEMPERED
                                                    or → SLAG
```

The zombie grows a memory (`dumpster-dive/intake/.zombie_memory.json`) — every file it eats teaches it what patterns exist in the codebase, what imports are common, what SIDs have been seen. Future hunger scans get smarter.

**Quick commands:**
- `uv run scripts/zombie_consumer.py hunger` — what does the zombie want to eat?
- `uv run scripts/zombie_consumer.py feed <path> --dry-run` — preview full consumption
- `uv run scripts/zombie_consumer.py feed <path>` — consume: extract intelligence + move to intake
- `uv run scripts/zombie_consumer.py memory` — what has the zombie learned?

### 0A. Backup Corpses → `dumpster-dive/intake/scripts-restructure-2026-03-20/bak/`

```
scripts/chthonic.ps1.bak-20260316-181658
scripts/chthonic.ps1.bak-20260316-185259
scripts/chthonic.ps1.bak-20260316-190744
scripts/chthonic.ps1.bak-20260316-193348
scripts/chthonic.ps1.bak-20260316-193439
scripts/chthonic.ps1.bak-20260316-193628
scripts/probe_toolchain_path.ps1.bak-20260316-184959
scripts/probe_toolchain_path.ps1.bak-20260316-185111
scripts/probe_toolchain_path.ps1.bak-20260316-193348
scripts/probe_toolchain_path.ps1.bak-20260316-193439
```

**Ore rating: 2** — Low-grade. The live `.ps1` files already absorbed their changes. Value: diff forensics only (what was tried and rejected on 2026-03-16).

### 0B. Legacy File → `dumpster-dive/intake/scripts-restructure-2026-03-20/legacy/`

```
scripts/wpth_repeatable_cycle_LEGACY
```

**Ore rating: 3** — Mixed. Contains an older WPTG cycle that may hold patterns not in the current [`wptg_repeatable_cycle.py`](../../scripts/wptg_repeatable_cycle.py). Worth a furnace pass.

### 0C. Root-Level Strays → `dumpster-dive/intake/scripts-restructure-2026-03-20/root-strays/`

```
claude_test.py
get_hash.py
purify_ssot.py
strip_post_ssot.py
strip_ssot.py
strip_ssot_v2.py
```

**Ore rating: 3** — Mixed. The `strip_ssot*` variants are iteration history — the winning version's logic lives in `scripts/ssot_*.py` now, but the progression shows what was tried. [`get_hash.py`](../../dumpster-dive/intake/scripts-restructure-2026-03-20/root-strays/get_hash.py) may have a unique hashing approach.

### 0D. Recovered Salvage → `dumpster-dive/intake/scripts-restructure-2026-03-20/recovered/`

```
scripts/recovered_shell_recipe_cli.go
scripts/recovered_batch_transliteration.ps1
scripts/recovered_python_cluster_registry.py
```

**Ore rating: 3** — These are already marked "recovered" — they came from somewhere, landed in scripts/, and never got processed. Let the forge decide.

### 0E. Deprecated Directory → `dumpster-dive/intake/scripts-restructure-2026-03-20/deprecated/`

```
scripts/.deprecated/*  (entire directory contents)
```

**Ore rating: 2-3** — Already flagged by a previous pass. Bulk move, let anvil sort them.

### 0F. How to Execute Phase 0

```powershell
# Create intake batch directory
$batch = "dumpster-dive/intake/scripts-restructure-2026-03-20"
mkdir -p "$batch/bak" "$batch/legacy" "$batch/root-strays" "$batch/recovered" "$batch/deprecated"

# 0A: Backup corpses
git mv scripts/*.bak-* "$batch/bak/"

# 0B: Legacy
git mv scripts/wpth_repeatable_cycle_LEGACY "$batch/legacy/"

# 0C: Root strays
git mv claude_test.py get_hash.py purify_ssot.py strip_post_ssot.py strip_ssot.py strip_ssot_v2.py "$batch/root-strays/"

# 0D: Recovered
git mv scripts/recovered_*.{go,ps1,py} "$batch/recovered/"

# 0E: Deprecated
git mv scripts/.deprecated/* "$batch/deprecated/"

# Commit
git add -A && git commit -m "Phase 0: Move dead/stray files to dumpster-dive intake for forge processing"
```

**Why first:** Dead files pollute every audit, collision index, and link scan. `link_audit.py collisions` will be cleaner after this. And the forge pipeline already exists — we're feeding it, not reinventing it.

---

## Phase 1: Freeze the Reference Map

Run `link_audit.py scan --json` and save the output. This is the **before** snapshot. Every broken link that exists *now* is pre-existing debt, not caused by the restructure.

```powershell
uv run scripts/link_audit.py scan --json > claude/mailbox/LINK_AUDIT_BEFORE_RESTRUCTURE_20260320.json
```

Also snapshot the collision index:

```powershell
uv run scripts/link_audit.py collisions --json > claude/mailbox/COLLISION_INDEX_BEFORE_RESTRUCTURE_20260320.json
```

**Why second:** Phase 0 removed noise from the collision index. Now the snapshot is accurate. Every subsequent phase can diff against this baseline to prove it didn't make things worse.

---

## Phase 2: Define the Target Directory Structure

Before moving a single live file, declare the target layout in a spec. No file moves until this is reviewed and approved.

```
scripts/
  tensor/          <- skill_tensor_*.py (11 files)
  mailbox/         <- mailbox_*.py (6 files)
  theme/           <- theme_*.py (8 files)
  hf/              <- hf_*.py (8 files)
  ssot/            <- ssot_*.py (7 files)
  icons/           <- icon_*.py, product_icon_*.py (8 files)
  decorator/       <- decorator_*.py (4 files)
  vscode/          <- vscode_*.py (4 files)
  poe/             <- poe_*.py (4 files)
  wptg/            <- wptg_*.py, universal_forge.py (3 files)
  claude/          <- claude_*.ps1 (11 files)
  mcp/             <- mcp-*.ts (4 files)
  lib/             <- (already exists, keep)
  bin/             <- (already exists, keep)
  hooks/           <- (already exists, keep)
  aws/             <- (already exists, keep)
  codex/           <- (already exists, keep)
  data/            <- (already exists, keep)
```

Standalone files that don't belong to a cluster stay in [`scripts/`](../../scripts/) root.

---

## Phase 3: Move One Cluster at a Time

For each cluster (starting with the most self-contained):

1. `git mv` the files into the new subdirectory
2. `uv run scripts/link_audit.py renames --staged --fix` — auto-fix markdown references
3. Grep for old Python import paths, update them
4. Run the relevant probe or test to verify nothing broke
5. Commit the single cluster

**One cluster per commit.** If something breaks, revert one commit, not everything.

Suggested order (least dependencies first):
1. `icons/` — standalone, no cross-imports
2. `poe/` — self-contained cluster with [`lib/poe_auth.py`](../../scripts/lib/poe_auth.py)
3. `decorator/` — internal cluster only
4. `theme/` — internal cluster only
5. `hf/` — internal cluster only
6. `ssot/` — uses [`lib/ssot_paths.py`](../../scripts/lib/ssot_paths.py)
7. `vscode/` — standalone
8. `mailbox/` — uses [`lib/shared.py`](../../scripts/lib/shared.py)
9. `wptg/` — internal [`wptg_common.py`](../../scripts/wptg_common.py) dependency
10. `mcp/` — TypeScript, different import model
11. `tensor/` — last, because it's the most connected and recently upcycled

---

## Phase 4: Fix Python Import Paths

After each cluster move, grep and fix:

```powershell
# Example after moving theme_*.py to scripts/theme/
rg "from scripts\.theme_" --type py   # find old imports
rg "import theme_" --type py          # find old relative imports
```

[`scripts/lib/`](../../scripts/lib/) does NOT move, so `from scripts.lib.shared import ...` stays stable throughout.

---

## Phase 5: Update Config References

Files that contain hardcoded paths:

- [`config/skill_tensor_rules.json`](../../config/skill_tensor_rules.json) — skill root paths
- [`config/skill_operator_capabilities.json`](../../config/skill_operator_capabilities.json) — operator references
- `.claude/skills/*/` frontmatter — `@Implements:` headers
- `.codex/skills/*/` frontmatter
- [`AGENT_COMMON.md`](../../AGENT_COMMON.md) — script path references
- [`SCRIPTS_README.md`](../../SCRIPTS_README.md) — script path references

---

## Phase 6: Post-Restructure Audit

Run the same scans from Phase 1 and diff:

```powershell
uv run scripts/link_audit.py scan --json > claude/mailbox/LINK_AUDIT_AFTER_RESTRUCTURE_20260320.json
uv run scripts/link_audit.py collisions --json > claude/mailbox/COLLISION_INDEX_AFTER_RESTRUCTURE_20260320.json
```

Compare before/after. The restructure should have **reduced** collisions and broken links, not increased them.

---

## What NOT to Do

- Do not move everything at once
- Do not try to fix [`link_audit.py`](../../scripts/link_audit.py) and restructure simultaneously
- Do not create new abstractions or wrappers during the move
- Do not rename files while moving them (move first, rename later if needed)
- Do not touch `scripts/lib/` — it's the foundation everything imports from
- Do not delete anything — feed the forge instead
