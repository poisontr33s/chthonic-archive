<!--
================================================================================
SEMANTIC IDENTITY (Anchor & Signal Protocol)
================================================================================
@SID:           DOC_CLAUDE_MD_ROOT
@Type:          Documentation
@Context:       Agent Guidance / Claude Code
@SessionOrigin: STANDALONE_2026_01_27
@References:    TOOL_COMPACT_MD_V1, TOOL_SID_RESOLVER_V1, TOOL_CHTHONIC_ROUTER_PWSH
================================================================================
-->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Execution Invariants

- **Shell:** PowerShell 7+ (`pwsh`) — verify via `.\scripts\shell_capabilities.ps1`. NEVER use bash syntax.
- **Package Manager:** `bun` only — NEVER `npm`, `pnpm`, `yarn`
- **SSOT:** `.github/copilot-instructions.md` (governance hierarchy — never parse whole file, it is massive)
- **Platform:** Windows (MSYS/MINGW paths may appear in git context; always use PowerShell-native paths)
- **IDE:** VS Code Insiders (`code-insiders`) — Claude Code is patched to resolve this binary. See [claude/README.md](./claude/README.md) for details. After any Claude Code update, run `.\scripts\patch-claude-insiders.ps1`

## Commands

- `bun run dev` - Start dev mode
- `bun run build` - Build all packages
- `bun run test` - Run tests (note: `bunfig.toml` excludes `bun-playwright-poc/**` and `*.spec.ts`)
- `bun run lint` - Lint check
- Add dep: `bun add -d <package>` | Workspace: `bun add -d <pkg> --cwd <folder>`
- VSCode extension: `cd chthonic-vscode-extension && bun run build` (CJS format, not ESM)
- MCP validation: `bun run mcp/scripts/validate.ts`
- Rust build: `cargo build` (workspace root `Cargo.toml`)

## Architecture

Bun + Rust + Python polyglot repo — no unified monorepo workspace; each subdirectory is semi-independent.

- `src/` - Rust core binary (`main.rs`), render engine, data structures
- `scripts/` - Python tooling + PowerShell scripts (SID resolver, health audit, compactor, chthonic CLI router)
- `mas_mcp/` - Python async MCP server (GPU orchestration, SSOT extractor — large `server.py`)
- `mcp/` - TypeScript MCP server (integration tests, validation, smoke tests)
- `bun-playwright-poc/` - Playwright browser automation PoC
- `chthonic-vscode-extension/` - VSCode sidebar extension (CJS, uses `vscode.lm` Copilot API)
- `ankh_atlas/` - Anchor atlas / cartography
- `claude/` - Claude Code patches, IDE fixes, session methodology (see [README.md](./claude/README.md))
  - [WET_PAPER_TO_GOLD_METHODOLOGY.md](./claude/WET_PAPER_TO_GOLD_METHODOLOGY.md) - PR/session harvest transmutation pattern
- `dumpster-dive/` - Ore processing (intake → forge → tempered artifacts)
  - `intake/pr-harvest-*/` - PR content harvests with tier extraction
  - [HARVEST_REGISTRY.md](./dumpster-dive/HARVEST_REGISTRY.md) - Completed harvest tracking
- `docs/` - Shell governance (`PWSH_RULES.md`), session docs, state files

### SID System

Semantic Identity (`@SID`) tags appear in file headers throughout the codebase. They provide cross-referencing and traceability. The SID index lives at `data/indices/sid_index.json` and is rebuilt via `chthonic resolve --root .`.

## Key References

- **Chthonic CLI:** `.\scripts\chthonic.ps1 --help` (unified tool interface)
  - Resolve SIDs: `chthonic resolve --list`
  - Compact markdown: `chthonic compact FILE.md`
  - Analyze patterns: `chthonic analyze FILE.md --top 20`
  - Audit health: `chthonic audit --root .`
  - Map codebase: `chthonic map --root .`
- **IDE Patch:** `.\scripts\patch-claude-insiders.ps1` (re-apply after Claude Code updates)
- **IDE Update wrapper:** `.\scripts\update-claude-code.ps1` (updates Claude Code + re-patches)
- Shell rules: [docs/PWSH_RULES.md](./docs/PWSH_RULES.md)
- Tool docs: [scripts/README.md](./scripts/README.md) (see "Chthonic CLI" section)
- Full architecture: [.github/copilot-instructions.md](./.github/copilot-instructions.md)

## Compact Instructions

When compacting, preserve: @SID headers, architectural decisions, cross-references, table data.
Summarize: tool call sequences, terminal output, exploratory searches.

## Session Waypoint

For next steps and session continuity, see `codex/NEXT.md`.
