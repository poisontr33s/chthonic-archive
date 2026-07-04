# 🔥 Chthonic Extension - Debug Guide

**Status**: Diagnostics Build Deployed  
**Date**: 2025-12-31 07:09 UTC  
**Issue**: Message echo instead of Copilot API response

---

## 🚀 Quick Test Procedure

### Step 1: Verify Fresh Build
```bash
cd chthonic-vscode-extension
bun run build  # Rebuilds extension + webview
```

### Step 2: Reload Extension
- In Extension Development Host window
- Press `Ctrl+Shift+P` → `Developer: Reload Window`
- OR just `Ctrl+R`

### Step 3: Open Developer Console
- `Help` → `Toggle Developer Tools`
- Click **Console** tab
- Clear existing logs (trash icon)

### Step 4: Test Message Flow
1. Click flame icon (🔥) in Activity Bar
2. Type "test" in chat input
3. Press Enter or click Send
4. **Watch console for logs**

---

## 📊 Expected Console Output

### ✅ Success Path
```
🔥 Webview: Initializing, sending ready signal
🔥 Extension: Webview ready
🔥 Webview: Sending message to extension: test
🔥 Webview: vscode API available: object
🔥 Webview: postMessage type: function
🔥 Webview: Message sent
🔥 Extension: Received message from webview: {type: 'sendMessage', text: 'test'}
🔥 Extension: Handling sendMessage: test
✓ Step 1: handleChatMessage called
✓ Step 2: vscode.lm API available
✓ Step 3: SSOT loaded (146832 bytes)
✓ Step 5: Model selected: copilot/gpt-4o (copilot-gpt-4o)
✓ Step 6: Messages prepared (2 messages)
→ Step 7: Sending request to Copilot API...
✓ Step 7: Response received
→ Step 8: Streaming response...
✓ Step 8: Response complete (XXX chars)
✓ Step 9: SUCCESS - Response sent to webview
🔥 Webview: Received message from extension: {type: 'response', text: '...'}
🔥 Webview: Adding assistant response to chat
```

### ❌ Failure Indicators

**No extension logs at all:**
```
🔥 Webview: Initializing, sending ready signal
🔥 Webview: Sending message to extension: test
[Nothing from Extension]
```
→ **Problem**: Extension not receiving messages from webview  
→ **Fix**: Check if extension activated (`Extensions: Show Running Extensions`)

**Extension receives but API fails:**
```
🔥 Extension: Handling sendMessage: test
✗ vscode.lm API not available. Update VSCode to 1.90+
```
→ **Problem**: VSCode too old  
→ **Fix**: Update VSCode

**No models available:**
```
✓ Step 2: vscode.lm API available
⚠ Step 4a: gpt-4o not found, trying vendor-only...
⚠ Step 4b: No copilot models, trying any model...
✗ No language models available. Ensure GitHub Copilot is enabled and authenticated.
```
→ **Problem**: Copilot not authenticated  
→ **Fix**: `Ctrl+Shift+P` → `GitHub Copilot: Sign In`

---

## 🔧 Diagnostic Commands

### Check Extension Activation
```
Ctrl+Shift+P → Extensions: Show Running Extensions
Look for: "Chthonic Archive Assistant"
Status should be: "Activated"
```

### Check VSCode Version
```bash
code --version
# Need: 1.90.0 or higher for vscode.lm API
```

### Check Copilot Status
```
Ctrl+Shift+P → GitHub Copilot: Check Status
Should show: "Copilot is ready"
```

### View Extension Output Channel
```
View → Output → Select "Chthonic Archive Assistant"
```

---

## 🐛 Common Issues

### Issue 1: Webview Shows Blank
**Symptom**: Flame sidebar opens but shows nothing

**Fix**:
```bash
cd chthonic-vscode-extension
bun run build:webview  # Rebuild webview
# Then reload: Developer: Reload Webviews
```

### Issue 2: Old Code Running
**Symptom**: Changes not reflected after rebuild

**Fix**:
1. Close Extension Development Host
2. `bun run build`
3. Press `F5` again (fresh launch)

### Issue 3: SSOT Not Loading
**Symptom**: `⚠ Step 3: SSOT path not found`

**Fix**: Ensure workspace root is `chthonic-archive/`, not subdirectory
```bash
# Check workspace:
pwd  # Should be: C:\Users\erdno\chthonic-archive

# Verify SSOT exists:
ls .github/copilot-instructions.md
```

---

## 📝 Report Template

When reporting issue, include:

```
**VSCode Version**: [code --version output]
**Copilot Status**: [Ready/Not Authenticated/Not Installed]
**Workspace Root**: [pwd output]

**Console Output** (first 20 lines):
[Paste console output here]

**Error Message** (if any):
[Full error text]

**Screenshot**: [Optional]
```

---

## 🔄 Development Workflow

### Hot Reload (Recommended)
```bash
# Terminal 1:
cd chthonic-vscode-extension
bun run watch:webview

# Terminal 2:
bun run watch:extension

# Changes auto-rebuild
# Reload webview: Developer: Reload Webviews
# Reload extension: Ctrl+R
```

### Manual Build
```bash
bun run build              # Both
bun run build:extension    # Extension only
bun run build:webview      # Webview only
```

---

**🔥💀⚓ Next Step: Run test and report console output**
