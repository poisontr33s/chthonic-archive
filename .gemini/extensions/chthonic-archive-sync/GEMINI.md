# Chthonic Archive: Gemini CLI Sync

Purpose: Keep Gemini CLI aligned with Codex + Claude without re-running onboarding.

## Execution Invariants (Do Not Drift)
- Workspace root: `C:\Users\erdno\chthonic-archive`
- Shell: PowerShell only (no bash syntax)
- Package manager: `bun` only
- Python: `uv run python` only
- SSOT: `.github/copilot-instructions.md` (reference only, do not duplicate)

## Onboarding State (Locked)
- Codex config: `.codex/config.toml` (workspace behavior SSOT)
- Codex auth: `~/.codex/config.toml` + `~/.codex/auth.json` (do not modify)
- Gemini settings:
  - User: `~/.gemini/settings.json`
  - Workspace: `.gemini/settings.json`

## Primary Instruction Sources
- `AGENTS.md` (Codex instructions)
- `CLAUDE.md` (Claude instructions)
- `.github/instructions/*.instructions.md` (modular rules)

## Working Practice
- Prefer referencing existing instructions to avoid duplication.
- If new guidance is needed, add it to the appropriate instruction branch.

## Session Handshake (Minimal)
1. Confirm workspace root is `C:\Users\erdno\chthonic-archive`.
2. Load instruction anchors:
   - `AGENTS.md`
   - `CLAUDE.md`
   - `.github/instructions/*.instructions.md` (as needed)
3. Treat this file as a waypoint only; do not expand SSOT here.
