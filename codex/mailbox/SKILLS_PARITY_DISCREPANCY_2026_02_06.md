---
type: parity-report
created: 2026-02-06
scope: codex-vs-claude-skills
---

# Skills Parity Discrepancy Report

## Summary
- Compared `.codex/skills` vs `.claude/skills` by file inventory and per-skill structure.
- Structural parity is partial: skill names align, implementation payload does not.
- Audit status is clean on both sides (`skill_audit.py` passes), but content parity is not equivalent.

## High-Signal Findings
- File count mismatch:
  - `.codex/skills`: 115 files
  - `.claude/skills`: 36 files
- For all 16 shared skill names:
  - `SKILL.md` content differs (`skillmd_equal=False` for all)
  - Codex has `agents/` for all 16
  - Claude has `agents/` for 0
  - Codex has scripts in 8 skills; Claude has scripts in 0
  - Codex has references in 5 skills; Claude has references in 0

## Per-Skill Structural Gap (Codex -> Claude)
- `artifact-upcycle`: missing `agents/`, `scripts/`, `references/`
- `claude-skill-bridge`: missing `agents/`
- `codex-skill-bridge`: missing `agents/`
- `conceptualize`: missing `agents/`, `references/`
- `decision-razor`: missing `agents/`
- `gh-address-comments`: missing `agents/`, `scripts/`
- `gh-fix-ci`: missing `agents/`, `scripts/`
- `gh-mcp-autonomy`: missing `agents/`
- `imagegen`: missing `agents/`, `scripts/`, `references/`
- `mailbox-handoff`: missing `agents/`
- `meta-polisher-validator`: missing `agents/`
- `openai-docs`: missing `agents/`
- `python-header-canon`: missing `agents/`, `scripts/`
- `script-envelope`: missing `agents/`, `scripts/`, `references/`
- `skill-polisher`: missing `agents/`, `scripts/`
- `sora`: missing `agents/`, `scripts/`, `references/`

## Interpretation
- This is expected if Claude-side is kept Claude-native and intentionally minimal.
- This is a discrepancy if your goal is operational equivalence across all cross-run paths.

## Surgical Equalization Paths
1. Metadata parity only (recommended baseline):
- Keep Claude `SKILL.md` Claude-native.
- Add parity manifest per skill describing equivalent command contract.
- Keep scripts centralized in repo `scripts/` and referenced by both sides.

2. Full payload parity (strict equivalence):
- Mirror `scripts/` + `references/` into `.claude/skills/*`.
- Keep Claude frontmatter semantics in `SKILL.md` while sharing script bodies.
- Add CI parity check to fail on drift.

3. Hybrid proxy parity:
- Keep `.claude/skills` lightweight.
- Add bridge hooks from Claude skills to run canonical scripts under `.codex/skills/*/scripts` or root `scripts/`.
- Preserve one implementation source while exposing both IDE flavors.

## Current Recommendation
- Use Path 3 now (least churn, best KISS).
- Add one machine-readable parity map JSON and enforce it via `run_e2e_parity_gate.ps1`.

## Fresh Upstream Baseline (Confirmed)
- Source: Claude Developer Platform release notes overview:
  - https://platform.claude.com/docs/en/release-notes/overview
- Relevant update date: February 5, 2026.
- Confirmed platform changes affecting cross-equivalence design:
  - Claude Opus 4.6 launched.
  - Adaptive thinking is recommended; manual `budget_tokens` path is deprecated on Opus 4.6.
  - `effort` is GA and replaces older thinking-depth controls on new models.
  - Compaction API is available (beta) for long-context workflows.
  - 1M context window is available in beta on Opus 4.6.

## Symmetric Equivalence Implication (Codex/OpenAI <-> Claude/Anthropic)
- Keep skill contracts equivalent at the workflow level, not by forcing identical model knobs.
- Store provider-specific knobs in flavor overlays:
  - OpenAI/Codex overlay: model + reasoning/effort controls per OpenAI surface.
  - Claude overlay: `thinking.type=adaptive`, `effort`, compaction-aware settings.
- Keep a shared parity core (commands, artifacts, mailbox routes, check/audit hooks).
