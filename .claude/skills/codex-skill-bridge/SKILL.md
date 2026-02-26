---
name: codex-skill-bridge
description: "REDIRECT — Merged into skill-polisher. Use skill-polisher for Codex skill audits."
allowed-tools: "Read"
user-invocable: false
---

# Codex Skill Bridge — REDIRECT

Absorbed into **skill-polisher** (SKILL-HARDENING-3.0). All Codex audit commands live there now.

## Equivalent commands in skill-polisher

```powershell
# Codex polisher sweep (was: run_codex_polisher.ps1)
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .codex/skills --all

# Cross-flavor structural audit
uv run scripts/skill_audit.py --flavor codex --root .codex/skills
```

## Provenance

Original hook script (`run_codex_polisher.ps1`) was never implemented. The polisher CLI was always the real entry point.



