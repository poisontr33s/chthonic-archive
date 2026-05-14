# Git rot index digest

Generated: 2026-05-14T06:10:14.285596+00:00
Source: `manifest/git_rot_index.json` (regenerate via `uv run scripts/git_rot_index.py`)

## Summary

- Tracked markdown files: 1117
- Rot entries: 24
- Historical renames in repo: 757

### By category

- `broken_no_known_target`: 9
- `line_anchor_stale`: 9
- `anchor_missing`: 5
- `ambig_truly_ambiguous`: 1

### By priority

- `medium`: 17
- `low`: 7

### By code (grouped by gitological level)

**L1 — SURFACE  — raw symptoms visible at the link site**

- `ROT-001` (9): target_missing — no candidate file exists anywhere
- `ROT-002` (1): target_ambig_broken — basename matches multiple, link broken

**L3 — ANCHOR   — positional / semantic reference alignment**

- `ROT-007` (9): line_anchor_stale — #LNNN out of range for current file
- `ROT-006` (5): anchor_missing — file exists, #anchor doesn't


## Hotspots (top 10 files by rot count)

- `dumpster-dive/archive/sessions_2026-01/session_resumption_chthonic_progress.md` — 11 entries
- `dumpster-dive/intake/templates/TRIUMVIRATE_TASK_TEMPLATE.md` — 8 entries
- `WET_PAPER_TO_GOLD_METHODOLOGY.md` — 6 entries
- `.github/instructions/reference-appendix.reference.md` — 5 entries
- `dumpster-dive/archive/docs-sessions/SESSION_2026-01-17_CLEANUP.md` — 4 entries
- `dumpster-dive/forge/quench/README.md` — 4 entries
- `dumpster-dive/protocols/FORGE_CIRCULATION_PROTOCOL.md` — 4 entries
- `docs/design/SFS_WPTG_ITERATION_PLAN.md` — 3 entries
- `dumpster-dive/CIRCULATION_DIAGRAM.md` — 3 entries
- `dumpster-dive/README.md` — 3 entries

## Top 30 entries by priority

### [MEDIUM / ROT-001 / broken_no_known_target] `.github/agents/IronMaiden.agent.md:L19`

- Target: `../../codex/codex-session-logs/archive/The-Iron-Maiden-(SSOT`
- Source last touched: 2026-05-13T06:25:25+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/agent-priority-protocol.md:L4`

- Target: `../copilot-instructions.md#L6812`
- Resolves to: `.github/copilot-instructions.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/agent-priority-protocol.md:L10`

- Target: `../copilot-instructions.md#L6812`
- Resolves to: `.github/copilot-instructions.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/asc-entity-generation.reference.md:L47`

- Target: `../copilot-instructions.md#L2443`
- Resolves to: `.github/copilot-instructions.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/behavioral-scenarios.reference.md:L17`

- Target: `../copilot-instructions.md#L3789`
- Resolves to: `.github/copilot-instructions.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/dcrp-operational-guide.md:L3`

- Target: `../copilot-instructions.md#L6643`
- Resolves to: `.github/copilot-instructions.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/dcrp-operational-guide.md:L9`

- Target: `../copilot-instructions.md#L6643`
- Resolves to: `.github/copilot-instructions.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/dev-conventions.reference.md:L17`

- Target: `../copilot-instructions.md#L6634`
- Resolves to: `.github/copilot-instructions.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/magistra-logic.reference.md:L17`

- Target: `../copilot-instructions.md#L4780`
- Resolves to: `.github/copilot-instructions.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-007 / line_anchor_stale] `.github/instructions/magistra-logic.reference.md:L18`

- Target: `../copilot-instructions.md#L6500`
- Resolves to: `.github/copilot-instructions.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-006 / anchor_missing] `docs/architecture/SESSION_CORPUS.md:L304`

- Target: `VAMPIRISM_SATELLITES.md#nightly-escapades`
- Resolves to: `docs/architecture/VAMPIRISM_SATELLITES.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-05-05T02:32:12+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-002 / ambig_truly_ambiguous] `docs/design/SFS_WPTG_ITERATION_PLAN.md:L639`

- Target: `../../.claude/skills/sfa/SKILL.md`
- Candidate matches: `.claude/skills/artifact-upcycle/SKILL.md`, `.claude/skills/artifact-upcycle/artifact-upcycle/SKILL.md`, `.claude/skills/conceptualize/SKILL.md`, `.claude/skills/conceptualize/conceptualize/SKILL.md`, `.claude/skills/decision-razor/SKILL.md`
- Source last touched: 2026-05-13T07:12:29+02:00 by erdnorddd@gmail.com

### [MEDIUM / ROT-006 / anchor_missing] `docs/frameworks/ankh/ANKH_GENERATIVE_ENGINE.md:L110`

- Target: `./ANKH_FOUNDATIONAL_AXIOMS.md#dynamic-altitude-focal-point-dafp--the-alchemists-scope`
- Resolves to: `docs/frameworks/ankh/ANKH_FOUNDATIONAL_AXIOMS.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-006 / anchor_missing] `docs/frameworks/ankh/ANKH_GENERATIVE_ENGINE.md:L123`

- Target: `./ANKH_FOUNDATIONAL_AXIOMS.md#prism--prismatic-reflection-illuminating-spectral-metamorphosis`
- Resolves to: `docs/frameworks/ankh/ANKH_FOUNDATIONAL_AXIOMS.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-001 / broken_no_known_target] `docs/reference/HANDOFF0001.md:L44`

- Target: `instructions/xyz.instructions.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-006 / anchor_missing] `dumpster-dive/protocols/FORGE_CIRCULATION_PROTOCOL.md:L560`

- Target: `../../.github/copilot-instructions.md#section-4512`
- Resolves to: `.github/copilot-instructions.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [MEDIUM / ROT-006 / anchor_missing] `dumpster-dive/protocols/FORGE_CIRCULATION_PROTOCOL.md:L561`

- Target: `../../.github/copilot-instructions.md#section-4511`
- Resolves to: `.github/copilot-instructions.md` (file resolves; anchor missing/stale)
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [LOW / ROT-001 / broken_no_known_target] `claude/mailbox/archive/series/SESSION_HANDOFF/SESSION_HANDOFF_2026_03_01_WPTG_SFS_LANE_TRANSFER_TO_CODEX.md:L48`

- Target: `../../extensions/chthonic-archive/package.json`
- Source last touched: 2026-05-13T07:12:29+02:00 by erdnorddd@gmail.com

### [LOW / ROT-001 / broken_no_known_target] `claude/mailbox/archive/series/SESSION_HANDOFF/SESSION_HANDOFF_2026_03_01_WPTG_SFS_LANE_TRANSFER_TO_CODEX.md:L57`

- Target: `../../.vscode/settings.json`
- Source last touched: 2026-05-13T07:12:29+02:00 by erdnorddd@gmail.com

### [LOW / ROT-001 / broken_no_known_target] `codex/codex-session-logs/archive/MILF-Core-META.md:L120`

- Target: `The-Iron-Maiden-(SSOT`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [LOW / ROT-001 / broken_no_known_target] `codex/codex-session-logs/archive/MILF-Core-META.md:L121`

- Target: `The-Iron-Maiden-(SSOT`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [LOW / ROT-001 / broken_no_known_target] `docs/archive/reports/TRUE_MISSING_FILES_REVIEW.md:L229`

- Target: `docs/FILE.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [LOW / ROT-001 / broken_no_known_target] `docs/archive/sessions/DEVELOPMENT_STATE.md:L350`

- Target: `../logs/sessions/session_2025-12-31_0746_vscode-extension-debug.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com

### [LOW / ROT-001 / broken_no_known_target] `dumpster-dive/from-github/macro-prompt-world/even-more-disparate-extranerrous-md-documentation/in-a-possible-future-when-other-stuff-is-done/README.md:L130`

- Target: `../frameworks/nextjs.md`
- Source last touched: 2026-04-28T05:23:27+02:00 by vscode@users.noreply.github.com
