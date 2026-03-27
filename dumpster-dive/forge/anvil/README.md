# Forge State 2: ANVIL

**Purpose:** Heat & Analysis — deep structural investigation  
**State Type:** Active investigation  
**Protocol Step:** HEAT + ANALYZE  
**Current Files:** Multiple (forge receipts + analyzed artifacts)

---

## Overview

ANVIL is where **deep analysis** happens. Files rated 3-5 from INTAKE are "heated" to expose structural patterns, dependencies, and extractable components. This is investigation work — understanding what's valuable before separation begins.

---

## Processing Steps

### 1. HEAT (Deep Analysis)
- Apply analytical heat (structural decomposition)
- Identify extractable patterns and reusable code
- Map internal and external dependencies
- Document findings and extraction targets

### 2. ANALYZE (Pattern Mapping)
- Classify valuable components vs. noise
- Identify integration targets in production codebase
- Assess extraction complexity and labor cost
- Route to appropriate next state

---

## Movement Options

From ANVIL, files can move to:
- **→ FURNACE** — Patterns identified, ready for surgical separation
- **→ QUENCH** — Simple extraction, skip separation (clean ore)
- **→ TEA-VAULT** — Superposition detected, multiple valid timelines
- **→ INTAKE** — Needs complete re-scoping
- **→ SLAG** — Analysis reveals no extractable value

---

## Forge Receipts

Files in ANVIL carry `.forge_receipt_*.json` sidecars recording:
- Origin path and timestamp
- Initial ore rating from INTAKE
- Analysis findings and extraction targets
- Routing decision and next-state recommendation

---

## Current Status

**Files in ANVIL:** Multiple (see directory listing)  
**Last Activity:** 2026-03-05  
**Avg. Processing Time:** 3-12 hours

---

## Cross-References

**Process Context:**
- [**../PROCESS_FLOW.md**](../PROCESS_FLOW.md) — Complete forge process overview (acyclic hub)

**Upstream Dependencies:**
- [../../protocols/FORGE_CIRCULATION_PROTOCOL.md](../../protocols/FORGE_CIRCULATION_PROTOCOL.md) — State 2 definition
- [../../ORE_MANIFEST.json](../../ORE_MANIFEST.json) — Ore rating system (3-5 for ANVIL)
- [../../BLACKSMITH_MATRIARCH.md](../../BLACKSMITH_MATRIARCH.md) — SFS analysis standards

**Downstream Targets:**
- [../furnace/](../furnace/) — Surgical extraction
- [../quench/](../quench/) — Direct validation (clean ore)

**Tracking:**
- [../../DUMPSTER_DIVE_REGISTRY.json](../../DUMPSTER_DIVE_REGISTRY.json) — Files in this state

**Status:**
- **Last Validated:** 2026-03-26
- **Deprecation Risk:** None (critical analysis stage)
- **Circular Refs:** Resolved via PROCESS_FLOW.md hub pattern

---

**Operator:** Sister Ferrum Scoriae (SFS)  
**Model:** [Circulation Protocol](../../protocols/FORGE_CIRCULATION_PROTOCOL.md)

