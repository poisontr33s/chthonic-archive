## Triadic Session Shared 0002 (Structured Snapshot)

### Purpose
Shared, raw continuity log for Codex + Claude + Gemini. This entry captures the GitHub MCP configuration status and the decision to use PAT-only auth (no OAuth).

### Layer 1 — Executive Index (Stable)
1) **Session Identity**
   - Scope: Gemini CLI GitHub MCP Authentication & Configuration.
2) **Date, Agents Active, Workspace, Goal**
   - Date: 2026-02-01
   - Agents: Gemini CLI (Primary)
   - Workspace: `C:\Users\eldno\chthonic-archive`
   - Goal: Authenticate Gemini CLI with GitHub Copilot via MCP using a Personal Access Token (PAT), since OAuth is not supported for GitHub MCP in Gemini CLI.
3) **Canonical Artifacts**
   - Triadic index:
     - `claude-codex-gemini/triadic-session-shared-0002.md`
4) **Files Created/Modified (Authoritative)**
   - Global Gemini Settings:
     - `C:\Users\eldno\.gemini\settings.json`
   - Extension enablement:
     - `C:\Users\eldno\.gemini\extensions/extension-enablement.json` (GitHub extension re-enabled)
   - Handover:
     - `codex/reports/gemini_mcp_status_report.md`
5) **Decisions & Locks**
   - **Auth Method:** Use PAT-based bridge (`GITHUB_MCP_PAT`) instead of browser OAuth flow (not supported for GitHub MCP).
   - **Persistence:** Use user environment variable (preferred). No `.env` and no hardcoding in JSON.
   - **WIP MCP:** `chthonic-archive-mcp` intentionally disabled/removed from Gemini extension until stabilized.
6) **Critical Fixes**
   - Re-enabled GitHub MCP extension in enablement registry.
   - Confirmed Gemini CLI OAuth is not supported for GitHub MCP; PAT is required.
7) **Error → Root Cause → Fix → Verification**
   - OAuth attempt failed → GitHub MCP does not support OAuth registration → Use PAT via `GITHUB_MCP_PAT`.
   - "Authorization header is badly formatted" → missing/empty PAT → set env var → restart Gemini → `/mcp list`.
8) **Open Threads**
   - Confirm PAT present in user env var after restart.
   - Validate GitHub MCP connectivity in Gemini CLI.
9) **Smallest Next Move**
   - Restart Gemini and run `/mcp list`.

### Layer 2 — Deep Index (Navigates Raw Log)
1) **Timeline Anchors**
   - A) Identified missing OAuth capability in CLI for GitHub MCP.
   - B) Re-enabled GitHub MCP extension.
   - C) PAT required for MCP auth.
2) **Topic Clusters**
   - MCP Configuration.
   - OAuth vs PAT Authentication.
   - Environment variable persistence.
3) **File Map**
   - `~/.gemini/settings.json`: Global Gemini config.
   - `C:\Users\eldno\.gemini\extensions/extension-enablement.json`: Extension enablement.
   - `codex/reports/gemini_mcp_status_report.md`: Handover snapshot (dummy token).

### Structured Log (Compressed)

#### A) Primary Request & Intent
- "Wire up" GitHub MCP for Gemini CLI with PAT-based auth (OAuth not supported).

#### B) Key Concepts
- **Remote MCP:** Using GitHub's hosted MCP endpoint (`api.githubcopilot.com`).
- **PAT Bridge:** Use `GITHUB_MCP_PAT` env var; no OAuth flow for GitHub MCP.

#### C) Authoritative Files (Created/Modified)
- `C:\Users\eldno\.gemini\extensions/extension-enablement.json`: GitHub extension enabled.
- `codex/reports/gemini_mcp_status_report.md`: Status handover (dummy token).

#### D) Errors → Root Cause → Fix → Verification
- OAuth attempt failed → unsupported for GitHub MCP → use PAT.
- Missing PAT → "Authorization header badly formatted" → set env var + restart.

#### E) Pending / Open Threads (Smallest Next Move)
- Restart Gemini to load env var.
- Run `/mcp list` to verify GitHub tools are available.

