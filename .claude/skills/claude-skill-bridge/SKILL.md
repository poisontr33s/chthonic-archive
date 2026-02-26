---
name: claude-skill-bridge
description: "One-command Claude skill audit. Runs local audit; add --cross-polish for cross-flavor check."
allowed-tools: "Read, Write, Glob, Grep, Bash"
user-invocable: true
---

# Claude Skill Bridge

## Command

```powershell
# Audit all Claude skills
.\scripts\run_claude_local_audit.ps1 -Root .claude/skills

# Cross-polish (Claude ↔ Codex parity check)
.\scripts\run_claude_cross_polish.ps1 -CodexRoot .codex/skills -ClaudeRoot .claude/skills
```



