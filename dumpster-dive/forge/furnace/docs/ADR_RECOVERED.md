---
sid: FORGE_ADR_RECOVERED_V1
title: Recovered Architecture Decisions
created: 2026-03-05T16:04:23+00:00
source_files: ["codex/mailbox/RESEARCH_DIGEST_PREAMBLE.md", "codex/mailbox/RESEARCH_DIGEST_PREAMBLE.md", "codex/mailbox/RESEARCH_DIGEST_PREAMBLE.md", "codex/mailbox/RESEARCH_DIGEST_PREAMBLE.md", "codex/mailbox/RESEARCH_DIGEST_PREAMBLE.md", "codex/mailbox/RESEARCH_DIGEST_PREAMBLE.md", "claude/mailbox/GENRE_EXTRACTION_2026_02_24.md", "claude/mailbox/GENRE_EXTRACTION_2026_02_24.md", "dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md", "dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md", "dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md", "dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md", "dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md", "dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md", "dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md", "dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md", "dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md", "dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md"]
pathway: markdown fragments -> decision capture -> recovered ADR anthology
kept: Headings, rationale sentences, and provenance.
discarded: Formatting noise and broken draft fragments.
---
# Recovered Architecture Decisions

## ADR-01: Research Digest: **\[PREAMBLE:\]**

- Classification: **research-results** - Source: `claude-codex-gemini/engineering_agentic_deep_research_candidates/gemini-deep-research-2026-02/ANNO_RUSTIFICATION_ENDO_DOT_LIFE.md`

_Provenance: `codex/mailbox/RESEARCH_DIGEST_PREAMBLE.md` / `c088250b990ab94d`_

## ADR-02: Findings

- ***The Insiders Shell:** The IDE executable (devenv.exe) and the graphical shell are pulled from the high-frequency Insiders feed. This ensures access to the latest "Fluent Design" UI updates, AI-driven refactoring tools, and the advanced layout engines required for next-generation extensions.2* - ***The Build Tools LSL:** Crucially, the compiler toolsets (MSVC, Clang-CL,.NET SDKs) are configured to the "Latest Stable Lane." This "LSL" designation acts as a filter within the installer, rejecting experimental compiler builds that might introduce binary incompatibility or codified regressions.* - ***Operational Mechanic:** When the user engages the "Modify" interface in the Visual Studio 2026 Installer, the GUI dynamically queries the channel manifest. By selecting the "Insiders LSL" option for the **Visual Studio 2026 Build Tools**, the user effectively creates a "stable core" wrapped in an "experimental shell." This architecture prevents the common "bleeding edge" scenario where an IDE update breaks the ability to compile production code.3* - ***Resource Reclamation:** Legacy installers maintain gigabytes of cached packages (Package Cache) and redundant MSVC libraries. Removing the 2022 LSL frees significantly high-performance NVMe storage, which is better utilized for the extensive caching mechanisms of uv and mise.*

_Provenance: `codex/mailbox/RESEARCH_DIGEST_PREAMBLE.md` / `c088250b990ab94d`_

## ADR-03: Decisions

| Decision | Options | Recommendation | |---|---|---| | ***Operational Mechanic:** When the user engages the "Modify" interface in the Visual Studio 2026 Installer, the GUI dynamically queries the channel manifest. By selecting the "Insiders LSL" option for the **Visual Studio 2026 Build Tools**, the user effectively creates a "stable core" wrapped in an "experimental shell." This architecture prevents the common "bleeding edge" scenario where an IDE update breaks the ability to compile production code.3* | Yes / No | Needs explicit choice after review. | | ***Bun:** The Zig-based JavaScript runtime bun replaces Node.js for tooling scripts. Its instant startup time aligns with the "Rustified" philosophy, making it the preferred runner for lightweight automation tasks within the mise ecosystem.8* | Yes / No | Needs explicit choice after review. |

_Provenance: `codex/mailbox/RESEARCH_DIGEST_PREAMBLE.md` / `c088250b990ab94d`_

## ADR-04: Actionable Items

- [ ] [manual] ***Operational Mechanic:** When the user engages the "Modify" interface in the Visual Studio 2026 Installer, the GUI dynamically queries the channel manifest. By selecting the "Insiders LSL" option for the **Visual Studio 2026 Build Tools**, the user effectively creates a "stable core" wrapped in an "experimental shell." This architecture prevents the common "bleeding edge" scenario where an IDE update breaks the ability to compile production code.3* (manual-review) - [ ] [manual] ***Challenge:** The AI must implement a ViewContainer provider that dynamically changes the icon of the container based on the active toolchain.* (manual-review) - [ ] [chthonic] ***Challenge:** The "Chthonic Archive" must implement a "Context-Aware Layout Engine."* (scripts/chthonic.ps1) - [ ] [codex] ***Validate:** Query the local mise instance to verify that the active tools are the "Rustified" variants (uv instead of pip).* (manual-review)

_Provenance: `codex/mailbox/RESEARCH_DIGEST_PREAMBLE.md` / `c088250b990ab94d`_

## ADR-05: Dependencies

| Dependency | Install Vector | Evidence | |---|---|---| | cmake | manual | Mentioned in source text: cmake | | ninja | manual | Mentioned in source text: ninja |

_Provenance: `codex/mailbox/RESEARCH_DIGEST_PREAMBLE.md` / `c088250b990ab94d`_

## ADR-06: Contradictions

- None detected.

_Provenance: `codex/mailbox/RESEARCH_DIGEST_PREAMBLE.md` / `c088250b990ab94d`_

## ADR-07: session gone sterile issue Handover discernment

**Path:** `dumpster-dive/from-github/macro-prompt-world/disparate-md-documentation/session_gone_sterile_issue_Handover_discernment.md` **Tags:** **Ankh Layer:** unknown **Tribunal:** unspecified

_Provenance: `claude/mailbox/GENRE_EXTRACTION_2026_02_24.md` / `0737f75ccb97de80`_

## ADR-08: SSOT TRIBUNAL BRIDGE

**Path:** `.temple/governance/SSOT_TRIBUNAL_BRIDGE.md` **Tags:** **Ankh Layer:** unknown **Tribunal:** unspecified

_Provenance: `claude/mailbox/GENRE_EXTRACTION_2026_02_24.md` / `0737f75ccb97de80`_

## ADR-09: ☥ Overnight Intelligence Report — 2026-02-11T02-19-33

**Duration:** 1.3 minutes **Tasks:** 5 done, 0 failed, 5 total **Model:** claude-haiku-4.5

_Provenance: `dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md` / `3c682443993f4f3d`_

## ADR-10: File Census — 2026-02-11T02-19-33

**Total files:** 1075

_Provenance: `dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md` / `3c682443993f4f3d`_

## ADR-11: By Extension

| Ext | Count | Total Lines | |-----|-------|-------------| | .py | 798 | 222,983 | | .ts | 113 | 49,479 |

_Provenance: `dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md` / `3c682443993f4f3d`_

## ADR-12: Top 20 Largest Files

| File | Lines | Size | |------|-------|------| | meta-ide\copilot-cli-0.0.406\sdk\index.d.ts | 15,475 | 532.9 KB | | meta-ide\copilot-sdk\sdk\index.d.ts | 15,475 | 532.9 KB |

_Provenance: `dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md` / `3c682443993f4f3d`_

## ADR-13: Analysis: GitHub Copilot SDK Type Definitions

**None visible in snippet.** Only type/interface exports shown.

_Provenance: `dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md` / `3c682443993f4f3d`_

## ADR-14: 1. Exported Functions

**None visible in snippet.** Only type/interface exports shown.

_Provenance: `dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md` / `3c682443993f4f3d`_

## ADR-15: 2. Key Interfaces/Types

| Name | Purpose | |------|---------| | `AbortEvent` | User abort event; triggers completion of orphaned tool calls |

_Provenance: `dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md` / `3c682443993f4f3d`_

## ADR-16: 3. Integration Patterns Worth Noting

1. **Zod-based validation**: All events use `z_2.infer<typeof [Schema]>` for type-safe schema definitions. 2. **Ephemeral vs persistent**: Events flagged `ephemeral: true` (streaming) vs persistent (transcript). 3. **Streaming support**: `AssistantMessageDeltaEvent` accumulates chunks for incremental response building.

_Provenance: `dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md` / `3c682443993f4f3d`_

## ADR-17: VS Code Extension Source Review

**Purpose:** Implements the ACP protocol client handling agent requests (file I/O, terminal creation, permission checks).

_Provenance: `dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md` / `3c682443993f4f3d`_

## ADR-18: 1. **extensions\chthonic-archive\src\acp\client.ts**

**Purpose:** Implements the ACP protocol client handling agent requests (file I/O, terminal creation, permission checks). **Issues Found:**

_Provenance: `dumpster-dive/intake/overnight-intelligence/2026-02-11T02-19-33/report.md` / `3c682443993f4f3d`_

