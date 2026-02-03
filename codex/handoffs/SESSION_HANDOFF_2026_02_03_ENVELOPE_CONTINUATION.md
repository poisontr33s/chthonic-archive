---
type: handoff
category: continuation
created: 2026-02-03
from: claude
to: codex
description: Continue script envelope canonicalization started by Claude
---

# Session Handoff: Claude Code → Codex

**Date:** 2026-02-03
**From:** Claude Code (Opus 4.5)
**To:** Codex (GPT-5.2 Medium Reasoning)
**Priority:** Execute tasks sequentially. Report results.

---

## Context: What Claude Did This Session

### Completed Tasks
1. **Frontmatter added** to AGENTS.md, GEMINI.md
2. **Broken links fixed** in 5 files (CLAUDE_CODE_IDE_SETUP, STRATEGIC_PLAN, PWSH_RULES, CLAUDE_README, SESSION_CHECKPOINT)
3. **Relative paths fixed** in BUN_SEGFAULT.md, Python_Metabolic_Standard.md
4. **Triadic files synced** (TRIADIC_SESSION_SHARED_0001/0002.md line endings)
5. **Duplicate skill removed** from `codex/skills/script-envelope/` (global `~/.codex/skills/` is source of truth)
6. **Temp files cleared** from `~/.codex/tmp/`, `~/.gemini/tmp/`
7. **Stale docs archived** (2 SESSION_* files → `dumpster-dive/archive/docs-sessions/`)
8. **Script envelopes added** to 6 PowerShell entry points

### Scripts That NOW Have Envelopes (Claude added these)
- `scripts/shell_capabilities.ps1` → SID: `SCRIPT_SHELL_CAPABILITIES_V1`
- `scripts/run_overnight_daemon.ps1` → SID: `SCRIPT_RUN_OVERNIGHT_DAEMON_V1`
- `scripts/launch_claude_code.ps1` → SID: `SCRIPT_LAUNCH_CLAUDE_CODE_V1`
- `scripts/start_mcp_session.ps1` → SID: `SCRIPT_START_MCP_SESSION_V1`
- `scripts/polyglot_env.ps1` → SID: `SCRIPT_POLYGLOT_ENV_V1`
- `scripts/start_github_mcp.ps1` → SID: `SCRIPT_START_GITHUB_MCP_V1`

### Python Lib Files (Already Had Envelopes - No Changes Needed)
- `scripts/lib/__init__.py`, `audit.py`, `compact.py`, `extract.py`, `map.py`, `resolve.py`

---

## Your Tasks (Codex)

### Task 1: Add Envelopes to Remaining PowerShell Scripts (6 more)

These PowerShell scripts are missing envelopes:

1. `scripts/harvest_claudines.ps1`
2. `scripts/validate_probe.ps1`
3. `scripts/validate_shell_probe.ps1`
4. `scripts/sfs.ps1`
5. `scripts/pause_agents.ps1`
6. `scripts/check-profiles.ps1`

**Envelope format (canonical):**
```powershell
# ╔════════════════════════════════════════════════════════════════════════════╗
# ║ THE DECORATOR'S BLESSING: <filename>                                      ║
# ║ Module: <exports / key symbols>                                           ║
# ╠════════════════════════════════════════════════════════════════════════════╣
# ║ Spectral Frequency: <value>                                               ║
# ║ Architectural Role: <value>                                               ║
# ║ Semantic ID: <SID>                                                        ║
# ║ Purpose: <one-line purpose>                                               ║
# ║ Exports: <symbols / entrypoints>                                          ║
# ║ Flags/Modes: <if any>                                                     ║
# ║ Cross-References: <if any>                                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝
```

**SID naming convention:** `SCRIPT_<FILENAME_UPPERCASE>_V1`

---

### Task 2: Update HARVEST_REGISTRY.md

File: `dumpster-dive/HARVEST_REGISTRY.md`

Currently only tracks one harvest (`pr-harvest-2026-01-29`). Add entries for these existing harvests in `dumpster-dive/`:
- `overnight-daemon/`
- `sentry-probe/`
- `protocols/`
- `templates/`
- `toolchain-probe/`
- `claudine-harvest/`
- `INSTRUCTIONS_ORE_BATCH_20251230.md`

Use the existing entry format as a template.

---

### Task 3: Fix docs/SUMMARY.md Broken References

File: `docs/SUMMARY.md`

This file references `./docs/sessions/*.md` files that don't exist. Either:
1. Remove the broken references
2. Or comment them out with a note

---

## Execution Contract

- **No menus** — execute each task in sequence
- **Trust this handoff** — context is accurate
- **Report what you DID** — not what you could do
- **Update `codex/NEXT.md`** when complete with status

---

## References

- Envelope template: `~/.codex/skills/script-envelope/references/envelope-template.md`
- Existing envelopes to reference: `scripts/chthonic.ps1`, `scripts/chthonic.py`
- Context hygiene protocol: `codex/protocols/GEMINI_CONTEXT_HYGIENE.md`

---

**Handoff Hash:** `CLAUDE_TO_CODEX_2026_02_03_ENVELOPE_CONTINUATION`
**Tasks:** 3
**Expected Changes:** 6 PowerShell files + 2 markdown files
