---
name: git-snapshot
description: "Snapshot the latest git state (recent commits, branch, diff stats, changed files) into claude/mailbox/ as a structured handoff. Zero context burn — run at session start or before handoff."
---

# Git Snapshot

Captures current git state and writes `claude/mailbox/GIT_SNAPSHOT_LATEST.md`. Run at session start or before handoff to avoid token burn on git exploration.

## Commands

```powershell
uv run scripts/git_snapshot.py         # standard (15 commits)
uv run scripts/git_snapshot.py full    # extended (30 commits, author info)
uv run scripts/git_snapshot.py diff    # uncommitted changes only
uv run scripts/git_snapshot.py --json  # JSON to stdout
```

## Rules

- Read git state and write the mailbox file only. No other actions.
- Always overwrites `GIT_SNAPSHOT_LATEST.md` (not append).

## References

- Full spec: `.codex/skills/git-snapshot/SKILL.md`
- Script: `scripts/git_snapshot.py`
- `AGENT_COMMON.md`
