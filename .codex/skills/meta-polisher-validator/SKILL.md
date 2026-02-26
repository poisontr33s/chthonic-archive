---
name: meta-polisher-validator
description: Validate that meta-skills (Codex skill-polisher, Claude skill-polisher) correctly enforce their declared scope and cross-flavor contracts. Use when auditing the auditors or verifying that meta-skills align with Codex/Claude rules.
metadata:
  short-description: "Validate that meta-skills (Codex/Claude skill-polisher) enforce scope and cross-flavor contracts."
---

# Meta Polisher Validator

Validate the **meta-skills** that audit other skills. This is a second-order check.

## Targets
- Codex meta-skill: `.codex/skills/skill-polisher/`
- Claude meta-skill: `.claude/skills/skill-polisher/`
- Shared auditor: `scripts/skill_audit.py`
- Meta validators: `scripts/validate_meta_polishers.py`, `scripts/validate_claude_meta.py`

## Validation checklist
1. **Scope alignment**
   - `skill-polisher` must enforce Codex structure.
   - `skill-polisher` must enforce Claude frontmatter/tooling rules.
2. **Cross-flavor compatibility**
   - Both must reference `scripts/skill_audit.py` with correct `--flavor` usage.
3. **Hook integrity**
   - Claude hooks (`run_claude_skill_polisher.ps1`, `run_claude_cross_polish.ps1`) are referenced and exist.
   - Codex hooks (`run_codex_polisher.ps1`) are referenced and exist.
4. **No scope drift**
   - Codex rules are not applied to Claude skills and vice versa.

## Recommended commands
```powershell
uv run scripts/skill_audit.py --flavor codex --root .codex/skills
uv run scripts/skill_audit.py --flavor claude --root .claude/skills
uv run scripts/validate_meta_polishers.py
uv run scripts/validate_claude_meta.py
```

## Output
Provide a short report:
- Pass/Fail per checklist item
- Files inspected
- Any required remediation

<!-- @POLISHED: 2026-02-05 -->


