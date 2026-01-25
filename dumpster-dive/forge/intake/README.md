# Forge State 1: INTAKE

**Purpose:** Reception & initial assessment  
**State Type:** Entry point  
**Protocol Step:** RECEIVE + ASSESS  
**Current Files:** 0

---

## Overview

INTAKE is the **entry point** for all materials entering the dumpster-dive forge. Files arrive here from:
- `.github/` archives
- External sources
- User uploads
- Other project locations

---

## Processing Steps

### 1. RECEIVE
- Accept file into `forge/intake/`
- Record origin and timestamp
- Create initial metadata

### 2. ASSESS
- Apply ore quality rating (1-5)
- Determine processing level (Standard/Extended/QMR/CTF)
- Identify initial extraction targets
- Route to appropriate next state

---

## Movement Options

From INTAKE, files can move to:
- **→ ANVIL** — Rating 3-5, requires deep analysis
- **→ FURNACE** — Rating 3, clear separation path identified
- **→ QUENCH** — Rating 5, simple extraction (fast-track)
- **→ SLAG** — Rating 1-2, minimal immediate value
- **→ TEA-VAULT** — Superposition detected, cannot rate

---

## Current Status

**Files in INTAKE:** 0  
**Last Activity:** N/A  
**Avg. Processing Time:** < 1 hour (assessment only)

---

## Cross-References

**Process Context:**
- [**../PROCESS_FLOW.md**](../PROCESS_FLOW.md) — Complete forge process overview (read this for full context)

**Upstream Dependencies:**
- [../../ORE_MANIFEST.json](../../ORE_MANIFEST.json) — Ore rating system (1-5)
- [../../protocols/FORGE_CIRCULATION_PROTOCOL.md](../../protocols/FORGE_CIRCULATION_PROTOCOL.md) — State definitions
- [../../../.github/](../../../.github/) — Primary source of incoming materials

**Tracking:**
- [../../DUMPSTER_DIVE_REGISTRY.json](../../DUMPSTER_DIVE_REGISTRY.json) — Files entering this state

**Status:**
- **Last Validated:** 2026-01-01
- **Deprecation Risk:** None (permanent entry point)
- **Circular Refs:** Resolved via PROCESS_FLOW.md hub pattern

---

**Operator:** Sister Ferrum Scoriae (SFS)  
**Model:** [Circulation Protocol](../../protocols/FORGE_CIRCULATION_PROTOCOL.md)
