# Chthonic Golden Visual Studio Code — Architecture Plan

> **Phase:** 2 — Fork Prototype  
> **Status:** Active  
> **Generated:** 2026-02-26 (updated Phase 2)  
> **Scope:** Diagnose → Harden → Customize → Fork

---

## 1. Problem Statement

VS Code Insiders on this system scores **0/100 stability** (autopsy) and **72/100 matrix baseline** vs 100/100 on clean user-data. Root causes:

| Category | Count | Severity | Root Cause |
|---|---:|---|---|
| GPU | 47 | HIGH-CRITICAL | SwiftShader software rendering, no hardware GPU accel |
| EXTHOST | 46 | MEDIUM-HIGH | Extension activation failures, deprecated APIs |
| MEMORY | 22 | HIGH | Event listener leaks (175+ per emitter), no heap tuning |
| PTY | 1 | MEDIUM | Shell integration timeout on first terminal |
| NETWORK | 1 | LOW | Embeddings CDN 404 (version mismatch) |
| UI | 1 | HIGH | TypeError null reference in chat thinking renderer |

**Primary vector:** User-data-dir corruption and accumulated state (3.27GB / 20,765 files / 31 log sessions).

---

## 2. Hardening Actions Taken (Phase 1)

### 2a. Created `scripts/vscode_error_autopsy.py`
- Auto-discovers 228+ log files (repo, mailbox, AppData)
- 20 compiled error patterns across 7 categories
- Severity scoring (CRITICAL/HIGH/MEDIUM/LOW/INFO)
- Deduplication engine (1,214 raw → 118 unique this run)
- Stability score formula: `100 - (crit*25) - (high*10) - (med*3) - (low*1)`
- Dual output: JSON + Markdown + terminal summary

### 2b. Created `scripts/vscode_electron_hardener.py`
- Diagnose: reads `argv.json`, user-data-dir, workspace settings
- Patch: creates/updates `argv.json` with:
  - `disable-hardware-acceleration: false`
  - `enable-gpu-rasterization: true`
  - `ignore-gpu-blocklist: true`
  - `js-flags: --max-old-space-size=8192` (8GB V8 heap)
- Audit: user-data size, log session accumulation, crash dumps, stale caches
- Launch: generates safe CLI launch flags
- Backup: always backs up existing argv.json before patching

### 2c. Applied `argv.json` to Insiders
- Created `%APPDATA%/Code - Insiders/argv.json` with GPU + memory flags
- Next VS Code Insiders restart will use hardware GPU + 8GB heap

---

## 3. Existing Infrastructure (To Recycle)

| Asset | Location | Purpose |
|---|---|---|
| Error Classifier | `error-classifier/` | Bun/TS + SQLite phase-based classification |
| Matrix Runner | `scripts/vscode_insiders_matrix.ps1` | 4-case stability matrix |
| Crash Doctor | `scripts/vscode_terminal_crash_doctor.ps1` | Terminal crash triage |
| Extension | `extensions/chthonic-archive/` | VS Code extension (themes, native, wasm, MCP) |
| Error Autopsy | `scripts/vscode_error_autopsy.py` | **NEW** — Log classification |
| Electron Hardener | `scripts/vscode_electron_hardener.py` | **NEW** — GPU/memory repair |

---

## 4. The Chthonic Golden Fork — Roadmap

### Phase 1: Foundation (Current)
- [x] Error autopsy tool (classify all VS Code log errors)
- [x] Electron hardener (GPU, memory, user-data audit)
- [x] Apply argv.json with GPU + heap fixes
- [x] Stability baseline report generated

### Phase 2: Fork Prototype (Current)
- [x] Gemini Deep Research briefing (`docs/GEMINI_DEEP_RESEARCH_BRIEFING.md`)
- [x] Fork prototype scaffold (`chthonic-golden/`)
- [x] product.json + quality.json (stable + insider channels)
- [x] Hardened Electron bootstrap (`electron-main/bootstrap.js`)
- [x] GPU policy baked into build (`electron-main/gpu-policy.json`)
- [x] Extension allowlist/blocklist
- [x] Build pipeline scripts (build.ps1, patch.ps1, package.ps1)
- [x] ANKH semantic token definitions
- [x] ANKH integration mapping document
- [ ] Upstream VS Code clone + first successful build
- [ ] Generate actual .patch files from prototype
- [ ] Branding assets (icon.ico, icon.png)

### Phase 3: Stabilization
- [ ] Clean user-data-dir: purge stale caches, compress log sessions
- [ ] Re-run matrix post-hardening to measure improvement
- [ ] Extension host isolation: identify and disable unstable extensions
- [ ] PTY host warm-up optimization (profile loading pipeline)

### Phase 4: Customization
- [ ] Custom launch wrapper: `scripts/chthonic_golden_launch.ps1`
  - Auto-applies GPU flags
  - Monitors crash dump dir
  - Restarts on PTY host death
  - Applies extension allow-list
- [ ] Custom extension pack: curated stable extensions only
- [ ] Theme integration: chthonic-mandala themes as default
- [ ] MCP server auto-registration on startup

### Phase 5: Fork Architecture (Absorbed into Phase 2 Prototype)
- [ ] Clone `microsoft/vscode` repo
- [ ] Apply product.json overrides (branding, telemetry, update channel)
- [ ] Integrate ANKH abstraction layer (custom command palette, semantic navigation)
- [ ] Build custom Electron with hardened GPU defaults
- [ ] Custom marketplace or VSIX sideloading pipeline
- [ ] CI/CD for automated builds (GitHub Actions)

### Phase 5: ANKH Integration
- [ ] Semantic navigation: ANKH coordinate system in editor
- [ ] Custom activity bar entries for Archive tools
- [ ] Built-in MCP client connecting to `mas_mcp`
- [ ] Deep research artifact viewer (inline rendering)
- [ ] Triadic agent panel (Claude + Codex + Gemini status)

---

## 5. Key Metrics

| Metric | Before | After Phase 1 | Target |
|---|---|---|---|
| Autopsy stability score | 0/100 | Pending restart | ≥70/100 |
| Matrix baseline | 72/100 | Pending restart | ≥90/100 |
| User-data size | 3,270MB | 3,270MB | <500MB |
| GPU acceleration | SwiftShader (SW) | Hardware (pending) | Hardware |
| V8 heap | ~4GB default | 8GB configured | 8GB |
| Log sessions | 31 | 31 | ≤5 |
| Extension host errors | 46 unique | 46 unique | <5 |

---

## 6. API / Tooling Expansion Research

### Available APIs
- **VS Code Extension API**: Full access via `extensions/chthonic-archive/`
- **OpenAI API**: Image gen, Sora, Chat — keys managed by `scripts/api_manager.ps1`
- **GitHub API**: MCP server available, `gh` CLI configured
- **Hugging Face API**: Discovery + model ranking scripts exist

### Needed for Phase 4+
- **Electron Forge / electron-builder**: For custom Electron packaging
- **Azure DevOps / GitHub Actions**: CI/CD for fork builds
- **VS Code Marketplace API**: For private extension publishing (or VSIX direct install)
- **Chromium GPU Telemetry**: For diagnosing hardware GPU issues programmatically

---

## 7. Files Created This Phase

```
scripts/vscode_error_autopsy.py          # ~450 lines — log classifier
scripts/vscode_electron_hardener.py      # ~430 lines — GPU/memory repair
docs/CHTHONIC_GOLDEN_PLAN.md             # this document
docs/GEMINI_DEEP_RESEARCH_BRIEFING.md    # Gemini 3.1 context packet (~220 lines)
claude/mailbox/VSCODE_ERROR_AUTOPSY_LATEST.md
claude/mailbox/VSCODE_ERROR_AUTOPSY_LATEST.json
claude/mailbox/VSCODE_ELECTRON_HARDENER_LATEST.md

# Phase 2 — Fork Prototype
chthonic-golden/README.md                # Fork overview + quick start
chthonic-golden/product.json             # Distribution identity (Open VSX, no telemetry)
chthonic-golden/quality.json             # Stable + insider channel defs
chthonic-golden/electron-main/bootstrap.js    # Hardened Electron entry (~120 lines)
chthonic-golden/electron-main/gpu-policy.json # Baked GPU + V8 + crash config
chthonic-golden/extensions/allowlist.json     # Curated extension list
chthonic-golden/extensions/blocklist.json     # Blocked extensions
chthonic-golden/patches/README.md             # Patch strategy docs
chthonic-golden/scripts/build.ps1             # Full build pipeline
chthonic-golden/scripts/patch.ps1             # Patch applicator
chthonic-golden/scripts/package.ps1           # Packaging pipeline
chthonic-golden/ankh/semantic-tokens.json     # Custom @ankh: token types
chthonic-golden/ankh/integration.md           # ANKH → fork mapping
chthonic-golden/branding/README.md            # Brand asset specs
```
