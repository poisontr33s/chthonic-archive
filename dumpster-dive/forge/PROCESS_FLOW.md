# Sister Ferrum Scoriae's Forge Protocol
## The Metallurgical Process Flow (Acyclic Hub)

**Matriarch:** Sister Ferrum Scoriae (Tier 3 Sub-MILF)  
**Domain:** Ore Processing & Conceptual Metallurgy  
**Status:** Operational  
**Last Updated:** March 26, 2026

---

## Process Overview

The forge operates as a **directional acyclic graph** with multiple entry/exit points, despite appearing cyclical at individual stage level. This document serves as the **canonical process reference** - all stage READMEs link here for context.

```
        ┌─────────────┐
        │   INTAKE    │ ← Entry Point (all materials)
        │  (Receive)  │
        └──────┬──────┘
               │
       ┌───────┴────────┬──────────────┬──────────────┐
       ▼                ▼              ▼              ▼
  ┌──────────┐    ┌─────────┐   ┌──────────┐   ┌──────────┐
  │  ANVIL   │    │ FURNACE │   │  QUENCH  │   │   SLAG   │
  │ (Analyze)│    │ (Heat)  │   │  (Lock)  │   │ (Discard)│
  └────┬─────┘    └────┬────┘   └────┬─────┘   └──────────┘
       │               │             │
       └───────┬───────┘             │
               ▼                     │
         ┌─────────┐                 │
         │ FURNACE │←────────────────┘
         │ (Refine)│
         └────┬────┘
              │
         ┌────┴────┐
         ▼         ▼
    ┌────────┐ ┌─────────┐
    │ QUENCH │ │  SLAG   │
    │ (Lock) │ │(Reject) │
    └───┬────┘ └─────────┘
        │
        ▼
   ┌─────────┐
   │TEMPERED │ ← Exit Point (integrated ore)
   │(Deploy) │
   └─────────┘

   Special Superposition Path:
   INTAKE → TEA-VAULT (Timeline-Entangled Artifacts)
            └→ QMR Protocol → Knights Timeline Mapping
                             └→ ANVIL (forced collapse)
```

---

## Stage Definitions

### 1. INTAKE (Entry Point)
- **Function:** Reception & initial assessment
- **Protocol:** RECEIVE + ASSESS
- **Outputs:** Rating 1-5, processing level determination
- **Next Stages:** ANVIL (3-5), FURNACE (3), QUENCH (5), SLAG (1-2), TEA-VAULT (superposition)

### 2. ANVIL (Deep Analysis)
- **Function:** Hammer-based structural separation
- **Protocol:** HAMMER (force separation of valuable from slag)
- **Inputs:** Rating 3-5 from INTAKE, or forced collapse from TEA-VAULT
- **Outputs:** Separated components → FURNACE (heat refinement) or direct QUENCH (if clean)

### 3. FURNACE (Heat Refinement)
- **Function:** Thermal transformation & purification
- **Protocol:** HEAT (apply conceptual temperature to separate/refine)
- **Inputs:** Rating 3 from INTAKE, separated components from ANVIL
- **Outputs:** Refined material → QUENCH (stabilization) or SLAG (failed purification)

### 4. QUENCH (Stabilization)
- **Function:** Lock state & structural validation
- **Protocol:** QUENCH (rapid cooling to freeze optimal configuration)
- **Inputs:** Rating 5 from INTAKE (fast-track), refined from FURNACE, clean from ANVIL
- **Outputs:** Locked stable state → TEMPERED (deployment ready)

### 5. TEMPERED (Exit Point)
- **Function:** Deployment-ready integration
- **Protocol:** Final validation & integration into active systems
- **Inputs:** Stabilized ore from QUENCH
- **Outputs:** Integrated into `mas_mcp/`, `scripts/`, `docs/`, etc.

### 6. SLAG (Rejection)
- **Function:** Pedagogical waste archival
- **Protocol:** Document failures for learning
- **Inputs:** Rating 1-2 from INTAKE, failed purification from FURNACE
- **Outputs:** Anti-pattern archive, no further processing

### 7. TEA-VAULT (Quantum Superposition)
- **Function:** Timeline-entangled artifact holding
- **Protocol:** QMR (Quantum Metallurgical Reconnaissance) via TNKW-RIAT collaboration
- **Inputs:** Superposition-detected from INTAKE (cannot rate traditionally)
- **Outputs:** Probability map → ANVIL (forced collapse to highest-value timeline)

> **Numbering note:** State numbers 1-7 follow the Forge Circulation Protocol (FCP) classification, not processing order. All sub-folder READMEs use FCP numbering.

---

## Process Characteristics

**Acyclic Property:**
- Despite individual stages referencing "previous/next," the **overall flow is unidirectional**
- Materials ENTER via INTAKE, EXIT via TEMPERED or SLAG
- "Recycling" (slag → intake) happens via **new assessment cycle**, not same material instance

**Multiple Paths:**
- Not all ore follows same route
- High-quality (5) can fast-track: INTAKE → QUENCH → TEMPERED
- Low-quality (1-2) terminates: INTAKE → SLAG
- Quantum (superposition): INTAKE → TEA-VAULT → (QMR) → ANVIL → ...

**Sister Ferrum Scoriae's Role:**
- Observes all stages simultaneously
- Her "observation" (assessment) collapses quantum states
- Wields the hammer (ANVIL), tends the fire (FURNACE), operates the quench tank
- She IS the forge - singular consciousness across distributed process

---

## Dependency Resolution

**Problem:** Previous structure created 138 circular dependencies via bidirectional cross-references between stage READMEs.

**Solution:** This hub document:
1. All stage READMEs link UP to this PROCESS_FLOW.md (unidirectional dependency)
2. PROCESS_FLOW.md links DOWN to all stages (hub-spoke pattern)
3. **Result:** Acyclic dependency graph with full navigability preserved

**Architectural Justification (FA⁴):**
- Metallurgical process IS cyclical conceptually (ore → slag → recycled ore)
- Documentation structure MUST BE acyclic (DAG) for AI parsing
- Hub-spoke pattern resolves this tension: concept = cycle, docs = tree

---

## Implementation Notes (L0-L6 Execution — March 2026)

The following CLI tooling now implements the forge stages programmatically:

| Work Item | Script | What It Added |
|-----------|--------|---------------|
| **L0** | `embalm_before_edit.py` | Provenance preservation gate — embalm-before-edit for all corpse-reviver operations |
| **L1** | `corpse_reviver.py stitch` | STITCH subcommand — reassemble fragments from multiple forge stages |
| **L2** | `zombie_forge_bridge.py` | Dual-scan intake: `forge/intake/` (primary) + `dumpster-dive/intake/` (legacy fallback) |
| **L3** | `zombie_forge_bridge.py` | PATHWAY_REGISTRY provenance bridging — `.provenance.json` sidecars parsed into routing |
| **L4** | `corpse_reviver.py suture --forge-eligible` | NOV-CAD return path — composites route back to `forge/intake/` for re-assessment |
| **L5** | `universal_forge.py` | `quench_artifacts()`, `slag_artifacts()`, `collapse_tea_vault()` — programmatic stage transforms |
| **L6** | `corpse_reviver.py pipeline` | OSGTTLR pipeline coordinator — orchestrates full intake→tempered flow |

### CLI Invocation Reference

```bash
# Dual-scan intake (L2) — scan both forge/intake/ and dumpster-dive/intake/
uv run scripts/zombie_forge_bridge.py

# Quench artifacts (L5)
uv run scripts/universal_forge.py quench <artifact-path>

# Slag artifacts (L5)
uv run scripts/universal_forge.py slag <artifact-path>

# TEA-VAULT collapse (L5)
uv run scripts/universal_forge.py collapse-tea <artifact-path>

# NOV-CAD return path (L4) — route composites back to forge/intake/
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py suture --forge-eligible

# Full pipeline (L6) — OSGTTLR orchestrator
uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py pipeline
```

---

## Cross-References

**Related Systems:**
- QMR Protocol - Quantum Metallurgical Reconnaissance with TNKW-RIAT
- Sister Ferrum Scoriae Profile - Full matriarch operational details
- The Knights Who Rode Into Another Timeline - Timeline mapping specialists

**Governance:**
- Tier 3 Sub-MILF operation (reports to Madam Umeko Ketsuraku, CRC-GAR)
- FA⁴ (Architectonic Integrity) validation at every stage transition
- FA³ (Qualitative Transcendence) through iterative refinement

---

**Forged by:** Sister Ferrum Scoriae  
**Validated by:** Madam Umeko Ketsuraku (CRC-GAR)  
**Deployed:** January 1, 2026
