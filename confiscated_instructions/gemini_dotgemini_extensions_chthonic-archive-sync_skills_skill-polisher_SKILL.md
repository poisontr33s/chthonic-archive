---
name: skill-polisher
description: "Meta-skill to audit, validate, and fix other skills. Structural integrity checks, cross-flavor audits, WPTG alignment, fixture eval."
metadata:
  short-description: "Audit and fix skills across both lanes"
  triggers:
    - "polish skill"
    - "upgrade skill"
    - "fix skill"
    - "audit skill"
---

# Skill Polisher

Audit skills for structural integrity, standardization, and cross-flavor compatibility.

## Commands

### Single skill
```powershell
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .codex/skills/<skill-name>
```

### Full sweep
```powershell
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .codex/skills --all
```

### Cross-flavor (Codex vs Claude)
```powershell
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .codex/skills --all --mode verify --target-flavor codex
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .claude/skills --all --mode verify --target-flavor claude
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .claude/skills --all --mode verify --target-flavor auto
```

### WPTG alignment
```powershell
# Baseline (informational)
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .codex/skills --all --mode verify --target-flavor codex --wptg-profile baseline
# Strict (blocking)
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .codex/skills --all --mode verify --target-flavor codex --wptg-profile strict
```

### Train Stop operations
```powershell
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .codex/skills --train-stop envelope-canon
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .codex/skills --train-stop decision-razor-hardening
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .codex/skills --train-stop artifact-upcycle-pass
```

### Fixture eval (regression)
```powershell
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .codex/skills/skill-polisher --fixture-eval .codex/skills/skill-polisher/fixtures
```

### Shared auditor
```powershell
uv run scripts/skill_audit.py --flavor codex --root .codex/skills
uv run scripts/skill_audit.py --flavor claude --root .claude/skills
```

## Notes
- Default: enforces `assets/` with canonical SVGs. Use `--no-require-assets` for metadata-only checks.
- WPTG profiles: `off` (default), `baseline` (informational), `strict` (blocking).
- Fixture runs use isolated temp copy under `codex/mailbox/.tmp_fixture_eval`.
