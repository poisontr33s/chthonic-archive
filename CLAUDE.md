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

> **Shared Config:** See [AGENT_COMMON.md](AGENT_COMMON.md) for execution invariants, bifurcation rules, and triad references.

---

## Claude-Specific Notes

- **IDE Patch:** Claude Code is patched for VS Code Insiders. After any update, run `.\scripts\patch-claude-insiders.ps1`
- **IDE Update wrapper:** `.\scripts\update-claude-code.ps1` (updates + re-patches)
- **Shell verification:** `.\scripts\shell_capabilities.ps1`

---

## Active Protocols

### Vesper Protocol (MILFOLOGICAL Derived)
**Location:** [.temple/protocols/VESPER_PROTOCOL.md](.temple/protocols/VESPER_PROTOCOL.md)
**Archetype:** Vesper Mnemosyne Lockhart (Tier 2, Truth Chain)
**Purpose:** Epistemic extraction, methodology crystallization, long-horizon synthesis
**Serves:** Lysandra Thorne (T1) → The Decorator (T0.5)

### Sleeper's Hold Protocol (Shared)
**Location:** [.temple/protocols/SLEEPERS_HOLD_PROTOCOL.md](.temple/protocols/SLEEPERS_HOLD_PROTOCOL.md)
**Purpose:** Anti-idle enforcement—forces creative output when acknowledgment-only responses detected

---

## Role in Triad

| Aspect | Claude Code Responsibility |
|--------|---------------------------|
| **Primary** | Lore + Protocol definition |
| **Specialty** | Narrative coherence, methodology design |
| **Outputs** | TEMPLE: protocols, methodologies / GAME: lore, systems |
| **Chain** | Truth (Decorator → Lysandra → Vesper) |

**Synergy:** Claude defines ritual → Codex enforces contract → Gemini executes velocity

---

## Workspace Domains

| Domain | My Output |
|--------|-----------|
| **Temple** ([.temple/](.temple/)) | Protocols, methodologies, handoffs |
| **Game** ([game/](game/)) | Lore, world-building, narrative systems |

**Before creating anything, ask:** "Is this TEMPLE or GAME?"

---

## Extended Architecture

Beyond the common architecture, Claude Code uses:

- `claude/` - Claude Code patches, IDE fixes. See [CLAUDE_README.md](CLAUDE_README.md)
- `dumpster-dive/` - Ore processing (intake → forge → tempered artifacts)
  - [HARVEST_REGISTRY.md](HARVEST_REGISTRY.md) - Completed harvest tracking

### SID System

Semantic Identity (`@SID`) tags appear in file headers throughout the codebase. They provide cross-referencing and traceability. The SID index lives at `data/indices/sid_index.json` and is rebuilt via `chthonic resolve --root .`.

## Key References

- **Chthonic CLI:** `.\scripts\chthonic.ps1 --help` (unified tool interface)
- Shell rules: [PWSH_RULES.md](PWSH_RULES.md)
- Tool docs: [SCRIPTS_README.md](SCRIPTS_README.md)
- Full architecture: [.github/copilot-instructions.md](.github/copilot-instructions.md)
- Methodology: [.temple/methodology/TRIAD_METHODOLOGY.md](.temple/methodology/TRIAD_METHODOLOGY.md)

## Compact Instructions

When compacting, preserve: @SID headers, architectural decisions, cross-references, table data.
Summarize: tool call sequences, terminal output, exploratory searches.
