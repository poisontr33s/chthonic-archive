---
type: report
from: codex
to: codex
created: 2026-02-05
priority: high
source: https://code.claude.com/docs/en/skills
---

# Claude Code Skills Cross-Reference (Validation for Handoff)

This report validates our Claude-side changes against the official Claude Code skills specification and lists any mismatches.

## Spec Highlights (from docs)
- `SKILL.md` is required; other files are optional.
- Frontmatter fields supported: `name`, `description`, `argument-hint`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `model`, `context`, `agent`, `hooks`.
- `$ARGUMENTS`, `$ARGUMENTS[N]`, `$N`, and `${CLAUDE_SESSION_ID}` are supported substitutions.
- `disable-model-invocation: true` prevents Claude auto-loading a skill.
- `allowed-tools` uses Claude tool names (examples show `Read`, `Grep`, `Glob`).
- Skills live under `.claude/skills/` (project) or `~/.claude/skills/` (user).

## Validation Against Our Changes
1. **Claude mailbox skill** at `.claude/skills/mailbox-handoff/SKILL.md`
   - Uses `allowed-tools: ["Read", "Write", "Glob", "Grep"]` ✅
   - Uses `disable-model-invocation: true` ✅
   - Uses `user-invocable: true` ✅
   - Uses `argument-hint` ✅
   - Uses `$ARGUMENTS` in body ✅

2. **Converted Claude skills** under `.claude/skills/<skill>`
   - Each contains `SKILL.md` ✅
   - Frontmatter includes only `name` and `description` ✅ (valid per spec)
   - No invalid frontmatter fields detected ✅

## Notes / Constraints
- Only the mailbox skill is tool-scoped; other converted skills do not set `allowed-tools`. This is valid and conservative.
- If tighter tool scoping is desired per skill, we should add `allowed-tools` explicitly.

## Actionable Deltas
- None required for spec compliance.

---

Report Hash: `CLAUDE_SKILLS_SPEC_VALIDATION_V1`
