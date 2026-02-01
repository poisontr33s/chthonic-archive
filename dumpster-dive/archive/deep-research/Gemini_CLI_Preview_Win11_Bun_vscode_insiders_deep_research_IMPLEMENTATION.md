# Gemini CLI Preview (Win11 + Bun + VS Code Insiders) — Implementation Extract

This is a compressed, actionable implementation plan derived from:
`deep-research-documents/Gemini_CLI_Preview_Win11_Bun_vscode_insiders_deep_research.md`.

## A) Current State Alignment (Already Done)
- Gemini settings schema fixed:
  - `general.previewFeatures`
  - `model.name`
- VS Code Insiders Gemini companion installed:
  - `google.gemini-cli-vscode-ide-companion`
- Local Gemini extension wired:
  - `.gemini/extensions/chthonic-archive-sync/`
- GitHub MCP extension linked:
  - `.gemini/extensions/_sources/github-mcp-server/`
- MCP server for workspace uses `uv run python mas_mcp/server.py`.

## B) Required (Minimal) Changes
1) **GitHub MCP PAT**
   - Set env var:
     - `GITHUB_MCP_PAT`
   - Restart Gemini CLI.
   - Validate:
     - `/mcp list`
     - `/mcp desc`

2) **IDE Bridge**
   - Reload VS Code Insiders.
   - Run:
     - `/ide enable`

## C) Optional (If You Want Full “Zero Redundancy”)
1) **PowerShell UTF-8 hardening**
   - Add UTF‑8 enforcement to `$PROFILE.CurrentUserAllHosts`.
   - Apply only if your console still shows garbled output.

2) **Bun launcher alias**
   - Create a PowerShell function (e.g., `g`) wrapping:
     - `bunx --bun @google/gemini-cli@preview`

3) **Gemini settings enhancements**
   - `general.enablePromptCompletion = true`
   - `general.sessionRetention.enabled = true`
   - Keep `general.previewFeatures = true`

## D) Safe Verification Sequence
1) Launch Gemini CLI.
2) `/model` → confirm Gemini 3 Pro (or your preferred model).
3) `/mcp list` → both `mas-mcp` + `github` connected.
4) `/ide status` → VS Code connected.

## E) Do Not Do (Guardrails)
- Do not reintroduce Docker MCP (not installed here).
- Do not duplicate SSOT into this file.
- Do not move global auth settings into workspace.

