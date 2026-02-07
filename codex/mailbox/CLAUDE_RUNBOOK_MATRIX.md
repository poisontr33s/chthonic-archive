# Claude Runbook: Polisher Matrix (Codex-generated)

Goal: reproduce the same matrix runs from Claude Code.

All commands are PowerShell and follow repo policy: `uv run <script.py>`.

## 1. Codex contract on Codex skills
```powershell
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .codex/skills --all --mode verify --subprocess-fix --target-flavor codex --emit-stamps-json codex/mailbox/tatragrammatron_stamps_2026_02_07_codex_on_codex.json --emit-summary-md codex/mailbox/TATRAGRAMMATRON_SUMMARY_2026_02_07_CODEX_ON_CODEX.md
```

## 2. Claude contract on Claude skills
```powershell
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .claude/skills --all --mode verify --subprocess-fix --target-flavor claude --emit-stamps-json codex/mailbox/tatragrammatron_stamps_2026_02_07_codex_on_claude.json --emit-summary-md codex/mailbox/TATRAGRAMMATRON_SUMMARY_2026_02_07_CODEX_ON_CLAUDE.md
```

## 3. Auto detection on Claude skills
```powershell
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .claude/skills --all --mode verify --subprocess-fix --target-flavor auto --emit-stamps-json codex/mailbox/tatragrammatron_stamps_2026_02_07_auto_on_claude.json --emit-summary-md codex/mailbox/TATRAGRAMMATRON_SUMMARY_2026_02_07_AUTO_ON_CLAUDE.md
```

## 4. Cross-flavor auditor (independent check)
```powershell
uv run scripts/skill_audit.py --flavor codex --root .codex/skills --json --json-path codex/mailbox/codex_skill_audit_2026_02_07.json
uv run scripts/skill_audit.py --flavor claude --root .claude/skills --json --json-path codex/mailbox/claude_skill_audit_2026_02_07.json
```

## Expected artifacts
- `codex/mailbox/tatragrammatron_matrix_2026_02_07.json`
- stamps JSONs + summaries as above

## Notes
- If a run creates new icons/yaml scaffolds, that is expected under `--subprocess-fix`.
- Re-run `scripts/mailbox_scribe.py` after matrix runs to refresh the packet.
