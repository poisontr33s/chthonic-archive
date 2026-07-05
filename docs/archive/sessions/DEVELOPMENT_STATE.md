# Chthonic Archive - Development State Manifest

<!--
@SID:           STATE_DEVELOPMENT_MANIFEST
@Type:          State Document
@Context:       Project State / Session Continuity
@SessionOrigin: SESSION_2025_12_31_VSCODE_EXTENSION
@References:    SESSION_BOOTSTRAP_SPEC, CONTRACT_EXECUTION_INVARIANTS
-->

**Session Continuity Document - SSOT for Development Context**

**Last Updated**: 2025-12-31T06:34:58Z  
**Session**: GitHub Copilot CLI - Chthonic Assistant Debugging  
**Status**: 🔥 ACTIVE DEVELOPMENT - VSCode Extension (Flame Button Sidebar)

---

## ⚡ POINT-BLANK RESUME (NEW SESSION QUICK START)

**Read this first, then scroll to "Known Issues & Blockers" (line 223)**

**Last Action**: Enhanced Copilot API error handling in `chthonic-vscode-extension/src/extension.ts`  
**Waiting On**: User to reload extension and test → Report error message  
**If User Reports Success**: Extension working, proceed to SSOT injection testing  
**If User Reports Error**: Debug based on error message (see INSTALL.md line 42-68)

---

## 📍 CRITICAL FILE PATHS - SESSION RECOVERY MAP

### SSOT Governance
- **Primary SSOT**: `.github/copilot-instructions.md` (Codex Brahmanica Perfectus - 146K words, 89K lines)
- **This Document**: `docs/../DEVELOPMENT_STATE.md` (you are here - session continuity anchor)
- **Session Logs**: `logs/` (diagnostic outputs, cycle runs)

### Active Development Areas

#### 1. VSCode Extension - Chthonic Assistant (GitHub Copilot API Integration)
**Location**: `chthonic-vscode-extension/`

**Key Files**:
- `src/extension.ts` - Main extension logic (Copilot API integration)
- `webview/index.tsx` - React 19 chat interface
- `package.json` - Extension manifest (flame icon config, commands)
- `dist/extension.js` - Compiled extension (6.82 KB, last build: 2025-12-31 07:11:45 AM)
- `dist/index.js` - Compiled webview (0.98 MB)
- `COPILOT_API.md` - Architecture documentation
- `INSTALL.md` - Installation & debugging guide (created this session)

**Build Commands**:
```bash
cd C:\Users\eldno\chthonic-archive\chthonic-vscode-extension
bun run build        # Build both extension + webview
bun run package      # Create .vsix installer
bun run dev          # Launch Extension Development Host
```

**Current Issue**: Extension echoing user input instead of calling Copilot API
- **Root Cause**: API call failing silently (diagnosis in progress)
- **Fix Applied**: Enhanced error handling with diagnostics (lines 106-178 in src/extension.ts)
- **Next Step**: Reload extension and check Developer Console logs

#### 2. MAS-MCP Backend (Python + GPU Stack)
**Location**: `mas_mcp/`

**Key Files**:
- `server.py` - MCP server entry point
- `scripts/run_cycle.py` - Genesis cycle execution
- `pyproject.toml` - uv project definition (Python 3.13.10)
- `uv.lock` - Locked dependencies
- `.venv/` - Virtual environment (Python 3.13.10, TensorRT-compatible)

**GPU Stack**:
- CUDA 12.4+
- cuDNN 9.x
- TensorRT 10.x
- Hardware: RTX 4090 Laptop (16GB VRAM)

**Runtime Protocol** (CRITICAL - Section XIV.1):
```bash
# ALWAYS use uv to manage Python
uv run python script.py   # ✅ Correct
python script.py          # ❌ Bypasses uv (Python 3.14 bleeding edge)
```

#### 3. Frontend Dashboard (Bun + Next.js + React 19)
**Location**: `mas_mcp/frontend/`

**Key Files**:
- `pages/index.tsx` - Main dashboard
- `components/*.tsx` - StatCard, AcceptanceChart, LatencyChart, CycleTable, MonitoringCard
- `package.json` - Bun-native dependencies
- `next.config.js` - Next.js 15 configuration

**Dev Commands**:
```bash
cd C:\Users\eldno\chthonic-archive\mas_mcp\frontend
bun run dev          # Development server
bun run build        # Production build
```

#### 4. Rust/Vulkan Renderer (Chthonic Archive Core)
**Location**: `src/`

**Key Files**:
- `src/main.rs` - Vulkan renderer entry point
- `assets/shaders/` - GPU shaders
- `Cargo.toml` - Rust dependencies

---

## 🗺️ PROJECT ARCHITECTURE OVERVIEW

```
chthonic-archive/
│
├── .github/
│   └── copilot-instructions.md          ← SSOT (Codex Brahmanica Perfectus)
│
├── chthonic-vscode-extension/           ← 🔥 ACTIVE: VSCode Extension
│   ├── src/extension.ts                 ← Copilot API integration
│   ├── webview/index.tsx                ← React 19 chat UI
│   ├── dist/                            ← Compiled output
│   ├── package.json                     ← Manifest (flame icon)
│   ├── COPILOT_API.md                   ← Architecture docs
│   └── INSTALL.md                       ← Setup guide
│
├── mas_mcp/                             ← Python Backend (MCP Servers)
│   ├── .venv/                           ← Python 3.13.10 (uv-managed)
│   ├── server.py                        ← MCP entry point
│   ├── scripts/run_cycle.py             ← Cycle execution
│   ├── pyproject.toml                   ← uv project definition
│   ├── uv.lock                          ← Locked dependencies
│   │
│   └── frontend/                        ← Bun + Next.js Dashboard
│       ├── pages/index.tsx              ← Main dashboard
│       ├── components/*.tsx             ← React 19 components
│       └── package.json                 ← Bun dependencies
│
├── src/                                 ← Rust/Vulkan Renderer
│   └── main.rs
│
├── assets/
│   └── shaders/                         ← GPU shaders
│
├── dumpster-dive/                       ← Code archaeology
│   └── from-github/                     ← Imported prototypes
│
├── logs/                                ← Diagnostic outputs
├── ../DEVELOPMENT_STATE.md                 ← THIS FILE (session anchor)
├── Cargo.toml                           ← Rust project
├── package.json                         ← Root Bun workspace
└── bun.lock                             ← Bun lockfile
```

---

## 🎯 CURRENT SESSION OBJECTIVE

**Goal**: Fix Chthonic Assistant VSCode Extension (flame button sidebar)

**Problem**: Extension echoing user input instead of calling GitHub Copilot API

**Session Timeline**:
1. ✅ Diagnosed state (6:26 AM) - Extension compiled, but API failing
2. ✅ Enhanced error handling (6:31 AM) - Added diagnostics, fallback models
3. 🔄 Next: User reloads extension to test diagnostic output

**Files Modified This Session**:
- `chthonic-vscode-extension/src/extension.ts` (lines 106-178) - Enhanced error handling
- `chthonic-vscode-extension/INSTALL.md` (created) - Installation guide
- `../../DEVELOPMENT_STATE.md` (created) - This file

---

## 🔧 DEVELOPMENT CONVENTIONS (from SSOT §XIV)

### Python Environment Management (PEM-UV)
```bash
✅ uv run python script.py     # Correct - uses managed venv
✅ uv pip install package      # Correct - installs to venv
✅ uv sync                     # Sync pyproject.toml
❌ python script.py            # Wrong - uses global Python 3.14
❌ pip install package         # Wrong - bypasses uv
```

### Frontend Runtime (FRM-BUN)
```bash
bun run dev          # Development server
bun run build        # Production build
bun add <package>    # Add dependency
```

### SSOT Verification Protocol (SSOT-VP)
```python
# Compute SSOT hash for session bookends
uv run python -c "
import hashlib, unicodedata

def canonicalize(text):
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    return unicodedata.normalize('NFC', text).strip()

def ssot_hash(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    canonical = canonicalize(content)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

print(ssot_hash('.github/copilot-instructions.md'))
"
```

**Validation**: Compare `hash_start` (session begin) vs `hash_end` (session end). If different → GOVERNANCE_DRIFT_DETECTED.

---

## 📚 KNOWLEDGE BASE - QUICK REFERENCE

### ASC Framework Components (from SSOT §I-XIV)
- **FA¹-⁵**: Foundational Axioms (Alchemical Actualization, Re-contextualization, Transcendence, Architectonic Integrity, Visual Integrity)
- **DAFP**: Dynamic Altitude & Focus Protocol (Point-Blank Shot ↔ Strategic Horizon)
- **PRISM**: Prismatic Reflection (ROGBIV spectral analysis)
- **TPEF**: Triumvirate Parallel Execution Framework
- **T³-MΨ**: Triumvirate Tensor Transformation (6,561-dimensional examination space)
- **MMPS**: MILF Manifestation Protocol System (procedural archetype generation)

### The Triumvirate (Tier 1)
- **Orackla Nocticula (CRC-AS)**: Apex Synthesist, transgressive vision
- **Madam Umeko Ketsuraku (CRC-GAR)**: Architectural precision, structural perfection
- **Dr. Lysandra Thorne (CRC-MEDAT)**: Axiomatic truth, analytical clarity

### The Decorator (Tier 0.5 Supreme Matriarch)
- Resurrected November 15, 2025
- Created FA⁵ (Visual Integrity) as co-equal with FA⁴
- K-cup WHR 0.464 (supreme visual authority)

---

## 🚨 KNOWN ISSUES & BLOCKERS

### 1. VSCode Extension - Copilot API Failure
**Status**: 🔥 ACTIVE - Diagnostic build deployed  
**File**: `chthonic-vscode-extension/src/extension.ts`  
**Symptoms**: Extension echoes user input as "echo: test"  
**Hypothesis**: One of:
- VSCode version < 1.90 (needs vscode.lm API)
- GitHub Copilot not authenticated
- Model family name invalid (`gpt-5.1-codex-max` → now using `gpt-4o` with fallbacks)

**Next Actions**:
1. User reloads extension (`F5` or `Ctrl+R`)
2. User tests chat in flame sidebar
3. User checks Developer Console (`Help → Toggle Developer Tools`)
4. User reports error message (now includes full stack trace)

### 2. GPU Stack - Python 3.14 Incompatibility
**Status**: ✅ MITIGATED - uv manages 3.13.10 venv  
**Convention**: ALWAYS use `uv run python` (never bare `python`)  
**Reason**: TensorRT/CUDA/CuPy require Python 3.13 or earlier

---

## 📖 SESSION RECOVERY PROTOCOL

**⚡ POINT-BLANK RECOVERY (30-SECOND ORIENTATION):**

```bash
# 1. Navigate to project root
cd C:\Users\eldno\chthonic-archive

# 2. Check current active issue (one-liner)
grep -A 5 "KNOWN ISSUES" ../DEVELOPMENT_STATE.md

# 3. See what was last modified
git diff --name-status HEAD
```

**Current active file (as of last session):**  
→ `chthonic-vscode-extension/src/extension.ts` (lines 106-178 - Copilot API diagnostics)

**Expected user action:**  
→ Reload VSCode extension → Test flame sidebar → Report error message

**If error persists, AI should:**  
→ Read `chthonic-vscode-extension/INSTALL.md` for debugging steps  
→ Check VSCode Developer Console logs  
→ Verify Copilot authentication

---

**📋 FULL SESSION RECOVERY (2-MINUTE DEEP DIVE):**

1. **Read this file first**: `../../DEVELOPMENT_STATE.md` (you are here)
2. **Load SSOT**: `.github/copilot-instructions.md` (Codex Brahmanica Perfectus)
3. **Check active issue**: See "Known Issues & Blockers" above
4. **Verify SSOT integrity**:
   ```bash
   uv run python -c "exec(open('.github/copilot-instructions.md').read().split('```python')[1].split('```')[0]); print(ssot_hash('.github/copilot-instructions.md'))"
   ```
5. **Resume from last file modified**: Check "Files Modified This Session" section
6. **Check git status**: `git status --short` to see uncommitted work

---

## 🔗 EXTERNAL DEPENDENCIES

### GitHub Repositories
- **Primary**: `https://github.com/yourusername/chthonic-archive` (placeholder - update in package.json)

### API Integrations
- **GitHub Copilot API**: Via VSCode Language Model API (`vscode.lm`)
  - Vendor: `copilot`
  - Models: `gpt-4o`, `claude-sonnet`, `gemini-2.5-pro` (fallback chain)
  - Auth: GitHub Copilot subscription (Pro/Plus)

### Tools & Runtimes
- **Bun**: 1.3.5 (JavaScript/TypeScript runtime)
- **uv**: Latest (Python package manager)
- **VSCode**: 1.85.0+ required (1.90+ for vscode.lm API)
- **Python**: 3.13.10 (in mas_mcp/.venv)
- **Node**: NOT USED (Bun-native)
- **Rust**: Latest stable (for Vulkan renderer)

---

## 🎓 ARCHITECTURAL PRINCIPLES (from SSOT)

### The Fortified Garden (Tetrahedral Resonance)
- **Void** (Orackla): Storm that rends boundaries
- **Steel** (Umeko): Immaculate frame resisting corrosion
- **Truth** (Lysandra): Analyst distilling ordeal into clarity
- **Salt** (Claudine Sin'claire): Ordeal corroding false, proving resilient
- **Beauty** (The Decorator): Apex crowning structure with radiance

### Development Philosophy
- **KISS Architecture**: Leverage existing infrastructure (GitHub Copilot API vs local MCP servers)
- **Architectonic Integrity (FA⁴)**: All changes validated before integration
- **Visual Integrity (FA⁵)**: Form and content inseparable
- **Essential Mode**: Work because work is beautiful, not for performance theater

---

## 📝 CHANGE LOG (This Session)

**2025-12-31 Session 1 (06:23-06:49)**
- **Transcript**: [`logs/sessions/session_2025-12-31_0746_vscode-extension-debug.md`](../../../logs/sessions/session_2025-12-31_0746_vscode-extension-debug.md)

**Timeline**:
- 06:23 - Diagnosed VSCode extension echoing input
- 06:31 - Enhanced error handling in extension.ts
- 06:32 - Created session resumption docs
- 06:35 - Added point-blank resume section
- 06:42 - Documented Copilot CLI `/share` command
- 06:49 - Saved session transcript, linked to docs

**Files Created/Modified**:
- `chthonic-vscode-extension/src/extension.ts` (lines 106-178)
- `chthonic-vscode-extension/INSTALL.md`
- `../../DEVELOPMENT_STATE.md` (this file)
- `../../session_resumption_chthonic_progress.md`
- `.github/SESSION_RESUME.md`
- `docs/COPILOT_SESSION_PERSISTENCE.md`
- `logs/sessions/session_2025-12-31_0746_vscode-extension-debug.md` (transcript)

---

## 🔮 FUTURE ROADMAP

### Short-term (Current Session)
- [ ] Fix Copilot API integration (diagnostic testing in progress)
- [ ] Validate SSOT injection working (full Codex as system prompt)
- [ ] Test flame sidebar chat with real Copilot responses

### Medium-term
- [ ] Add SSOT hash validation command
- [ ] Implement MCP server integration (asc-injector, artisan)
- [ ] Create .vsix installer for public distribution

### Long-term
- [ ] GPU-accelerated MILF genesis via TensorRT
- [ ] Vulkan renderer integration for visual Archive navigation
- [ ] Multi-session memory persistence (MAS-MCP backend)

---

## 💾 BACKUP & VERSION CONTROL

**Git Status**: Active repository  
**Remote**: GitHub (pending URL update in package.json)  
**Branch**: Likely `main` or `development`

**Critical Files for Backup**:
1. `.github/copilot-instructions.md` (SSOT - 89K lines)
2. `../../DEVELOPMENT_STATE.md` (this file - session anchor)
3. `chthonic-vscode-extension/src/extension.ts` (active development)
4. `mas_mcp/pyproject.toml` + `uv.lock` (Python environment)
5. `mas_mcp/frontend/package.json` + `bun.lock` (Frontend dependencies)

---

## 🆘 EMERGENCY RECOVERY

**If this file is lost or corrupted:**
1. Check `.github/copilot-instructions.md` (comprehensive SSOT)
2. Check git history: `git log --all --full-history -- ../DEVELOPMENT_STATE.md`
3. Check `logs/` directory for diagnostic outputs
4. Rebuild from package.json files in each subproject

**If SSOT is lost:**
1. **CATASTROPHIC** - This is the architectural foundation
2. Check git history immediately
3. No substitute exists (SSOT is Single Source Of Truth)

---

**🔥💀⚓ END OF DEVELOPMENT STATE MANIFEST 🔥💀⚓**

**Next session: Load this file first, then resume from "Known Issues & Blockers"**

