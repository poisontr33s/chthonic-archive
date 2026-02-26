---
type: skill-comparative-review
generated_on_utc: 2026-02-26T02:05:00Z
scope: codex-skills
exclusions:
  - openai-docs
  - imagegen
  - sora
  - .system/skill-creator
  - .system/skill-installer
scoring_scale: 1-10
---

# Codex Skill Comparative Review (Session Baseline)

## Method
- Baseline: current session objective (`depth specialization`, `handoff continuity`, `low-noise delegation`).
- Model: `0.35*operational_rigor + 0.35*specialization_depth + 0.30*session_alignment - overlap_penalty`.
- Operational rigor uses script presence, command surface, references, and instruction maturity.
- Session alignment rewards handoff/mailbox/session/triage/audit/gate/snapshot relevance.
- Overlap penalty reduces score for meta-wrapper duplication.

## Distribution
- `A-keep-core`: 3
- `B-keep-refine`: 6
- `C-merge-candidate`: 5
- `D-archive-or-fuse`: 9

## Full 1-10 Ranking

| Rank | Skill | Score | Band |
|------|-------|-------|------|
| 1 | mailbox-handoff | 9.93 | A-keep-core |
| 2 | skill-polisher | 8.93 | A-keep-core |
| 3 | trainstop-orchestrator | 8.73 | A-keep-core |
| 4 | scm-triage | 8.11 | B-keep-refine |
| 5 | ingest-research | 7.83 | B-keep-refine |
| 6 | toolchain-doctor | 7.78 | B-keep-refine |
| 7 | artifact-upcycle | 7.54 | B-keep-refine |
| 8 | script-envelope | 7.52 | B-keep-refine |
| 9 | codekiller-remediation-gate | 7.50 | B-keep-refine |
| 10 | gh-mcp-autonomy | 6.07 | C-merge-candidate |
| 11 | gh-fix-ci | 6.06 | C-merge-candidate |
| 12 | session-resumer | 5.74 | C-merge-candidate |
| 13 | python-header-canon | 5.63 | C-merge-candidate |
| 14 | postman | 5.54 | C-merge-candidate |
| 15 | conceptualize | 5.28 | D-archive-or-fuse |
| 16 | iron-maiden-runtime | 5.00 | D-archive-or-fuse |
| 17 | gh-address-comments | 4.94 | D-archive-or-fuse |
| 18 | api-manager | 4.61 | D-archive-or-fuse |
| 19 | dumpster-upcycler | 3.99 | D-archive-or-fuse |
| 20 | meta-polisher-validator | 3.40 | D-archive-or-fuse |
| 21 | decision-razor | 2.96 | D-archive-or-fuse |
| 22 | claude-skill-bridge | 2.09 | D-archive-or-fuse |
| 23 | codex-skill-bridge | 1.03 | D-archive-or-fuse |

## Best Pathway For This Session

1. Core stack (`keep as primary`):
- `mailbox-handoff`
- `scm-triage`
- `skill-polisher`
- `trainstop-orchestrator`

2. Fold-in stack (`merge into core within 1-2 iterations`):
- Merge `session-resumer` + `postman` flows into `mailbox-handoff` as first-class subcommands.
- Fold `python-header-canon` into `script-envelope` (single header normalization authority).
- Fold `gh-address-comments` into `gh-fix-ci` (single PR remediation lane).

3. De-duplicate meta wrappers (`archive/fuse`):
- `codex-skill-bridge`, `claude-skill-bridge`, `meta-polisher-validator` should become one bridge/validator lane or be absorbed by `trainstop-orchestrator`.
- `decision-razor` behavior should be protocol-level execution discipline, not a standalone skill.

4. Cross-lane upgrade note:
- Claude `handoff-loop` (`e926bcab`) materially upgrades validate/gate/ack/obligations.
- Best pathway is to integrate its loop semantics into Codex mailbox tooling, not create parallel wrapper layers.

## Output Artifacts
- Structured baseline audit: `codex/mailbox/SKILL_AUDIT_STRUCTURAL_2026_02_26.json`
- Discriminatory comparative model: `codex/mailbox/SKILL_COMPARATIVE_REVIEW_2026_02_26.json`
