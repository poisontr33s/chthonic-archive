# MCP Configuration Log 2026-02-01

**Status:** ✅ RESOLVED
**Topic:** Unified GitHub MCP Configuration (Triad)

## Summary
We successfully unified the GitHub MCP configuration across **Codex**, **Gemini**, and **Claude Code** using the hosted `api.githubcopilot.com` endpoint and a single valid Personal Access Token (PAT).

## The Critical Fix
**Root Cause:**
- We initially used a token found in an environment variable (`ghp_ir...`) which proved to be **invalid/revoked** (HTTP 401).
- The working token was found in `~/.gemini/settings.json` (`ghp_SIG...`).

**Resolution:**
1.  **Validated:** Confirmed `ghp_SIG...` works against GitHub API via `curl`.
2.  **Environment:** Updated user-scope env var `GITHUB_MCP_PAT` to the valid token.
3.  **Claude:** Updated `.mcp.json` with the valid token.
4.  **Codex:** Relies on the now-fixed env var `GITHUB_MCP_PAT`.

## Final Configuration State

### 1. Codex (CLI & IDE)
- **Config:** `~/.codex/config.toml` (Global)
- **Method:** Env Var Reference
- **Entry:**
  ```toml
  [mcp_servers.github]
  url = "https://api.githubcopilot.com/mcp/"
  bearer_token_env_var = "GITHUB_MCP_PAT"
  ```

### 2. Gemini (CLI)
- **Config:** `~/.gemini/settings.json` (Global)
- **Method:** Direct Token (Source of Truth)
- **Entry:**
  ```json
  "github": {
    "httpUrl": "https://api.githubcopilot.com/mcp/",
    "headers": { "Authorization": "Bearer ghp_SIG..." }
  }
  ```

### 3. Claude Code (CLI & IDE)
- **Config:** `.mcp.json` (Project Scope: `C:\Users\erdno\chthonic-archive\.mcp.json`)
- **Method:** Direct Token (CLI arg parsing failed, so file-based config used)
- **Entry:**
  ```json
  "github": {
    "type": "http",
    "url": "https://api.githubcopilot.com/mcp/",
    "headers": { "Authorization": "Bearer ghp_SIG..." }
  }
  ```

## Verification
- `claude mcp list` → **✓ Connected**
- Codex → **Verified Parity** (Config matches)
- Gemini → **Verified Source**

## Lessons Learned
- **Trust but Verify:** Always test tokens with `curl` before troubleshooting transport layers.
- **Windows CLI:** PowerShell/Windows parsing of `claude mcp add` flags is fragile; direct file editing (`.mcp.json`) is more reliable.
- **Triad Parity:** Shared env vars are the best way to keep agents in sync (implemented for Codex, partially for Claude).

---

## Update: 2026-02-04 - Post-Update Recovery

**Symptom:** After Claude Code extension update, "Manage MCP Servers" UI showed "No running MCP servers" despite previous working config.

**Root Cause:** Multiple issues compounded:
1. `github@claude-plugins-official` plugin was conflicting (showed as `plugin:github:github` - failed)
2. Attempted env var interpolation `${GITHUB_MCP_PAT}` in `.mcp.json` doesn't work on Windows
3. VS Code extension UI doesn't reflect actual MCP state (UI bug)

**Fix Applied:**
1. Disabled plugin in project settings:
   ```json
   // .claude/settings.json (project)
   { "enabledPlugins": { "github@claude-plugins-official": false } }
   ```

2. Restored direct token in `.mcp.json` (env var interpolation FAILS on Windows):
   ```json
   "headers": { "Authorization": "Bearer ghp_SIG..." }
   ```
   **NOT:** `"Bearer ${GITHUB_MCP_PAT}"` ← This doesn't work!

3. Enabled MCP servers in global settings:
   ```json
   // ~/.claude/settings.json (global)
   { "enableAllProjectMcpServers": true, "enabledMcpjsonServers": ["github"] }
   ```

**Verification:**
```powershell
claude mcp list
# → github: https://api.githubcopilot.com/mcp/ (HTTP) - ✓ Connected
```

**Key Insight:** The "Manage MCP Servers" UI may show "No running servers" even when MCP IS working. Trust `claude mcp list` CLI output, not the UI.

**Recovery Checklist (for future updates):**
1. [ ] Run `claude mcp list` - if shows connected, MCP works (ignore UI)
2. [ ] If disconnected, check `.mcp.json` has direct token (not env var)
3. [ ] Check `github@claude-plugins-official` plugin is disabled
4. [ ] Verify token by checking `~/.gemini/settings.json` (source of truth)
