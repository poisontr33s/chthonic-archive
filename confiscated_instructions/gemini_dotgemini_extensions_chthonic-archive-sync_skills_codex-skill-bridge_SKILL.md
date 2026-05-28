---
name: codex-skill-bridge
description: "REDIRECT — Merged into skill-polisher. Use skill-polisher for Codex skill audits."
metadata:
  short-description: "Merged into skill-polisher"
---

# Codex Skill Bridge — REDIRECT

Absorbed into **skill-polisher** (SKILL-HARDENING-3.0). All Codex audit commands live there now.

## Equivalent commands in skill-polisher

```powershell
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .codex/skills --all
uv run scripts/skill_audit.py --flavor codex --root .codex/skills
```

## Provenance

Original hook scripts (`run_codex_polisher.ps1`, `run_cross_audit.ps1`) were never implemented. The polisher CLI is the real entry point.

<!-- @POLISHED: 2026-02-05 → REDIRECTED: 2026-02-26 -->


