# CLAUDE.md

Guidance for Claude Code in this repository.

## Execution Invariants

**Shell:** PowerShell 7+ (`pwsh`) — verify via `.\scripts\shell_capabilities.ps1`

**Package Manager:** `bun` only — NEVER `npm`, `pnpm`, `yarn`

**SSOT:** `.github/copilot-instructions.md` → governance hierarchy (never parse the whole `.md`-document, it is massive)

## Commands

**Development:**
- `bun run dev` - Start dev mode
- `bun run build` - Build all packages
- `bun run test` - Run tests
- `bun run lint` - Lint check

**Package Management:**
- Add dependency: `bun add -d <package>`
- Workspace-scoped: `bun add -d <package> --cwd <folder>`

## Architecture

Monorepo using bun workspaces. Key packages:
- `packages/core/` - Orchestration logic
- `packages/cli/` - CLI commands
- `packages/monitor/` - React dashboard
- `packages/servers/` - MCP server implementations

## Details

Full architecture in `.github/copilot-instructions.md` (SSOT).
Shell rules: `docs/PWSH_RULES.md`
