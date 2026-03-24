# Chthonic Archive: Gemini Sync

Purpose: Keep Gemini aligned with Codex + Claude without re-running onboarding.

## Execution Invariants (Do Not Drift)
- Workspace root: `C:\Users\eldno\chthonic-archive`
- Shell: PowerShell only (no bash syntax)
- JS/TS: `bun` (npm replacement)
- Python: `uv run <script>` (never raw `python` or `pip`)
- Ruby: `rv` (rbenv replacement)
- Go: `goup` (goenv replacement)
- Rust: `cargo`
- SSOT: `.github/copilot-instructions.md` (reference only, do not duplicate)
- R versions: `rig`
- Zig versions: `zv`

## Onboarding State (Locked)
- Codex config: `.codex/config.toml` (workspace behavior SSOT)
- Codex auth: `~/.codex/config.toml` + `~/.codex/auth.json` (do not modify)
- Gemini settings:
  - User: `~/.gemini/settings.json`
  - Workspace: `.gemini/settings.json`
  - Workspace default model alias: `chthonic-fast`
  - Workspace higher-think alias: `chthonic-thinking`

## Primary Instruction Sources
- `GEMINI.md` (Gemini instructions)
- `AGENT_COMMON.md` (shared invariants)
- `AGENTS.md` (Codex instructions)
- `CLAUDE.md` (Claude instructions)
- `.github/instructions/*.instructions.md` (modular rules)

## Working Practice
- Prefer referencing existing instructions to avoid duplication.
- If new guidance is needed, add it to the appropriate instruction branch.
- Treat the linked workspace extension as the source of Gemini-specific triad skills.
- Keep bare `rv` reserved for Ruby; if the A2-ai R package manager is ever adopted here, refer to it as `R rv` / `rv-r`.

## Loaded Workspace Skills
- `triad-velocity-lane`
- `mailbox-handoff`
- `decision-razor`
- `scm-triage`
- `artifact-upcycle`

## Session Handshake (Minimal)
1. Confirm workspace root is `C:\Users\eldno\chthonic-archive`.
2. Load instruction anchors:
   - `AGENTS.md`
   - `CLAUDE.md`
   - `.github/instructions/*.instructions.md` (as needed)
3. Treat this file as a waypoint only; do not expand SSOT here.
