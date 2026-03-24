# Handoff A5: Build `zombie_forge_bridge.py`

**Date:** 2026-03-23
**From:** Claude (zombie evolution session)
**To:** Next Claude session
**Priority:** Critical path — unblocks `zombie learn` feedback loop
**Prerequisite chain:** A1-A4 ✅ → **A5** → A6, A7, A8

---

## What This Is

A bridge script that reads zombie extract files from `dumpster-dive/intake/` and routes the corresponding consumed files into `dumpster-dive/forge/` stages based on `ore_rating`. Without this, the zombie's `learn` command returns 0 matches — the forge feedback loop is wired but has no data to backpropagate.

## Why It Matters

```
zombie feed → intake/       (done, 20 files)
                ↓
        [A5 BRIDGE]         ← THIS IS THE GAP
                ↓
        forge/{anvil,furnace,slag,...}
                ↓
zombie learn ← reads forge  (wired, returns 0 without A5)
                ↓
        cluster_profiles adjusted → next bite() smarter
```

---

## Inputs Available (verified 2026-03-23)

### Zombie extracts: 12 files across 4 subdirectories

```
dumpster-dive/intake/scripts-restructure-2026-03-20/
├── bak/          (backup corpses — 10 files + extracts)
├── legacy/       (1 file + extract)
├── recovered/    (3 files + extracts)
└── root-strays/  (6 files + extracts)
```

Each `.zombie_extract_*.json` has this schema:

```json
{
  "source": "scripts/chthonic.ps1.bak-20260316-193628",
  "timestamp": "2026-03-21T03:20:39.142331+00:00",
  "ore_rating": 3,
  "category": "backup",
  "signals": ["backup_file", "has_decorator_header"],
  "intelligence": {},
  "content_hash": "a3b3b04e5db51a79"
}
```

Key fields for routing: `ore_rating` (int 1-5), `category` (str), `source` (original path before excretion).

### Forge stage directories (all exist)

```
dumpster-dive/forge/
├── intake/       (forge's own intake, currently has only a README)
├── anvil/
├── furnace/
├── quench/
├── slag/
├── tea-vault/
└── tempered/
```

### PATHWAY_REGISTRY.json (existing)

Located at [dumpster-dive/forge/PATHWAY_REGISTRY.json](../../dumpster-dive/forge/PATHWAY_REGISTRY.json). Currently has entries for `.log`, `.env`, `.off`, `.vsconfig` pathways. The bridge should **append** entries, not overwrite.

Schema per entry:
```json
{
  "input_type": ".py",
  "output_type": ".json",
  "pathway": "zombie extract -> ore routing -> forge stage",
  "path": "dumpster-dive/forge/anvil/some_file.py",
  "novel": true
}
```

---

## Routing Table (canonical, from CIRCULATION_DIAGRAM + PROCESS_FLOW)

| `ore_rating` | Forge Stage | Rationale |
|---|---|---|
| 5 | `quench/` (fast-track) or `anvil/` (if complex) | High-grade, skip furnace |
| 4 | `anvil/` | Workable, needs analysis |
| 3 | `furnace/` | Mixed, needs heat refinement |
| 2 | `slag/` | Low-grade, archival only |
| 1 | `slag/` + tag `upcycle_pending: true` | Tailings, mark for possible future re-assessment |

**Superposition case:** If extract has signal `content_duplicate` or contradictory ore signals, route to `tea-vault/`. (Edge case — implement but don't expect to hit it on the first 20 files.)

---

## What To Build

### `scripts/zombie_forge_bridge.py`

Subcommands:

| Command | Purpose |
|---|---|
| `route --dry-run` | Scan all extracts in `intake/`, show proposed routing without moving |
| `route` | Execute routing: copy/move files into forge stages, update PATHWAY_REGISTRY.json |
| `route --batch <name>` | Route only files from a specific batch subdirectory |
| `status` | Show current bridge state: how many files routed, how many pending, forge stage counts |

### Core logic:

1. **Scan** `dumpster-dive/intake/` recursively for `.zombie_extract_*.json` files
2. **Parse** each extract for `ore_rating`, `category`, `source`, `content_hash`
3. **Find** the corresponding consumed file (same directory as the extract, matching stem)
4. **Route** by ore_rating per the routing table above
5. **Write** PATHWAY_REGISTRY.json entry per routed file
6. **Write** a `.forge_receipt_*.json` sidecar in the target forge stage directory with:
   - `source_extract`: path to the zombie extract
   - `routed_from`: intake path
   - `routed_to`: forge stage path
   - `ore_rating`: from extract
   - `category`: from extract
   - `timestamp`: ISO 8601
   - `provenance_sidecar`: path to EMBALM provenance if present, `null` if not (future-proof for Novia integration)

### EMBALM provenance integration (future-proof):

Per [SFS_QML_BRIDE_SYNC_FINDINGS_20260323.md](../../codex/mailbox/SFS_QML_BRIDE_SYNC_FINDINGS_20260323.md) Track 2, Novia Cadaveris's EMBALM mode writes provenance sidecars (`sha256`, language, structural landmarks, source path, git HEAD). The bridge should:

- **Check** for a provenance sidecar adjacent to the zombie extract (naming convention TBD — suggest `.embalm_provenance_*.json`)
- If present: include its path in the forge receipt and copy it alongside the routed file
- If absent: proceed without it, set `provenance_sidecar: null`

This is a read-if-exists pattern, not a hard dependency. The bridge works without EMBALM operational.

---

## Implementation Constraints

- **Use `uv run`** — no raw `python`. Follow repo conventions in [AGENT_COMMON.md](../../AGENT_COMMON.md).
- **Follow zombie_consumer.py patterns** — same `find_repo_root()`, same `ROOT`/`INTAKE` constants, same JSON formatting, same `safe_relative()` for path display.
- **Do not move zombie extracts** — they stay in `intake/` as the intelligence record. Copy or move the consumed *files* only.
- **Append to PATHWAY_REGISTRY.json** — load existing, append, write back. Do not overwrite.
- **Rich output** — use `rich` tables/panels for CLI output, matching zombie_consumer.py's rendering style. Keep `--json` flag for machine-readable output.
- **Idempotent** — running `route` twice should not create duplicates. Check if a forge receipt already exists for a given content_hash before routing.

---

## Verification Steps

After building:

1. `uv run scripts/zombie_forge_bridge.py route --dry-run` — should show 20 files with proposed forge destinations
2. `uv run scripts/zombie_forge_bridge.py route` — should move files, update PATHWAY_REGISTRY.json
3. `uv run scripts/zombie_forge_bridge.py status` — should show routed counts per forge stage
4. `uv run scripts/zombie_consumer.py learn` — should now find matched files and produce forge feedback (this is the critical test — if `learn` still returns 0 matches, the bridge isn't wired correctly to the zombie's consumption_log name matching)

### Name matching caveat

`zombie learn` matches forge files by **filename** against `consumption_log[].consumed` (which stores the original relative path). The bridge must preserve the original filename when routing into forge stages — e.g., `intake/bak/chthonic.ps1.bak-20260316-193628` → `forge/slag/chthonic.ps1.bak-20260316-193628`. If the filename changes, `learn` won't match.

---

## Files To Read Before Starting

| File | Why |
|---|---|
| [scripts/zombie_consumer.py](../../scripts/zombie_consumer.py) | Pattern source — `load_memory()`, `_scan_forge_outcomes()`, `learn_from_forge()`, Rich rendering |
| [dumpster-dive/forge/PROCESS_FLOW.md](../../dumpster-dive/forge/PROCESS_FLOW.md) | Canonical stage definitions and routing rules |
| [dumpster-dive/forge/PATHWAY_REGISTRY.json](../../dumpster-dive/forge/PATHWAY_REGISTRY.json) | Existing registry format — append, don't overwrite |
| [dumpster-dive/CIRCULATION_DIAGRAM.md](../../dumpster-dive/CIRCULATION_DIAGRAM.md) | Visual routing reference |
| [codex/mailbox/SFS_QML_BRIDE_SYNC_FINDINGS_20260323.md](../../codex/mailbox/SFS_QML_BRIDE_SYNC_FINDINGS_20260323.md) | Track 1 (gap detail) + Track 2 (EMBALM integration spec) |
| [claude/mailbox/ZOMBIE_EVOLUTION_PROJECT_20260321.md](ZOMBIE_EVOLUTION_PROJECT_20260321.md) | Full zombie architecture context |

---

## Do Not

- Do not modify `zombie_consumer.py` — it's the upstream producer, not a build target
- Do not restructure `dumpster-dive/forge/` directories — they're operational
- Do not delete zombie extracts — they're the intelligence record
- Do not overwrite PATHWAY_REGISTRY.json — append only
