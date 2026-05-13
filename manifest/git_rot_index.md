# Git rot index digest

Generated: 2026-05-13T06:33:44.755260+00:00
Source: `manifest/git_rot_index.json` (regenerate via `uv run scripts/git_rot_index.py`)

## Summary

- Tracked markdown files: 1111
- Rot entries: 463
- Historical renames in repo: 757

### By category

- `ambig_resolves_fine`: 266
- `ambig_truly_ambiguous`: 99
- `broken_no_known_target`: 88
- `placeholder_literal`: 10

### By priority

- `background`: 266
- `medium`: 124
- `low`: 73

### By code

- `ROT-003` (266): target_ambig_resolves — basename ambiguous but link resolves (false positive)
- `ROT-002` (99): target_ambig_broken — basename matches multiple, link broken
- `ROT-001` (88): target_missing — no candidate file exists anywhere
- `ROT-008` (10): placeholder_literal — target is literal 'path'/'url'/template residue

## Hotspots (top 10 files by rot count)

- `dumpster-dive/from-github/macro-prompt-world/disparate-md-documentation/session_gone_sterile_issue_Handover_discernment.md` — 140 entries
- `docs/archive/reports/SUMMARY.md` — 85 entries
- `dumpster-dive/protocols/CROSS_REFERENCE_STANDARD.md` — 20 entries
- `docs/protocols/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md` — 15 entries
- `dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md` — 12 entries
- `dumpster-dive/archive/sessions_2026-01/session_resumption_chthonic_progress.md` — 11 entries
- `dumpster-dive/forge/furnace/docs/ADR_RECOVERED.md` — 10 entries
- `dumpster-dive/forge/tempered/docs/ADR_RECOVERED.md` — 10 entries
- `codex/codex-session-logs/archive/copilot-instructions-copy.archived.md` — 8 entries
- `.gemini/extensions/chthonic-archive-sync/skills/.system/skill-creator/SKILL.md` — 6 entries

## Clusters (derived patterns)

- `CLUSTER-001` `dumpster-dive/from-github/macro-prompt-world/disparate-md-documentation/session_gone_sterile_issue_Handover_discernment.md` — 140 entries. agent dump candidate — consider archive or delint exclusion
- `CLUSTER-001` `docs/archive/reports/SUMMARY.md` — 85 entries. agent dump candidate — consider archive or delint exclusion
- `CLUSTER-002` target `../../../intake/overnight-intelligence/2026-02-11T02-19-33/report.md` — 20 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `dumpster-dive/forge/furnace/docs/ADR_RECOVERED.md`, `dumpster-dive/forge/furnace/docs/ADR_RECOVERED.md`, `dumpster-dive/forge/furnace/docs/ADR_RECOVERED.md`, `dumpster-dive/forge/furnace/docs/ADR_RECOVERED.md`, `dumpster-dive/forge/furnace/docs/ADR_RECOVERED.md`
- `CLUSTER-002` target `[^"\']+` — 6 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `docs/reference/TYPESCRIPT_INTELLIGENCE_ENHANCEMENT.md`, `docs/reference/TYPESCRIPT_INTELLIGENCE_ENHANCEMENT.md`, `docs/reference/TYPESCRIPT_INTELLIGENCE_ENHANCEMENT.md`, `docs/reference/TYPESCRIPT_INTELLIGENCE_ENHANCEMENT.md`, `docs/reference/TYPESCRIPT_INTELLIGENCE_ENHANCEMENT.md`
- `CLUSTER-002` target `../claude/mailbox/FORGE_PIPELINE_DEV_PLAN.md` — 4 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `docs/protocols/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md`, `docs/protocols/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md`, `docs/protocols/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md`, `docs/protocols/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md`
- `CLUSTER-002` target `copilot-instructions.md` — 3 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `.github/INTEGRATION_MAP.md`, `.github/SESSION_RESUME.md`, `.github/SSOT_EVOLUTION_1.0_TO_1.5_BLUEPRINT.md`, `.github/STRUCTURAL_INTEGRITY_ANALYSIS.md`, `.github/VALIDATION_REPORT.md`
- `CLUSTER-002` target `../claude/mailbox/BOUNTY_00000031_STEWARD_AUDIT.md` — 3 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `docs/protocols/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md`, `docs/protocols/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md`, `docs/protocols/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md`
- `CLUSTER-002` target `[^\'"]+` — 3 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `dumpster-dive/archive/sessions_2026-01/AUTONOMOUS_SESSION_3_MISSION_REPORT.md`, `dumpster-dive/archive/sessions_2026-01/AUTONOMOUS_SESSION_3_MISSION_REPORT.md`, `dumpster-dive/archive/sessions_2026-01/AUTONOMOUS_SESSION_3_MISSION_REPORT.md`

## Top 30 entries by priority

### [MEDIUM / ROT-001 / broken_no_known_target] `.github/agents/IronMaiden.agent.md:L19`

- Target: `../../codex/codex-session-logs/archive/The-Iron-Maiden-(SSOT`
- Source last touched: 2026-05-13T06:25:25+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `claude/mailbox/copilot-instructions.archive.md:L3`

- Target: `copilot-instructions.md`
- Candidate matches: `.github/copilot-instructions.md`, `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`
- Source last touched: 2026-05-13T07:12:29+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `claude/mailbox/copilot-instructions.archive.md:L10`

- Target: `copilot-instructions.md`
- Candidate matches: `.github/copilot-instructions.md`, `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`
- Source last touched: 2026-05-13T07:12:29+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `claude/mailbox/copilot-instructions.archive.md:L12`

- Target: `copilot-instructions.md`
- Candidate matches: `.github/copilot-instructions.md`, `claude/mailbox/briefcase/extracted/.github/copilot-instructions.md`
- Source last touched: 2026-05-13T07:12:29+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `codex/codex-session-logs/archive/copilot-instructions-copy.archived.md:L2731`

- Target: `../dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md`
- Candidate matches: `dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `codex/codex-session-logs/archive/copilot-instructions-copy.archived.md:L3785`

- Target: `instructions/mathematical-engines.reference.md`
- Candidate matches: `.github/instructions/mathematical-engines.reference.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `codex/codex-session-logs/archive/copilot-instructions-copy.archived.md:L6302`

- Target: `../dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md`
- Candidate matches: `dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `codex/codex-session-logs/archive/copilot-instructions-copy.archived.md:L6637`

- Target: `instructions/technical-directives.instructions.md`
- Candidate matches: `.github/instructions/technical-directives.instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `codex/codex-session-logs/archive/copilot-instructions-copy.archived.md:L6646`

- Target: `../docs/protocols/CROSS_REFERENCE_TRIPTYCH.md`
- Candidate matches: `docs/protocols/CROSS_REFERENCE_TRIPTYCH.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/architecture/CHTHONIC_ARCHIVE_WORLD_TPEF.md:L9825`

- Target: `./The_Chthonic_Archive_World.md`
- Candidate matches: `dumpster-dive/from-github/macro-prompt-world/The_Chthonic_Archive_World.md`, `dumpster-dive/from-github/macro-prompt-world/macro-prompt-world-v2/archive-world/The_Chthonic_Archive_World.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L3`

- Target: `README.md`
- Candidate matches: `.github/prompts/README.md`, `adapters/claudine-v1/README.md`, `adapters/claudine-v1/checkpoints/checkpoint-1500/README.md`, `adapters/claudine-v1/checkpoints/checkpoint-2000/README.md`, `birdcage/README.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L7`

- Target: `DEVELOPMENT_STATE.md`
- Candidate matches: `docs/archive/sessions/DEVELOPMENT_STATE.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L10`

- Target: `architecture/CHTHONIC_ARCHIVE_WORLD_TPEF.md`
- Candidate matches: `docs/architecture/CHTHONIC_ARCHIVE_WORLD_TPEF.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L11`

- Target: `architecture/MILF_TRINITY_CHROMATIC_LINEAGE.md`
- Candidate matches: `docs/architecture/MILF_TRINITY_CHROMATIC_LINEAGE.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L15`

- Target: `design/GENRE_EXTRACTION.md`
- Candidate matches: `docs/design/GENRE_EXTRACTION.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L22`

- Target: `EXECUTION_CONTRACT.md`
- Candidate matches: `docs/ops/EXECUTION_CONTRACT.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L23`

- Target: `PROBE_CONTRACT.md`
- Candidate matches: `docs/ops/PROBE_CONTRACT.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L24`

- Target: `PWSH_RULES.md`
- Candidate matches: `PWSH_RULES.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L25`

- Target: `CLI_EDITING_POLICY.md`
- Candidate matches: `docs/ops/CLI_EDITING_POLICY.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L26`

- Target: `SSOTIFICATION_METHODOLOGY.md`
- Candidate matches: `docs/protocols/SSOTIFICATION_METHODOLOGY.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L30`

- Target: `protocols/ANCHOR_SIGNAL_PROTOCOL.md`
- Candidate matches: `docs/protocols/ANCHOR_SIGNAL_PROTOCOL.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L31`

- Target: `protocols/CROSS_REFERENCE_TRIPTYCH.md`
- Candidate matches: `docs/protocols/CROSS_REFERENCE_TRIPTYCH.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L32`

- Target: `protocols/CROSS_TIER_MATRIX.md`
- Candidate matches: `docs/protocols/CROSS_TIER_MATRIX.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L33`

- Target: `protocols/TEA_EXAMPLES.md`
- Candidate matches: `docs/protocols/TEA_EXAMPLES.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L35`

- Target: `protocols/LATEST_STABLE_POLICY.md`
- Candidate matches: `docs/protocols/LATEST_STABLE_POLICY.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L39`

- Target: `DCRP_SYNTHESIS.md`
- Candidate matches: `docs/reference/DCRP_SYNTHESIS.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L43`

- Target: `MCP_AUTONOMOUS_PREREQUISITES.md`
- Candidate matches: `docs/ops/MCP_AUTONOMOUS_PREREQUISITES.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L44`

- Target: `MCP_SERVER_TEMPLATE.md`
- Candidate matches: `docs/ops/MCP_SERVER_TEMPLATE.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L45`

- Target: `MCP_USER_WORKFLOWS.md`
- Candidate matches: `docs/ops/MCP_USER_WORKFLOWS.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/archive/reports/SUMMARY.md:L46`

- Target: `SESSION_BOOTSTRAP_SPEC.md`
- Candidate matches: `docs/archive/sessions/SESSION_BOOTSTRAP_SPEC.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com
