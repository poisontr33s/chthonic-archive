## Triadic Session Shared 0001 (Structured Snapshot)

### Purpose
Shared, raw continuity log for Codex + Claude + Gemini. The structured index below maps the raw Claude-lineage log into a navigable cross-reference.

### Layer 1 — Executive Index (Stable)
1) **Session Identity**
   - Scope: Codex + Claude + Gemini triad onboarding and stabilization.
2) **Date, Agents Active, Workspace, Goal**
   - Date: 2026-02-01
   - Agents: Claude + Codex + Gemini
   - Workspace: `C:\Users\eldno\chthonic-archive`
   - Goal: Stable triad onboarding; Gemini CLI + MCP wiring.
3) **Canonical Artifacts**
   - Instruction anchors:
     - `AGENTS.md`
     - `CLAUDE.md`
     - `GEMINI.md`
   - Waypoint:
     - `codex/NEXT.md`
   - Triadic index:
     - `claude-codex-gemini/triadic-session-shared-0001.md`
4) **Files Created/Modified (Authoritative)**
   - Workspace behavior SSOT:
     - `.codex/config.toml`
   - Instruction anchors:
     - `AGENTS.md`
     - `CLAUDE.md`
     - `GEMINI.md`
   - Waypoint:
     - `codex/NEXT.md`
   - Gemini settings:
     - `.gemini/settings.json`
     - `C:\Users\eldno\.gemini\settings.json`
   - Gemini extensions:
     - `.gemini/extensions/chthonic-archive-sync/`
     - `.gemini/extensions/_sources/github-mcp-server/`
   - Gemini MCP status handover:
     - `codex/reports/gemini_mcp_status_report.md`
5) **Decisions & Locks**
   - Codex global config = auth-only; workspace config = behavior.
   - Gemini preview features set via `general.previewFeatures`.
   - Gemini model set via `model.name`.
   - No Docker MCP on this system.
6) **We decided X, therefore Y is locked**
   - Decided: Codex auth lives globally; behavior lives in workspace.
     Therefore: `~/.codex/config.toml` stays auth-only.
   - Decided: Gemini preview features must match schema.
     Therefore: top-level `previewFeatures` is not used.
7) **Critical Fixes**
   - Codex keyring limit bypass via `CODEX_HOME` isolation.
   - Gemini settings schema corrected (preview features/model).
   - Gemini IDE companion installed in VS Code Insiders.
8) **Error → Root Cause → Fix → Verification**
   - Keyring error → Windows 2560 char limit → `CODEX_HOME` isolation → login success.
   - Preview not detected → wrong settings keys → move to `general.previewFeatures`/`model.name` → Gemini 3 Pro visible.
   - IDE connect fail → missing extension → install `google.gemini-cli-vscode-ide-companion` → `/ide enable` works.
9) **Open Threads**
   - GitHub MCP auth via `GITHUB_MCP_PAT` (PAT only; no OAuth flow).
   - Confirm Gemini model selection after restart.
   - `/ide enable` after VS Code Insiders reload.
10) **Smallest Next Move**
   - Set `GITHUB_MCP_PAT`, restart Gemini, run `/mcp list`.

### Layer 2 — Deep Index (Navigates Raw Log)
1) **Timeline Anchors**
   - A) Codex auth failure → `CODEX_HOME` isolation fix.
   - B) Config split (global auth vs workspace behavior).
   - C) AGENTS.md + codex/NEXT.md created + cross-referenced.
   - D) Gemini preview features mismatch → schema correction.
   - E) Gemini IDE companion install (VS Code Insiders).
   - F) Gemini extensions: local sync + GitHub MCP.
2) **Phase Checkpoints (5–10)**
   - Phase 1: Codex auth + config split.
   - Phase 2: Instruction anchors (AGENTS/CLAUDE/GEMINI).
   - Phase 3: Gemini preview features + model selection.
   - Phase 4: Gemini IDE companion install.
   - Phase 5: Extensions + MCP wiring.
3) **Topic Clusters**
   - Auth & config.
   - Gemini CLI preview features.
   - MCP servers & extensions.
   - Instruction hierarchy (AGENTS/CLAUDE/GEMINI).
4) **File Map (Why It Matters)**
   - `AGENTS.md`: Codex execution invariants.
   - `CLAUDE.md`: Claude execution invariants.
   - `GEMINI.md`: Gemini execution invariants.
   - `codex/NEXT.md`: shared next-action waypoint.
   - `.codex/config.toml`: workspace behavior lock.
   - `.gemini/settings.json`: Gemini workspace settings.
   - `C:\Users\eldno\.gemini\settings.json`: Gemini global settings.
   - `.gemini/extensions/chthonic-archive-sync/GEMINI.md`: Gemini sync context.
5) **Command Map (State-Changing Only)**
   - `codex login` (with `CODEX_HOME` isolation).
   - `gemini extensions link ...`
   - `code-insiders --install-extension google.gemini-cli-vscode-ide-companion`.

### Structured Log (Compressed)
This is the canonical triad summary. Raw logs are intentionally excluded to prevent dumping.

#### A) Primary Request & Intent
- Triad setup in VS Code Insiders on Windows 11: Claude (existing), Codex (auth + config), Gemini CLI (preview + IDE + MCP).

#### B) Key Concepts
- Windows Credential Manager 2560 UTF-16 limit.
- `CODEX_HOME` isolation for clean auth.
- Codex config split: global auth-only vs workspace behavior.
- Gemini settings schema: `general.previewFeatures`, `model.name`.
- MCP wiring: Bun/uv servers, extension-based MCP registration.

#### C) Authoritative Files (Created/Modified)
- Auth-only config:
  - `C:\Users\eldno\.codex\config.toml`
- Workspace behavior:
  - `.codex/config.toml`
- Instruction anchors:
  - `AGENTS.md`
  - `CLAUDE.md`
  - `GEMINI.md`
- Waypoint:
  - `codex/NEXT.md`
- Gemini settings:
  - `.gemini/settings.json`
  - `C:\Users\eldno\.gemini\settings.json`
- Gemini extensions:
  - `.gemini/extensions/chthonic-archive-sync/`

#### D) Errors → Root Cause → Fix → Verification
- Keyring error → token too long → `CODEX_HOME` isolation → login success.
- Preview not detected → wrong keys → set `general.previewFeatures` + `model.name` → Gemini 3 Pro visible.
- IDE connect fail → missing companion extension → install `google.gemini-cli-vscode-ide-companion` → `/ide enable`.

#### E) Pending / Open Threads (Smallest Next Move)
- Set `GITHUB_MCP_PAT` (PAT-only), restart Gemini, run `/mcp list`.

