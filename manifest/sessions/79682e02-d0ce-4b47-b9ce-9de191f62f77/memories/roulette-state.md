# Roulette Session State

## Commit trail this session
- 128e8d82 — poe_lane.py + poe_sdk_lane.py + pyproject.toml + poe_transport_audit.py
- 3e30721c — poe_account.ps1
- 2e0e02b2 — mistralrs_model_manager.py

## T2 count: 33/~40

## Commits this session (latest batch)
- 66c1d1ef — vscode_settings_live_audit.py (registry fallback; --timeout)
- f8082694 — vscode_electron_hardener.py (discover_user_data_dir via code-insiders --status)
- b311543b — vscode_error_autopsy.py (--log-dir override; --severity-min alias)
- 96ed8107 — insiders-sync.ps1 ($DryRun; $RepoRoot; vsix validation)
- 19e0cc0c — update-claude-code.ps1 (remove patch-claude-insiders call; version diff)
- 86013ced — chthonic_new.py + chthonic.ps1 (errors field; VERIFY_CHECKS; --verify)
- 6e79d2b4 — chthonic_workflow.py (--list; --dry-run; profile nargs=?)
- 10974857 — apply_canonize_uv.sh (git remote preflight; --dry-run; explicit exit checks)
- 15a03dda — siphon_to_dumpster_dive.ps1 (self-exclude; siphon-manifest.json)
- 13f225ea — zombie_consumer.py + pyproject.toml (ImportError prompt; analysis sklearn)

## Next: zombie_forge_bridge.py
- Spec: Auto-create forge stage directories; emit batch-level receipt JSON; add --undo <batch>

## Remaining after zombie_forge_bridge.py (from roulette lines 126+):
- overnight_daemon.ts
- plus ~6 more T2 items

## ✅ T2 items done this session
poe_lane.py, poe_sdk_lane.py, poe_transport_audit.py, poe_account.ps1, mistralrs_model_manager.py

## Next ⬜ T2 items (in order from roulette)
1. **mcp-chthonic-server.ts** (score 1.5, effort 2)
   Spec: SENTRY_DSN presence check at startup; JSON error objects {code, message, context} in all catch handlers; add `tools/describe` introspection tool
   File: scripts/mcp-chthonic-server.ts
   Already has: `initSentry()` call after ALL_TOOLS defined (~line 420); catch handlers return `{success:false, output:...}`; no `tools/describe` tool; no SENTRY_DSN check
   Structure: POLYGLOT_TOOLS, ARCHIVE_TOOLS, META_TOOLS arrays → ALL_TOOLS; handlers in dispatch switch; MCP server reads stdin line-by-line

2. **gemini-model-router.ts** (score 1.5, effort 2)
   Spec: Backup settings.json → .bak before write; registry version mismatch = warning with migration path; add --dry-run

3. **vscode_terminal_crash_doctor.ps1** — PSScriptRoot-relative repo detection; scoring formula in header; --score-only
4. **vscode_insiders_matrix.ps1**
5. **vscode_settings_live_audit.py**
... more after that

## Key facts
- Commit trailer: `Co-authored-by: Pentea <223556219+Penteaa@users.noreply.github.com>`
- SCRIPTS_ROULETTE.md: claude/mailbox/SCRIPTS_ROULETTE.md
- Toolchain: uv run <script>, bun, pwsh -NoProfile
- mcp-chthonic-server.ts: ~700+ lines; initSentry() called at line ~420 (after ALL_TOOLS array); SENTRY_DSN check needs to be added BEFORE initSentry() call; JSON error objects need to go into catch blocks in dispatch/handler functions
