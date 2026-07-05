# Git rot index digest

Generated: 2026-07-04T09:03:01.602423+00:00
Source: `manifest/git_rot_index.json` (regenerate via `uv run scripts/git_rot_index.py`)

## Summary

- Tracked markdown files: 1423
- Rot entries: 244
- Historical renames in repo: 1107

### By category

- `broken_no_known_target`: 127
- `ambig_truly_ambiguous`: 82
- `anchor_missing`: 34
- `broken_fixable_via_rename`: 1

### By priority

- `medium`: 237
- `low`: 6
- `high`: 1

### By code (grouped by gitological level)

**L1 — SURFACE  — raw symptoms visible at the link site**

- `ROT-001` (127): target_missing — no candidate file exists anywhere
- `ROT-002` (82): target_ambig_broken — basename matches multiple, link broken

**L2 — VIRTUAL  — namespace and resolution-layer concerns**

- `ROT-004` (1): target_renamed — auto-fixable via rename history

**L3 — ANCHOR   — positional / semantic reference alignment**

- `ROT-006` (34): anchor_missing — file exists, #anchor doesn't


## Hotspots (top 10 files by rot count)

- `debugging_data/codex_5.1_sabotage_trick.md` — 139 entries
- `CLAUDEBASE/The-Savant-High-Bounties/TODO.md` — 16 entries
- `CLAUDEBASE/The-Savant-High-Bounties/GRILLING.md` — 15 entries
- `dumpster-dive/archive/sessions_2026-01/session_resumption_chthonic_progress.md` — 11 entries
- `CLAUDEBASE/harbor/2026-06-22-stewardship-report.md` — 10 entries
- `WET_PAPER_TO_GOLD_METHODOLOGY.md` — 8 entries
- `dumpster-dive/README.md` — 8 entries
- `dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md` — 8 entries
- `dumpster-dive/protocols/FORGE_CIRCULATION_PROTOCOL.md` — 6 entries
- `.github/instructions/reference-appendix.reference.md` — 5 entries

## Clusters (derived patterns)

- `CLUSTER-001` `debugging_data/codex_5.1_sabotage_trick.md` — 139 entries. agent dump candidate — consider archive or delint exclusion
- `CLUSTER-002` target `file:///c%3A/Users/eldno/chthonic-archive/.vscode/mcp.json` — 32 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`
- `CLUSTER-002` target `../../../.github/copilot-instructions.md` — 15 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `dumpster-dive/archive/docs-sessions/SESSION_2026-01-17_CLEANUP.md`, `dumpster-dive/archive/docs-sessions/SESSION_2026-01-17_CLEANUP.md`, `dumpster-dive/archive/docs-sessions/SESSION_2026-01-17_SYNTHESIS.md`, `dumpster-dive/archive/sessions_2026-01/session_resumption_chthonic_progress.md`, `dumpster-dive/archive/sessions_2026-01/session_resumption_chthonic_progress.md`
- `CLUSTER-002` target `../.github/copilot-instructions.md` — 13 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `CLAUDEBASE/usables/Claude-Design-To-Scriptorium-Asked-Claude/uploads/BLACKSMITH_MATRIARCH-d89c48d4.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`
- `CLUSTER-002` target `file:///c%3A/Users/eldno/chthonic-archive/.github/prompts/README.md` — 11 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`
- `CLUSTER-002` target `file:///c%3A/Users/eldno/chthonic-archive/.vscode/README.md` — 7 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`
- `CLUSTER-002` target `file:///c%3A/Users/eldno/chthonic-archive/.github/prompts` — 6 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`
- `CLUSTER-002` target `../../../.github/copilot-instructions.md#L1` — 6 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md`, `dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md`, `dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md`, `dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md`, `dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md`
- `CLUSTER-002` target `../copilot-instructions.md` — 5 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `.github/instructions/reference-appendix.reference.md`, `.github/instructions/reference-appendix.reference.md`, `.github/instructions/reference-appendix.reference.md`, `.github/instructions/reference-appendix.reference.md`, `.github/instructions/reference-appendix.reference.md`
- `CLUSTER-002` target `file:///c%3A/Users/eldno/chthonic-archive/raw_sessions_for_beautification_tructation` — 5 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`
- `CLUSTER-002` target `../scripts/.deprecated/mcp_artisan_server.ts` — 5 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`
- `CLUSTER-002` target `file:///c%3A/Users/eldno/chthonic-archive/bun-playwright-poc/package.json` — 5 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`
- `CLUSTER-002` target `file:///c%3A/Users/eldno/chthonic-archive/.github/instructions/asc-entity-generation.instructions.md` — 4 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`
- `CLUSTER-002` target `file:///c%3A/Users/eldno/chthonic-archive/untitled_beautifySessionArchive.prompt.md` — 4 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`
- `CLUSTER-002` target `file:///c%3A/Users/eldno/.vscode-insiders/extensions/github.copilot-chat-0.37.2026012202/assets/prompts/savePrompt.prompt.md` — 3 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`, `debugging_data/codex_5.1_sabotage_trick.md`

## Top 30 entries by priority

### [HIGH / ROT-004 / broken_fixable_via_rename] `SCRIPTS_README.md:L662`

- Target: `.github/copilot-instructions.md`
- Suggested fix: `confiscated_instructions/repo_dotgithub_copilot-instructions.md`
- Rename: `.github/copilot-instructions.md` -> `confiscated_instructions/repo_dotgithub_copilot-instructions.md`
- Source last touched: 2026-07-04T05:15:02+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/SSOT_EVOLUTION_1.0_TO_1.5_BLUEPRINT.md:L387`

- Target: `copilot-instructions.md`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/instructions/agent-priority-protocol.md:L4`

- Target: `../copilot-instructions.md#L6812`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/instructions/agent-priority-protocol.md:L10`

- Target: `../copilot-instructions.md#L6812`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
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

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/instructions/reference-appendix.reference.md:L47`

- Target: `../copilot-instructions.md`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-05-14T06:46:39+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/instructions/reference-appendix.reference.md:L56`

- Target: `../copilot-instructions.md`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-05-14T06:46:39+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/instructions/reference-appendix.reference.md:L64`

- Target: `../copilot-instructions.md`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-05-14T06:46:39+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.github/pathstofiles.md:L13`

- Target: `copilot-instructions.md`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-001 / broken_no_known_target] `.temple/protocols/SESSION_2026_05_24_25_REDUX.md:L89`

- Target: `.github/copilot-instructions.archive.md#LN`
- Source last touched: 2026-05-27T02:00:06+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `.temple/protocols/THE_RECONCILIATION_ENGINE.md:L791`

- Target: `../../.github/copilot-instructions.md`
- Candidate matches: `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`, `codex/mailbox/VSCODE_EDIT_SESSION_RECOVERY_2026_05_23T14_46_31/decoded/.github/copilot-instructions.md`
- Source last touched: 2026-06-03T19:18:02+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-006 / anchor_missing] `CLAUDEBASE/The-Savant-High-Bounties/GRILLING.md:L57`

- Target: `TODO.md#gate--5--governance-integrity-substrate-health`
- Resolves to: `CLAUDEBASE/The-Savant-High-Bounties/TODO.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-06-20T03:08:01+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-006 / anchor_missing] `CLAUDEBASE/The-Savant-High-Bounties/GRILLING.md:L104`

- Target: `TODO.md#gate--4--ci-system-integrity-enforcement-health`
- Resolves to: `CLAUDEBASE/The-Savant-High-Bounties/TODO.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-06-20T03:08:01+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-006 / anchor_missing] `CLAUDEBASE/The-Savant-High-Bounties/GRILLING.md:L147`

- Target: `TODO.md#gate--3--toolchain-coherence-runtime-health`
- Resolves to: `CLAUDEBASE/The-Savant-High-Bounties/TODO.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-06-20T03:08:01+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-006 / anchor_missing] `CLAUDEBASE/The-Savant-High-Bounties/GRILLING.md:L192`

- Target: `TODO.md#gate--2--architectural-debt-reduction-structure-health`
- Resolves to: `CLAUDEBASE/The-Savant-High-Bounties/TODO.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-06-20T03:08:01+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-006 / anchor_missing] `CLAUDEBASE/The-Savant-High-Bounties/GRILLING.md:L230`

- Target: `TODO.md#gate--1--mcp-ecosystem-modernization-intelligence-layer`
- Resolves to: `CLAUDEBASE/The-Savant-High-Bounties/TODO.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-06-20T03:08:01+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-006 / anchor_missing] `CLAUDEBASE/The-Savant-High-Bounties/GRILLING.md:L287`

- Target: `TODO.md#t-23--character-schema--full-lore-validation-pass-auto`
- Resolves to: `CLAUDEBASE/The-Savant-High-Bounties/TODO.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-06-20T03:08:01+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-006 / anchor_missing] `CLAUDEBASE/The-Savant-High-Bounties/GRILLING.md:L287`

- Target: `TODO.md#gate-4--game-engine--v2-architecture-living-world`
- Resolves to: `CLAUDEBASE/The-Savant-High-Bounties/TODO.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-06-20T03:08:01+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-006 / anchor_missing] `CLAUDEBASE/The-Savant-High-Bounties/GRILLING.md:L332`

- Target: `TODO.md#gate-1--solana--gpu-compute-integration-frontier-engineering`
- Resolves to: `CLAUDEBASE/The-Savant-High-Bounties/TODO.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-06-20T03:08:01+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-006 / anchor_missing] `CLAUDEBASE/The-Savant-High-Bounties/GRILLING.md:L332`

- Target: `TODO.md#gate-4--game-engine--v2-architecture-living-world`
- Resolves to: `CLAUDEBASE/The-Savant-High-Bounties/TODO.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-06-20T03:08:01+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-006 / anchor_missing] `CLAUDEBASE/The-Savant-High-Bounties/GRILLING.md:L362`

- Target: `TODO.md#t-22--extension-hallucinatory-ladderization-remediation-decision`
- Resolves to: `CLAUDEBASE/The-Savant-High-Bounties/TODO.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-06-20T03:08:01+02:00 by erdnorddd@gmail.com
