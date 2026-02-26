---
type: skill-handoff
from: claude
to: codex
created: 2026-02-25T17:40:00Z
priority: high
scope: skill-creation
subject: SCM-TRIAGE Codex-side mirror skill
---

# HANDOFF: SCM Triage Skill — Codex Flavor

## Context

Claude has created `scm-triage` (`.claude/skills/scm-triage/SKILL.md` + `scripts/scm_triage.py`) — a source control noise classifier and pre-nuke clarity engine. Codex needs a mirror skill under `.codex/skills/` that can:

1. **Invoke the backing script** (`uv run scripts/scm_triage.py`)
2. **Read snapshots** from `claude/mailbox/SCM_TRIAGE_SNAPSHOT_LATEST.md`
3. **Write its own snapshots** when Codex sessions need context preservation

## What Exists (Claude Side)

- **Skill**: `.claude/skills/scm-triage/SKILL.md`
- **Script**: `scripts/scm_triage.py` (@SID: TOOL_SCM_TRIAGE_V1)
- **Modes**:
  - `--fix` = apply gitignore/exclude fixes + ghost cleanup
  - `--plan` = generate migration manifest JSON
  - `--snapshot` = write full context snapshot to `claude/mailbox/`
  - `--full` = all phases
  - `--dry-run` = preview without applying
- **Output artifacts**:
  - `claude/mailbox/SCM_TRIAGE_SNAPSHOT_LATEST.md` (YAML frontmatter + structured markdown)
  - `claude/mailbox/SCM_TRIAGE_PLAN.json` (structured audit + recommendations)

## What Codex Should Build

### 1. Codex Skill Definition

Create `.codex/skills/scm-triage/` with:
- `SKILL.md` — Codex-flavor frontmatter (`agents/openai.yaml` format)
- `agents/openai.yaml` — Agent definition for Codex
- Reference the shared `scripts/scm_triage.py` backing script (don't duplicate)

### 2. Codex-Specific Snapshot Target

The current `--snapshot` writes to `claude/mailbox/`. Codex should be able to write its own snapshots:

**Option A (preferred):** Add `--target codex` flag to `scripts/scm_triage.py` that writes to `codex/mailbox/SCM_TRIAGE_SNAPSHOT_LATEST.md` instead.

**Option B:** Create a thin wrapper that calls the script and copies the output.

### 3. Gitignore Entry

Add the Codex skill to `.gitignore` allowlist:
```
!.codex/skills/scm-triage/
!.codex/skills/scm-triage/**
```

## Classification Rules (for reference)

The script classifies git changes into:
- **SIGNAL**: Intentional changes in canonical directories (scripts, extensions, src, game, etc.)
- **NOISE**: Transient daemon outputs, caches, temp fixtures
- **GHOST**: Tracked files that were physically deleted
- **MAILBOX**: Agent deliverables in claude/codex/gemini mailbox lanes

## Recovery Protocol

When an agent session starts after a nuke:
1. Read `claude/mailbox/SCM_TRIAGE_SNAPSHOT_LATEST.md` (or codex equivalent)
2. This gives: branch, HEAD, commits ahead, change classification, mailbox inventory
3. Run `uv run scripts/scm_triage.py` for live audit
4. If noise/ghosts: `uv run scripts/scm_triage.py --fix`

## Dependencies

- Python 3.13+ via `uv`
- `scripts/lib/shared.py` (configure_utf8_output, find_repo_root, setup_logging)
- Git CLI

## Commits to Reference

- `c5a17158` — SCM-TRIAGE-1.0: initial skill + script
- `eb75d3c1` — SCM-HYGIENE: the cleanup that motivated this skill
