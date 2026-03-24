---
name: meta-polisher-validator
description: "REDIRECT — Merged into skill-polisher. Use skill-polisher --mode verify for meta-skill validation."
metadata:
  short-description: "Merged into skill-polisher --mode verify"
allowed-tools: "Read"
user-invocable: false
---

# Meta Polisher Validator — REDIRECT

Absorbed into **skill-polisher** `--mode verify` (SKILL-HARDENING-3.0).

## Equivalent command

```powershell
# Validates both meta-skills in one pass (scope, cross-flavor, hooks)
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .codex/skills/skill-polisher --mode verify --target-flavor auto
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .claude/skills/skill-polisher --mode verify --target-flavor auto
```

## Provenance

Original 4-item checklist (scope alignment, cross-flavor compat, hook integrity, scope drift) is enforced by the polisher’s verify mode. Referenced scripts `validate_meta_polishers.py` and `validate_claude_meta.py` were never implemented — the polisher covers their intent.

<!-- @POLISHED: 2026-02-05 → REDIRECTED: 2026-02-26 -->


