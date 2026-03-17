---
type: mailbox-policy
created: 2026-03-08
subject: mailbox-rotation
---

# Mailbox Rotation Policy

## Current Census

- `codex/mailbox/` total files: `662`
- `codex/mailbox/` total directories: `133`
- Root mailbox files: `167`
- Root mailbox directories: `24`
- Archive file count: `113`
- Protected working queue: `ACTUAL-WORKING-HANDOFFS/` (`6` files)

High-volume root series:

| Prefix | Count | Recommended Keep Set |
|---|---:|---|
| `TOOLCHAIN_DOCTOR_REPORT` | 15 | `TOOLCHAIN_DOCTOR_LATEST.md` + newest timestamped |
| `SESSION_HANDOFF` | 6 | newest timestamped + current-cycle working handoff if referenced |
| `SCM_TRIAGE_SNAPSHOT` | 2 | both, until superseded |
| `SESSION_COMPACT` | 2 | JSON + Markdown pair |
| `SKILL_COMPARATIVE_REVIEW` | 2 | JSON + Markdown pair |

High-volume root directory series:

| Prefix | Count | Recommended Keep Set |
|---|---:|---|
| `VSCODE_TERMINAL_TRIAGE` | 14 | newest timestamped directory + one representative baseline |
| `VSCODE_INSIDERS_MATRIX` | 6 | newest timestamped directory + one representative baseline |

## Protected Surfaces

Never rotate automatically:

- `MAILBOX_CURRENT_STATE.md`
- `mailbox_manifest.json`
- `ACTUAL-WORKING-HANDOFFS/`
- `archive/`

Treat as temporary fixture output, not durable handoff material:

- `.tmp_fixture_eval/`

## Rotation Rules

### 1. Timestamped File Series

For any root mailbox prefix with more than three timestamped files:

- Keep `*_LATEST.*` aliases if present.
- Keep the most recent timestamped artifact.
- Archive the rest to:
  - `codex/mailbox/archive/series/<PREFIX>/`

### 2. Timestamped Directory Series

For any root mailbox directory prefix with more than three timestamped members:

- Keep the newest timestamped directory.
- Optionally keep one earlier baseline for comparison.
- Archive the rest to:
  - `codex/mailbox/archive/directories/<PREFIX>/`

### 3. Staleness Threshold

Root mailbox files older than 30 days with no:

- `LATEST` alias role,
- explicit working-handoff role,
- or current governance reference

become archive candidates.

### 4. Pair Preservation Rule

If a timestamped artifact exists as a JSON + Markdown pair for the same event, rotate them together.

### 5. No Destroy Rule

Rotation is move-only. No deletion.

## Engine

The repo-local engine is [mailbox_rotation.py](../../scripts/mailbox_rotation.py).

Recommended usage:

```powershell
uv run scripts/mailbox_rotation.py --target codex
uv run scripts/mailbox_rotation.py --target codex --write-state
uv run scripts/mailbox_rotation.py --target codex --execute --write-state
```

Default mode is dry-run and emits a JSON plan.
