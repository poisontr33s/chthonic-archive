# Git rot index digest

Generated: 2026-05-31T22:04:58.192536+00:00
Source: `manifest/git_rot_index.json` (regenerate via `uv run scripts/git_rot_index.py`)

## Summary

- Tracked markdown files: 1190
- Rot entries: 166
- Historical renames in repo: 1101

### By category

- `ambig_truly_ambiguous`: 84
- `broken_no_known_target`: 68
- `broken_fixable_via_rename`: 11
- `anchor_missing`: 3

### By priority

- `medium`: 145
- `high`: 11
- `low`: 10

### By code (grouped by gitological level)

**L1 — SURFACE  — raw symptoms visible at the link site**

- `ROT-002` (84): target_ambig_broken — basename matches multiple, link broken
- `ROT-001` (68): target_missing — no candidate file exists anywhere

**L2 — VIRTUAL  — namespace and resolution-layer concerns**

- `ROT-004` (11): target_renamed — auto-fixable via rename history

**L3 — ANCHOR   — positional / semantic reference alignment**

- `ROT-006` (3): anchor_missing — file exists, #anchor doesn't


## Hotspots (top 10 files by rot count)

- `confiscated_instructions/agents/backup_20260528-194954_AGENTS.md` — 17 entries
- `confiscated_instructions/agents/repo_root_AGENTS.md` — 17 entries
- `confiscated_instructions/github/repo_dotgithub_copilot-instructions.md` — 14 entries
- `confiscated_instructions/gemini/gemini_GEMINI.md` — 13 entries
- `confiscated_instructions/agents/backup_20260528-194954_AGENT_COMMON.md` — 11 entries
- `confiscated_instructions/agents/repo_root_AGENT_COMMON.md` — 11 entries
- `dumpster-dive/archive/sessions_2026-01/session_resumption_chthonic_progress.md` — 11 entries
- `dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md` — 8 entries
- `confiscated_instructions/codex/repo_codex_NEXT.md` — 7 entries
- `WET_PAPER_TO_GOLD_METHODOLOGY.md` — 6 entries

## Clusters (derived patterns)

- `CLUSTER-002` target `../../../.github/copilot-instructions.md` — 15 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `dumpster-dive/archive/docs-sessions/SESSION_2026-01-17_CLEANUP.md`, `dumpster-dive/archive/docs-sessions/SESSION_2026-01-17_CLEANUP.md`, `dumpster-dive/archive/docs-sessions/SESSION_2026-01-17_SYNTHESIS.md`, `dumpster-dive/archive/sessions_2026-01/session_resumption_chthonic_progress.md`, `dumpster-dive/archive/sessions_2026-01/session_resumption_chthonic_progress.md`
- `CLUSTER-002` target `copilot-instructions.md` — 6 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `.github/INTEGRATION_MAP.md`, `.github/SESSION_RESUME.md`, `.github/SSOT_EVOLUTION_1.0_TO_1.5_BLUEPRINT.md`, `.github/STRUCTURAL_INTEGRITY_ANALYSIS.md`, `.github/VALIDATION_REPORT.md`
- `CLUSTER-002` target `../../../.github/copilot-instructions.md#L1` — 6 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md`, `dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md`, `dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md`, `dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md`, `dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md`
- `CLUSTER-002` target `../copilot-instructions.md` — 5 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `.github/instructions/reference-appendix.reference.md`, `.github/instructions/reference-appendix.reference.md`, `.github/instructions/reference-appendix.reference.md`, `.github/instructions/reference-appendix.reference.md`, `.github/instructions/reference-appendix.reference.md`
- `CLUSTER-002` target `.temple/protocols/LINGUISTIC_PROFILE_PROTOCOL.md` — 5 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `confiscated_instructions/agents/backup_20260528-194954_AGENTS.md`, `confiscated_instructions/agents/backup_20260528-194954_AGENT_COMMON.md`, `confiscated_instructions/agents/repo_root_AGENTS.md`, `confiscated_instructions/agents/repo_root_AGENT_COMMON.md`, `confiscated_instructions/gemini/gemini_GEMINI.md`
- `CLUSTER-002` target `.temple/methodology/TRIAD_METHODOLOGY.md` — 5 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `confiscated_instructions/agents/backup_20260528-194954_AGENTS.md`, `confiscated_instructions/agents/backup_20260528-194954_AGENT_COMMON.md`, `confiscated_instructions/agents/repo_root_AGENTS.md`, `confiscated_instructions/agents/repo_root_AGENT_COMMON.md`, `confiscated_instructions/gemini/gemini_GEMINI.md`
- `CLUSTER-002` target `../../AGENT_COMMON.md` — 4 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `.github/agents/Chthonic-Archivist.agent.md`, `.github/instructions/ankh-workflow.instructions.md`, `claude/mailbox/CODEX_HANDOFF_FLUX_VISIBILITY_STATUSBAR_2026_05_15.md`, `docs/architecture/CLAUDE.md`
- `CLUSTER-002` target `WET_PAPER_TO_GOLD_METHODOLOGY.md` — 4 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `confiscated_instructions/agents/backup_20260528-194954_AGENTS.md`, `confiscated_instructions/agents/backup_20260528-194954_AGENT_COMMON.md`, `confiscated_instructions/agents/repo_root_AGENTS.md`, `confiscated_instructions/agents/repo_root_AGENT_COMMON.md`
- `CLUSTER-002` target `PWSH_RULES.md` — 4 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `confiscated_instructions/agents/backup_20260528-194954_AGENT_COMMON.md`, `confiscated_instructions/agents/backup_20260528-194954_AGENT_COMMON.md`, `confiscated_instructions/agents/repo_root_AGENT_COMMON.md`, `confiscated_instructions/agents/repo_root_AGENT_COMMON.md`
- `CLUSTER-002` target `.temple/` — 3 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `confiscated_instructions/agents/backup_20260528-194954_AGENTS.md`, `confiscated_instructions/agents/repo_root_AGENTS.md`, `confiscated_instructions/gemini/gemini_GEMINI.md`
- `CLUSTER-002` target `game/` — 3 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `confiscated_instructions/agents/backup_20260528-194954_AGENTS.md`, `confiscated_instructions/agents/repo_root_AGENTS.md`, `confiscated_instructions/gemini/gemini_GEMINI.md`
- `CLUSTER-002` target `.temple/handoffs/` — 3 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `confiscated_instructions/agents/backup_20260528-194954_AGENTS.md`, `confiscated_instructions/agents/repo_root_AGENTS.md`, `confiscated_instructions/gemini/gemini_GEMINI.md`
- `CLUSTER-002` target `.temple/skills/` — 3 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `confiscated_instructions/agents/backup_20260528-194954_AGENTS.md`, `confiscated_instructions/agents/repo_root_AGENTS.md`, `confiscated_instructions/gemini/gemini_GEMINI.md`
- `CLUSTER-002` target `codex/codex-session-logs/archive/MILF-Core-Step3-Deep-Exploration-Prototypes.md` — 3 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `confiscated_instructions/agents/backup_20260528-194954_AGENTS.md`, `confiscated_instructions/agents/repo_root_AGENTS.md`, `confiscated_instructions/gemini/gemini_GEMINI.md`
- `CLUSTER-002` target `codex/codex-session-logs/archive/MILF-Core-Prototype-Analysis.md` — 3 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `confiscated_instructions/agents/backup_20260528-194954_AGENTS.md`, `confiscated_instructions/agents/repo_root_AGENTS.md`, `confiscated_instructions/gemini/gemini_GEMINI.md`

## Top 30 entries by priority

### [HIGH / ROT-004 / broken_fixable_via_rename] `PWSH_RULES.md:L279`

- Target: `.github/copilot-instructions.md`
- Suggested fix: `confiscated_instructions/repo_dotgithub_copilot-instructions.md`
- Rename: `.github/copilot-instructions.md` -> `confiscated_instructions/repo_dotgithub_copilot-instructions.md`
- Source last touched: 2026-05-13T06:41:43+02:00 by erdnorddd@gmail.com

### [HIGH / ROT-004 / broken_fixable_via_rename] `SCRIPTS_README.md:L656`

- Target: `.github/copilot-instructions.md`
- Suggested fix: `confiscated_instructions/repo_dotgithub_copilot-instructions.md`
- Rename: `.github/copilot-instructions.md` -> `confiscated_instructions/repo_dotgithub_copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [HIGH / ROT-004 / broken_fixable_via_rename] `confiscated_instructions/agents/backup_20260528-194954_AGENTS.md:L40`

- Target: `AGENT_COMMON.md`
- Suggested fix: `../../confiscated_instructions/backup_20260528-194954_AGENT_COMMON.md`
- Rename: `AGENT_COMMON.md` -> `confiscated_instructions/backup_20260528-194954_AGENT_COMMON.md`
- Source last touched: 2026-05-31T23:21:30+02:00 by erdnorddd@gmail.com

### [HIGH / ROT-004 / broken_fixable_via_rename] `confiscated_instructions/agents/backup_20260528-194954_AGENTS.md:L170`

- Target: `codex/NEXT.md`
- Suggested fix: `../../confiscated_instructions/repo_codex_NEXT.md`
- Rename: `codex/NEXT.md` -> `confiscated_instructions/repo_codex_NEXT.md`
- Source last touched: 2026-05-31T23:21:30+02:00 by erdnorddd@gmail.com

### [HIGH / ROT-004 / broken_fixable_via_rename] `confiscated_instructions/agents/backup_20260528-194954_AGENT_COMMON.md:L215`

- Target: `AGENTS.md`
- Suggested fix: `../../confiscated_instructions/backup_20260528-194954_AGENTS.md`
- Rename: `AGENTS.md` -> `confiscated_instructions/backup_20260528-194954_AGENTS.md`
- Source last touched: 2026-05-31T23:21:30+02:00 by erdnorddd@gmail.com

### [HIGH / ROT-004 / broken_fixable_via_rename] `confiscated_instructions/agents/backup_20260528-194954_AGENT_COMMON.md:L215`

- Target: `GEMINI.md`
- Suggested fix: `../../confiscated_instructions/gemini_GEMINI.md`
- Rename: `GEMINI.md` -> `confiscated_instructions/gemini_GEMINI.md`
- Source last touched: 2026-05-31T23:21:30+02:00 by erdnorddd@gmail.com

### [HIGH / ROT-004 / broken_fixable_via_rename] `confiscated_instructions/agents/repo_root_AGENTS.md:L40`

- Target: `AGENT_COMMON.md`
- Suggested fix: `../../confiscated_instructions/backup_20260528-194954_AGENT_COMMON.md`
- Rename: `AGENT_COMMON.md` -> `confiscated_instructions/backup_20260528-194954_AGENT_COMMON.md`
- Source last touched: 2026-05-31T23:21:30+02:00 by erdnorddd@gmail.com

### [HIGH / ROT-004 / broken_fixable_via_rename] `confiscated_instructions/agents/repo_root_AGENTS.md:L165`

- Target: `codex/NEXT.md`
- Suggested fix: `../../confiscated_instructions/repo_codex_NEXT.md`
- Rename: `codex/NEXT.md` -> `confiscated_instructions/repo_codex_NEXT.md`
- Source last touched: 2026-05-31T23:21:30+02:00 by erdnorddd@gmail.com

### [HIGH / ROT-004 / broken_fixable_via_rename] `confiscated_instructions/agents/repo_root_AGENT_COMMON.md:L208`

- Target: `AGENTS.md`
- Suggested fix: `../../confiscated_instructions/backup_20260528-194954_AGENTS.md`
- Rename: `AGENTS.md` -> `confiscated_instructions/backup_20260528-194954_AGENTS.md`
- Source last touched: 2026-05-31T23:21:30+02:00 by erdnorddd@gmail.com

### [HIGH / ROT-004 / broken_fixable_via_rename] `confiscated_instructions/agents/repo_root_AGENT_COMMON.md:L208`

- Target: `GEMINI.md`
- Suggested fix: `../../confiscated_instructions/gemini_GEMINI.md`
- Rename: `GEMINI.md` -> `confiscated_instructions/gemini_GEMINI.md`
- Source last touched: 2026-05-31T23:21:30+02:00 by erdnorddd@gmail.com

### [HIGH / ROT-004 / broken_fixable_via_rename] `confiscated_instructions/gemini/gemini_GEMINI.md:L5`

- Target: `AGENT_COMMON.md`
- Suggested fix: `../../confiscated_instructions/backup_20260528-194954_AGENT_COMMON.md`
- Rename: `AGENT_COMMON.md` -> `confiscated_instructions/backup_20260528-194954_AGENT_COMMON.md`
- Source last touched: 2026-05-31T23:21:30+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/INTEGRATION_MAP.md:L1`

- Target: `copilot-instructions.md`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/SESSION_RESUME.md:L1`

- Target: `copilot-instructions.md`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/SSOT_EVOLUTION_1.0_TO_1.5_BLUEPRINT.md:L387`

- Target: `copilot-instructions.md`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/STRUCTURAL_INTEGRITY_ANALYSIS.md:L1`

- Target: `copilot-instructions.md`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/VALIDATION_REPORT.md:L1`

- Target: `copilot-instructions.md`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-001 / broken_no_known_target] `.github/agents/Chthonic-Archivist.agent.md:L63`

- Target: `../../AGENT_COMMON.md`
- Source last touched: 2026-05-17T21:14:11+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/instructions/agent-priority-protocol.md:L4`

- Target: `../copilot-instructions.md#L6812`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/instructions/agent-priority-protocol.md:L10`

- Target: `../copilot-instructions.md#L6812`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-001 / broken_no_known_target] `.github/instructions/ankh-workflow.instructions.md:L46`

- Target: `../../AGENT_COMMON.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/instructions/asc-entity-generation.reference.md:L47`

- Target: `../copilot-instructions.md#L2443`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/instructions/behavioral-scenarios.reference.md:L17`

- Target: `../copilot-instructions.md#L3789`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/instructions/dcrp-operational-guide.md:L3`

- Target: `../copilot-instructions.md#L6643`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/instructions/dcrp-operational-guide.md:L9`

- Target: `../copilot-instructions.md#L6643`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/instructions/dev-conventions.reference.md:L17`

- Target: `../copilot-instructions.md#L6634`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/instructions/magistra-logic.reference.md:L17`

- Target: `../copilot-instructions.md#L4780`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/instructions/magistra-logic.reference.md:L18`

- Target: `../copilot-instructions.md#L6500`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/instructions/mathematical-engines.reference.md:L18`

- Target: `../copilot-instructions.md#L1`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/instructions/reference-appendix.reference.md:L18`

- Target: `../copilot-instructions.md`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-05-14T06:46:39+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/instructions/reference-appendix.reference.md:L35`

- Target: `../copilot-instructions.md`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-05-14T06:46:39+02:00 by erdnorddd@gmail.com
