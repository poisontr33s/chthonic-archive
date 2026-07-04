# Chthonic Assistant - GitHub Copilot API Integration

## Architecture (KISS Pattern)

Instead of running local MCP stdio servers, the extension now uses the **same backend as VSCode's built-in Copilot Chat**.

```
User types in Chthonic sidebar
  ↓
Extension calls vscode.lm.selectChatModels()
  ↓
GitHub Copilot Chat API (HTTPS)
  ↓ (authenticated via your Pro/Plus subscription)
GitHub Models / Azure OpenAI
  ↓
Response streamed back to sidebar
```

## Key Changes

### 1. Removed MCP SDK Dependency
```json
// OLD: "@modelcontextprotocol/sdk": "^1.25.1"
// NEW: (none - uses built-in VSCode API)
```

### 2. Using VSCode Language Model API
```typescript
const models = await vscode.lm.selectChatModels({
  vendor: 'copilot',
  family: 'gpt-5.1-codex-max', // Your premium tier model
});

const response = await model.sendRequest(messages, {}, token);
```

### 3. SSOT Injection via System Prompt
```typescript
const ssotContent = await readFile('.github/copilot-instructions.md', 'utf-8');
const messages = [
  vscode.LanguageModelChatMessage.User(ssotContent), // Full SSOT as context
  vscode.LanguageModelChatMessage.User(userQuery),
];
```

## Models Available (from your settings.json)

Your Copilot Pro/Plus subscription has access to:
- `copilot/gpt-5.1-codex-max` ⭐ (selected by default)
- `copilot/gpt-5.1-codex`
- `copilot/claude-sonnet-4.5`
- `copilot/claude-opus-4.5`
- `copilot/gemini-2.5-pro`
- `copilot/gpt-4o`
- And many more...

## Benefits of This Approach

✅ **No local servers** - No need to manage stdio processes
✅ **Same auth** - Uses your existing Copilot subscription
✅ **Same models** - Access to premium GPT-5.1, Claude 4.5, etc.
✅ **SSOT injection** - Full Codex Brahmanica Perfectus as context
✅ **Simple** - KISS principle - leverages existing infrastructure

## Testing

1. Reload VSCode window: `Ctrl+R` or `Cmd+R`
2. Click the flame icon (🔥) in activity bar
3. Type a message
4. Should now get responses from **actual Copilot API** instead of echo

## Configuration

Edit `src/extension.ts` line ~123 to change model:
```typescript
family: 'gpt-5.1-codex-max', // Change to any model from your settings.json
```

Or make it user-configurable via `chthonic.copilotModel` setting in `package.json`.
