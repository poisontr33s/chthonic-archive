# AGENTS.md

This file provides guidance to OpenAI Codex when working with code in this repository.

## Execution Invariants

- **Workspace Lock:** Run Codex from repo root (`C:\Users\erdno\chthonic-archive`). Do not use `-C` to change directories unless explicitly instructed.
- **Shell:** PowerShell 7+ (`pwsh`) — NEVER use bash syntax on Windows
- **Package Manager:** `bun` only — NEVER `npm`, `pnpm`, `yarn`
- **SSOT:** `.github/copilot-instructions.md` (governance hierarchy — never parse whole file, it is massive)
- **Platform:** Windows 11 (MSYS/MINGW paths may appear in git context; always use PowerShell-native paths)
- **IDE:** VS Code Insiders (`code-insiders`)
- **Python:** Use `uv run python` — never raw `python` or `pip`

## Commands

- `bun run dev` - Start dev mode
- `bun run build` - Build all packages
- `bun run test` - Run tests
- `bun run lint` - Lint check
- Add dep: `bun add -d <package>`
- Rust build: `cargo build`
- MCP validation: `bun run mcp/scripts/validate.ts`

## Architecture

Bun + Rust + Python polyglot repo — each subdirectory is semi-independent.

| Directory | Purpose |
|-----------|---------|
| `src/` | Rust core binary, render engine |
| `scripts/` | Python + PowerShell tooling |
| `mas_mcp/` | Python async MCP server |
| `mcp/` | TypeScript MCP server |
| `chthonic-vscode-extension/` | VSCode sidebar extension |
| `.github/instructions/` | Modular instruction branches |

## Key Constraints

1. **No Content Duplication** — Never duplicate content from SSOT into other files
2. **PowerShell Only** — All shell commands must be pwsh-compatible
3. **Bun Only** — Never use npm/yarn/pnpm
4. **UV for Python** — `uv run python script.py`, never raw `python`

## Instruction References

For detailed guidance, see modular instructions in `.github/instructions/`:
- `technical-directives.instructions.md` - Dev conventions
- `python-scripting.instructions.md` - Python/UV rules
- `project-workflow.instructions.md` - Workflow patterns

## Codex-Specific Config

Codex workspace config lives at `.codex/config.toml` (this workspace).
Global auth config lives at `~/.codex/config.toml`.

Do not modify auth settings — they are workspace-locked.

## Session Waypoint

For next steps and session continuity, see `codex/NEXT.md`.

## Triadic Shared Log

Shared, structured triad session index lives at:
- `claude-codex-gemini/triadic-session-shared-0001.md`
- `claude-codex-gemini/triadic-session-context/` (knowledge base)
