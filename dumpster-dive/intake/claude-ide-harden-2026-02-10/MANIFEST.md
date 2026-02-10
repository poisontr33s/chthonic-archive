# MANIFEST: claude-ide-harden-2026-02-10

**Date:** 2026-02-10  
**Method:** Wet-Paper-to-Gold (see `claude/WET_PAPER_TO_GOLD_METHODOLOGY.md`)  
**Focus:** Collapse the VS Code Insiders + Claude Code + MCP “patch cascade” into a canonical, learned entrypoint.

## Source (Drift Artifacts)

Observed failure patterns:
- VS Code Insiders updates overwrite/shift the extension-bundled Claude binary behavior and/or IDE detection.
- Windows process environment inheritance causes IDE-launched Claude to miss token env vars loaded only in a terminal session.
- Claude CLI plugin enable returns non-zero on no-op (“already enabled”), producing false-negative “failed” output.
- Token formatting drift (whitespace, `<...>` wrappers, accidental `Bearer ` prefix) causes Copilot MCP 400 “badly formatted Authorization”.

## Extraction Tiers

### Tier 1 (Direct Use): Canonical, learned entrypoint

**Goal:** One choke-point that runs on every IDE launch.

Files copied to `tier-1-direct/`:
- `scripts/claude_ide.ps1`
  - canonical CLI entrypoint: `heal|health|write-mcp|persist-env|crossover`
- `scripts/claude_process_wrapper.ps1` + `scripts/claude_process_wrapper.bat`
  - VS Code extension supported wrapper path (`claudeCode.claudeProcessWrapper`)
- `scripts/claude_healthcheck.ps1`
  - emits `codex/mailbox/CLAUDE_IDE_HEALTH_LATEST.json` (invariant artifact)
- `scripts/claude_insiders_selfheal.ps1`
  - idempotent “heal” implementation (now treated as shim target)
- `scripts/mcp_write_local.ps1`
  - deterministic `.mcp.json` generator (local, gitignored)
- `scripts/api_pool.ps1`
  - token loader + normalization + compatibility aliases
- `scripts/api_pool_persist_user_env.ps1`
  - persists required vars into Windows User env (presence only in logs)
- `scripts/claude_plugin_ensure.ps1`
  - idempotent plugin enable (neutralizes “already enabled” failure)

### Raw (Unprocessed): Historical/legacy scripts kept for mining

Files copied to `raw/`:
- `scripts/patch-claude-insiders.ps1`
- `scripts/launch_claude_code.ps1`
- `scripts/start_github_mcp.ps1`
- `scripts/start_mcp_session.ps1`

Rationale: these encode previous assumptions and can be mined for missing invariants, but should not be expanded into new variants.

## Compression / Disposition

- **Disposition:** Keep canonical path in `scripts/` (repo operational). Keep historical sources here for audit/mining.
- **Compression:** Many scripts/patch variants → one choke-point (`claude_process_wrapper` → `claude_ide`) + one health artifact.

## Next Actions

- Convert remaining legacy scripts into thin shims to `scripts/claude_ide.ps1` (repurpose, don’t delete).
- Add new invariants only via the health artifact + wrapper gate, not via new scripts.

