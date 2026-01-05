# Claude Code Integration Scripts

**Architecture:** GitHub Copilot CLI (launcher) → PowerShell scripts (orchestrator) → Bun MCP server (executor) → filesystem/graph

These scripts enable clean integration between Claude Code/Desktop and the chthonic-archive MCP server on Windows 11, keeping orchestration **outside** the MCP server.

---

## Files

### `scripts/launch_claude_code.ps1`
**Purpose:** Install and start Claude Code/Desktop on Windows 11

**Usage:**
```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\launch_claude_code.ps1
pwsh -File .\scripts\launch_claude_code.ps1 -Force           # Force reinstall
pwsh -File .\scripts\launch_claude_code.ps1 -WaitSeconds 60  # Longer wait for manual install
```

**Behavior:**
- Prefers `winget install -e --id Anthropic.Claude` if winget available
- Falls back to opening browser to Claude Code docs for manual download
- Detects running Claude process variants (claude, Claude, claude-code)
- Exits with code 0 if Claude running, code 2 if installation failed

**Security Notes:**
- Does NOT bypass interactive sign-in (required by Anthropic)
- Downloads only from official landing page
- No credential scripting

---

### `scripts/run_mcp_session.ps1`
**Purpose:** Bootstrap complete MCP session (Claude Code + Bun MCP server)

**Usage:**
```powershell
pwsh -File .\scripts\run_mcp_session.ps1                    # Start MCP server only
pwsh -File .\scripts\run_mcp_session.ps1 -EnsureClaude      # Ensure Claude + start MCP
pwsh -File .\scripts\run_mcp_session.ps1 -McpCmd "custom"   # Custom MCP start command
```

**Behavior:**
- Optionally calls `launch_claude_code.ps1` if `-EnsureClaude` flag present
- Spawns MCP server as background job (continues after script exits)
- Lists running Claude processes for verification
- Outputs instruction to register local MCP server in Claude Code

**One-Command Bootstrap:**
```powershell
# Complete environment setup in one line
pwsh -File .\scripts\run_mcp_session.ps1 -EnsureClaude
```

---

### `mcp/claude_code_mcp_hint.json`
**Purpose:** Example manifest for registering local MCP server in Claude Code

**How to Use:**
1. Open Claude Code/Desktop → Settings → Integrations → Add Server
2. Either:
   - **Import this JSON** (if Claude supports manifest import), OR
   - **Manually fill UI form** using these values:
     - Label: `chthonic-archive (local)`
     - Command: `bun`
     - Args: `["run", "mcp/server.ts"]`
     - Working Directory: `C:\Users\erdno\chthonic-archive`
     - Transport: `stdio`
     - Manifest Path: `C:\Users\erdno\chthonic-archive\mcp\mcp.json`

**After Registration:**
- Claude Code will discover 4 MCP tools via `mcp/mcp.json` manifest
- Tools available: `ping`, `scan_repository`, `validate_ssot_integrity`, `query_dependency_graph`

---

## Integration with Bun Smoke Runner

The `run_mcp_validation.ts` runner includes optional `--ensure-claude-code` flag:

```bash
# Ensure Claude Code installed/running before MCP validation
bun run run_mcp_validation.ts --ensure-claude-code

# Combine with other flags
bun run run_mcp_validation.ts --ensure-claude-code --spectral GOLD
```

**Behavior (Windows only):**
- Calls `scripts\launch_claude_code.ps1` before spawning MCP server
- Throws error if installation fails
- Skips silently on non-Windows platforms

---

## Architecture Principles

**DO:**
- Use GitHub Copilot CLI or PowerShell scripts as launchers
- Keep orchestration in scripts (external to MCP)
- Register MCP server in Claude via official UI/manifest
- Let Claude Code act as **MCP client**, not orchestrator

**DON'T:**
- Add MCP tools that call other MCP servers (self-tooling)
- Script credential bypass (interactive sign-in required)
- Turn Claude into an orchestrator (it's a **client**)
- Download installers from non-official sources

---

## Quick Start

### First-Time Setup
```powershell
# 1. Install Claude Code and sign in
pwsh -File .\scripts\launch_claude_code.ps1

# 2. Start MCP server
pwsh -File .\scripts\run_mcp_session.ps1

# 3. Register local server in Claude Code UI
#    (Use values from mcp/claude_code_mcp_hint.json)

# 4. Verify MCP connection
bun run run_mcp_validation.ts
```

### Daily Workflow
```powershell
# One command: ensure environment + validate
bun run run_mcp_validation.ts --ensure-claude-code
```

---

## Exit Codes

### `launch_claude_code.ps1`
- `0` - Claude running successfully
- `2` - Installation failed or Claude not detected after wait

### `run_mcp_session.ps1`
- Throws exception if Claude ensure fails
- Otherwise completes successfully (server runs as background job)

### `run_mcp_validation.ts --ensure-claude-code`
- `0` - All validations passed (7/7)
- `1` - One or more validations failed
- Throws if Claude installation fails

---

## Security & Legal

- **Interactive sign-in required:** Scripts cannot and do not bypass Anthropic authentication
- **Official sources only:** Downloads from `code.claude.com` landing page
- **No credential storage:** Scripts do not persist tokens/passwords
- **Enterprise environments:** Check SSO/deployment policies before use

---

## Troubleshooting

**"Claude not detected after wait"**
- Install manually from https://code.claude.com
- Sign in interactively
- Re-run script with `-Force` flag

**"winget install returned non-zero"**
- Normal if winget prompts for user confirmation
- Script will fall back to browser download
- Accept prompts or use manual download

**"MCP server not responding"**
- Verify Bun installed: `bun --version`
- Check server logs in terminal
- Test server directly: `bun run mcp/server.ts`

**"Claude Code doesn't show MCP tools"**
- Verify server registered in Settings → Integrations
- Check manifest path points to `mcp/mcp.json`
- Restart Claude Code after registration

---

## See Also

- `docs/MCP_USER_WORKFLOWS.md` - Canonical MCP workflow patterns
- `docs/SESSION_BOOTSTRAP_SPEC.md` - MCP session provisioning contract
- `mcp/mcp.json` - MCP server manifest (4 tools)
- `run_mcp_validation.ts` - Local validation runner (7 checks)
