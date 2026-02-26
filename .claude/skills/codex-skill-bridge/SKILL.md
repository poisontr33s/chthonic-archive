---
name: codex-skill-bridge
description: "One-command Codex skill audit from Claude IDE. Runs polisher or cross-flavor audit."
allowed-tools: "Read, Write, Glob, Grep, Bash"
user-invocable: true
---

# Codex Skill Bridge

## Command

```powershell
# Audit all Codex skills (polisher sweep)
.\scripts\run_codex_polisher.ps1 -Root .codex/skills

# Cross-flavor structural audit
uv run scripts/skill_audit.py --flavor codex --root .codex/skills
```



