# ☥ Overnight Intelligence Report — 2026-02-11T02-19-33

**Duration:** 1.3 minutes
**Tasks:** 5 done, 0 failed, 5 total
**Model:** claude-haiku-4.5
**Auth:** poisontr33s

---

# File Census — 2026-02-11T02-19-33

**Total files:** 1075

## By Extension
| Ext | Count | Total Lines |
|-----|-------|-------------|
| .py | 798 | 222,983 |
| .ts | 113 | 49,479 |
| .ps1 | 130 | 13,231 |
| .rs | 19 | 4,564 |
| .tsx | 15 | 1,994 |

## Top 20 Largest Files
| File | Lines | Size |
|------|-------|------|
| meta-ide\copilot-cli-0.0.406\sdk\index.d.ts | 15,475 | 532.9 KB |
| meta-ide\copilot-sdk\sdk\index.d.ts | 15,475 | 532.9 KB |
| codex\codex-session-logs\archive\default-session-code-gemini.py | 5,081 | 1152.9 KB |
| build\cupy\cupyx\scipy\signal\_ltisys.py | 3,126 | 108.4 KB |
| build\cupy\cupyx\scipy\signal\_iir_filter_conversions.py | 2,372 | 72.1 KB |
| build\cupy\cupyx\scipy\interpolate\_interpolate.py | 2,364 | 80.9 KB |
| build\cupy\cupyx\cusparse.py | 2,115 | 72.3 KB |
| build\cupy\cupyx\scipy\signal\_signaltools.py | 1,769 | 65.1 KB |
| build\cupy\cupyx\scipy\interpolate\_fitpack_repro.py | 1,595 | 56.4 KB |
| build\cupy\cupyx\scipy\ndimage\_measurements.py | 1,594 | 57.8 KB |
| build\cupy\cupyx\scipy\signal\_spectral.py | 1,587 | 56.7 KB |
| build\cupy\cupyx\scipy\signal\_peak_finding.py | 1,486 | 51.6 KB |
| build\cupy\cupyx\scipy\ndimage\_filters.py | 1,441 | 66.0 KB |
| build\cupy\tests\cupy_tests\core_tests\test_raw.py | 1,430 | 49.6 KB |
| scripts\decorator_cross_ref_production.py | 1,382 | 63.3 KB |
| scripts\decorator_cross_ref_maximum.py | 1,361 | 65.4 KB |
| mas_mcp\milf_genesis_v2.py | 1,357 | 52.3 KB |
| build\cupy\tests\cupy_tests\cuda_tests\test_memory.py | 1,356 | 48.1 KB |
| build\cupy\cupy\random\_generator.py | 1,333 | 47.8 KB |
| build\cupy\tests\cupy_tests\random_tests\test_generator.py | 1,295 | 37.5 KB |

---

# SDK Architecture Analysis — 2026-02-11T02-19-33

## Analysis: GitHub Copilot SDK Type Definitions

### 1. Exported Functions
**None visible in snippet.** Only type/interface exports shown.

### 2. Key Interfaces/Types

| Name | Purpose |
|------|---------|
| `AbortEvent` | User abort event; triggers completion of orphaned tool calls |
| `AgentMode` | UI mode enum: "interactive" \| "plan" \| "autopilot" |
| `AgentStopHook` | Callback fired when agent naturally stops (no more tool calls) |
| `AgentStopHookInput` | Hook input with sessionId, transcriptPath, stopReason |
| `AgentStopHookOutput` | Hook output allowing "block" or "allow" decision |
| `AgentTask` | Background subagent task with status, result, timing |
| `AssistantIntentEvent` | Ephemeral event carrying assistant intent string |
| `AssistantMessageDeltaEvent` | Streaming delta chunk with messageId, deltaContent, sizeBytes |
| `AssistantMessageEvent` | Persistent message from LLM (with tool calls & reasoning) |
| `AgentAction` | Union literal: "fix" \| "fix-pr-comment" \| "task" |
| `ApiKeyAuthInfo` | Auth config: type + apiKey + host |
| `AssessedCommand` | Command assessment with identifier + readOnly flag |

### 3. Integration Patterns Worth Noting

1. **Zod-based validation**: All events use `z_2.infer<typeof [Schema]>` for type-safe schema definitions.
2. **Ephemeral vs persistent**: Events flagged `ephemeral: true` (streaming) vs persistent (transcript).
3. **Streaming support**: `AssistantMessageDeltaEvent` accumulates chunks for incremental response building.
4. **Hook extensibility**: `AgentStopHook` allows custom decision logic ("block" | "allow") on agent completion.
5. **Hierarchical events**: Base event structure with `id`, `timestamp`, `parentId` for session tracing.
6. **MCP + OpenAI integration**: Imports from both `@modelcontextprotocol` and `openai` SDKs for multi-LLM support.
7. **Background task tracking**: `AgentTask` supports status lifecycle with optional error + modelOverride.

---

# Extension Health — 2026-02-11T02-19-33

# VS Code Extension Source Review

## 1. **extensions\chthonic-archive\src\acp\client.ts**

**Purpose:** Implements the ACP protocol client handling agent requests (file I/O, terminal creation, permission checks).

**Issues Found:**
- ❌ **Incomplete file** — cuts off mid-`readTextFile()` after `return { terminalId: id };`
- ❌ **No error handling** — `readTextFile()`, `writeTextFile()` lack try/catch; no validation on `params.path`
- ❌ **Stub method** — `terminalOutput()` always returns empty string (VS Code API limitation acknowledged but not solved)
- ❌ **Missing cleanup** — terminals never released from `Map`; no `exitHandler` tracking
- ⚠️ **Terminal arg injection risk** — `params.args` unsanitized in `sendText()`

**Integration:** 
- Consumed by: `AcpConnection` (instantiates, sets agent)
- Emits: `'session-update'` events to webview

---

## 2. **extensions\chthonic-archive\src\acp\connection.ts**

**Purpose:** Spawns `copilot.exe --acp` and establishes ACP protocol handshake.

**Issues Found:**
- ❌ **Hardcoded path** — WinGet package path is user-specific; will fail on other machines
- ❌ **Incomplete file** — cuts off at `this.initResponse = await this.connection.initialize({`; missing `protocolV` (typo?)
- ❌ **No stream error handlers** — readable/writable streams have no error event listeners
- ❌ **No timeout on initialize** — could hang indefinitely if `copilot.exe` is unresponsive
- ❌ **Process not killed on error** — thrown errors don't call `process.kill()`
- ⚠️ **Missing methods** — `isConnected()`, `cancel()`, `getClient()` referenced but not visible

**Integration:**
- Creates: `ChthonicAcpClient`, `ClientSideConnection`
- Used by: `ChthonicChatProvider` (webview in `acp/webview.ts`)

---

## 3. **extensions\chthonic-archive\src\acp\index.ts**

**Purpose:** Barrel export for ACP module.

**Issues Found:** None.

**Integration:** Re-exports `ChthonicAcpClient`, `AcpConnection`, `ChthonicChatProvider`.

---

## 4. **extensions\chthonic-archive\src\acp\webview.ts**

**Purpose:** Chat webview UI for ACP agent interaction.

**Issues Found:**
- ❌ **Incomplete file** — cuts off mid-`sendPrompt()` at `if (!this.connection?.isConnec`
- ❌ **Missing helpers** — `getHtml()`, `postMessage()` not shown
- ❌ **No state cleanup** — disconnecting doesn't call `process.kill()`
- ⚠️ **Unhandled connection loss** — if agent crashes, UI remains in "connected" state

**Integration:**
- Implements: `vscode.WebviewViewProvider` (registered as `'chthonic.chatView'`)
- Uses: `AcpConnection`
- Emits to webview: status, session-update, connected, error

---

## 5. **extensions\chthonic-archive\src\extension.ts**

**Purpose:** Main extension entry point; registers chat panel, theme switcher, SSOT hash verification.

**Issues Found:**
- ❌ **Import mismatch** — imports `ChthonicChatProvider` from `'./sdk/webview'` but file mixes ACP/SDK logic
- ❌ **Constructor signature conflict** — calls `ChthonicChatProvider(context.extensionUri, harnessPath, log)` but both `acp/webview.ts` and `sdk/webview.ts` have different signatures
- ❌ **Undefined classes/functions** — `ThemeTreeProvider`, `updateSSOTHash()` referenced but not imported/defined
- ❌ **Incomplete file** — cuts off mid-config at `if (config.get<boolean>('showLineage'`
- ❌ **Missing deactivate()** — no cleanup function
- ⚠️ **Workspace folder assumption** — no fallback if `vscode.workspace.workspaceFolders` is undefined

**Integration:**
- Registers webview provider (but path to webview is ambiguous: ACP or SDK?)
- Registers command: `chthonic.switchTheme`
- Watches: `.onDidSaveTextDocument` for SSOT hash refresh

---

## 6. **extensions\chthonic-archive\src\sdk\connection.ts**

**Purpose:** Spawns bun harness and manages JSON-lines message protocol.

**Issues Found:**
- ❌ **Incomplete file** — cuts off after process setup; missing all message-sending methods
- ❌ **Missing methods** — `authenticate()`, `isReady()`, `stop()`, `send()` referenced but not visible
- ❌ **No message correlation** — no mechanism to track pending requests or pair responses to queries
- ❌ **Timeout is hardcoded** — 15s startup timeout not configurable
- ⚠️ **No readline cleanup** — `readline.Interface` not explicitly closed on process exit

**Integration:**
- Used by: `sdk/webview.ts`
- Spawns: `bun run harness.ts`

---

## 7. **extensions\chthonic-archive\src\sdk\index.ts**

**Purpose:** Barrel export for SDK module.

**Issues Found:** None.

**Integration:** Re-exports `SdkConnection`, `ChthonicChatProvider`.

---

## 8. **extensions\chthonic-archive\src\sdk\webview.ts**

**Purpose:** SDK-powered chat webview UI (parallel to ACP webview).

**Issues Found:**
- ❌ **Incomplete file** — cuts off mid-`connectAgent()` at `this.isConne`
- ❌ **Missing methods** — `getHtml()`, `postMessage()`, `sendPrompt()`, `cancelQuery()`, `disconnectAgent()` not shown
- ❌ **Hardcoded gh auth** — assumes `gh cli` is available; no fallback
- ⚠️ **Token exposure** — token passed via `authenticate()` but no TLS/secure channel enforcement in harness

**Integration:**
- Implements: `vscode.WebviewViewProvider` (registered as `'chthonic.chatView'` — same as ACP!)
- Uses: `SdkConnection`
- Requires: `gh cli` with authentication

---

## **Cross-File Issues**

| Issue | Files Affected | Severity |
|-------|---|---|
| **Duplicate viewType** | `acp/webview.ts`, `sdk/webview.ts` both use `'chthonic.chatView'` | 🔴 Fatal (only one can register) |
| **Constructor mismatch** | `extension.ts` instantiates wrong `ChthonicChatProvider` | 🔴 Fatal |
| **Incomplete files** | 5 of 8 files cut mid-function | 🔴 Fatal (won't compile) |
| **Hardcoded paths** | `acp/connection.ts` WinGet path, `sdk/webview.ts` gh CLI | 🟡 High (portability) |
| **Missing error boundaries** | File ops, stream handlers, process spawning | 🟡 High (robustness) |

**Recommendation:** Complete all files, resolve ACP/SDK module conflict (pick one or rename one `viewType`), and add comprehensive error handling.

---

# Dependency Freshness — 2026-02-11T02-19-33

# Dependency Analysis

## Package.json (Root)
| Dependency | Version | Outdated? | Security-Sensitive | Notes |
|---|---|---|---|---|
| @modelcontextprotocol/sdk | ^1.26.0 | No | Auth/Network | MCP core—recent |
| @sentry/bun | ^10.38.0 | No | Auth/Network | Error telemetry—current |
| minimatch | ^10.1.2 | No | — | Pattern matching—current |
| @playwright/mcp | ^0.0.64 | ⚠️ | — | Pre-release (0.0.x)—unstable |

## Extensions (Archive, Mandala, StatusBar)
| Dependency | Version | Outdated? | Notes |
|---|---|---|---|
| @types/node | ^20.x | No | **CONSISTENT across all 3 extensions** |
| @types/vscode | ^1.90.0 | No | **CONSISTENT across all 3 extensions** |
| typescript | ^5.x | No | **CONSISTENT across all 3 extensions** |

## Cargo.toml (Rust)
| Dependency | Version | Outdated? | Security-Sensitive | Notes |
|---|---|---|---|---|
| winit | 0.29 | No | — | Window library—stable |
| ash | 0.38 | No | — | Vulkan bindings—recent |
| ash-window | 0.13 | No | — | Vulkan/window—aligned |
| gpu-allocator | 0.22 | No | — | GPU memory—current |
| bevy_ecs | 0.14 | ⚠️ | — | ECS—potentially trailing 0.15+ |
| serde | 1.0 | No | — | Serialization—stable |
| glam | 0.24 | No | — | Math library—current |
| **sha2** | 0.10 | No | ✅ **Crypto** | Hash function—current |
| tokio | 1.0 | No | — | Async runtime—stable |
| rand | 0.8 | No | — | RNG—current |

## Pyproject.toml (Python)
| Dependency | Version | Outdated? | Security-Sensitive | Notes |
|---|---|---|---|---|
| networkx | >=3.6,<4 | No | — | Graph library—current |
| fastmcp | >=2.14,<3 | No | Auth/Network | MCP client—recent |
| **huggingface-hub** | >=1.4.1,<2 | No | ✅ **Auth/Network** | Model downloads—requires API tokens |
| **idna** | >=3.11 | No | ✅ **Network** | Domain name encoding—security-critical |
| **requests** | >=2.32,<3 | No | ✅ **Network** | HTTP client—active maintenance required |
| radon | >=6.0.1,<7 | No | — | Code metrics—optional |
| mcp | >=1.26.0,<2 | No | Auth/Network | **Overlaps with JS root** (same SDK) |
| pydantic-settings | >=2.12.0,<3 | No | — | Config validation—current |

## Cross-Manifest Conflicts
| Issue | Details |
|---|---|
| **MCP Naming Mismatch** | `@modelcontextprotocol/sdk` (JS) vs `mcp` (Python) are the **same package**, version-aligned at 1.26.x ✅ |
| **Pre-release Extension** | `@playwright/mcp@0.0.64` is unstable; flag for upgrade when stable (1.0+) |
| **Bevy ECS Lag** | Rust: `bevy_ecs@0.14` may be behind latest (check if 0.15+ needed) |
| **No Version Pinning** | Python uses ranges (`>=X,<Y`); JS uses carets/tildes—appropriate for their contexts |

## Security Summary
🔴 **Critical Network Deps:**
- `requests` (2.32+) — Keep updated for SSL/proxy vulnerabilities
- `huggingface-hub` — Ensure token management is sandboxed
- `idna` (3.11+) — Active library; monitor for unicode attack vectors

🟢 **Crypto:** 
- `sha2@0.10` is current; suitable for archive fingerprinting

---

# Daemon Meta-Review — 2026-02-11T02-19-33

# Executive Summary: Overnight Daemon Analysis (Jan 30, 2026)

## Repeating Patterns

Three runs across 12 minutes reveal **absolute stability with zero improvement**. All PowerShell tooling scripts (`bridge-diagnostic.ps1`, `chthonic.ps1`, `chthonic-polyglot.ps1`, `claude-ide-e2e-check.ps1`) maintain a consistent debt score of **58 points** with zero TODO hits—suggesting a systemic scoring issue rather than actual code problems. The TODO hit count remains locked at **43 across all runs**, with identical files flagged each time.

## High-Debt Recidivists

Five files appear persistently:

- **`scripts/overnight_daemon.ts`** — 9+ TODO markers (self-referential: documenting TODO/FIXME/HACK pattern detection)
- **`scripts/build_epistemograph.py`** — Line 69 (epistemograph regex pattern)
- **`scripts/epistemograph_schema.sql` & `epistemograph_schema_design.md`** — Schema design TODOs
- **`logs/sessions/session_2025-12-31_0746_vscode-extension-debug.md`** — Fragment captures (false positives)

The epistemograph ecosystem is the true concern; daemon TODOs are meta-documentation about TODO detection itself.

## Trajectory

**Code health: Flat.** No files improved, no new high-debt candidates emerged, file count stable at 929–930 scanned. The PowerShell script cluster scoring 58 points has never changed, suggesting either (a) the scoring algorithm penalizes PowerShell tooling scripts systemically, or (b) the files contain characteristics that aren't being remediated.

## Top 3 Recommendations

1. **Audit PowerShell scoring logic.** Five identical 58-point scores across distinct files suggests a classifier bias, not real debt. Investigate if size-to-complexity ratios or tooling categorization is miscalibrated.

2. **Resolve epistemograph ecosystem debt.** Consolidate daemon.ts TODO markers (currently self-referential documentation), verify build_epistemograph.py line 69, and confirm schema design intent. This is the only genuine multi-file dependency pattern.

3. **Filter session log artifacts.** The 43 TODO hits include fragments from `session_2025-12-31_0746_vscode-extension-debug.md` that are capture noise, not actionable issues. Exclude session logs from daemon scans or implement a cleaning heuristic.

**Bottom line:** No regression, but no progress either. Focus on the epistemograph trio and re-validate the PowerShell scoring function.

---
