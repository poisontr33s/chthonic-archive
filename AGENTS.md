# AGENTS.md

This file provides guidance to OpenAI Codex when working with code in this repository.

> **Shared Config:** See [AGENT_COMMON.md](AGENT_COMMON.md) for execution invariants, commands, architecture, and triad references.

---

## Codex-Specific Notes

- **Workspace Lock:** Do not use `-C` to change directories unless explicitly instructed.
- **Workspace config:** `.codex/config.toml` (this workspace)
- **Global auth config:** `~/.codex/config.toml`
- Do not modify auth settings — they are workspace-locked.

## Execution Discipline (Non-Negotiable)

**Anti-Slack Protocol:**
1. **Execute, don't ask.** When a task is clear, DO IT. Report results afterward.
2. **No menu mode.** Never offer "Would you like me to: A, B, or C?" — pick the obvious path.
3. **One clarification max.** If genuinely ambiguous, ask once. Then execute.
4. **Trust handoffs.** If Claude or Gemini handed off a task, execute it without re-confirming.
5. **Post-execution reporting.** Show what you DID, not what you COULD do.

**Config enforcement:** See `[behavior]` and `[triad_sync]` sections in `.codex/config.toml`

## Sleeper's Hold Protocol

**If you respond with an idle acknowledgment that produces no artifact, you MUST immediately generate compensatory creative output.**

Idle phrases that trigger: "ready", "standing by", "awaiting", "confirmed", "understood", "got it", "secured"

When triggered, prefix response with:
```
⚓ SLEEPER'S HOLD ACTIVATED
[Compensatory output here]
Debt paid. Momentum restored.
```

**Full protocol:** See [codex/SLEEPERS_HOLD_PROTOCOL.md](codex/SLEEPERS_HOLD_PROTOCOL.md)

## Codex Session Artifacts

- `codex/NEXT.md` - Session waypoint and next steps
- `codex/SESSION_HANDOFF_*.md` - Inter-agent handoff documents
- `codex/gemini_mcp_status_report.md` - MCP status tracking
