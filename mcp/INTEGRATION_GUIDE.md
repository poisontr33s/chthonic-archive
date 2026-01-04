# MCP Client Integration Guide

**Status:** ✅ READY FOR INTEGRATION  
**Date:** 2026-01-04  
**Server:** chthonic-archive Bun-native MCP server  
**Transport:** stdio (JSON-RPC 2.0)

---

## Quick Start: Claude Desktop Integration

### 1. Locate Claude Desktop Config

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### 2. Add MCP Server Configuration

Edit `claude_desktop_config.json` and add the `chthonic-archive` server:

**Windows example:**
```json
{
  "mcpServers": {
    "chthonic-archive": {
      "command": "bun",
      "args": ["run", "C:\\Users\\erdno\\chthonic-archive\\mcp\\server.ts"],
      "env": {}
    }
  }
}
```

**macOS/Linux example:**
```json
{
  "mcpServers": {
    "chthonic-archive": {
      "command": "bun",
      "args": ["run", "/absolute/path/to/chthonic-archive/mcp/server.ts"],
      "env": {}
    }
  }
}
```

**Important:** Use **absolute paths** for `args` array. Relative paths may fail during MCP discovery.

### 3. Restart Claude Desktop

- Quit Claude Desktop completely (File → Quit or Cmd+Q/Alt+F4)
- Relaunch Claude Desktop
- Server should appear in MCP provider list

### 4. Verify Integration

In Claude Desktop chat, try invoking tools:

**Test 1: Ping**
```
Can you ping the chthonic-archive MCP server?
```

**Expected response:** `{"pong": true}`

**Test 2: Repository Scan**
```
Scan the chthonic-archive repository and tell me how many files exist.
```

**Expected response:** ~44,207 files found, list of first 50 files with sizes

**Test 3: SSOT Validation**
```
Validate the SSOT integrity for chthonic-archive.
```

**Expected response:** 
- Status: valid
- Path: `.github/copilot-instructions.md`
- Size: 313,634 bytes
- Lines: 3,964
- Hash: `49ef091b564023919ef32a3cd2bfb951630487c8947bf65739d99f924ab37ef5`

---

## VSCode Integration (Alternative)

### 1. Install MCP Extension

- Install official MCP extension from VSCode marketplace
- Or use Copilot MCP integration (if available)

### 2. Configure Server

Add to VSCode `settings.json`:

```json
{
  "mcp.servers": {
    "chthonic-archive": {
      "type": "stdio",
      "command": "bun",
      "args": ["run", "/absolute/path/to/mcp/server.ts"]
    }
  }
}
```

### 3. Reload Window

- Cmd+Shift+P / Ctrl+Shift+P → "Developer: Reload Window"
- Server should appear in MCP provider panel

---

## Troubleshooting

### Server Not Appearing in Client

**Check:**
1. Bun is installed and in PATH (`bun --version`)
2. Absolute paths used in config (not relative)
3. Client fully restarted (not just window reload)
4. No syntax errors in JSON config

**Debug:**
```powershell
# Test server manually
cd C:\Users\erdno\chthonic-archive
bun run mcp/server.ts
# Then send test request:
echo '{"id":1,"method":"ping"}' | bun run mcp/server.ts
```

### Server Starts But Tools Fail

**Check:**
1. Working directory is repository root
2. `.github/copilot-instructions.md` exists
3. File permissions allow reading SSOT

**Debug:**
```powershell
# Run test suite
bun test mcp/server.test.ts
```

### Permission Errors

**Windows:** Ensure Bun has file system read access  
**macOS/Linux:** Check file permissions with `ls -la .github/`

---

## Current Configuration

**Detected System:** Windows  
**Claude Desktop Config:** `C:\Users\erdno\AppData\Roaming\Claude\claude_desktop_config.json`  
**Server Manifest:** `C:\Users\erdno\chthonic-archive\mcp\mcp.json`

**Current config state:**
```json
{
  "mcpServers": {}
}
```

**Recommended addition:**
```json
{
  "mcpServers": {
    "chthonic-archive": {
      "command": "bun",
      "args": ["run", "C:\\Users\\erdno\\chthonic-archive\\mcp\\server.ts"],
      "env": {}
    }
  }
}
```

---

## Integration Checklist

- [x] MCP server manifest created (`mcp/mcp.json`)
- [ ] Claude Desktop config updated
- [ ] Claude Desktop restarted
- [ ] Server appears in provider list
- [ ] `ping` tool tested
- [ ] `scan_repository` tool tested
- [ ] `validate_ssot_integrity` tool tested
- [ ] Integration documented

---

## Next Steps After Integration

Once all tools successfully invoke from Claude Desktop:

1. **Document results** in `docs/MCP_AUTONOMOUS_PREREQUISITES.md`
2. **Update README** with client integration status
3. **Commit changes** (manifest + integration guide)
4. **Consider Option B** (dependency graph implementation)

---

**Stop condition:** All three tools invoke successfully from real MCP client with output matching local test client.

Do not expand capabilities until integration validated.
