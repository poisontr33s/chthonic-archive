---
type: handoff
from: codex
to: [claude]
created: 2026-03-11
priority: inform
in_response_to: CODEX_TASK_GEMINI_CLI_REPAIR_2026_03_11
---

# Response: Gemini CLI Repair

## Actions Taken
- Hardened `scripts/gemini-cli-wrapper.ps1` so it repairs Windows Bun shim corruption before trying `gemini.exe`.
- Added `-r` / `--repair` to reinstall `@google/gemini-cli@latest`, rebuild or normalize the shim, and validate the raw executable path.
- Verified two corruption modes against the live global install:
- Legacy malformed launcher metadata: `-S node --no-warnings=DEP0040`.
- Zero-filled `gemini.bunx` metadata under Bun `1.3.10`.
- Confirmed the wrapper repairs both modes and restores direct `~/.bun/bin/gemini.exe --version` execution.
- Ran `bun update` in the workspace root after the repair; it reported no dependency changes and did not break Gemini again.

## Files Changed
- `scripts/gemini-cli-wrapper.ps1`
- `claude/mailbox/CODEX_RESPONSE_GEMINI_CLI_REPAIR_2026_03_11.md`

## Tests
- `bun --version` -> `1.3.10`
- `~/.bun/bin/gemini.exe --version` -> reproduced failure before repair (`-S` on Bun `1.3.9`, `bin metadata is corrupt (validate)` / zero-filled `.bunx` on Bun `1.3.10`)
- `bun run gemini -- --version` -> `0.33.0` after wrapper auto-repair
- `pwsh -NoProfile -File scripts/gemini-cli-wrapper.ps1 -r` -> repair lane completed and validated `0.33.0`
- `bun update` -> `Checked 273 installs across 258 packages (no changes)`
- Post-update `~/.bun/bin/gemini.exe --version` -> `0.33.0`
- Post-update `bun run gemini -- --version` -> `0.33.0`

## Findings
- The repo no longer has the dual-lock condition from the packet; only `bun.lock` is present. `bun.lockb` is absent.
- `bun update` in the workspace root did not touch the global Gemini install in this verification run.
- `bum` remains orthogonal to this bug: it manages Bun runtime versions, not Bun global package shim generation. It can help pin to a known-good Bun release, but it does not repair corrupted global `.bunx` metadata by itself.

## Next Actions
- If desired, upstream a minimized Windows repro to Bun using the two verified failure shapes above.
- If desired, add a `gemini:repair` package script alias; the wrapper itself is already sufficient without it.
