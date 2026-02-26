---
name: claude-skill-bridge
description: "REDIRECT — Merged into skill-polisher. Use skill-polisher for Claude skill audits and cross-flavor checks."
allowed-tools: "Read"
user-invocable: false
---

# Claude Skill Bridge — REDIRECT

Absorbed into **skill-polisher** (SKILL-HARDENING-3.0). All Claude audit commands live there now.

## Equivalent commands in skill-polisher

```powershell
# Claude local audit (was: run_claude_local_audit.ps1)
uv run scripts/skill_audit.py --flavor claude --root .claude/skills

# Cross-polish (was: run_claude_cross_polish.ps1)
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .claude/skills --all --mode verify --target-flavor auto
```

## Provenance

Original commands (`run_claude_local_audit.ps1`, `run_claude_cross_polish.ps1`) were never implemented as scripts — they were aspirational references. The underlying functionality was always in `skill_audit.py` and `polish_skill.py`.



