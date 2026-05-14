# Git rot index digest

Generated: 2026-05-13T10:54:50.266477+00:00
Source: `manifest/git_rot_index.json` (regenerate via `uv run scripts/git_rot_index.py`)

## Summary

- Tracked markdown files: 1114
- Rot entries: 66
- Historical renames in repo: 757

### By category

- `line_anchor_stale`: 23
- `ambig_truly_ambiguous`: 16
- `broken_no_known_target`: 12
- `placeholder_literal`: 10
- `anchor_missing`: 5

### By priority

- `medium`: 46
- `low`: 20

### By code (grouped by gitological level)

**L1 — SURFACE  — raw symptoms visible at the link site**

- `ROT-002` (16): target_ambig_broken — basename matches multiple, link broken
- `ROT-001` (12): target_missing — no candidate file exists anywhere
- `ROT-008` (10): placeholder_literal — target is literal 'path'/'url'/template residue

**L3 — ANCHOR   — positional / semantic reference alignment**

- `ROT-007` (23): line_anchor_stale — #LNNN out of range for current file
- `ROT-006` (5): anchor_missing — file exists, #anchor doesn't


## Hotspots (top 10 files by rot count)

- `dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md` — 12 entries
- `dumpster-dive/archive/sessions_2026-01/session_resumption_chthonic_progress.md` — 11 entries
- `codex/codex-session-logs/archive/copilot-instructions-copy.archived.md` — 8 entries
- `WET_PAPER_TO_GOLD_METHODOLOGY.md` — 6 entries
- `docs/reference/FAF_CHTHONIC_EXTENSION_PHASE3_HANDOFF.md` — 6 entries
- `.github/instructions/reference-appendix.reference.md` — 5 entries
- `docs/ops/MIGRATION_GUIDE_CHTHONIC_CLI.md` — 4 entries
- `dumpster-dive/CIRCULATION_DIAGRAM.md` — 4 entries
- `dumpster-dive/archive/docs-sessions/SESSION_2026-01-17_CLEANUP.md` — 4 entries
- `dumpster-dive/forge/quench/README.md` — 4 entries

## Clusters (derived patterns)

- `CLUSTER-002` target `copilot-instructions.md` — 3 refs. missing file referenced widely — confirm intent (typo? deleted?)
  sample: `.github/INTEGRATION_MAP.md`, `.github/SESSION_RESUME.md`, `.github/SSOT_EVOLUTION_1.0_TO_1.5_BLUEPRINT.md`, `.github/STRUCTURAL_INTEGRITY_ANALYSIS.md`, `.github/VALIDATION_REPORT.md`

## Top 30 entries by priority

### [MEDIUM / ROT-001 / broken_no_known_target] `.github/agents/IronMaiden.agent.md:L19`

- Target: `../../codex/codex-session-logs/archive/The-Iron-Maiden-(SSOT`
- Source last touched: 2026-05-13T06:25:25+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/agent-priority-protocol.md:L4`

- Target: `../copilot-instructions.md#L6812`
- Resolves to: `.github/copilot-instructions.md` (false positive — link works)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/agent-priority-protocol.md:L10`

- Target: `../copilot-instructions.md#L6812`
- Resolves to: `.github/copilot-instructions.md` (false positive — link works)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/asc-entity-generation.reference.md:L47`

- Target: `../copilot-instructions.md#L2443`
- Resolves to: `.github/copilot-instructions.md` (false positive — link works)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/behavioral-scenarios.reference.md:L17`

- Target: `../copilot-instructions.md#L3789`
- Resolves to: `.github/copilot-instructions.md` (false positive — link works)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/dcrp-operational-guide.md:L3`

- Target: `../copilot-instructions.md#L6643`
- Resolves to: `.github/copilot-instructions.md` (false positive — link works)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/dcrp-operational-guide.md:L9`

- Target: `../copilot-instructions.md#L6643`
- Resolves to: `.github/copilot-instructions.md` (false positive — link works)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/dev-conventions.reference.md:L17`

- Target: `../copilot-instructions.md#L6634`
- Resolves to: `.github/copilot-instructions.md` (false positive — link works)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/magistra-logic.reference.md:L17`

- Target: `../copilot-instructions.md#L4780`
- Resolves to: `.github/copilot-instructions.md` (false positive — link works)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/magistra-logic.reference.md:L18`

- Target: `../copilot-instructions.md#L6500`
- Resolves to: `.github/copilot-instructions.md` (false positive — link works)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/reference-appendix.reference.md:L18`

- Target: `../copilot-instructions.md#L6991`
- Resolves to: `.github/copilot-instructions.md` (false positive — link works)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/reference-appendix.reference.md:L35`

- Target: `../copilot-instructions.md#L7130`
- Resolves to: `.github/copilot-instructions.md` (false positive — link works)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/reference-appendix.reference.md:L47`

- Target: `../copilot-instructions.md#L7220`
- Resolves to: `.github/copilot-instructions.md` (false positive — link works)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/reference-appendix.reference.md:L56`

- Target: `../copilot-instructions.md#L7279`
- Resolves to: `.github/copilot-instructions.md` (false positive — link works)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/reference-appendix.reference.md:L64`

- Target: `../copilot-instructions.md#L7331`
- Resolves to: `.github/copilot-instructions.md` (false positive — link works)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

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

### [MEDIUM / ROT-006 / anchor_missing] `docs/architecture/SESSION_CORPUS.md:L304`

- Target: `VAMPIRISM_SATELLITES.md#nightly-escapades`
- Resolves to: `docs/architecture/VAMPIRISM_SATELLITES.md` (false positive — link works)
- Source last touched: 2026-05-05T02:32:12+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/design/SFS_WPTG_ITERATION_PLAN.md:L639`

- Target: `../../.claude/skills/sfa/SKILL.md`
- Candidate matches: `.claude/skills/artifact-upcycle/SKILL.md`, `.claude/skills/artifact-upcycle/artifact-upcycle/SKILL.md`, `.claude/skills/conceptualize/SKILL.md`, `.claude/skills/conceptualize/conceptualize/SKILL.md`, `.claude/skills/decision-razor/SKILL.md`
- Source last touched: 2026-05-13T07:12:29+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-006 / anchor_missing] `docs/frameworks/ankh/ANKH_GENERATIVE_ENGINE.md:L110`

- Target: `./ANKH_FOUNDATIONAL_AXIOMS.md#dynamic-altitude-focal-point-dafp--the-alchemists-scope`
- Resolves to: `docs/frameworks/ankh/ANKH_FOUNDATIONAL_AXIOMS.md` (false positive — link works)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-006 / anchor_missing] `docs/frameworks/ankh/ANKH_GENERATIVE_ENGINE.md:L123`

- Target: `./ANKH_FOUNDATIONAL_AXIOMS.md#prism--prismatic-reflection-illuminating-spectral-metamorphosis`
- Resolves to: `docs/frameworks/ankh/ANKH_FOUNDATIONAL_AXIOMS.md` (false positive — link works)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/ops/MIGRATION_GUIDE_CHTHONIC_CLI.md:L395`

- Target: `../scripts/README.md`
- Candidate matches: `.github/prompts/README.md`, `adapters/claudine-v1/README.md`, `adapters/claudine-v1/checkpoints/checkpoint-1500/README.md`, `adapters/claudine-v1/checkpoints/checkpoint-2000/README.md`, `birdcage/README.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/ops/MIGRATION_GUIDE_CHTHONIC_CLI.md:L396`

- Target: `PHASE_3_TEST_REPORT.md`
- Candidate matches: `docs/archive/reports/PHASE_3_TEST_REPORT.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/ops/MIGRATION_GUIDE_CHTHONIC_CLI.md:L397`

- Target: `TOOL_CONSOLIDATION_ROADMAP.md`
- Candidate matches: `docs/protocols/TOOL_CONSOLIDATION_ROADMAP.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com
