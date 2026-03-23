---
type: handoff
from: codex
to: [claude]
created: 2026-03-16
priority: inform
in_response_to: CODEX_TASK_GEMINI_CLI_REPAIR_2026_03_11
status: SUPERSEDED
superseded: 2026-03-23
superseded_reason: Parent task CANCELLED/INVALID — Gemini CLI operational as of 2026-03-23. Wrapper hardening in this response is retained as useful defensive work, but the repair narrative is no longer the system truth.
---

# Response: Gemini CLI Repair

## Actions Taken
- Reproduced the Windows Bun global shim bug on live `bun 1.3.10`: fresh `bun add -g @google/gemini-cli@latest` writes `gemini.bunx` with `-S node --no-warnings=DEP0040`, and direct `gemini.exe --version` fails.
- Hardened `scripts/gemini-cli-wrapper.ps1` to discover Gemini's global package under both `C:\Users\<user>\node_modules\@google\gemini-cli` and the legacy `.bun\install\global\node_modules\...` layout, silence probe noise, and fall back cleanly to `bun <entry>` when the shim is missing or invalid.
- Kept `-r` / `--repair` as the explicit lane that reinstalls globally and normalizes the real Bun-generated `gemini.bunx`. I removed the synthetic bunx rewrite path after it produced a bad module root; missing metadata now falls back to the entrypoint instead of fabricating shim bytes.
- Disabled the unfinished embalm lane per user direction by marking it `DO-NOT-USE-UNFINISHED-DEV--WIP` in `AGENT_COMMON.md`, `.codex/skills/corpse-reviver/SKILL.md`, `.codex/skills/corpse-reviver/scripts/embalm_before_edit.py`, and `.codex/skills/corpse-reviver/scripts/corpse_reviver.py`.

## Files Changed
- `scripts/gemini-cli-wrapper.ps1`
- `AGENT_COMMON.md`
- `.codex/skills/corpse-reviver/SKILL.md`
- `.codex/skills/corpse-reviver/scripts/embalm_before_edit.py`
- `.codex/skills/corpse-reviver/scripts/corpse_reviver.py`
- `claude/mailbox/CODEX_RESPONSE_GEMINI_CLI_REPAIR_2026_03_11.md`

## Tests
- `bun --version` -> `1.3.10`
- `bun add -g @google/gemini-cli@latest` -> installed `0.33.2`, reproduced broken `-S node` launcher in `~/.bun/bin/gemini.bunx`
- `GEMINI_DISABLE_MCP=1 ~/.bun/bin/gemini.exe --version` before repair -> `error: interpreter executable "-S" not found in %PATH%`
- `pwsh -NoProfile -File scripts/gemini-cli-wrapper.ps1 -v` -> `0.33.2`
- `pwsh -NoProfile -File scripts/gemini-cli-wrapper.ps1 -r` -> `Updated Gemini CLI version: 0.33.2` and `Repair validated: 0.33.2`
- `bun run gemini -- --version` -> `0.33.2`
- `GEMINI_DISABLE_MCP=1 ~/.bun/bin/gemini.exe --version` after repair -> `0.33.2`
- Missing metadata probe: moved `gemini.bunx` aside, `pwsh -NoProfile -File scripts/gemini-cli-wrapper.ps1 -v` still returned `0.33.2`, and Bun recreated a working `gemini.bunx`
- Temp workspace probe: copied root `package.json` and `bun.lock` to `%TEMP%`, ran `bun update`, result `shim-unchanged`
- `uv run --no-project .codex/skills/corpse-reviver/scripts/embalm_before_edit.py` -> `DO-NOT-USE-UNFINISHED-DEV--WIP: embalm_before_edit.py is unfinished and disabled.`
- `uv run --no-project .codex/skills/corpse-reviver/scripts/corpse_reviver.py embalm-before-edit` -> `DO-NOT-USE-UNFINISHED-DEV--WIP: embalm-before-edit is unfinished and disabled.`
- `git diff --check` -> no diff errors; only LF normalization warnings on touched docs/scripts

## Findings
- Current Bun global package layout is `C:\Users\eldno\node_modules\@google\gemini-cli`, not the older `~/.bun/install/global/node_modules/...` path hard-coded in the wrapper.
- The immediate corruption trigger is Bun's own global install and shim generation on Windows, not the workspace dependency graph.
- A workspace-style `bun update` did not rewrite or corrupt the global Gemini shim in the temp probe (`shim-unchanged`).
- `bum` remains orthogonal: it manages Bun runtime versions, not Bun global package shim generation.

## Next Actions
- Upstream a minimized Bun Windows repro using the broken `-S node --no-warnings=DEP0040` `.bunx` payload.
