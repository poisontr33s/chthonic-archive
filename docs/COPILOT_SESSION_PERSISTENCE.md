# Copilot CLI Session Persistence Guide

<!--
@SID:           DOC_COPILOT_SESSION_PERSISTENCE
@Type:          User Guide
@Context:       Workflow / Session Management
@SessionOrigin: SESSION_DOC_2026_01_17_CLEANUP
@References:    SESSION_BOOTSTRAP_SPEC
-->

**Immaculate session saving using built-in Copilot CLI commands**

---

## 🎯 Built-In Session Commands

The GitHub Copilot CLI has **native session persistence**:

### `/share` - Save Session to File or GitHub Gist

**Syntax**:
```bash
/share [file|gist] [path]
```

**Options**:
- `/share file` - Save to local markdown file (default location)
- `/share file <path>` - Save to specific path
- `/share gist` - Upload to GitHub Gist (requires authentication)

**Default Save Location**:
- Likely: `$HOME/.copilot/sessions/` or similar
- Check with: `/session` command for current session info

---

## 📋 Session Commands

### `/session` - Show Current Session Info

```bash
/session
```

**Shows**:
- Session ID
- Duration
- Token usage
- Model used
- Conversation history metadata

### `/context` - View Context Window

```bash
/context
```

**Shows**:
- Token usage visualization
- Files loaded
- Context size

### `/usage` - Session Metrics

```bash
/usage
```

**Shows**:
- Session usage statistics
- Premium request count
- Token consumption

---

## 🔥 Recommended Session Workflow

### During Active Session

**Every major milestone** (e.g., after fixing a bug, completing a feature):
```bash
/share file C:\Users\erdno\chthonic-archive\logs\sessions\session_2025-12-31_0642_vscode-extension.md
```

**Naming Convention**:
```
session_YYYY-MM-DD_HHMM_<topic>.md
```

**Example**:
```
session_2025-12-31_0642_vscode-extension.md
session_2025-12-31_0830_gpu-stack-debug.md
session_2025-12-31_1415_frontend-dashboard.md
```

### End of Session

1. **Save final state**:
   ```bash
   /share file logs/sessions/session_FINAL_2025-12-31.md
   ```

2. **Check session stats**:
   ```bash
   /usage
   ```

3. **Update session docs** (manual):
   - Add summary to `../session_resumption_chthonic_progress.md`
   - Update `../DEVELOPMENT_STATE.md` with changes
   - Commit to git

---

## 🗂️ Session Archive Structure

**Create in project**:
```
chthonic-archive/
├── logs/
│   └── sessions/
│       ├── session_2025-12-31_0642_vscode-extension.md
│       ├── session_2025-12-31_0830_gpu-stack-debug.md
│       └── session_FINAL_2025-12-31.md
```

**Each saved session contains**:
- Full conversation history
- Code snippets generated
- File modifications discussed
- Commands executed (if mentioned)
- Timestamps

---

## 🔄 Session Recovery Workflow

### Starting New Session

1. **Load session resumption hub**:
   ```bash
   cat session_resumption_chthonic_progress.md
   ```

2. **Load previous session transcript** (if exists):
   ```bash
   cat logs/sessions/session_FINAL_<date>.md
   ```

3. **Tell Copilot** (in chat):
   ```
   I'm resuming from a previous session. Key context:
   - Last working on: VSCode extension Copilot API
   - Last file modified: chthonic-vscode-extension/src/extension.ts
   - Next step: Test diagnostic build
   
   See session_resumption_chthonic_progress.md for full context.
   ```

4. **Copilot loads context** from:
   - Your message
   - `../session_resumption_chthonic_progress.md` (if mentioned)
   - `.github/copilot-instructions.md` (auto-loaded as SSOT)

---

## 💡 Advanced: GitHub Gist Integration

**Share to public/private gist**:
```bash
/share gist
```

**Benefits**:
- Shareable URL
- Version history (if updated)
- Accessible from anywhere
- Can be referenced in GitHub issues/PRs

**Use Case**: Share debugging session with collaborators

---

## 🛠️ Session Metadata Best Practices

**At session start** (first message):
```
Session Start: 2025-12-31 06:42
Focus: VSCode Extension - Copilot API Integration
Context loaded from: session_resumption_chthonic_progress.md
Previous session: logs/sessions/session_2025-12-30_final.md
```

**At major checkpoints**:
```bash
# After fixing bug
/share file logs/sessions/session_2025-12-31_0642_checkpoint1_api-fixed.md

# After testing
/share file logs/sessions/session_2025-12-31_0715_checkpoint2_tested.md
```

**At session end**:
```bash
/share file logs/sessions/session_2025-12-31_FINAL.md
/usage  # Record token usage
```

---

## 📊 Integration with Existing Docs

**Update workflow** after session save:

1. **Save Copilot session**:
   ```bash
   /share file logs/sessions/session_2025-12-31_0642.md
   ```

2. **Update DEVELOPMENT_STATE.md**:
   - Add session to change log
   - Update "Files Modified This Session"
   - Update "Last Updated" timestamp

3. **Update session_resumption_chthonic_progress.md**:
   - Add session to "Session History"
   - Update "Last Modified" date

4. **Commit to git**:
   ```bash
   git add logs/sessions/ DEVELOPMENT_STATE.md session_resumption_chthonic_progress.md
   git commit -m "Session checkpoint: VSCode extension Copilot API fix"
   ```

---

## 🎓 Complete Session Persistence Stack

**Tier 1: Real-time (Copilot CLI built-in)**
- `/share` - Save conversation transcript
- `/session` - Current session metadata
- `/context` - Live context window
- `/usage` - Token usage stats

**Tier 2: Human-maintained (Our docs)**
- `../session_resumption_chthonic_progress.md` - Navigation hub
- `.github/SESSION_RESUME.md` - Point-blank recovery
- `../DEVELOPMENT_STATE.md` - Full context

**Tier 3: Version Control (Git)**
- Commit saved sessions to `logs/sessions/`
- Track file modifications
- Preserve history

**Result**: Triple-redundant session recovery with zero data loss

---

## 🚀 Try It Now

**Save current session**:
```bash
/share file logs/sessions/session_2025-12-31_0642_vscode-copilot-api.md
```

**Then check**:
```bash
cat logs/sessions/session_2025-12-31_0642_vscode-copilot-api.md
```

**You should see**:
- This entire conversation
- All code snippets
- File paths discussed
- Commands suggested

---

**🔥💀⚓ Immaculate Session Persistence Achieved 🔥💀⚓**

**Created**: 2025-12-31T06:42:51Z  
**Session ID**: (check with `/session` command)
