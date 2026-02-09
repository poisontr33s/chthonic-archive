---
type: research
created: 2026-02-09
scope: claude-code (agents, hooks, plugins, mcp, sdk) -> parity with codex lane
status: active
---

# Claude Code: Hierarchical Research (Parity Expansion Plan)

## Intent

Scale Claude Code to match the repo’s current “Codex lane” capabilities without degenerating into meta loops:

- Deterministic automation first (hooks + lanes + artifacts)
- Then extensibility (agents/subagents + MCP)
- Then packaging/portability (plugins)
- Then programmatic scaling (headless + Agent SDK)

## Layer 1: Settings (project-level SSOT)

Claude Code supports a hierarchical `settings.json` mechanism:

- User: `~/.claude/settings.json`
- Project: `.claude/settings.json` (committed)
- Local project overrides: `.claude/settings.local.json` (gitignored)

Relevant settings keys include `model`, `hooks`, `permissions`, and MCP approvals.

Repo implication: put shareable defaults in `.claude/settings.json`, keep personal/cost overrides in `.claude/settings.local.json`.

## Layer 2: Hooks (determinism injector)

Hooks are the key to “Claude behaves like the repo contract even when tired”.

Use cases that matter here:

- SessionStart: inject canonical paths + command policy
- PermissionRequest: fail closed on secret/auth edits
- PostToolUse: run fast invariants after writes/edits

Repo implication: hooks should call existing gates (`uv run scripts/check_python_policy.py`, `uv run scripts/check_mailbox_layout.py`) rather than invent new ones.

## Layer 3: Subagents (segmentation, parallelism, cost control)

Subagents are the correct unit of specialization:

- “runner” agents: execute lanes and summarize artifacts
- “doctor” agents: validate MCP/auth readiness and explain failures
- “auditor” agents: run parity gates and fix contract-level issues only

Repo implication: treat subagents as specialized wrappers around the existing lanes and artifact schema, not independent inventors.

## Layer 4: MCP (tools/data)

MCP support is the correct way to share tool integrations between Codex and Claude:

- Project MCP config is already in `.mcp.json`
- Claude Code can selectively approve servers from `.mcp.json`

Repo implication: the authoritative proof of “MCP works” is the repo artifacts:

- `artifacts/mcp_run_validation_*.json` (local MCP)
- `codex/mailbox/HF_MCP_TOOLS_LATEST.json` + `artifacts/hf_mcp_tools_*.json` (HF MCP)

## Layer 5: Plugins (packaging)

Plugins are the right way to distribute:

- agents
- skills/commands
- hooks

Repo implication: do not convert to plugin format until `.claude/` stabilizes and the parity gates are green for multiple cycles.

## Layer 6: Headless (automation/CI)

Claude Code supports a headless mode via the `claude` CLI:

- `claude -p "..."`
- `--allowedTools ...`
- `--output-format json|stream-json`
- `--resume <session-id>`

Repo implication: use headless mode to produce mailbox artifacts deterministically (same way train lanes do).

## Layer 7: Claude Agent SDK (programmable Claude Code loop)

Claude’s Agent SDK (Python + TypeScript) is “Claude Code as a library”:

- Built-in tool execution loop: read/edit/run commands without you writing the tool loop.
- Streamed messages via an async iterator.

Repo implication: the Agent SDK is the way to create a *Claude-side orchestrator* that mirrors `.codex/skills/trainstop-orchestrator/scripts/orchestrate.py`, but only after the hooks + subagents posture is stable.

## Parity Strategy (No Stalemate)

1. Hooks enforce invariants + secret protection automatically.
2. Subagents wrap existing repo lanes (cheap when possible; Opus for synthesis).
3. MCP is validated via artifacts, not UI vibes.
4. Headless/SDK comes last, when you want CI and “Claude as a worker process”.

