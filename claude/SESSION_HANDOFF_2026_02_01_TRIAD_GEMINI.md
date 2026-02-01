# Session Handoff 2026-02-01 (Triad + Gemini CLI)

## Strategic Summary
- Triad stabilized: Codex (auth/config split), Gemini (preview model + MCP wiring), Claude (instruction anchors) now aligned.
- Gemini MCP reality: GitHub MCP requires PAT; OAuth doesn’t work. PAT must live in user env var, not JSON, not `.env`.
- Repo hygiene: Trimmed oversized `_sources/github-mcp-server` to only `gemini-extension.json` to keep functionality without repo bloat.
- Waypoints updated: `codex/NEXT.md` now reflects PAT-only MCP and references status report + triadic logs.
- Triadic logs updated: 0001 + 0002 now reflect correct auth lane, remove hardcoding claims, and add handover references.

## Files Already Updated
- `codex/NEXT.md`
- `claude-codex-gemini/triadic-session-shared-0001.md`
- `claude-codex-gemini/triadic-session-shared-0002.md`
- `.gemini/extensions/_sources/github-mcp-server` trimmed to `gemini-extension.json`
- `.gemini/extensions/chthonic-archive-sync/gemini-extension.json` (removed `mas-mcp` WIP)

## Stale/Outdated Items to Fix
- Any doc that claims OAuth works for GitHub MCP → replace with PAT-only.
- Any doc that says PAT is hardcoded in JSON → replace with user env var.
- Any doc that treats `_sources/github-mcp-server` as required runtime data → mark as optional repo clone (trimmed).
- Any “Gemini model = gemini-3-pro” references → replace with `auto-gemini-3` or `gemini-3-pro-preview`.

## Task List for Claude
1) Sweep docs for OAuth/PAT misstatements  
   - Targets: `BRIDGE_COMPLETE_SUMMARY.md`, `GEMINI.md`, deep-research docs
2) Update Gemini MCP guidance  
   - “PAT via user env var” + “no OAuth for GitHub MCP”
3) Sync model naming  
   - Replace `gemini-3-pro` with `auto-gemini-3` or `gemini-3-pro-preview`
4) Add a note on `_sources`  
   - “Repo clone not required; only `gemini-extension.json` used”
5) Optional: Add a short validation checklist  
   - Restart Gemini → `/mcp list` → confirm GitHub MCP status

## Workflow Additions (Gemini CLI)
feat: Add Gemini CLI workflows for issue triage and review
- Implemented scheduled triage workflow to automatically label issues every hour.
- Created triage command for analyzing individual issues and assigning labels.
- Developed review command for assessing pull requests and providing feedback.
- Introduced invoke command for executing custom commands via Gemini CLI.
- Added structured prompts and guidelines for consistent issue labeling.
- Established debugging job to assist in troubleshooting workflow executions.
- Ensured security measures against command injection in shell commands.
- Enhanced label management by validating against available labels before application.
