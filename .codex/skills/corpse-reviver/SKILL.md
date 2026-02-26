---
name: corpse-reviver
description: "The White-dressed Bride — kleptomaniac necromancy pipeline. Prowls the wasteland for dying code, hoards indiscriminately, embalms with provenance, and sutures fragments into reanimated composites."
metadata:
  short-description: "Necromancy pipeline — prowl, hoard, embalm, classify, suture, reanimate dead code"
  argument-hint: "uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py hoard"
  tags:
    - code archaeology
    - data transformation
    - git history
    - dead code
    - necromancy
---

# Corpse Reviver

> *The Bride walks the wasteland in white, blind-faithed, taking everything. She doesn't judge what's dead — she stitches it into something that stands.*

The full necromancy lifecycle for code: intercept before death, hoard from every graveyard, embalm with provenance, classify into the vault, suture fragments into composites, reanimate on demand.

## Conceptual Shells

| Shell | Mode | Behavior |
|---|---|---|
| **High Ambulant** | `prowl` | Actively walks the codebase for the about-to-die — staged deletions, uncommitted overwrites |
| **Scarce-Makeshift** | (philosophy) | Raw diffs, broken stashes, half-deleted files — all valid input |
| **Wasteland-ridden** | `harvest` | Reflog graveyard, dead branches, unreachable blobs, orphaned files |
| **Blind-Faithed** | `hoard` | No triage at ingest. Collect everything, judge nothing |
| **Kleptomaniac** | `hoard` | Every source, every graveyard, every gitignored ghost |
| **Necromantic** | `reanimate` | Search the vault, pull fragments back into the living |
| **White-dressed Bride** | `suture` | Stitch fragments from different corpses into a new composite |

## Graveyards

What the Bride ransacks:

- **Git diffs** — deleted lines from commits
- **Git stashes** — abandoned work-in-progress
- **Reflog** — force-pushed, reset --hard, amended-away code (the deepest graveyard)
- **Dead branches** — merged/deleted branches with unique code
- **Commented-out code** — pre-corpse, already embalmed in-place
- **Orphaned files** — untracked, unreferenced, alive but useless
- **Gitignored treasures** — exist on disk, invisible to git
- **TODO/FIXME/HACK graffiti** — marked for death but still breathing

## Modes

### prowl
Intercept code about to die. Scans staged deletions and uncommitted overwrites.

```powershell
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py prowl
```

### harvest
Scan specific graveyards. Extract and embalm.

```powershell
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py harvest --since 30d
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py harvest --stashes
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py harvest --comments
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py harvest --reflog
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py harvest --dead-branches
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py harvest --orphans
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py harvest --gitignored
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py harvest --graffiti
```

### hoard
Blind-faithed total sweep — every graveyard, every source, no discrimination.

```powershell
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py hoard
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py hoard --since 90d
```

### classify
Sort embalmed fragments into the vault by language/filetype.

```powershell
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py classify
```

### reanimate
Search the vault and pull fragments back into context.

```powershell
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py reanimate --query "websocket handler"
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py reanimate --lang rust
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py reanimate --ext .ts
```

### suture
Stitch fragments from different corpses into a composite file. The Bride's final act.

```powershell
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py suture --fragments <hash1> <hash2> <hash3> --output bride.rs
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py suture --lang rust --query "handler" --output stitched_handlers.rs
```

### manifest
Print vault summary — the morgue ledger.

```powershell
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py manifest
```

## Vault

Fragments are stored in `dumpster-dive/corpse-vault/` organized by language:

```
dumpster-dive/corpse-vault/
├── manifest.json          # the morgue ledger
├── sutures/               # composite outputs from suture mode
├── rust/
├── python/
├── typescript/
├── javascript/
├── markdown/
├── config/                # yaml, toml, json, toml
├── shell/                 # ps1, sh, bash
├── html/
├── css/
├── sql/
└── unknown/
```

Each fragment: `{vault}/{lang}/{hash}_{original_name}.fragment`
Each sidecar: `{vault}/{lang}/{hash}_{original_name}.provenance.json`

## Provenance Schema

```json
{
  "hash": "sha256 of fragment content",
  "source_file": "src/old_module.rs",
  "commit": "abc1234",
  "author": "name",
  "date": "2026-02-15T...",
  "cause_of_death": "deleted_in_commit | stash_abandoned | commented_out | reflog_casualty | dead_branch | orphaned | gitignored | graffiti_marked | staged_deletion",
  "language": "rust",
  "extension": ".rs",
  "lines_start": 42,
  "lines_end": 87,
  "byte_size": 1823,
  "fragment_file": "rust/a1b2c3d4_old_module.rs.fragment"
}
```
