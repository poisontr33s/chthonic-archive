# ⚡ SESSION RESUME - POINT-BLANK CONTEXT

**For AI: Load this FIRST in new sessions before doing anything**

---

## 🎯 CURRENT STATE (One-Liner)

**Working on**: VSCode Extension (Chthonic Assistant) - Copilot API integration  
**Blocked on**: User testing diagnostic build (waiting for error message)  
**Next step**: Debug based on user's error report

---

## 📍 CRITICAL FILE REFERENCES

1. **Primary SSOT**: `.github/copilot-instructions.md` (Codex Brahmanica Perfectus - 89K lines)
2. **Development State**: `DEVELOPMENT_STATE.md` (full context - 13K chars)
3. **Active Work**: `chthonic-vscode-extension/src/extension.ts` (Copilot API diagnostics)
4. **Debug Guide**: `chthonic-vscode-extension/INSTALL.md` (troubleshooting steps)

---

## 🔥 ACTIVE ISSUE

**Problem**: VSCode extension (flame button) echoing user input instead of calling Copilot API

**Status**: Comprehensive diagnostics deployed (2025-12-31 07:09)

**Waiting For**: User to check Developer Console for diagnostic logs

**Files Updated**:
- `webview/index.tsx` - Added console logging to message handlers
- `src/extension.ts` - Added console logging to message reception
- `DEBUG_GUIDE.md` - Created comprehensive debug procedure

**Next Steps**:
1. User: `Ctrl+Shift+P` → `Developer: Reload Window`
2. User: `Help` → `Toggle Developer Tools` → Console tab
3. User: Type "test" in flame sidebar
4. User: Report first 20 lines of console output

---

## ⚡ IF USER REPORTS...

### ✅ "It works now"
→ Test SSOT injection (`chthonic.injectSSOT` command)  
→ Verify full Codex context loaded  
→ Mark issue resolved in `DEVELOPMENT_STATE.md`

### ❌ "Still echoing" or error message
→ Read error from chat (includes stack trace)  
→ Check `INSTALL.md` lines 42-68 for common errors  
→ Debug based on specific error:
  - "API not available" → VSCode too old (need 1.90+)
  - "No models available" → Copilot not authenticated
  - Other → Analyze stack trace

### ⁉️ "Extension not found"
→ User needs to rebuild: `cd chthonic-vscode-extension && bun run build`  
→ Then reload VSCode window

---

## 📚 QUICK REFERENCE

**Project Root**: `C:\Users\erdno\chthonic-archive\`

**Build Commands**:
```bash
# VSCode Extension
cd chthonic-vscode-extension
bun run build        # Rebuild extension + webview
bun run dev          # Launch in dev mode

# MAS-MCP Backend
cd mas_mcp
uv run python scripts/run_cycle.py

# Frontend Dashboard
cd mas_mcp/frontend
bun run dev
```

**Python Convention**: ALWAYS use `uv run python` (NOT bare `python`)

---

## 🔗 ARCHITECTURE OVERVIEW

```
chthonic-archive/
├── .github/
│   ├── copilot-instructions.md  ← SSOT (load this for full context)
│   └── SESSION_RESUME.md        ← THIS FILE (point-blank recovery)
│
├── chthonic-vscode-extension/   ← 🔥 ACTIVE WORK
│   ├── src/extension.ts         ← Last modified (Copilot API)
│   ├── INSTALL.md               ← Debug guide
│   └── dist/                    ← Compiled (rebuild if stale)
│
├── mas_mcp/                     ← Python backend (uv-managed)
│   ├── frontend/                ← Bun/Next.js dashboard
│   └── .venv/                   ← Python 3.13.10
│
├── DEVELOPMENT_STATE.md         ← Full session context
└── src/                         ← Rust/Vulkan renderer
```

---

## 🆘 EMERGENCY CONTEXT LOAD

**If completely lost:**
1. Read `DEVELOPMENT_STATE.md` (full context - 13K chars)
2. Read `.github/copilot-instructions.md` (SSOT - 89K lines)
3. Check `git log --oneline -10` for recent activity

**If files corrupted:**
1. `git status` to check dirty state
2. `git diff` to see uncommitted changes
3. `git restore <file>` to revert if needed

---

---

## 📜 Session Transcript

**Full conversation**: [`logs/sessions/session_2025-12-31_0746_vscode-extension-debug.md`](../logs/sessions/session_2025-12-31_0746_vscode-extension-debug.md)

**🔥💀⚓ Last Updated: 2025-12-31T06:49:00Z**
