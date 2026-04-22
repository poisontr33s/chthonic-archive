# Claude Code MCP Server Registration

<!--
@SID:           DOC_CLAUDE_CODE_REGISTRATION
@Type:          Setup Guide
@Context:       MCP / Configuration
@SessionOrigin: SESSION_DOC_2026_01_04_MCP
@References:    MCP_SERVER_TEMPLATE, SESSION_BOOTSTRAP_SPEC
-->

**Status:** Ready for registration (all prerequisites verified)

## Prerequisites

> **Verified:** All prerequisites met as of January 27, 2026. MCP server fully operational.

- ✅ Claude Code installed and running
- ✅ MCP server validated (7/7 checks passing) - **Verified via `bun run scripts/run_mcp_validation.ts`**
- ✅ MCP server functional - **Tested with all 5 tools operational**
- ✅ Dependency graph available - **dependency_graph_production.json present at repo root**

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
  "total_nodes": 10,
  "total_hyperedges": 8,
  "directed": true,
  "spectral_distribution": {
    "BLUE": 3,
    "GOLD": 4,
    "ORANGE": 2,
    "WHITE": 1
  },
  "void_directories": 0,
  "clusters": 0,
  "validation": {
    "graph_is_connected": true,
    "graph_is_dag": true,
    "largest_component_size": 10
  }
}
```

> **Note:** Values reflect current dependency_graph_production.json state (10 nodes: 3 BLUE, 4 GOLD, 2 ORANGE, 1 WHITE).

## Troubleshooting

### Server Not Visible in Claude Code

- Check MCP server is running: `Get-Process -Name bun`
- Restart Claude Code after registration
- Verify working directory path is correct (absolute path required)

### Tool Invocation Fails

- Run validation suite: `bun run scripts/run_mcp_validation.ts` (should show 7/7 passing)
- Check server logs (stderr if available)
- Verify stdio transport configuration
- Verify dependency_graph_production.json exists at repo root

## Architecture Reminder

```
Claude Code (MCP client)
    ↓ stdio
MCP Server (mcp/server.ts via Bun)
    ↓
Tools: ping, preflight_execution_context, scan_repository, validate_ssot_integrity, query_dependency_graph
```

**Critical:** Claude Code is a **client**, not an orchestrator. Orchestration stays in PowerShell scripts.

## Next Steps After Registration

1. Test basic tool invocation (ping)
2. Test read-only query (dependency graph stats)
3. Document any UI-specific registration details discovered
4. Optional: Create short integration note if needed

---

**Created:** 2026-01-05  
**Updated:** 2026-01-27 (verified all prerequisites functional)  
**Purpose:** Manual registration guide for Claude Code MCP integration  
**Status:** ✅ All systems operational - ready for Claude Code registration
