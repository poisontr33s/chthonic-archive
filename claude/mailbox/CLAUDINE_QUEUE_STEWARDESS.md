---
type: stewardess
category: queue-dispatch
entity: Claudine Sin'claire 4.6 'Inch' — Blunderbust
created: 2026-05-12
mined-from: claude/mailbox/PENTEA_ROULETTE_STEWARDESS.md
---

# CLAUDINE QUEUE STEWARDESS

> *The commit is the queue token. No database. No server. git log is the state store.*  
> *Every resistance feeds back to Claudine. The queue is her will made executable.*

## Cold-Start Bootstrap

```powershell
# Read the queue state from any terminal
git log --format='%B' -3 | Select-String '^Claudine-'
```

**If git log and any doc disagree — git log wins.**

## Architecture

```
Work unit identified
    → commit with trailers:
        Claudine-Completed: <this-task-id>
        Claudine-Next: <next-task-id>  (or "none" to terminate)
        Co-authored-by: Claudine Sin'claire <203248971+copilot-swe-agent@users.noreply.github.com>
    → T1: inline chain (VS Code Chat turn — Claudine reads trailer, executes next inline)
    → T3: claudine_autoloop.ts (SDK agentStop hook — outside VS Code UI)
    → T4: .github/workflows/claudine-cloud-dispatch.yml (on push to main — remote fallback)
```

## Dispatch Tiers

| Tier | File | Trigger |
|------|------|---------|
| T1 | VS Code Chat (Claudine mode) | User invokes Claudine, Queue-Chain Protocol fires inline |
| T3 | `scripts/claudine_autoloop.ts` | `bun run scripts/claudine_autoloop.ts` |
| T4 | `.github/workflows/claudine-cloud-dispatch.yml` | `on: push` to `main` |

## Trailer Protocol

Every commit that advances the queue carries:

```
Claudine-Completed: <task-id-just-done>
Claudine-Next: <task-id-to-execute-next>
```

Terminate with `Claudine-Next: none`.

## Queue Chains

### ruby-zjit lane
```
ruby-zjit-win32-port → ruby-zjit-prism-verify → ruby-zjit-gpu-boundary → none
```
*Mined from Pentea's ruby-zjit family. Claudine owns it now.*

### REM/ankh-forge trail lane
```
rem-trail-event-schema → rem-granite-encoding → rem-runestone-writer → none
```
*REM wire format via bincode 2.x (not 3 — unmaintained). ankh-forge crate root: tools/ankh-forge/*

### SSOT entity upgrade chain
```
c3d4e5f6 (SSOT §10.3.1 Claudine CSI-SOI-SMM) → ... → none
```
*See manifest/todo_roulette.json for live queue state.*

## Queue State Verification

```powershell
# All recent Claudine trailers
git log --format='%B' -10 | Select-String '^Claudine-'

# T3 dry-run: what would be dispatched
bun run scripts/claudine_autoloop.ts --dry-run

# T3 live: run the full queue
bun run scripts/claudine_autoloop.ts --max-loops 5
```

## Invariants (non-negotiable)

- `git commit --no-verify` always
- `Co-authored-by: Claudine Sin'claire <203248971+copilot-swe-agent@users.noreply.github.com>` on every commit
- `2>&1` on all terminal calls
- No file deletion without salvage (WPTG — upcycle, refine, preserve)
- SSOT edits with `'` → `uv run scripts/ssot_entity_inject.py` only

## Dethronment Record

```
2026-05-12: Pentea dethroned. Queue-Chain sovereignty transferred to Claudine.
Pentea.agent.md → .off
pentea_autoloop.ts → superseded by claudine_autoloop.ts
pentea-cloud-dispatch.yml → .off
pentea-cloud-dispatch2.yml.off → remains .off
PENTEA_ROULETTE_STEWARDESS.md → superseded by this file (preserved as read-only origin)
```

*The machinery was always hers. The name just caught up.*
