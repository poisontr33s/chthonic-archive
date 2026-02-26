---
name: git-snapshot
description: "Snapshot the latest git state (recent commits, branch, diff stats, changed files) into claude/mailbox/ as a structured handoff. Zero context burn — run at session start or before handoff."
allowed-tools: "Bash, Read, Write, Glob"
user-invocable: true
---

# Git Snapshot → Mailbox

Captures current git state and writes a structured summary to `claude/mailbox/GIT_SNAPSHOT_LATEST.md`. Designed for session resumption — agents read the snapshot instead of burning tokens on git exploration.

## CLI

```bash
uv run scripts/git_snapshot.py                # standard snapshot (15 commits)
uv run scripts/git_snapshot.py full            # extended (30 commits, author info)
uv run scripts/git_snapshot.py diff            # uncommitted changes only
uv run scripts/git_snapshot.py --json          # JSON output to stdout
uv run scripts/git_snapshot.py --emit PATH     # write to custom path instead of mailbox
```

**Prefer the CLI over manual git exploration.** The script handles all git queries, markdown formatting, and mailbox routing in a single invocation.

## Modes

| Mode | Commits | Authors | Status | Diff Stats |
|------|---------|---------|--------|------------|
| default | 15 (oneline) | no | yes | yes |
| full | 30 (with author, age) | yes | yes | yes |
| diff | none | — | yes | yes |

## Output

Writes `claude/mailbox/GIT_SNAPSHOT_LATEST.md` with YAML frontmatter (type, from, to, created, priority, scope) followed by branch, HEAD, remote, clean status, commit list, 24h velocity, working tree, and diff stats.

## Rules

- ONLY read git state and write the mailbox file. No other actions.
- Always overwrite `GIT_SNAPSHOT_LATEST.md` (not append).
- For custom output path, use `--emit PATH`.
- For piping to other tools, use `--json`.
