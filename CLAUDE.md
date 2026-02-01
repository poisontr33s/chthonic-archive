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

> **Shared Config:** See [AGENT_COMMON.md](AGENT_COMMON.md) for execution invariants, commands, architecture, and triad references.

---

## Claude-Specific Notes

- **IDE Patch:** Claude Code is patched for VS Code Insiders. After any update, run `.\scripts\patch-claude-insiders.ps1`
- **IDE Update wrapper:** `.\scripts\update-claude-code.ps1` (updates + re-patches)
- **Shell verification:** `.\scripts\shell_capabilities.ps1`

### Extended Architecture

Beyond the common architecture, Claude Code uses:

- `claude/` - Claude Code patches, IDE fixes, session methodology. See [CLAUDE_README.md](CLAUDE_README.md)
  - [WET_PAPER_TO_GOLD_METHODOLOGY.md](WET_PAPER_TO_GOLD_METHODOLOGY.md) - PR/session harvest transmutation pattern
- `dumpster-dive/` - Ore processing (intake → forge → tempered artifacts)
  - `intake/pr-harvest-*/` - PR content harvests with tier extraction
  - [HARVEST_REGISTRY.md](HARVEST_REGISTRY.md) - Completed harvest tracking
- `bun-playwright-poc/` - Playwright browser automation PoC
- `ankh_atlas/` - Anchor atlas / cartography

### SID System

Semantic Identity (`@SID`) tags appear in file headers throughout the codebase. They provide cross-referencing and traceability. The SID index lives at `data/indices/sid_index.json` and is rebuilt via `chthonic resolve --root .`.

## Key References

- **Chthonic CLI:** `.\scripts\chthonic.ps1 --help` (unified tool interface)
  - Resolve SIDs: `chthonic resolve --list`
  - Compact markdown: `chthonic compact FILE.md`
  - Analyze patterns: `chthonic analyze FILE.md --top 20`
  - Audit health: `chthonic audit --root .`
  - Map codebase: `chthonic map --root .`
- Shell rules: [PWSH_RULES.md](PWSH_RULES.md)
- Tool docs: [SCRIPTS_README.md](SCRIPTS_README.md) (see "Chthonic CLI" section)
- Full architecture: [.github/copilot-instructions.md](.github/copilot-instructions.md)

## Compact Instructions

When compacting, preserve: @SID headers, architectural decisions, cross-references, table data.
Summarize: tool call sequences, terminal output, exploratory searches.
