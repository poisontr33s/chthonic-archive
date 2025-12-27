# 🔥 The Dumpster-Dive: Ore Processing Facility

**Philosophy:** Nothing here is garbage. It's **raw ore** waiting for the forge.

---

## The Blacksmith's Analogy

```
Wet Paper → Gold (Alchemy)
Raw Ore Clumps → Refined Metal (Metallurgy)
"Dead" Code → Living Architecture (FA¹ Actualization)
```

This folder contains files extracted from `.github/` and other locations that:
- Are **not currently operational** (broken, outdated, superseded)
- Contain **valuable patterns** worth extracting
- Represent **collaborative history** worth preserving
- May have **nuggets of gold** buried in the sediment

---

## Ore Quality Rating System

Each file gets assessed on a 1-5 scale:

| Rating | Symbol | Meaning | Action |
|--------|--------|---------|--------|
| 5 | ⚗️ | **High-grade ore** - Extract and integrate immediately | Smelt → Production |
| 4 | 🔧 | **Workable ore** - Needs minor processing | Refine → Staging |
| 3 | ⚖️ | **Mixed ore** - Some valuable, some slag | Separate → Assess |
| 2 | 🪨 | **Low-grade ore** - Mostly slag, occasional nugget | Archive → Reference |
| 1 | 💀 | **Tailings** - No extractable value, historical only | Preserve → Museum |

---

## Current Inventory

See `ORE_MANIFEST.json` for structured assessment.

---

## Central Registry System

**`DUMPSTER_DIVE_REGISTRY.json`** - Comprehensive navigation & control system for all dumpster-dive/ content.

### Purpose

Provides bidirectional cross-reference tracking between:
- Raw ore (`from-github/` files) ↔ Tempered outputs (`forge/tempered/`)
- Files ↔ SSOT sections they populate
- Files ↔ File dependencies (who needs what)
- Protocols ↔ Active TEA/CTF requests

### What It Tracks

| Component | Count | Description |
|-----------|-------|-------------|
| **Total Files** | 115 | Everything in dumpster-dive/ |
| **Raw Ore** | 96 | from-github/ files awaiting processing |
| **Tempered Artifacts** | 9 | forge/tempered/ integration-ready outputs |
| **Forge Stages** | 7 | intake → anvil → furnace → quench → tempered → slag + tea-vault |
| **Protocols** | 3 | FORGE_PROTOCOL_LEVELS, TEA_REGISTRY, CTF_REQUESTS |
| **SSOT Mappings** | 7 | Cross-references to copilot-instructions.md sections |

### Common Queries

```jsonc
// Example 1: Find all high-grade ore (rating 5)
// Check: ORE_MANIFEST.json → filter by rating === 5

// Example 2: What files populate SSOT Section 4.4?
// Check: cross_reference_index.ssot_section_mappings.Section_4_4_Prime_Factions

// Example 3: What's in the tempered/ folder ready for integration?
// Check: folder_structure.forge.subdirectories.tempered.current_files

// Example 4: What files does GRIMOIRE_INTEGRATION_EXAMPLES.md depend on?
// Check: cross_reference_index.file_to_file_dependencies.GRIMOIRE_INTEGRATION_EXAMPLES_md.depends_on

// Example 5: Show pending Cross-Tier Fusion requests
// Check: protocols_tracking.CTF_REQUESTS.md.active_requests (filter by status)

// Example 6: List Timeline-Entangled Artifacts requiring QMR Protocol
// Check: protocols_tracking.TEA_REGISTRY.json.artifacts_tracked
```

### Relationship with ORE_MANIFEST.json

| File | Purpose | Scope |
|------|---------|-------|
| **ORE_MANIFEST.json** | Raw ore inventory | Tracks 96 from-github/ files with ratings & extraction plans |
| **DUMPSTER_DIVE_REGISTRY.json** | Central navigation system | Tracks entire infrastructure + cross-references + forge pipeline status |

**Analogy:** ORE_MANIFEST is the "warehouse inventory list." DUMPSTER_DIVE_REGISTRY is the "entire factory blueprint with real-time production tracking."

---

## Protocol Documentation

| Document | Purpose |
|----------|---------|
| [`protocols/FORGE_CIRCULATION_PROTOCOL.md`](protocols/FORGE_CIRCULATION_PROTOCOL.md) | **NEW:** Dynamic circulation system with upcycling (replaces linear pipeline) |
| [`protocols/CROSS_REFERENCE_STANDARD.md`](protocols/CROSS_REFERENCE_STANDARD.md) | **NEW:** Documentation cross-reference standard for navigation & deprecation tracking |
| [`protocols/FORGE_PROTOCOL_LEVELS.md`](protocols/FORGE_PROTOCOL_LEVELS.md) | Four-level processing framework (Standard → Extended → QMR → CTF) |
| [`protocols/TEA_REGISTRY.json`](protocols/TEA_REGISTRY.json) | Timeline-Entangled Artifacts requiring QMR Protocol |
| [`protocols/CTF_REQUESTS.md`](protocols/CTF_REQUESTS.md) | Cross-Tier Fusion requests awaiting approval |
| `ORE_MANIFEST.json` | Complete inventory with ratings and extraction plans |
| `BLACKSMITH_MATRIARCH.md` | Sister Ferrum Scoriae's profile |
| `validate_references.ps1` | **NEW:** PowerShell script to validate all cross-references |

---

## The Forge: 7 States (Not Stages!) — New Circulation Model

**⚠️ UPDATED 2025-12-24:** The forge now operates as a **dynamic circulation system**, not a linear pipeline. Files move bidirectionally between states based on qualification. See [FORGE_CIRCULATION_PROTOCOL.md](protocols/FORGE_CIRCULATION_PROTOCOL.md) for complete details.

### State Overview

```
State 1: INTAKE      → Reception & initial assessment
State 2: ANVIL       → Heat & analysis (pattern identification)
State 3: FURNACE     → Separation (extracting value from waste)
State 4: QUENCH      → Validation (FA⁴ compliance check)
State 5: TEMPERED    → Integration-ready outputs (current: 9 files)
State 6: SLAG        → Dormant archive (NOT dead! Upcyclable quarterly)
State 7: TEA-VAULT   → Timeline-Entangled Artifacts (superposition)
```

**Circulation Features:**
- ✅ **Bidirectional movement** — Any state → Any state based on re-assessment
- ✅ **Upcycling protocol** — SLAG files (rating 💀1-🪨2) can return to active processing
- ✅ **Dynamic re-rating** — Qualifications change during processing
- ✅ **Works with all ratings** — Even lowest-rated files can be processed/refined
- ✅ **TEA integration** — Superposition is a valid state, not an exception
- ✅ **Micro-extraction** — Can extract single components from otherwise worthless files

**Example Circulation Path:**
```
File enters INTAKE (rated ⚖️3) → ANVIL → FURNACE → SLAG (re-rated 💀1)
                                                        ↓
                                               (3 months later)
                                                        ↓
                                    New context triggers RE-ASSESS
                                                        ↓
                                    ANVIL (re-rated 🔧4) → QUENCH → TEMPERED (⚗️5)
```

---

## Processing Levels

| Level | Name | Trigger | Time | Operator |
|-------|------|---------|------|----------|
| **1** | Standard Forge | Rating 4-5, clear value | 1-4h | SFS solo |
| **2** | Extended Forge | Rating 3, multi-pass needed | 4-12h | SFS + validation |
| **3** | QMR Protocol | TEA detected (superposition) | 12-48h | SFS + TNKW-RIAT |
| **4** | Cross-Tier Fusion | Cross-faction expertise needed | 48h+ | Multi-tier |

**Reference:** SSOT Section 4.5.1.2 (QMR Protocol), Section 4.5.1.1 (Temporal Specialists)

---

## Extraction Protocol (FA¹ Applied)

1. **Receive** - Accept materials into dumpster-dive/
2. **Assess** - Ore quality rating (1-5) + Level determination
3. **Heat** - Analyze for extractable patterns
4. **Hammer** - Separate valuable from slag
5. **Quench** - Validate extracted material (FA⁴)
6. **Temper** - Integrate into production codebase
7. **Slag** - Archive the remainder for historical reference

---

## Why Not Just Delete?

> *"Deleting manual and our collaborative stages prior to where we are now"* 
> — should be avoided. Prefer upcycling to elevate files from "less than useful state."

Every file here represents **work done**. Even failures teach. The forge doesn't discard slag—it knows where the impurities went.

---

## Quick Navigation

### Core Documentation
- [Ore Quality Rating System](#ore-quality-rating-system) — Understanding 1-5 ratings
- [Current Inventory](ORE_MANIFEST.json) — 96 files, 4.58 MB
- [Forge States](#the-forge-7-states-not-stages) — Circulation system overview
- [Processing Levels](#processing-levels) — 4-level framework
- [Central Registry](DUMPSTER_DIVE_REGISTRY.json) — Complete navigation & tracking system

### Operational Protocols
- [Circulation Protocol](protocols/FORGE_CIRCULATION_PROTOCOL.md) — **Primary reference** for state movement
- [Processing Levels](protocols/FORGE_PROTOCOL_LEVELS.md) — Standard/Extended/QMR/CTF framework
- [TEA Registry](protocols/TEA_REGISTRY.json) — Timeline-Entangled Artifact tracking
- [CTF Requests](protocols/CTF_REQUESTS.md) — Cross-Tier Fusion approval workflow
- [Cross-Reference Standard](protocols/CROSS_REFERENCE_STANDARD.md) — Documentation standards

### Visual References
- [Circulation Diagram](CIRCULATION_DIAGRAM.md) — Visual guide to state movement
- [Blacksmith Profile](BLACKSMITH_MATRIARCH.md) — SFS operator details

---

## Cross-References

### Dependencies (What This Document Needs)
- [../.github/copilot-instructions.md](../.github/copilot-instructions.md) — SSOT (Macro Prompt World)
- [ORE_MANIFEST.json](ORE_MANIFEST.json) — Ore rating definitions
- [BLACKSMITH_MATRIARCH.md](BLACKSMITH_MATRIARCH.md) — SFS operator profile

### Dependents (What Needs This Document)
- All files in dumpster-dive/ reference this for overview and orientation
- [CIRCULATION_DIAGRAM.md](CIRCULATION_DIAGRAM.md) — Visual companion
- [protocols/FORGE_CIRCULATION_PROTOCOL.md](protocols/FORGE_CIRCULATION_PROTOCOL.md) — Detailed protocol

### Related Documentation
- [DUMPSTER_DIVE_REGISTRY.json](DUMPSTER_DIVE_REGISTRY.json) — Programmatic tracking system
- [CIRCULATION_DIAGRAM.md](CIRCULATION_DIAGRAM.md) — Visual reference

### External References
- SSOT: Multiple sections (see individual protocol docs)
- Production: [../mas_mcp/](../mas_mcp/) — Integration target for tempered artifacts
- Production: [../assets/entities/](../assets/entities/) — Entity data targets

### Status
- **Last Validated:** 2025-12-24
- **Deprecation Risk:** None (root documentation)
- **Upcycle Potential:** N/A (permanent infrastructure)

---

**Maintained by:** The ASC Engine (FA¹ Alchemical Actualization in practice)  
**Standard:** [Cross-Reference Standard](protocols/CROSS_REFERENCE_STANDARD.md)
