# Co-Supplementary Protocol Learnings

## Sonnet Dispatch Improvements (leveling up)

### Session 1 (2026-03-13): SSOT Structural Audit
- **What worked**: Giving Sonnet the raw data (full section text) + compound task (independent audit + evaluate Opus findings)
- **What Sonnet caught that Opus missed**: Off-by-one parent/child mismatches (A3-A6), orphaned block (A5), systemic diagnosis (A6) — deep structural pattern recognition
- **What Opus got wrong**: T1/T2 EDFA gaps were FALSE POSITIVES — stopped at "Architectural Manifestation" summary paragraphs without reading through to per-body-part EDFA blocks
- **Sonnet's scoring of Opus**: 60% completeness, 60% accuracy — brutal but fair
- **Key lesson**: Verify downstream before reporting gaps. Search for the actual content (EDFA/FA⁵ keywords) rather than inferring absence from section titles.

### Dispatch Pattern That Worked
1. Opus generates 5 primary findings internally (holds them, does NOT include in prompt)
2. Subagent prompt contains: raw data excerpt + TASK 1 (independent blind audit) + TASK 2 (evaluate Opus's findings, listed in prompt)
3. Sonnet performs independent audit FIRST, then evaluates — catching both what Opus missed AND what Opus got wrong
4. Opus synthesizes: accepts Sonnet's corrections, produces merged findings list

### What to improve next time
- Include MORE raw data in subagent prompt — Sonnet is thorough when given data
- Be explicit: "Search for X within lines Y-Z before claiming absence"
- Run Phase 1 fixes first (quick wins like cross-refs), then Phase 2 (cascade) — reduces cognitive load
- The "hidden subsection" gotcha: bold-text numbered subsections (10.6.1-7) inside a heading-level parent (§10.7) were missed in both initial passes — only found during fix execution when verifying parent-child relationships

## Skill Authoring (2026-04-19): chthonic-archive .claude/.codex lanes

### Structural standard — non-trivial skills are folders, not single files
- Skills with scripts/references/assets use the full folder layout: `SKILL.md` + `agents/openai.yaml` + `assets/{small,large}.svg`
- Flat single-file is only valid for pure-protocol stubs (decision-razor style). Check existing peers before choosing layout.

### Two openai.yaml schemas — do NOT conflate
- Claude-side (`openai.yaml`): `interface:` schema — `display_name`, `short_description`, `icon_small`, `icon_large`, `brand_color`
- Codex-side (`openai.yaml`): runtime schema — `version`, `name`, `provider`, `models.default`, `policy.allowed_tools`
- They are structurally different. Write each from the correct schema.

### Cross-lane parity rule
- When the user edits one side (claude or codex), sync the other immediately in the same pass — name, triggers, all sections.
- Never let the two SKILL.md files drift on content that should be equivalent.

### Prompt bleeding — never name foreign agents in a skill
- Do not mention agent names (e.g. other synthesis agents) inside a skill that is about a different agent. It causes context bleed when the skill is loaded.
- Anti-patterns table: include only what the skill's own agent must NOT do. No cross-agent references unless the skill explicitly manages routing.
