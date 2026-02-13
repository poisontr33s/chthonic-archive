# CLAUDE.md

Shared rules: [AGENT_COMMON.md](AGENT_COMMON.md) (execution invariants, bifurcation, paths, commands).
Shell rules: [PWSH_RULES.md](PWSH_RULES.md). Scripts: [SCRIPTS_README.md](SCRIPTS_README.md).

## Workspace

- `.temple/` = agent infrastructure. `game/` = cRPG content. Ask "TEMPLE or GAME?" before creating files.
- `claude/mailbox/` = inbound handoffs. `codex/mailbox/` = outbound to Codex.
- IDE patch after updates: `.\scripts\patch-claude-insiders.ps1`

## Triad

Claude (protocol/lore) → Codex (structure/enforcement) → Gemini (velocity/batch).

## Compact

Preserve: @SID headers, architecture decisions, cross-refs. Summarize: tool output, searches.
