---
name: claude-skill-bridge
description: "REDIRECT — Merged into skill-polisher. Use skill-polisher for Claude skill audits and cross-flavor checks."
metadata:
  short-description: "Merged into skill-polisher"
---

# Claude Skill Bridge — REDIRECT

Absorbed into **skill-polisher** (SKILL-HARDENING-3.0). All Claude audit commands live there now.

## Equivalent commands in skill-polisher

```powershell
uv run scripts/skill_audit.py --flavor claude --root .claude/skills
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .claude/skills --all --mode verify --target-flavor auto
```

## Provenance

Original hook scripts (`run_claude_skill_polisher.ps1`, `run_claude_cross_polish.ps1`) were never implemented. Underlying functionality lives in `skill_audit.py` and `polish_skill.py`.

<!-- @POLISHED: 2026-02-05 → REDIRECTED: 2026-02-26 -->


