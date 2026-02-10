---
type: consolidated-session-appendix
created: 2026-02-06
scope: train-stop_to_parity_gate
status: active
---

# Technical Appendix: Evidence and Traceability

## Core Active Artifacts (Codex Mailbox)
- `codex/mailbox/SKILLS_PARITY_DISCREPANCY_2026_02_06.md`
- `codex/mailbox/skills_parity_map_2026_02_06.json`
- `codex/mailbox/KISS_PARITY_BRIEF_2026_02_06.md`
- `codex/mailbox/e2e_matrix_codex_on_codex.json`
- `codex/mailbox/e2e_matrix_codex_on_claude.json`
- `codex/mailbox/e2e_matrix_claude_on_codex.json`
- `codex/mailbox/e2e_matrix_claude_on_claude.json`
- `codex/mailbox/e2e_matrix_compare_summary.json`
- `codex/mailbox/META_POLISHER_VALIDATION_SUMMARY.json`
- `codex/mailbox/mailbox_manifest.json`
- `codex/mailbox/MAILBOX_CURRENT_STATE_2026_02_06.md`

## Core Active Artifacts (Claude Mailbox)
- `claude/mailbox/SKILLS_PARITY_DISCREPANCY_2026_02_06.md`
- `claude/mailbox/skills_parity_map_2026_02_06.json`
- `claude/mailbox/KISS_PARITY_BRIEF_2026_02_06.md`
- `claude/mailbox/e2e_matrix_codex_on_codex.json`
- `claude/mailbox/e2e_matrix_codex_on_claude.json`
- `claude/mailbox/e2e_matrix_claude_on_codex.json`
- `claude/mailbox/e2e_matrix_claude_on_claude.json`
- `claude/mailbox/CLAUDE_META_VALIDATION_SUMMARY.json`
- `claude/mailbox/mailbox_manifest.json`
- `claude/mailbox/MAILBOX_CURRENT_STATE_2026_02_06.md`

## Archived Historical Reports (Preserved)
### Codex archive
- `codex/mailbox/archive/TRAIN_STOP_HANDOFF_CONSOLIDATED_2026_02_05.md`
- `codex/mailbox/archive/TRAIN_STOP_AUDIT_PRE_SEND_2026_02_05.md`
- `codex/mailbox/archive/MAILBOX_CONSOLIDATED_2026_02_05.md`
- `codex/mailbox/archive/CLAUDE_RESPONSE_TRAIN_STOP_2026_02_05.md`
- `codex/mailbox/archive/CLAUDE_SKILLS_SPEC_VALIDATION_2026_02_05.md`
- `codex/mailbox/archive/SESSION_HANDOFF_2026_02_05_PARITY_DELTA.md`
- `codex/mailbox/archive/EXECUTION_ORDER_RECAP_2026_02_05.md`
- `codex/mailbox/archive/MAILBOX_CMD_POLICY_2026_02_05.md`
- `codex/mailbox/archive/skill_audit_codex_2026_02_05.json`
- `codex/mailbox/archive/skill_audit_claude_2026_02_05.json`

### Claude archive
- `claude/mailbox/archive/SESSION_HANDOFF_2026_02_05_OPERATION_TRAIN_STOP.md`
- `claude/mailbox/archive/SESSION_HANDOFF_2026_02_05_MAILBOX_SKILL_UPDATE.md`
- `claude/mailbox/archive/SESSION_HANDOFF_2026_02_05_PARITY_DELTA.md`

## Verification Commands Used in This Lane
- `uv run scripts/skill_audit.py --flavor codex --root .codex/skills`
- `uv run scripts/skill_audit.py --flavor claude --root .claude/skills`
- `uv run scripts/check_mailbox_layout.py`
- `./scripts/run_e2e_parity_gate.ps1`

## Canonical Path Model
- Codex skills: `.codex/skills`
- Claude skills: `.claude/skills`
- Codex mailbox: `codex/mailbox`
- Claude mailbox: `claude/mailbox`
- Hidden mailbox roots are sentinel-only: `.codex/mailbox/.gitkeep`, `.claude/mailbox/.gitkeep`

## Decision Record
- Historical context is archived, not deleted.
- Operational context stays concise in mailbox root.
- Hand-off packet should include this appendix plus chronicle for complete continuity.
