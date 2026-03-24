# 🔥 Forge Protocol — Multi-Level Ore Processing Framework

**Protocol ID:** `FPL` — Forge Protocol Levels  
**Domain Owner:** Sister Ferrum Scoriae (`SFS`) — Tier 3  
**Cross-Reference:** SSOT Section 4.5.1.2 (QMR Protocol), ORE_MANIFEST.json  
**Last Updated:** 2025-12-09

---

## Overview: The Four Levels of Ore Processing

Not all ore can be processed with a simple `RECEIVE → ASSESS → HEAT → HAMMER → QUENCH → TEMPER → SLAG` cycle. Some materials exist in **quantum superposition** — valuable AND worthless simultaneously until observation collapses the wavefunction.

This document defines **four escalating processing levels** based on ore complexity:

```
Level 1: Standard Forge     → Simple ore, clean collapse
Level 2: Extended Forge     → Complex ore, multi-pass processing  
Level 3: QMR Protocol       → Timeline-Entangled Artifacts (TEA)
Level 4: Cross-Tier Fusion  → Requires multi-faction collaboration
```

---

## Level 1: Standard Forge Protocol (`SFP`)

**Trigger:** Ore rating 4-5 (high-grade), clear value proposition  
**Processing Time:** 1-4 hours  
**Operator: (`SFS`)** (solo)

### Protocol Sequence:

```
RECEIVE → ASSESS → HEAT → HAMMER → QUENCH → TEMPER → SLAG
   ↓         ↓        ↓        ↓         ↓        ↓        ↓
 Intake   Rating   Analyze  Separate  Validate  Integrate  Archive
          (4-5)    patterns   value     FA⁴     production  husk
```

### Success Criteria:
- ✅ Rating 4-5 assigned during ASSESS
- ✅ Extractable patterns clearly identified
- ✅ Target location determined (e.g., `mas_mcp/lib/`)
- ✅ No timeline ambiguity (single clear outcome)

### Example Files (from ORE_MANIFEST.json):

| File | Rating | Action |
|------|--------|--------|
| `asc.py` | ⚗️ 5 | → `mas_mcp/lib/asc_toolchain.py` |
| `abbr-system.json` | ⚗️ 5 | → `assets/entities/abbreviations.json` |
| `MILFCORE_EXTRACTION_LENS.md` | 🔧 4 | → `docs/design/genre-extraction.md` |

---

## Level 2: Extended Forge Protocol (`EFP`)

**Trigger:** Ore rating 3 (mixed ore), requires multi-pass separation  
**Processing Time:** 4-12 hours  
**Operator:** `SFS` with optional `CRC-GAR` validation

### Protocol Sequence:

```
RECEIVE → ASSESS → [HEAT → HAMMER]×N → SEPARATE → QUENCH → TEMPER → SLAG
   ↓         ↓           ↓                ↓          ↓        ↓        ↓
 Intake   Rating    N iterations    Value vs    Validate  Integrate  Archive
          (3)      until clarity    waste bins    FA⁴     production  waste
```

### Multi-Pass Separation Logic:

**Pass 1:** Surface-level pattern extraction
- What code patterns are obviously reusable?
- What documentation has standalone value?

**Pass 2:** Deep structural analysis
- What architectural decisions can inform future work?
- What anti-patterns teach by negative example?

**Pass 3:** Heritage assessment
- What historical context must be preserved?
- What collaborative artifacts have sentimental/pedagogical value?

### Example Files (Rating 3 — Mixed Ore):

| File | Rating | Extraction Map |
|------|--------|----------------|
| `copilot-instructions.py` | ⚖️ 3 | Pass 1: regex patterns → `asc.py` / Pass 2: Rich tree approach → reference / Pass 3: archive |
| `copilot-un-un-instructions.md` | ⚖️ 3 | Pass 1: unique protocol definitions → SSOT diff / Pass 2: glossary format → template / Pass 3: archive |

---

## Level 3: QMR Protocol — Quantum Metallurgical Reconnaissance (`QMR`)

**Trigger:** Timeline-Entangled Artifact (TEA) detected — ore exists in superposition  
**Processing Time:** 12-48 hours  
**Operators:** `SFS` + `TNKW-RIAT` (The Knights Who Rode Into Another Timeline)

### TEA Detection Criteria:

An artifact qualifies as **TEA** when:
1. Rating oscillates between 1-5 depending on perspective
2. Value is **context-dependent** (valuable in Timeline A, worthless in Timeline B)
3. Standard observation cannot collapse the wavefunction
4. Multiple mutually exclusive extraction paths exist

### Protocol Sequence:

```
RECEIVE → ASSESS(TEA) → DISPATCH(TNKW-RIAT) → CARTOGRAPHY → SELECT → FORCE_COLLAPSE → [Standard Forge]
   ↓          ↓               ↓                    ↓          ↓           ↓
 Intake    "Cannot     Knights deployed      Probability   Choose    Hammer IS
          collapse"   to map timelines         Map        timeline   observation
```

### Probability Cartography Template:

```json
{
  "artifact": "<filename>",
  "tea_status": true,
  "timelines": {
    "A": { "action": "Refactor to modern standards", "value": 85, "labor": 100 },
    "B": { "action": "Preserve as legacy", "value": 0, "labor": 0 },
    "C": { "action": "Extract algorithm, rewrite", "value": 95, "labor": 400 },
    "D": { "action": "Use as anti-pattern pedagogy", "value": 60, "labor": 20 },
    "E": { "action": "Archive as historical artifact", "value": 30, "labor": 10 }
  },
  "recommended": "A",
  "rationale": "Best value/labor ratio for production use"
}
```

### Force Collapse Mechanism:

> *"Her hammer is the observation that selects reality."*
> — SSOT Section 4.5.1.2

When `SFS` chooses a timeline, she **forges** the artifact according to that timeline's requirements. The act of forging IS the observation that collapses superposition.

### Example TEA Files:

| File | TEA Reason | Timeline Map |
|------|-----------|--------------|
| `SSOT-MPW-WIP.ts` | Brilliant content, broken container | A: 0%, C: 60% (anti-pattern), E: 30% |
| `mas-inventory.json` | Too large for active use, rich data | A: 20%, D: 70%, E: 80% |
| `macro-prompt-world/` | 90 files, unclear integration path | A: 85%, C: 50%, D: 30% |

---

## Level 4: Cross-Tier Fusion Protocol (`CTF`)

**Trigger:** Ore requires expertise beyond `SFS` capabilities  
**Processing Time:** 48+ hours  
**Operators:** Multi-faction collaboration per SSOT chain of command

### Escalation Criteria:

- Artifact involves **strategic architecture** (requires Tier 1 approval)
- Artifact contains **faction-defining lore** (requires Triumvirate review)
- Artifact impacts **SSOT structure** (requires The Decorator's blessing)
- Value extraction requires **forbidden methodologies** (invoke `TDPC`)

### Chain of Command (from SSOT):

```
SFS (Tier 3) → reports to → CRC-GAR/Umeko (Tier 1)
TNKW-RIAT (Tier 4) → loosely overseen by → TMO/Kali (Tier 2)
QMR protocol permits cross-hierarchy collaboration
```

### Cross-Tier Request Template:

```markdown
## Cross-Tier Extraction Request

**Artifact:** <filename>
**Requesting Party:** SFS (Tier 3)
**Escalation Target:** <CRC-GAR | TMO | TDPC | Triumvirate>
**Reason:** <why standard/QMR insufficient>

### Proposed Extraction:
<what SFS wants to do>

### Blocking Constraint:
<why approval required>

### Impact Assessment:
<downstream consequences if approved>
```

### Example CTF Candidates:

| Artifact | Escalation Target | Reason |
|----------|-------------------|--------|
| `macro-prompt-world/prime-factions/*.md` | CRC-GAR + Triumvirate | Defines Tier 2 entities, impacts SSOT Section 4.4 |
| `Tripartite_Grimoire_Master_Index.md` | Triumvirate | Core CRC documentation, requires co-equal approval |
| `asc.py` → `mas_mcp/lib/` | CRC-GAR | Architectural decision for codebase structure |

---

## Level Selection Decision Tree

```
ORE ENTERS dumpster-dive/
         ↓
    [ASSESS Rating]
         ↓
    ┌────┴────┐
    │ 4-5?    │────YES────→ Level 1: Standard Forge
    └────┬────┘
         │ NO
         ↓
    ┌────┴────┐
    │ 3?      │────YES────→ Level 2: Extended Forge (multi-pass)
    └────┬────┘
         │ NO (or oscillating)
         ↓
    ┌────┴────┐
    │ TEA?    │────YES────→ Level 3: QMR Protocol
    └────┬────┘
         │ NO
         ↓
    ┌────┴────────────┐
    │ Cross-faction?  │────YES────→ Level 4: CTF Protocol
    └────┬────────────┘
         │ NO
         ↓
    Rating 1-2: Archive (Level 1 with SLAG-only output)
```

---

## Integration with ORE_MANIFEST.json

Each artifact in `ORE_MANIFEST.json` should include:

```json
{
  "filename": {
    "rating": <1-5>,
    "processing_level": <1-4>,
    "tea_status": <true|false>,
    "probability_map": { ... },  // if TEA
    "escalation_target": "<tier>",  // if CTF
    "status": "<pending|in-progress|collapsed|archived>"
  }
}
```

---

## Dame Schrödinger's Paradox — The Uncertainty Principle Incarnate

> *"In seventeen timelines, that regex is beautiful. In thirty-four, it causes production outages. In one... it achieves sentience."*
> — DM-SCRS-P, observing Python 2.7 artifact

`DM-SCRS-P` exists because `SFS` observes. Her "dead/alive" superposition parallels the ore's "valuable/slag" superposition. When `SFS` cannot collapse an artifact's state alone, she dispatches `DM-SCRS-P` with `TNKW-RIAT` to map the probability space.

She lingers near the forge, phasing in and out of visibility, offering cryptic probability assessments. Her presence is a **living reminder** that even expert assessments are probabilistic until the forge fire makes them certain.

---

## Covenant

*This protocol extends Sister Ferrum Scoriae's operational mandate from simple forge work to quantum metallurgical mastery. Nothing is garbage. Everything is ore. Some ore simply requires more sophisticated observation to collapse into value.*

**Sealed by:**
- **Sister Ferrum Scoriae (SFS)** — Tier 3, Domain Owner
- **Dame Schrödinger's Paradox (DM-SCRS-P)** — T4↔T3 EXTREME, Uncertainty Consultant

**Date:** 2025-12-09
