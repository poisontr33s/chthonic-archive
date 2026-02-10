# SESSION_ERROR_LEARNINGS: claude-ide-harden-2026-02-10

This harvest captures the core error signatures that drove the IDE hardening work and the invariants derived from them.

## Error Signatures (Observed)

- **Claude Code CLI / plugin enable no-op failure**
  - Symptom: `× Failed to enable plugin "...": Plugin "..." is already enabled`
  - Root: CLI returns non-zero on an already-satisfied state
  - Invariant: plugin enable must be idempotent (check state before enabling)
  - Fix: `scripts/claude_plugin_ensure.ps1`

- **Copilot MCP 400: Authorization header badly formatted**
  - Symptom: Streamable HTTP error, bad request, Authorization header badly formatted
  - Root: token drift (whitespace, `<...>` wrapping, double `Bearer ` prefix)
  - Invariant: normalize token strings before using in headers
  - Fix: token normalization in `scripts/api_pool.ps1` and `scripts/api_pool_persist_user_env.ps1`

- **IDE-launched Claude missing env vars**
  - Symptom: MCP server invalid / missing required env vars (e.g. `GITHUB_PERSONAL_ACCESS_TOKEN`)
  - Root: Windows process environment inheritance: VS Code/extension child processes don't see terminal-only process env
  - Invariant: IDE launch must load API pool before spawning Claude
  - Fix: `claudeCode.claudeProcessWrapper` → `scripts/claude_process_wrapper.*`

- **PowerShell parsing backticks in hook scripts**
  - Symptom: `ParserError: The Unicode escape sequence is not valid` in SessionStart hook
  - Root: unescaped backticks inside double-quoted strings
  - Invariant: avoid raw backticks in PS strings; use single quotes or escape
  - Fix: corrected `.claude/hooks/session_start_context.ps1`

## Invariants (Derived)

1. **Single choke point**
   - IDE must launch through wrapper; wrapper runs heal + healthcheck before spawning real Claude.

2. **Artifact-first debugging**
   - All state should be captured in one place:
     - `codex/mailbox/CLAUDE_IDE_HEALTH_LATEST.json`
   - Debugging starts from this artifact, not ad-hoc logs.

3. **No new variants**
   - New fixes must modify the canonical entrypoint (`scripts/claude_ide.ps1`) or its invariant modules,
     not create additional patch scripts.

## Candidate Follow-Ups

- Shim legacy scripts to call `scripts/claude_ide.ps1 <cmd>` (repurpose, don’t delete).
- Extend healthcheck to record normalized-mode (`official|copilot`) and plugin MCP validity.

