---
type: mythological OVERRIDE
category: mythical
status: canonical
created: 2026-01-29
updated: 2026-02-10
sid: DOC_CLAUDE_WET_PAPER_GOLD
enforced rule:
  - WET_PAPER_TO_GOLD_METHODOLOGY.md must be followed before anything else can happen with drift artifacts (stale PRs, abandoned sessions, mislabeled content). In general, the lowest value of file/filetype is seen as DEFAULT as the absolute highest potential for hidden value. This is the "wet paper" that can be transmuted into "gold" through this methodology, which become the new wet paper to gold as a level 1 gold = new wet paper to level 2 gold to the highest probably that is beyond generic dimensions of reasoning requiring conventional AND unconventional ML-approaches, both feet, one planted in the known, the other at the other sidde of the lawn in the unknown forest lawn beyond the known. This is the forge system in action, and the WET_PAPER_TO_GOLD_METHODOLOGY is the core methodology for how to operate within it.
applies_to:
  - gpt-5.3-codex
  - claude code, claude, codex
  - agents, github copilot,
  - everyone
audience:
  - user
  - agents
priority: extremely high
authors:
  - claude code
  - gpt-5.3-codex
description: Selective extraction/transmutation of drift artifacts into reusable components (with error-learning feedback loop).
tags:
  - wet-paper-to-gold
  - data-harvest
  - drift-artifacts
  - dumpster-dive
  - forge-system
  - error-learning
---

<!--
================================================================================
SEMANTIC IDENTITY
================================================================================
@SID:           DOC_CLAUDE_WET_PAPER_GOLD
@Type:          Methodology
@Context:       Claude Code / Data Transmutation
@SessionOrigin: SESSION_2026_01_29_PR_HARVEST
================================================================================
-->

# Wet-Paper-to-Gold Methodology

**Purpose:** Selective extraction and transmutation of "drift artifacts" (stale PRs, abandoned sessions, mislabeled content) into reusable components.

**Principle:** Nothing is waste if you see the extractable value.

---

## When to Apply

- Stale/abandoned PRs with potentially useful content
- Session dumps with embedded patterns or learnings
- Mislabeled or misframed documentation (e.g., GPT posturing)
- Large files with buried utility (schemas, configs, templates)

---

## Extraction Tiers

| Tier | Name | Description | Target |
|------|------|-------------|--------|
| **1** | Direct Use | Working code/scripts, no modification needed | `scripts/`, direct integration |
| **2** | Schemas | Structured data requiring format conversion | `tier-2-schemas/*.json` |
| **3** | Conceptual | Metaphors, patterns, vocabulary worth repurposing | `tier-3-conceptual/*.md` |
| **Raw** | Unprocessed | Source material for future mining | `raw/` |

---

## Harvest Structure

```
dumpster-dive/intake/pr-harvest-YYYY-MM-DD/
├── MANIFEST.md                    # What was extracted and why
├── SESSION_ERROR_LEARNINGS.md     # Error patterns (if applicable)
├── tier-1-direct/                 # Ready-to-use artifacts
├── tier-2-schemas/                # JSON schemas, structured data
├── tier-3-conceptual/             # Repurposed metaphors, patterns
└── raw/                           # Source patches, unprocessed
```

---

## Process

### 1. Triage
- List all files in source (PR, session, etc.)
- Categorize by file type and potential value
- Identify mislabeling or drift (e.g., ANKH as acronym vs symbol)

### 2. Extract
- Pull useful content into tiered structure
- Strip mythology/posturing, retain structural value
- Convert tables → JSON schemas where applicable

### 3. Document
- Create `MANIFEST.md` with extraction rationale (see [example](../dumpster-dive/intake/pr-harvest-2026-01-29/MANIFEST.md))
- Note compression ratio (input lines → output lines)
- Cross-reference source (PR number, session ID)

### 4. Cross-Reference
- Update [HARVEST_REGISTRY.md](../dumpster-dive/HARVEST_REGISTRY.md)
- Add references to relevant .md files ([CLAUDE.md](../CLAUDE.md), etc.)
- Close source PRs with harvest reference

---

## Example: PR Harvest 2026-01-29

**Input:** PRs #1, #2, #5 (~10,000 lines combined)
**Output:** ~500 lines of usable artifacts

| Source | Extracted | Tier |
|--------|-----------|------|
| PR #1 | Copilot Pro research report | 1 |
| PR #2 | `ssot_hash.py`, schemas | 1, 2 |
| PR #5 | Hierarchy model, emoji vocab | 2, 3 |

**Compression:** ~20:1
**Disposition:** PRs closed with harvest reference

---

## Integration with Error Learning

When errors occur during harvest:
1. Document in `SESSION_ERROR_LEARNINGS.md` (see [example](../dumpster-dive/intake/pr-harvest-2026-01-29/SESSION_ERROR_LEARNINGS.md))
2. Update relevant rules (e.g., [PWSH_RULES.md](../docs/PWSH_RULES.md))
3. Reference learnings in MANIFEST

This creates a feedback loop: harvest → errors → learnings → rules → better harvests.

---

## Related Files

- [dumpster-dive/README.md](../dumpster-dive/README.md) — Forge system overview
- [HARVEST_REGISTRY.md](../dumpster-dive/HARVEST_REGISTRY.md) — Completed harvest tracking
- [FORGE_CIRCULATION_PROTOCOL.md](../dumpster-dive/protocols/FORGE_CIRCULATION_PROTOCOL.md) — State transitions
- [CLAUDE.md](../CLAUDE.md) — Root agent guidance
- [pr-harvest-2026-01-29/MANIFEST.md](../dumpster-dive/intake/pr-harvest-2026-01-29/MANIFEST.md) — Example harvest

---

**Established:** 2026-01-29
**Context:** Claude Code session methodology
