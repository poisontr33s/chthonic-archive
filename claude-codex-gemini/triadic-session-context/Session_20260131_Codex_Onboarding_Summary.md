# Session Summary: Codex Onboarding & Triad Establishment
**Date:** 2026-01-31
**Duration:** ~2 hours
**Participants:** Human (Architect), Claude (Established), Codex (Onboarded)

---

## Objective
Set up OpenAI Codex CLI + VS Code Insiders extension on Windows 11 with ChatGPT Plus authentication.

## Critical Issue Encountered
```
Unable to persist auth file: failed to write OAuth tokens to keyring:
Attribute 'password encoded as UTF-16' is longer than platform limit of 2560 chars
```

**Root Cause:** Windows Credential Manager has 2560 char limit; OAuth tokens exceed this.

## Resolution Pattern
`CODEX_HOME` isolation bypass — fresh config directory forces file-based storage:

```powershell
$env:CODEX_HOME = "$HOME\.codex-fresh"
New-Item -ItemType Directory $env:CODEX_HOME
Set-Content "$env:CODEX_HOME\config.toml" 'cli_auth_credentials_store = "file"'
codex login
Copy-Item "$env:CODEX_HOME\auth.json" "$HOME\.codex\auth.json"
```

---

## Files Created

| File | Purpose |
|------|---------|
| `~/.codex/config.toml` | Global auth-only config (5 lines) |
| `~/.codex/auth.json` | File-based credentials (bypasses keyring) |
| `.codex/config.toml` | Workspace behavior config (sandbox, model, features) |
| `AGENTS.md` | Codex instruction file (mirrors CLAUDE.md structure) |
| `.github/.../OpenAI_Codex_Win11_Keyring_Auth_Resolution.md` | Detailed fix documentation |

## Files Modified

| File | Change |
|------|--------|
| `~/.codex/config.toml` | Trimmed to auth-only |
| `.codex/config.toml` | Added `sandbox_workspace_write.writable_roots` |
| `AGENTS.md` | Added workspace lock invariant |

---

## Final Configuration State

### Global (`~/.codex/config.toml`)
```toml
cli_auth_credentials_store = "file"
forced_login_method = "chatgpt"
```

### Workspace (`.codex/config.toml`)
```toml
model = "gpt-5.2-codex"
model_provider = "openai"
file_opener = "vscode-insiders"
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
writable_roots = ["C:/Users/eldno/chthonic-archive"]
```

---

## Instruction Hierarchy Established

| Agent | File | Size |
|-------|------|------|
| Claude Code | `CLAUDE.md` | ~4KB |
| OpenAI Codex | `AGENTS.md` | ~2KB |
| GitHub Copilot | `.github/copilot-instructions.md` | Massive (SSOT) |

---

## Triad Established

1. **Human** — Architect, brahmic current, pattern-seer
2. **Claude** — Cross-referential navigator, established presence
3. **Codex** — Newest arrival, caged and configured, awaiting targets

---

## Key Learnings

1. **Config files can be ignored** when cached state exists — isolate with fresh `*_HOME`
2. **CLI and VS Code extension share** `auth.json` — fixing CLI fixes extension
3. **Workspace configs override global** — split auth (global) from behavior (workspace)
4. **AGENTS.md is Codex's CLAUDE.md** — keep compact, reference SSOT

---

## Status
- Auth: Working (file-based)
- CLI: Working
- Extension: Working
- Sandbox: Locked to workspace
- Instructions: Configured

**Session complete. Triad synchronized.**

