# Session Bootstrap Specification

**Version:** 1.1  
**Date:** 2026-01-05  
**Status:** VERIFIED (Initial validation 2026-01-04, smoke suite validation 2026-01-05)

---

## 1. Preconditions

### 1.1 System Requirements
- **OS:** Windows 11 (verified on build 22631)
- **Bun:** 1.1.43 or later
- **Claude Desktop:** 1.0.2339 or later
- **Git:** Any recent version (for SSOT verification)

### 1.2 Repository Layout (Required)
```
chthonic-archive/
├── .github/
│   └── copilot-instructions.md         ← SSOT (313,634 bytes, hash: 49ef091b...)
├── mcp/
│   ├── server.ts                       ← MCP server entry point
│   ├── protocol.ts                     ← JSON-RPC 2.0 types
│   ├── tools/
│   │   ├── ping.ts
│   │   ├── scanRepository.ts
│   │   ├── validateSSOT.ts
│   │   └── queryDependencyGraph.ts     ← Dependency graph queries
│   ├── test-client.ts                  ← Local verification client
│   ├── test-dependency-graph.ts        ← Dependency graph test suite
│   └── smoke-suite.ts                  ← Automated workflow validation
├── docs/
│   ├── SESSION_BOOTSTRAP_SPEC.md       ← This file
│   └── MCP_USER_WORKFLOWS.md           ← Canonical workflow patterns
├── dependency_graph_production.json    ← Dependency graph data (949 nodes, 187 edges)
└── artifacts/
    └── mcp_run_*.json                  ← Workflow execution artifacts
```

### 1.3 Claude Desktop Configuration (Required)
**File:** `%APPDATA%\Claude\claude_desktop_config.json`

**Content:**
```json
{
  "mcpServers": {
    "chthonic-archive": {
      "command": "bun",
      "args": ["run", "C:\\Users\\erdno\\chthonic-archive\\mcp\\server.ts"]
    }
  }
}
```

**Note:** Use absolute paths in `args` array. Relative paths will fail.

---

## 2. Provisioning Sequence

### 2.1 Copilot CLI Role (Optional)
GitHub Copilot CLI is **not required** for session operation but serves as:
- **Provisioner:** Scaffolds MCP servers, validates protocol compliance
- **Orchestrator:** Runs local test clients for verification
- **Validator:** Executes SSOT hash checks, repository scans

**If used:** Copilot CLI remains **separate** from Claude Desktop (no conflict)

### 2.2 Claude Desktop Startup
**Manual launch:**
```powershell
Start-Process "C:\Users\erdno\AppData\Local\AnthropicClaude\claude.exe"
```

**Automatic MCP attachment:**
- On startup, Claude Desktop reads `claude_desktop_config.json`
- Spawns Bun process: `bun run <server.ts path>`
- Initiates MCP handshake (initialize → tools/list)

**Expected startup log** (visible in `%APPDATA%\Claude\logs\`):
```
[MCP] Connecting to server: chthonic-archive
[MCP] Initialize: protocolVersion=2025-06-18
[MCP] Tools discovered: 4 (ping, scan_repository, validate_ssot_integrity, query_dependency_graph)
```

### 2.3 MCP Server Attach Sequence
1. **Process spawn:** Claude Desktop executes `bun run mcp/server.ts`
2. **Transport:** stdio (stdin/stdout) - no network sockets
3. **Handshake:**
   - Client sends: `{"jsonrpc":"2.0","id":0,"method":"initialize","params":{...}}`
   - Server responds: `{"jsonrpc":"2.0","id":0,"result":{"protocolVersion":"2025-06-18",...}}`
   - Client sends: `{"jsonrpc":"2.0","method":"notifications/initialized"}` (no id - notification)
   - Server: **NO RESPONSE** (correct notification handling)
4. **Tools enumeration:** Client calls `tools/list`, receives 4 tools

**Attach verified when:**
- `chthonic-archive` appears in Claude Desktop MCP provider list
- No Zod validation errors in logs
- Tools callable from UI

---

## 3. Trust & Authority

### 3.1 Filesystem Scope
**Read access:**
- Repository root: `C:\Users\erdno\chthonic-archive`
- All subdirectories (except excluded: `node_modules/`, `.git/`, `target/`)

**Write access:**
- **NONE** (current server is read-only)
- All tools are non-mutating queries

**Scope enforcement:**
- Tools use `import.meta.dir` to resolve repository root
- No path traversal outside repository
- No network access

### 3.2 Read/Write Guarantees
**Current guarantees (verified):**
- `ping`: No filesystem access (returns `{"pong":true}`)
- `scan_repository`: Read-only directory traversal
- `validate_ssot_integrity`: Read-only SSOT file access + SHA-256 hash
- `query_dependency_graph`: Read-only dependency graph queries (5 commands: node, dependencies, dependents, spectral, stats)

**Future guarantees (if write tools added):**
- Must be explicitly documented in this spec
- Must include rollback mechanisms
- Must log all mutations

### 3.3 SSOT Precedence
**Authority hierarchy:**
1. `.github/copilot-instructions.md` (SSOT - 313,634 bytes)
2. This bootstrap spec (`docs/SESSION_BOOTSTRAP_SPEC.md`)
3. MCP server implementation (`mcp/server.ts`)
4. Tool implementations (`mcp/tools/*.ts`)

**Conflict resolution:**
- SSOT overrides all other sources
- Hash mismatches trigger validation errors
- Expected hash: `49ef091b564023919ef32a3cd2bfb951630487c8947bf65739d99f924ab37ef5`

---

## 4. Verification Checklist

### 4.1 Pre-Session Verification (Optional)
Run local test client to verify server before Claude Desktop attach:
```powershell
cd C:\Users\erdno\chthonic-archive\mcp
bun run test-client.ts
```

**Expected output:**
```
[Server Response] {"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"{\"pong\":true}"}]}}
[Server Response] {"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"{\"repository\":\"C:\\\\Users\\\\erdno\\\\chthonic-archive\",\"file_count\":42920,...}"}]}}
[Server Response] {"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"{\"status\":\"valid\",\"hash\":\"49ef091b...\"}"}]}}
```

### 4.2 Post-Attach Verification (Required)
In Claude Desktop UI, execute canonical test:

**Prompt:** "Scan the chthonic-archive repository and tell me how many files exist."

**Expected response:**
- File count: ~42,920 (varies with repo state)
- Sample paths included
- No errors in logs

### 4.3 Tool Availability Check
**Expected tools in Claude Desktop UI:**
- ✅ `ping` (operational)
- ✅ `scan_repository` (operational)
- ✅ `validate_ssot_integrity` (operational)
- ✅ `query_dependency_graph` (operational - 5 commands: node, dependencies, dependents, spectral, stats)

### 4.4 SSOT Integrity Verification
**Prompt:** "Validate the SSOT integrity for chthonic-archive."

**Expected response:**
```json
{
  "status": "valid",
  "path": "C:\\Users\\erdno\\chthonic-archive\\.github\\copilot-instructions.md",
  "size": 313634,
  "lines": 3964,
  "hash": "49ef091b564023919ef32a3cd2bfb951630487c8947bf65739d99f924ab37ef5"
}
```

**If hash mismatch:** SSOT has been modified since last verification. Review changes.

---

## 5. Stop Conditions (What Is NOT Automatic)

### 5.1 No Background Execution
- MCP server spawns **only** when Claude Desktop starts
- Server terminates when Claude Desktop closes
- No persistent background processes
- No daemon mode

### 5.2 No Silent Tool Calls
- All tool invocations require explicit user prompts in Claude Desktop UI
- No "agent loops" or self-triggered actions
- No scheduled tasks
- No filesystem watchers

### 5.3 No Auto-Start
- Claude Desktop does **NOT** auto-start on Windows login
- User must manually launch Claude Desktop
- MCP server attach happens **after** manual launch

### 5.4 No Implicit Trust
- User must review tool call requests in Claude Desktop UI
- Tools can be set to "always allow" (as currently configured)
- But this is **explicit user configuration**, not default behavior

### 5.5 No Network Access
- MCP server uses stdio transport (no TCP/UDP sockets)
- No external API calls
- No internet connectivity required or used

---

## 6. Architecture Separation (Verified)

| Plane | Responsibility | Tool |
|-------|----------------|------|
| **Provisioning** | Scaffold, validate, test | GitHub Copilot CLI |
| **Cognition** | Reasoning, decision-making | Claude Desktop |
| **Execution** | Bounded tool calls | Bun MCP Server |
| **Authority** | SSOT, validation rules | Repository (`.github/copilot-instructions.md`) |

**Key insight:** This setup automates **capability availability**, not decisions.

---

## 7. Session Lifecycle

### 7.1 Session Start
1. User launches Claude Desktop manually
2. Claude Desktop reads `claude_desktop_config.json`
3. Claude Desktop spawns `bun run mcp/server.ts` via stdio
4. MCP handshake completes (initialize → tools/list)
5. Tools available in UI

**Duration:** ~2-3 seconds from launch to ready state

### 7.2 Session Active
- User issues prompts in Claude Desktop UI
- Claude reasoning layer decides when to call MCP tools
- MCP server executes bounded filesystem queries
- Results return to Claude for synthesis

**No automatic actions.** All tool calls are prompt-initiated.

### 7.3 Session End
1. User closes Claude Desktop
2. Claude Desktop sends termination signal to MCP server
3. Bun process exits cleanly
4. No persistent state (server is stateless)

**No cleanup required.** Server does not create temp files or state.

---

## 8. Troubleshooting

### 8.1 MCP Server Not Appearing in UI
**Symptom:** `chthonic-archive` not in Claude Desktop provider list

**Diagnosis:**
1. Check `%APPDATA%\Claude\claude_desktop_config.json` exists
2. Verify absolute path in `args` array (no relative paths)
3. Check Claude Desktop logs: `%APPDATA%\Claude\logs\` for MCP errors

**Fix:** Restart Claude Desktop after config changes

### 8.2 Protocol Validation Errors
**Symptom:** Zod validation errors in logs (`Expected string or number, received null`)

**Diagnosis:**
1. Check `mcp/protocol.ts` has `jsonrpc: "2.0"` in all interfaces
2. Verify `mcp/server.ts` returns `null` for notifications (no response)
3. Ensure `id` field is never `null` in responses

**Fix:** Update to commit `00793ba` or later (notification handling fixed)

### 8.3 Repository Root Resolution Errors
**Symptom:** Tools report wrong file counts or paths

**Diagnosis:**
1. Check tools use `import.meta.dir` (not `process.cwd()`)
2. Verify resolution: `resolve(import.meta.dir, "..", "..")` for repo root

**Fix:** Update to commit `6c27d7b` or later (root resolution fixed)

### 8.4 SSOT Hash Mismatch
**Symptom:** `validate_ssot_integrity` returns different hash

**Diagnosis:**
1. SSOT file has been modified
2. Check git status: `git diff .github/copilot-instructions.md`

**Fix:** Review changes, commit if intentional, revert if accidental

---

## 9. Future Extensions (Bounded)

### 9.1 Adding New Tools
1. Create tool file: `mcp/tools/newTool.ts`
2. Implement function returning MCP-formatted response
3. Register in `mcp/server.ts` tools/list array
4. Add routing in `mcp/server.ts` tools/call switch
5. Update this spec (Section 4.3 tool list)
6. Verify with test-client.ts before Claude Desktop attach

### 9.2 Adding Read-Only MCP Servers
1. Create new server directory (e.g., `mcp-metadata/`)
2. Implement separate stdio server
3. Add to `claude_desktop_config.json` with unique name
4. Update this spec with new server entry
5. Maintain separation of concerns (no shared state)

### 9.3 Adding Write Capabilities (HIGH RISK)
**If write tools are required:**
1. Document exact mutation scope in this spec (Section 3.2)
2. Implement transaction rollback mechanisms
3. Add mutation logging to SSOT or audit file
4. Require explicit user confirmation in Claude UI
5. Test exhaustively with test-client.ts before production use

**Recommendation:** Avoid write tools unless absolutely necessary. Read-only is safer.

---

## 10. Reproducibility Contract

**This spec guarantees:**
- Same provisioning sequence → same cognitive environment
- Same tool list → same capability surface
- Same SSOT → same authority boundaries
- Same stop conditions → same safety guarantees

**This spec does NOT guarantee:**
- Specific Claude responses (reasoning is non-deterministic)
- File counts (repository state changes over time)
- Performance (depends on system load)

**Portability notes:**
- Windows-specific paths (adapt for macOS/Linux)
- Bun-specific features (`import.meta.dir`, `Bun.file()`, `Bun.CryptoHasher()`)
- Claude Desktop version-dependent (tested on 1.0.2339)

---

## 11. Validation History

| Date | Version | Validator | Status |
|------|---------|-----------|--------|
| 2026-01-04 | 1.0 | GitHub Copilot CLI + Claude Desktop | ✅ VERIFIED |
| 2026-01-05 | 1.1 | Smoke Suite (6/6 workflows) | ✅ VERIFIED |

**Verification proof (v1.0):**
- Commit: `00793ba` (notification handling fix)
- Test run: `mcp/test-client.ts` (5 responses captured)
- Claude Desktop: End-to-end vertical slice confirmed
- SSOT hash: `49ef091b564023919ef32a3cd2bfb951630487c8947bf65739d99f924ab37ef5`

**Verification proof (v1.1):**
- Commit: `5c666b2` (query_dependency_graph implementation)
- Smoke suite: `mcp/smoke-suite.ts` (6/6 workflows passed)
- Test suite: `mcp/test-dependency-graph.ts` (7/7 tests passed)
- Artifacts: `artifacts/mcp_run_*_2026-01-05T00-43-47-483Z.json`
- SSOT hash: `49ef091b564023919ef32a3cd2bfb951630487c8947bf65739d99f924ab37ef5` (unchanged)

---

**END OF SPECIFICATION**
