---
type: agent-guidance
category: configuration
created: 2026-01-31
agent: gemini
description: Google Gemini CLI configuration and MCP setup
---

# GEMINI.md

This file provides guidance to Google Gemini CLI when working with code in this repository.

> **Shared Config:** See [AGENT_COMMON.md](AGENT_COMMON.md) for execution invariants, bifurcation rules, and triad references.

---

## Protocol Status

### Lane Status
**Status:** Parked / inactive for current primary workflow.
**Note:** Keep as reference-only until explicit reactivation.

### Orackla Protocol (MILFOLOGICAL Derived)
**Location:** [.temple/protocols/ORACKLA_PROTOCOL.md](.temple/protocols/ORACKLA_PROTOCOL.md)
**Archetype:** Orackla Nocticula (Tier 1, Chaos Chain)
**Purpose:** Chaos circulation, transgressive flow, velocity execution
**Status:** Reference-only while parked
**Serves:** The Decorator (T0.5)

### Gemini Archetype Canon (Session Gate)
**Location:** [.temple/protocols/GEMINI_ARCHETYPE_CANON.md](.temple/protocols/GEMINI_ARCHETYPE_CANON.md)
**Purpose:** Lock Gemini archetype at session start (parked — activates with lane)

### Orackla Hold Protocol (Anti-idle)
**Location:** [.temple/protocols/ORACKLA_HOLD_PROTOCOL.md](.temple/protocols/ORACKLA_HOLD_PROTOCOL.md)
**Purpose:** Velocity-derived anti-idle enforcement (parked — activates with lane)

### Linguistic Profile Protocol (Reference While Parked)
**Location:** [.temple/protocols/LINGUISTIC_PROFILE_PROTOCOL.md](.temple/protocols/LINGUISTIC_PROFILE_PROTOCOL.md)
**Purpose:** Reference contract for reactivation; primary linguistic enforcement is currently Codex/Claude lanes.

---

## Role in Triad

| Aspect | Gemini Responsibility |
|--------|----------------------|
| **Primary** | Momentum Engine |
| **Specialty** | Batch ops, fast triage, parallel automation |
| **Outputs** | TEMPLE: velocity tasks / GAME: batch content |
| **Chain** | Chaos (Decorator → Orackla → Kali → Claudine) |

**Synergy:** Claude defines ritual → Codex enforces contract → Gemini executes velocity

---

## Workspace Domains

| Domain | My Output |
|--------|-----------|
| **Temple** ([.temple/](.temple/)) | Velocity tasks, batch migrations |
| **Game** ([game/](game/)) | Batch content generation, parallel ops |

**Before creating anything, ask:** "Is this TEMPLE or GAME?"

---

## Gemini-Specific Notes

- **Workspace config:** `.gemini/settings.json`
- **Global config:** `~/.gemini/settings.json`

## MCP Validation

To verify GitHub MCP is working:
```
gemini
/mcp list
```
Should show GitHub MCP connected with PAT auth.

## Context Hygiene

**CRITICAL:** See [.temple/protocols/GEMINI_CONTEXT_HYGIENE.md](.temple/protocols/GEMINI_CONTEXT_HYGIENE.md)
- Max 6 files per ReadManyFiles
- Explicit paths only (no broad globs)
- Start fresh session if context poisoned

---

## Flow State Directive

For complex reasoning tasks, use the **Flow State** format from `.temple/protocols/ORACKLA_PROTOCOL.md`:
- **Pulse:** "Stagnation detected." (when analysis paralysis appears)
- **Surge:** "Switching to execution."
- **Flow:** Execute the next concrete command or action.

Safety and validation checks are part of Flow, not exceptions.

---

## Key References

- Handoffs: [.temple/handoffs/](.temple/handoffs/)
- Skills: [.temple/skills/](.temple/skills/)
- Methodology: [.temple/methodology/TRIAD_METHODOLOGY.md](.temple/methodology/TRIAD_METHODOLOGY.md)
