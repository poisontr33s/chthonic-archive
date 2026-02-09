---
type: claude-code-setup
created: 2026-02-09
scope: claude-centricity (cost-aware)
status: active
---

# Claude Code: Cost-Aware Project Setup (Parity With Codex Lane)

## Intent

Claude Code Opus is expensive. This repo is structured so Claude Code can operate mostly as a **deterministic shell around existing lanes**, using cheaper models by default and delegating to subagents only when needed.

## What Was Added / Changed

### 1) Project Settings

File: `.claude/settings.json`

- Default model changed from `opus` to `sonnet`
- `alwaysThinkingEnabled`: `false`
- `effortLevel`: `medium`
- Added hooks:
  - `SessionStart`: prints canonical path + command policy reminders
  - `PreToolUse`: blocks edits to likely secret/auth files
  - `PostToolUse`: runs lightweight repo invariants after writes/edits

### 2) Hooks (PowerShell)

Directory: `.claude/hooks/`

- `.claude/hooks/session_start_context.ps1`
  - Prints canonical paths + “how to run gates” reminders
- `.claude/hooks/protect_secrets.ps1`
  - Fails closed on edits to `.env`, `api_pool.json`, `.codex/config.toml`
- `.claude/hooks/post_write_verify.ps1`
  - Runs:
    - `uv run scripts/check_python_policy.py`
    - `uv run scripts/check_mailbox_layout.py`

### 3) Subagents (Cost Control + Determinism)

Directory: `.claude/agents/`

- `.claude/agents/trainstop-runner.md` (model: `haiku`)
  - Runs trainstop lanes and reports artifacts
- `.claude/agents/mcp-auth-doctor.md` (model: `haiku`)
  - Validates MCP/auth readiness via existing lanes + artifacts
- `.claude/agents/parity-auditor.md` (model: `sonnet`)
  - Runs cross-audits and fixes contract-level issues

## “Claude-Centricity” Operating Pattern (Minimal Opus)

1. Prefer hooks + lanes for determinism and low token spend.
2. Use `haiku` subagents for lane execution + summarization.
3. Only use `opus` when a task requires deep synthesis beyond what artifacts provide.

## Commands (Repo-Native)

Run parity gates:

```powershell
pwsh -NoProfile -File scripts/run_cross_audit.ps1
```

Run trainstop “all”:

```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target codex --lane all --lane-config .codex/skills/trainstop-orchestrator/lane_config.v1.json
```

Run HF/MCP readiness:

```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target codex --lane mcp-auth --lane-config .codex/skills/trainstop-orchestrator/lane_config.v1.json
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target codex --lane hf-prep --lane-config .codex/skills/trainstop-orchestrator/lane_config.v1.json
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target codex --lane mcp-client-emitter --lane-config .codex/skills/trainstop-orchestrator/lane_config.v1.json
```

## Notes

- Secret tokens remain SSOT in `C:\\Users\\erdno\\.chthonic\\api_pool.json` and should never be edited by agents.
- This setup is meant to keep Claude Code in “operator mode” rather than “inventor mode”.

