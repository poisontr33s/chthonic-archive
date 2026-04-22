<!--
================================================================================
SEMANTIC IDENTITY (Anchor & Signal Protocol)
================================================================================
@SID:           DOC_DOCS_README
@Type:          Documentation
@Context:       Project Knowledge Base
@UpdateFrequency: Low (Structural Changes Only)
@SessionOrigin: SESSION_DOC_2026_01_17_CLEANUP
@LastReorg:     2026-04-22
================================================================================
-->

# Directory: docs/

## Purpose
The central repository for project documentation, operational protocols, session records, and state artifacts. This directory serves as the **Memory Bank** of the Chthonic Archive.

## Directory Structure

```
docs/
  archive/
    reports/       Stale validation/audit reports and one-time summaries
    sessions/      Session state snapshots from past work epochs
  architecture/    System design and structural blueprints
  design/          Visual design contracts: icons, themes, SFS slabstone
  frameworks/      Autonomous orchestration and Ankh framework docs
  handoffs/        Cross-agent handoff documents
  lore/            World/character lore reference
  ops/             Operational policy: MCP, API pool, mailbox, CLI policy
  protocols/       SSOT rules, cross-reference doctrine, anchor protocol
  reference/       Static reference: toolchain, oxidized stack, curriculum
  standards/       Canonical specs: KCP, LAT, script metadata, anti-patterns
  zombie/          Zombie subsystem docs (convergence plan, upgrade log)
```

## Canonical Locations

| Category | Path |
|----------|------|
| Architecture | `docs/architecture/` |
| Design contracts | `docs/design/` |
| Frameworks (Ankh, orchestration) | `docs/frameworks/` |
| Ops policy (MCP, API, mailbox) | `docs/ops/` |
| Protocols (SSOT, cross-ref) | `docs/protocols/` |
| Reference (oxidized stack, toolchain) | `docs/reference/` |
| Standards (KCP, LAT, script meta) | `docs/standards/` |
| Lore | `docs/lore/` |
| Stale/archived | `docs/archive/` |

## Root-Level Policy Files (canonical locations NOT here)
- PowerShell rules → [`PWSH_RULES.md`](../PWSH_RULES.md) (repo root)
- Scripts guide → [`SCRIPTS_README.md`](../SCRIPTS_README.md) (repo root)
- WPtG methodology → [`WET_PAPER_TO_GOLD_METHODOLOGY.md`](../WET_PAPER_TO_GOLD_METHODOLOGY.md) (repo root)

## Ownership
- **Maintenance:** Human + Agent collaborative updates
- **Archive policy:** Reports >30 days old with no active reference → `docs/archive/reports/`
- **Session policy:** Completed epoch session docs → `docs/archive/sessions/`
