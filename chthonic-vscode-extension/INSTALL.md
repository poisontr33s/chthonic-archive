# Chthonic Assistant - Installation & Debugging

## 🔥 Quick Install

### Option 1: Developer Mode (Recommended for Testing)
```bash
# In VSCode, press F5 (opens Extension Development Host)
# OR
cd C:\Users\erdno\chthonic-archive\chthonic-vscode-extension
code --extensionDevelopmentPath=.
```

### Option 2: Build & Install VSIX
```bash
cd C:\Users\erdno\chthonic-archive\chthonic-vscode-extension

# Build
bun run build

# Package (creates .vsix)
bun run package

# Install in VSCode
# Method A: Via UI
#   1. Open Extensions (Ctrl+Shift+X)
#   2. Click ... → Install from VSIX
#   3. Select: chthonic-assistant-0.1.0.vsix

# Method B: Via Command Palette
#   1. Ctrl+Shift+P
#   2. Type: "Extensions: Install from VSIX"
#   3. Select the .vsix file
```

## 🔍 Debugging "Echo" Issue

The extension is now built with diagnostic logging. After reloading:

1. **Reload VSCode window**: `Ctrl+R` or `Developer: Reload Window`
2. **Open flame sidebar**: Click 🔥 icon in activity bar
3. **Type a message**: e.g., "test"
4. **Check Developer Console**: `Help → Toggle Developer Tools` → Console tab

### Expected Logs
```
🔥 Chthonic Archive Assistant activating...
Webview ready
Using model: copilot/gpt-4o (copilot-gpt-4o)
```

### Common Errors

**Error: "VSCode Language Model API not available"**
- **Cause**: VSCode < 1.90
- **Fix**: Update VSCode to latest version (currently 1.96+)

**Error: "No language models available"**
- **Cause**: GitHub Copilot not enabled/authenticated
- **Fix**: 
  1. Check Copilot status: Click GitHub icon in status bar
  2. Sign in if needed
  3. Verify subscription active at https://github.com/settings/copilot

**Error: "selectChatModels is not a function"**
- **Cause**: VSCode API version mismatch
- **Fix**: Check `engines.vscode` in package.json matches installed version

## 🎯 Testing Copilot Access

### Test 1: Check API Availability
Open VSCode's built-in Copilot Chat (Ctrl+Shift+I or Copilot icon) and verify it works.

### Test 2: Check Model Access
```typescript
// In VSCode Developer Console (Help → Toggle Developer Tools):
const vscode = require('vscode');
const models = await vscode.lm.selectChatModels({ vendor: 'copilot' });
console.log(models.map(m => `${m.vendor}/${m.family} (${m.name})`));
```

Expected output:
```
["copilot/gpt-4o (copilot-gpt-4o)", "copilot/claude-sonnet (...)", ...]
```

## 📝 Current Build Status

- ✅ Extension compiled: `dist/extension.js` (6.82 KB)
- ✅ Webview compiled: `dist/index.js` (0.98 MB)
- ✅ Diagnostic logging added
- ✅ Fallback model selection (gpt-4o → any copilot → any available)

## 🔄 Rebuild After Changes

```bash
cd C:\Users\erdno\chthonic-archive\chthonic-vscode-extension
bun run build  # Rebuilds both extension + webview
```

Then reload VSCode window (`Ctrl+R` in Extension Development Host).

## 🐛 If Still Echoing

The new diagnostic build will show **full error message + stack trace** in the chat. Copy that and we can debug further.
