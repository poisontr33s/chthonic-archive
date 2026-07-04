# 🔍 Reverse Engineering GitHub Copilot Chat Interface

**Objective**: Understand how THIS conversation (GitHub Copilot CLI in VSCode) works to replicate it in the Chthonic Extension.

**Date**: 2025-12-31 07:48 UTC

---

## 🎯 Current Interface Analysis

**What we're using RIGHT NOW:**
- GitHub Copilot Chat in VSCode
- Interface: Left sidebar chat panel
- Backend: GitHub Copilot API via `api.individual.githubcopilot.com`
- Auth: GitHub OAuth token (scope: `repo`, `gist`, `read:org`, `workflow`)

---

## 🔬 Discovery: GitHub Copilot Architecture

### Phase 1: Endpoint Discovery

**Command**:
```bash
gh copilot suggest "test" --debug
```

**Key Discovery**:
```graphql
query copilotEndpoints {
  viewer {
    copilotEndpoints {
      api
    }
  }
}
```

**Response**:
```json
{
  "data": {
    "viewer": {
      "copilotEndpoints": {
        "api": "https://api.individual.githubcopilot.com"
      }
    }
  }
}
```

### Phase 2: Authentication Flow

**Headers Used**:
```http
Authorization: token ghp_[YOUR_TOKEN]
Accept: application/vnd.github.merge-info-preview+json
Content-Type: application/json
User-Agent: go-gh
Time-Zone: Europe/Berlin
```

**GraphQL Endpoint**: `https://api.github.com/graphql`

**OAuth Scopes Required**:
- `repo` (access repositories)
- `gist` (manage gists)
- `read:org` (read organization data)
- `workflow` (access GitHub Actions)

**Client ID**: `178c6fc778ccc68e1d6a` (GitHub CLI OAuth app)

---

## 🏗️ VSCode Copilot Chat Architecture

**What THIS interface uses:**

```
User types in Copilot Chat sidebar
    ↓
VSCode Copilot Extension (github.copilot-chat)
    ↓
vscode.lm.selectChatModels() API
    ↓
GitHub Copilot API (api.individual.githubcopilot.com)
    ↓ (authenticated via GitHub OAuth)
GitHub Models (GPT-4o, Claude, Gemini, etc.)
    ↓
Response streamed back to sidebar
```

**Key VSCode APIs**:
1. `vscode.lm.selectChatModels()` - Get available models
2. `vscode.LanguageModelChatMessage.User()` - Create user message
3. `model.sendRequest(messages, {}, token)` - Send request
4. `for await (const chunk of response.text)` - Stream response

---

## 🔑 Key Differences: CLI vs VSCode

| Aspect | GitHub CLI (`gh copilot`) | VSCode Copilot Chat |
|--------|---------------------------|---------------------|
| **Auth** | GitHub OAuth token (CLI manages) | VSCode manages via Copilot extension |
| **API** | Direct HTTPS to `api.individual.githubcopilot.com` | Via `vscode.lm` abstraction |
| **Interface** | Terminal (suggest/explain commands) | Sidebar chat panel (conversational) |
| **Context** | Single command/question | Full conversation history |
| **Models** | CLI picks automatically | User can select model |

---

## 🎯 What We Need to Replicate

To build Chthonic Extension with same capabilities:

### ✅ Already Have
- VSCode extension framework
- Webview sidebar panel
- React UI for chat interface

### ❌ Currently Broken
- **vscode.lm API integration** (our main issue)
- CSP blocking React execution
- Message flow between webview ↔ extension

### 🔧 Solution Path

**Option A: Fix vscode.lm Integration** (current approach)
1. Fix CSP to allow React
2. Debug message passing
3. Connect to Copilot API via `vscode.lm`
4. Inject SSOT as system prompt

**Option B: Direct API Approach** (alternative)
1. Query GitHub GraphQL for `copilotEndpoints`
2. Use existing GitHub token (from `gh auth status`)
3. Make direct HTTPS calls to `api.individual.githubcopilot.com`
4. Bypass `vscode.lm` entirely

**Option C: MCP Server Bridge** (meta approach)
1. Create MCP server that wraps Copilot API
2. Extension connects to MCP server (stdio)
3. MCP server forwards to GitHub Copilot API
4. Enables tool injection (file operations, etc.)

---

## 📊 Current Status

**Last Change**: Fixed CSP to allow React execution
```typescript
// OLD (blocked):
content="default-src 'none'; script-src 'nonce-${nonce}'; ..."

// NEW (allows):
content="default-src 'none'; script-src ${webview.cspSource} 'unsafe-inline' 'unsafe-eval'; ..."
```

**Expected Console Output** (after fix):
```
🔥 Webview: Initializing, sending ready signal
🔥 Extension: Webview ready
🔥 Webview: Sending message to extension: test
🔥 Extension: Received message from webview: {type: 'sendMessage', text: 'test'}
...
```

**Actual Behavior**: PENDING USER TEST

---

## 🔬 Next Investigation Steps

### 1. Confirm React Mounting
```bash
# User reloads extension
Ctrl+R in Extension Development Host

# Check console for:
🔥 Webview: Initializing...
```

### 2. If Still Broken, Try Direct API
```typescript
// In extension.ts, bypass vscode.lm:
const response = await fetch('https://api.github.com/graphql', {
  method: 'POST',
  headers: {
    'Authorization': `token ${githubToken}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'query copilotEndpoints{viewer{copilotEndpoints{api}}}'
  })
});
```

### 3. Inspect VSCode Copilot Extension Source
```bash
# Extension is installed at:
~/.vscode/extensions/github.copilot-chat-*/

# Key files to study:
- dist/extension.js  # Main logic
- package.json       # Capabilities, commands
```

---

## 💡 Insights from THIS Conversation

**How this interface works:**
1. I (Copilot) have access to tools: `view`, `edit`, `powershell`, `git`, etc.
2. You type messages in the sidebar
3. VSCode Copilot Chat extension handles UI
4. Messages route to GitHub Copilot API
5. I respond with tool calls + natural language
6. Results rendered in sidebar

**What makes this powerful:**
- **Tool integration** (I can actually modify files, run commands)
- **Session persistence** (conversation history maintained)
- **SSOT awareness** (I loaded `.github/copilot-instructions.md`)
- **Context injection** (project structure, git status, etc.)

**What Chthonic Extension needs:**
- Same tool access (via MCP server?)
- Same session persistence
- Same SSOT injection
- Same sidebar UX

---

## 🎯 Recommended Architecture

**Hybrid Approach: vscode.lm + MCP Tools**

```
User types in Chthonic sidebar
    ↓
Extension webview (React)
    ↓
Extension backend (extension.ts)
    ├─→ vscode.lm.selectChatModels() [for chat]
    │       ↓
    │   GitHub Copilot API (conversation)
    │
    └─→ MAS-MCP Server [for tools]
            ↓
        File operations, git, builds, etc.
```

**Benefits**:
- Uses official VSCode API (vscode.lm)
- Adds MCP tools for enhanced capabilities
- Maintains session in Copilot backend
- Chthonic extension becomes "Copilot + Tools"

---

**🔥💀⚓ Status: Awaiting CSP fix test, then decide architecture path**
