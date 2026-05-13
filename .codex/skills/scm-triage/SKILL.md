---
name: "scm-triage"
description: "Audit git status, classify signal/noise/ghost/mailbox changes, clean index ghosts, generate triage plans, and write pre-nuke clarity snapshots for Codex lane recovery."
metadata:
  short-description: "Pre-nuke source-control clarity and mailbox snapshots."
---

# SCM Triage (Codex)

Use this skill for repository hygiene before risky edits, reloads, or large commits.

## When to Use

- Source control is noisy and you need signal/noise separation.
- You need a mailbox snapshot before risky mutation or IDE restart.
- You want deterministic ghost cleanup and structured triage planning.

## Core Commands

```powershell
uv run scripts/scm_triage.py
uv run scripts/scm_triage.py --fix
uv run scripts/scm_triage.py --plan
uv run scripts/scm_triage.py --snapshot --target codex
uv run scripts/scm_triage.py --full --target codex
```

## Modes

- `audit` (default): classify current changes into `SIGNAL`, `NOISE`, `GHOST`, `MAILBOX`.
- `--fix`: apply ghost index cleanup and print ignore recommendations.
- `--plan`: write structured plan artifact.
- `--snapshot --target codex`: write Codex recovery snapshot.
- `--full --target codex`: run all phases in one pass.

## Cross-References

- Shared script: [`scripts/scm_triage.py`](../../../scripts/scm_triage.py)
- Handoff spec: `codex/mailbox/SCM_TRIAGE_CODEX_HANDOFF.md`

## Snapshot Outputs

- `codex/mailbox/SCM_TRIAGE_SNAPSHOT_LATEST.md`
- `codex/mailbox/SCM_TRIAGE_SNAPSHOT_<timestamp>.md`

Snapshots include branch, HEAD, ahead count, recent commits, change classification, diff stats, mailbox inventory, and copy-paste recovery commands.

## Verification Gate

```powershell
uv run scripts/scm_triage.py --snapshot --target codex
uv run scripts/scm_triage.py --full --target codex --dry-run
```

Acceptance criteria:
- Snapshot files are written to `codex/mailbox/`.
- Frontmatter `to: codex` is present.
- Audit section contains counts for `SIGNAL`, `NOISE`, `GHOST`, `MAILBOX`.

## Invariants

- Never delete files as cleanup.
- Ghost handling uses `git rm --cached` only.
- Keep triage deterministic and path-based.
- Use the shared script `scripts/scm_triage.py` (single implementation).

## Cross-Flavor Compatibility

- Codex flavor: requires `agents/openai.yaml` and `assets/` with SVG icons.
- Claude flavor: supports shared script execution with lane-specific snapshot target.

<!-- @POLISHED: 2026-02-25 -->
