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