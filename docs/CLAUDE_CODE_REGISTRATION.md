# Claude Code MCP Server Registration

**Status:** Manual registration required (one-time setup)

## Prerequisites

- ✅ Claude Code installed and running
- ✅ MCP server validated (7/7 checks passing)
- ✅ MCP server process running (PID 62288)

## Registration Steps

### Option 1: Using Claude Code UI (Recommended)

1. **Open Claude Code** → Settings
2. **Navigate to:** Integrations → MCP Servers → Add Server (or similar)
3. **Configure server using these values:**

```json
{
  "label": "chthonic-archive (local)",
  "command": "bun",
  "args": ["run", "mcp/server.ts"],
  "workingDirectory": "C:\\Users\\erdno\\chthonic-archive",
  "transport": "stdio"
}
```

**Note:** Values from `mcp/claude_code_mcp_hint.json`

### Option 2: Manual Config File Edit (Alternative)

If Claude Code stores server configs in a JSON file (check documentation):

1. Locate Claude Code config directory (platform-specific)
2. Find MCP servers configuration file
3. Add server entry using values above

## Verification After Registration

### Test 1: Basic Connectivity (ping)

In Claude Code chat:
```
Use the ping tool from chthonic-archive server
```

Expected response:
```json
{"pong": true}
```

### Test 2: Read-Only Query (stats)

In Claude Code chat:
```
Query the dependency graph stats from chthonic-archive server
```

Expected response:
```json
{
  "total_nodes": 949,
  "total_hyperedges": 187,
  "spectral_frequencies": {
    "BLUE": 414,
    "GOLD": 308,
    "ORANGE": 100,
    "WHITE": 80,
    "VIOLET": 30,
    "RED": 15,
    "INDIGO": 2
  }
}
```

## Troubleshooting

### Server Not Visible in Claude Code

- Check MCP server is running: `Get-Process -Name bun`
- Restart Claude Code after registration
- Verify working directory path is correct (absolute path required)

### Tool Invocation Fails

- Run validation suite: `bun run run_mcp_validation.ts`
- Check server logs (stderr if available)
- Verify stdio transport configuration

## Architecture Reminder

```
Claude Code (MCP client)
    ↓ stdio
MCP Server (mcp/server.ts via Bun)
    ↓
Tools: ping, scan_repository, validate_ssot_integrity, query_dependency_graph
```

**Critical:** Claude Code is a **client**, not an orchestrator. Orchestration stays in PowerShell scripts.

## Next Steps After Registration

1. Test basic tool invocation (ping)
2. Test read-only query (dependency graph stats)
3. Document any UI-specific registration details discovered
4. Optional: Create short integration note if needed

---

**Created:** 2026-01-05  
**Purpose:** Manual registration guide for Claude Code MCP integration  
**Status:** Awaiting user completion of registration step
