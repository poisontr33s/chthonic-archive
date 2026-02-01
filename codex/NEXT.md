# Codex Scope: Next Steps

## Purpose
Capture what’s next for Codex in this workspace without expanding the SSOT. This is a lightweight waypoint for future sessions.

## Current State (Stable)
- Auth: file-based (`C:/Users/erdno/.codex/auth.json`)
- Global config: auth-only (`C:/Users/erdno/.codex/config.toml`)
- Workspace config: behavior SSOT (`.codex/config.toml`) with sandbox locked to this repo
- Instructions: `AGENTS.md` (compact) and `.github/copilot-instructions.md` (SSOT)
- Gemini MCP: GitHub Server **Enabled** (PAT-based auth required; no OAuth flow)

## Scope: What’s Next (When Ready)
1. **GitHub Tool Integration**
   - Confirm `GITHUB_MCP_PAT` in user env and verify via `/mcp list`.
   - Then leverage GitHub MCP for PR reviews and issue triage.
2. **Research ingestion**
   - Triage Gemini Deep Research outputs.
   - Decide target destination: `claude-codex-gemini/triadic-session-context/` or `deep-research-documents/`.
3. **Refinement pass**
   - Convert raw notes into structured, cross-referential artifacts.
   - Keep the SSOT clean; link out instead of duplicating.
4. **Selective automation**
   - Only after the content direction is settled, add scripts or workflows to reduce manual overhead.

## Guardrails
- Do not alter working auth or sandbox configs without explicit instruction.
- Keep AGENTS.md compact; reference SSOT instead of copying it.
- Prefer PowerShell commands; avoid bash syntax on Windows.

## References
- `AGENTS.md`
- `.codex/config.toml`
- `.github/copilot-instructions.md`
- `claude-codex-gemini/triadic-session-context/OpenAI_Codex_Win11_Keyring_Auth_Resolution.md`
- `claude-codex-gemini/triadic-session-context/Session_20260131_Codex_Onboarding_Summary.md`
- `claude-codex-gemini/triadic-session-shared-0001.md`
- `claude-codex-gemini/triadic-session-shared-0002.md`
- `codex/gemini_mcp_status_report.md`
- `codex/SESSION_HANDOFF_2026_02_01_CLAUDE.md`
- `claude/SESSION_HANDOFF_2026_02_01_TRIAD_GEMINI.md`
- `deep-research-documents/Gemini_CLI_Preview_Win11_Bun_vscode_insiders_deep_research_IMPLEMENTATION.md`
