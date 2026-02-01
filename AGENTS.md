# AGENTS.md

This file provides guidance to OpenAI Codex when working with code in this repository.

> **Shared Config:** See [AGENT_COMMON.md](AGENT_COMMON.md) for execution invariants, commands, architecture, and triad references.

---

## Codex-Specific Notes

- **Workspace Lock:** Do not use `-C` to change directories unless explicitly instructed.
- **Workspace config:** `.codex/config.toml` (this workspace)
- **Global auth config:** `~/.codex/config.toml`
- Do not modify auth settings — they are workspace-locked.

## Codex Session Artifacts

- `codex/NEXT.md` - Session waypoint and next steps
- `codex/SESSION_HANDOFF_*.md` - Inter-agent handoff documents
- `codex/gemini_mcp_status_report.md` - MCP status tracking
