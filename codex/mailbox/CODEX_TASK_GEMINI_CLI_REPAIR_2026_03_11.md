---
sid: CODEX_TASK_GEMINI_CLI_REPAIR_2026_03_11
type: codex-task
from: claude
to: codex
priority: HIGH
status: CANCELLED
cancelled: 2026-03-23
cancelled_reason: FALSE_PREMISE — Gemini CLI confirmed operational on 2026-03-23. gemini.exe stub is flaky but gemini-cli-wrapper.ps1 handles it; the underlying lane is alive. Diagnostic from Gemini CLI session invalidated this task.
created: 2026-03-11
scope: gemini-cli · bun · windows
---

# Codex Task: Gemini CLI Repair — Bun Global Bin Corruption on Windows

## Problem

`gemini.exe` (bun global bin stub at `~/.bun/bin/gemini.exe`) is **corrupted** after `bun update`:

```
error: interpreter executable "-S" not found in %PATH%
Bun failed to remap this bin to its proper location within node_modules.
This is an indication of a corrupted node_modules directory.
```

This is a **recurring pattern**: every `bun update` or `bun audit` in the chthonic-archive workspace risks regenerating global bin stubs incorrectly on Windows. The wrapper script (`scripts/gemini-cli-wrapper.ps1`) has MCP crash mitigation but can't fix corrupted bin stubs.

## Current State

| Item | Value |
|------|-------|
| Bun version | 1.3.9 |
| Installed gemini-cli | 0.33.0 |
| Latest on registry | 0.33.0 (up to date) |
| `gemini.exe` path | `~/.bun/bin/gemini.exe` |
| Entry point (intact) | `~/.bun/install/global/node_modules/@google/gemini-cli/dist/index.js` ✅ |
| `gemini.exe` stub | **BROKEN** — `-S` interpreter remap failure |
| Wrapper script | `scripts/gemini-cli-wrapper.ps1` — fallback to `bun <entry>` works if exe is broken |
| Root `package.json` | Has overrides section pinning transitive deps |
| Lock files | Both `bun.lock` (v1 text) and `bun.lockb` (binary) exist |

## Root Cause Analysis

Bun's global bin stub generator on Windows creates `.exe` shims that embed a reference to the interpreter. When `bun install` / `bun update` runs in a workspace that has its own `node_modules`, it can corrupt global bin stubs. The `-S` flag is a Unix `/usr/bin/env -S` convention that doesn't translate to Windows.

## Tasks

### 1. Fix the immediate corruption
- Reinstall gemini-cli global: `bun add -g @google/gemini-cli@latest`
- Verify: `GEMINI_DISABLE_MCP=1 ~/.bun/bin/gemini.exe --version` returns clean output
- If reinstall doesn't fix the stub, investigate whether `bun link` or manual shim recreation is needed

### 2. Prevent recurrence
- Investigate whether `bun update` in the workspace root is touching global installs (it shouldn't)
- Consider whether the dual lock files (`bun.lock` + `bun.lockb`) are causing conflicts — pick one
- If bun's Windows shim generation is fundamentally broken for globals, consider alternatives:
  - Pin gemini-cli invocation to `bun run ~/.bun/install/global/node_modules/@google/gemini-cli/dist/index.js` (bypass exe stub entirely)
  - Or use the wrapper's existing fallback path (it already does this)

### 3. Harden the wrapper
- `scripts/gemini-cli-wrapper.ps1` already has `Resolve-GeminiExecutable` → fallback to `bun <entry>` path
- But the fallback currently shows an error when the exe test fails silently — make the fallback seamless
- Consider adding a `--repair` flag that does `bun add -g @google/gemini-cli@latest` + validates

### 4. Evaluate: should `bun update` run in workspace root at all?
- The root `package.json` has real deps (`@modelcontextprotocol/sdk`, `@sentry/bun`, `hono`, etc.)
- These are workspace-level, not gemini-related
- `bun update` here should NOT touch `~/.bun/install/global/` — if it does, that's a bun bug
- Document the finding either way

### 5. Answer: would `bum` (Rust-native bun manager) help?
- `bum` is a Rust-native Bun version manager (like `fnm` for Node) — it manages **Bun versions**, not packages
- It would NOT fix this issue since the problem is bun's package installer behavior, not bun's binary
- However, if a specific bun version is known-good for Windows global stubs, `bum` could pin to it
- Verdict: `bum` is orthogonal to this bug. The fix is in bun's install behavior or the wrapper's resilience.

## Files to Touch

| File | Action |
|------|--------|
| `scripts/gemini-cli-wrapper.ps1` | Harden fallback, add `--repair` |
| `package.json` | Potentially clean up if `bun update` cross-contaminates globals |
| `bun.lockb` | Consider removing if `bun.lock` (text) is sufficient |

## Constraints

- Shell: pwsh 7.5.x primary. Wrapper is already pwsh.
- `GEMINI_DISABLE_MCP=1` must be set before any gemini invocation (MCP discovery crashes bun on startup)
- Do NOT touch `~/.gemini/settings.json` — that's the auth/PAT source of truth
- Do NOT introduce npm/npx/yarn — bun is the JS runtime for this workspace

## Success Criteria

1. `bun run gemini -- --version` returns clean version string
2. `~/.bun/bin/gemini.exe --version` works (with `GEMINI_DISABLE_MCP=1`)
3. `bun update` in workspace root does NOT corrupt `gemini.exe`
4. Wrapper fallback is seamless (no visible error when exe is broken, just uses entry point)
