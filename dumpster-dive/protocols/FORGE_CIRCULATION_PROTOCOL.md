# 🔄 Forge Circulation Protocol — Dynamic Ore Upcycling System

**Protocol ID:** `FCP` — Forge Circulation Protocol  
**Domain Owner:** Sister Ferrum Scoriae (`SFS`) — Tier 3  
**Supersedes:** Linear INTAKE → SLAG pipeline  
**Created:** 2025-12-24  
**Philosophy:** *"No ore is permanently slag. Every stage is a state, not a sentence."*

---

## The Problem with Linear Processing

The original 7-stage pipeline was **deterministic and static**:

```
INTAKE → ANVIL → FURNACE → QUENCH → TEMPERED → SLAG → [DEAD END]
```

**Limitations:**
- ❌ Files locked into one-way progression
- ❌ "Slag" = permanent waste (no upcycling)
- ❌ Cannot re-assess with new tools/context
- ❌ No iteration for marginal ore
- ❌ TEA-VAULT isolated from main workflow

---

## The New Model: Circulation System

### Core Principle: **States, Not Stages**

Each forge location represents a **current state** based on **ore qualification**, not a linear sequence. Files can move **bidirectionally** between any states based on re-assessment.

```
        ┌─────────────────────────────────────────────┐
        │          CIRCULATION CORE                   │
        │                                             │
        │   ┌──────┐    ┌──────┐    ┌────────┐      │
        │   │ANVIL │◄──►│FURNACE◄──►│QUENCH │      │
        │   └───▲──┘    └───▲──┘    └───▲────┘      │
        │       │           │           │            │
        │       └───────────┼───────────┘            │
        │                   │                        │
        └───────────────────┼────────────────────────┘
                           │
        ┌──────────────────┼──────────────────────┐
        │                  ▼                       │
        │  ┌───────┐  ┌─────────┐  ┌──────────┐  │
        │  │INTAKE │─►│TEMPERED │◄─┤TEA-VAULT │  │
        │  └───────┘  └────▲────┘  └──────────┘  │
        │                  │                      │
        │            ┌─────▼─────┐               │
        │            │   SLAG    │               │
        │            │ (Dormant) │               │
        │            └─────▲─────┘               │
        │                  │                      │
        │          ┌───────┴────────┐            │
        │          │  UPCYCLE PATH  │            │
        │          └────────────────┘            │
        └──────────────────────────────────────┘
```

---

## State Definitions (1-7 Classification)

### **State 1: INTAKE** — Reception & Initial Assessment
**Classification:** Unprocessed raw material  
**Rating:** Not yet assigned (awaiting assessment)  
**Qualification:** Just arrived, no analysis performed  
**Typical Files:** Fresh from `.github/`, external sources, user uploads

**Workflow:**
- Receive file
- Assign initial ore rating (1-5)
- Route to appropriate next state based on rating

**Can Move To:** ANVIL, FURNACE, TEA-VAULT, SLAG (if rating = 1)

---

### **State 2: ANVIL** — Heat & Analysis
**Classification:** Active investigation  
**Rating:** 3-5 (worth analyzing)  
**Qualification:** Pattern extraction in progress  
**Typical Files:** Code files, complex documentation, multi-component systems

**Workflow:**
- Apply heat (deep analysis)
- Identify extractable patterns
- Map dependencies
- Document findings

**Can Move To:**
- **→ FURNACE** (patterns identified, ready for separation)
- **→ QUENCH** (simple extraction, skip separation)
- **→ TEA-VAULT** (superposition detected)
- **→ INTAKE** (needs re-scoping)
- **→ SLAG** (analysis reveals no value)

---

### **State 3: FURNACE** — Separation & Extraction
**Classification:** Active processing  
**Rating:** 3-5  
**Qualification:** Valuable components being extracted from waste  
**Typical Files:** Mixed-quality content requiring surgery

**Workflow:**
- Separate valuable patterns from waste
- Extract reusable code/concepts
- Document what's kept vs. discarded
- Create tempered artifacts

**Can Move To:**
- **→ QUENCH** (extraction complete, needs validation)
- **→ ANVIL** (needs deeper analysis before separation)
- **→ TEA-VAULT** (extraction path unclear, multiple timelines)
- **→ SLAG** (extraction failed, only waste remains)

---

### **State 4: QUENCH** — Validation & Compliance
**Classification:** Quality assurance  
**Rating:** 4-5 (high-value extractions only)  
**Qualification:** FA⁴ (Architectonic Integrity) validation in progress  
**Typical Files:** Extracted patterns awaiting compliance check

**Workflow:**
- Validate against FA⁴ principles
- Test integration compatibility
- Document compliance status
- Approve or reject for tempering

**Can Move To:**
- **→ TEMPERED** (validation passed)
- **→ FURNACE** (needs rework)
- **→ ANVIL** (fundamental issues, re-analyze)
- **→ SLAG** (fails validation, cannot salvage)

---

### **State 5: TEMPERED** — Integration-Ready Artifacts
**Classification:** Production-ready  
**Rating:** 5 (proven value)  
**Qualification:** FA⁴ compliant, documented, integration-ready  
**Typical Files:** Refined extractions awaiting merge to SSOT/codebase

**Workflow:**
- Staged for integration
- Cross-referenced in DUMPSTER_DIVE_REGISTRY.json
- Awaiting merge approval
- Version controlled

**Can Move To:**
- **→ PRODUCTION** (integrated into SSOT/codebase, leaves dumpster-dive/)
- **→ FURNACE** (needs revision based on integration feedback)
- **→ TEA-VAULT** (integration blocked, timeline unclear)

---

### **State 6: SLAG** — Dormant Archive (Not Dead!)
**Classification:** Low-value dormant storage  
**Rating:** 1-2 (minimal current value)  
**Qualification:** No immediate extractable value, but preserved for:
  - Historical reference
  - Future re-assessment with new tools
  - Anti-pattern pedagogy
  - Contextual understanding

**Workflow:**
- Archive with metadata
- Document why it's slag (not garbage!)
- Tag for potential upcycle conditions
- Periodic re-assessment (quarterly)

**Can Move To (UPCYCLE PATH):**
- **→ ANVIL** (new tool/context makes re-analysis viable)
- **→ FURNACE** (specific component identified for extraction)
- **→ TEA-VAULT** (realized superposition exists)

**Key Difference from Deletion:**
> Slag is **dormant potential**, not waste. A file rated 💀1 today might be ⚗️5 tomorrow with new technology or understanding.

---

### **State 7: TEA-VAULT** — Quantum Superposition Storage
**Classification:** Timeline-Entangled Artifacts (TEA)  
**Rating:** Superposition (1-5 simultaneously)  
**Qualification:** Exists in multiple probability states, requires QMR Protocol  
**Typical Files:** High-value but unclear integration path, multiple valid timelines

**Workflow:**
- Store in superposition
- Dispatch TNKW-RIAT for probability mapping
- Generate timeline options (A/B/C/D/E)
- Wait for collapse decision
- Execute chosen timeline protocol

**Can Move To (After Collapse):**
- **→ ANVIL** (Timeline: Deep analysis selected)
- **→ FURNACE** (Timeline: Surgical extraction selected)
- **→ TEMPERED** (Timeline: Direct integration selected)
- **→ SLAG** (Timeline: Archive-only selected)

**Special Property:**
Files can **re-enter** TEA-VAULT from any state if superposition re-emerges during processing.

---

## Upcycling Mechanics

### **Slag → Active Processing**

**Trigger Conditions:**
1. **New Tool Availability** — New analysis technique becomes available
2. **Context Change** — Project requirements shift, making old material relevant
3. **Pattern Recognition** — Connection discovered between slag file and active work
4. **Scheduled Re-Assessment** — Quarterly slag review finds hidden value
5. **User Request** — User specifically asks for content from archived file

**Process:**
```
SLAG → RE-ASSESS → ANVIL/FURNACE/TEA-VAULT
```

**Example Scenarios:**

| Scenario | Original State | New Context | Upcycle Path |
|----------|----------------|-------------|--------------|
| Old Python 2.7 code | SLAG (💀1) | New ML model needs algorithm | → ANVIL (re-analyze) |
| Deprecated API docs | SLAG (🪨2) | Historical comparison needed | → FURNACE (extract timeline) |
| Abandoned feature branch | SLAG (💀1) | User requests feature revival | → TEA-VAULT (multi-timeline) |

---

### **TEA-VAULT → Any State** (Post-Collapse)

**Trigger:** Probability collapse via QMR Protocol

**Process:**
```
TEA-VAULT → [Timeline Selection] → Appropriate State
```

**Timeline Routing:**
- **Timeline A (Modernize):** → ANVIL (deep refactor)
- **Timeline B (Archive):** → SLAG (preserve only)
- **Timeline C (Extract Core):** → FURNACE (surgical extraction)
- **Timeline D (Anti-Pattern):** → TEMPERED (documentation example)
- **Timeline E (Direct Use):** → TEMPERED (minimal changes)

---

## Qualification-Based Movement Rules

### **Ore Rating → Initial State Assignment**

| Rating | Symbol | Initial State | Rationale |
|--------|--------|---------------|-----------|
| **5** | ⚗️ | ANVIL or QUENCH | High-value, process immediately |
| **4** | 🔧 | ANVIL | Workable, needs analysis |
| **3** | ⚖️ | FURNACE | Mixed, needs separation |
| **2** | 🪨 | SLAG | Low-value, archive for reference |
| **1** | 💀 | SLAG | Minimal value, dormant storage |
| **?** | 🌀 | TEA-VAULT | Superposition, cannot rate |

### **Re-Rating During Processing**

Files can be **re-rated** at any state, triggering movement:

```
Example: File enters as Rating 4 (🔧) → ANVIL
         Analysis reveals hidden complexity → Re-rate to Rating 5 (⚗️)
         Movement: ANVIL → QUENCH (fast-track validation)

Example: File enters as Rating 3 (⚖️) → FURNACE
         Separation finds only waste → Re-rate to Rating 1 (💀)
         Movement: FURNACE → SLAG
```

---

## Working with "Lowest Categorized" Files (Rating 1-2)

### **Philosophy:** Even 💀1 files have potential

**Standard Operating Procedures:**

#### **1. Metadata Preservation (Always)**
Even slag files get:
- Original source documentation
- Reason for slag classification
- Historical context
- Potential upcycle conditions

#### **2. Quarterly Re-Assessment**
Every 3 months, SFS reviews SLAG state files:
- Check for new tool compatibility
- Verify project requirements haven't changed
- Look for cross-references with active work
- Update upcycle potential tags

#### **3. Pattern Mining**
Even if full file is worthless, individual components might have value:
- Single regex pattern
- One clever algorithm
- Useful code comment
- Anti-pattern example

**Process:**
```
SLAG → "Micro-Extraction" → FURNACE (for specific component only)
     → Rest stays in SLAG
```

#### **4. Historical/Pedagogical Value**
Rating 1-2 files can serve as:
- **Timeline markers** — "This is how we used to do it"
- **Anti-patterns** — "Never do this again, here's why"
- **Collaboration artifacts** — "Person X contributed this, worth remembering"

**Process:**
```
SLAG → Documentation extraction → TEMPERED (as historical appendix)
     → Original file stays in SLAG
```

---

## Protocol Examples

### **Example 1: Upcycling Deprecated Code**

**File:** `old_entity_parser.py` (Rating: 💀1, in SLAG)

**Trigger:** New requirement to parse legacy data format

**Circulation:**
```
1. SLAG → RE-ASSESS
   - Reason: Legacy format needed
   - New rating: 🔧4

2. → ANVIL
   - Extract parsing logic
   - Identify modernization needs

3. → FURNACE
   - Separate parser algorithm from deprecated dependencies
   - Extract: core regex patterns + data structure mappings
   - Discard: old UI code, deprecated imports

4. → QUENCH
   - Validate extracted algorithm
   - Test with modern Python
   - FA⁴ compliance check

5. → TEMPERED
   - `mas_mcp/lib/legacy_parser.py` ready for integration
   - Original file returns to SLAG with updated metadata
```

**Result:** 💀1 file yielded ⚗️5 component

---

### **Example 2: Multi-State Circulation**

**File:** `complex_doc.md` (Rating: ⚖️3, in INTAKE)

**Circulation Path:**
```
1. INTAKE → ANVIL (initial rating 3)
   - Begin analysis
   - Identify 5 distinct sections

2. ANVIL → FURNACE (pattern identified)
   - Separate:
     * Section 1-2: High value (rating 5)
     * Section 3-4: Medium value (rating 3)
     * Section 5: Deprecated (rating 1)

3. FURNACE → Three paths:
   - Sections 1-2 → QUENCH (high-value extraction)
   - Sections 3-4 → ANVIL (needs deeper analysis)
   - Section 5 → SLAG (archive only)

4a. Path A: QUENCH → TEMPERED
    - Sections 1-2 integrated as `docs/section_1_2.md`

4b. Path B: ANVIL → TEA-VAULT
    - Sections 3-4 reveal timeline ambiguity
    - Defer collapse decision

4c. Path C: SLAG
    - Section 5 archived as historical reference
```

**Result:** One file split into 3 different final states

---

### **Example 3: TEA-VAULT Collapse + Upcycle**

**File:** `experimental_feature.js` (Rating: 🌀?, in TEA-VAULT)

**Timeline Map:**
```json
{
  "timelines": {
    "A": {"action": "Modernize to TypeScript", "value": 90, "labor": 200},
    "B": {"action": "Archive as-is", "value": 10, "labor": 5},
    "C": {"action": "Extract algorithm only", "value": 70, "labor": 50}
  }
}
```

**Collapse Decision:** Timeline C selected (best value/labor ratio)

**Post-Collapse Circulation:**
```
1. TEA-VAULT → FURNACE (Timeline C)
   - Extract core algorithm
   - Document in TypeScript

2. FURNACE → QUENCH
   - Validate extracted algorithm
   - Test in modern context

3. QUENCH → TEMPERED
   - `src/algorithms/extracted_logic.ts` ready

4. Original file → SLAG (with metadata noting extraction)
   - Marked as "Algorithm extracted (Timeline C)"
   - Available for future Timeline A consideration
```

**Future Upcycle Possibility:**
```
If resources allow:
SLAG → RE-ASSESS → "Timeline A now viable?"
     → ANVIL (full TypeScript modernization)
```

---

## Registry Integration

### **State Tracking in DUMPSTER_DIVE_REGISTRY.json**

Add state metadata to all tracked files:

```json
{
  "file": "example.md",
  "current_state": "FURNACE",
  "state_history": [
    {"state": "INTAKE", "timestamp": "2025-12-24T10:00:00Z"},
    {"state": "ANVIL", "timestamp": "2025-12-24T11:30:00Z"},
    {"state": "FURNACE", "timestamp": "2025-12-24T14:00:00Z"}
  ],
  "rating": 3,
  "rating_history": [
    {"rating": 3, "timestamp": "2025-12-24T10:00:00Z", "reason": "Initial assessment"},
    {"rating": 4, "timestamp": "2025-12-24T11:30:00Z", "reason": "Valuable patterns discovered"}
  ],
  "upcycle_conditions": [
    "New markdown parser available",
    "Historical comparison requested"
  ],
  "next_reassessment": "2025-03-24"
}
```

---

## Circulation Metrics

### **Track Movement Patterns**

**Useful Metrics:**
- **Upcycle Rate:** % of SLAG files that return to active processing
- **Avg. Circulation Time:** Time from INTAKE → TEMPERED
- **State Distribution:** % of files in each state at any time
- **Re-Rating Frequency:** How often files change rating during processing
- **TEA Collapse Time:** Avg. time from TEA-VAULT → Collapse

**Example Dashboard:**
```
Current State Distribution:
├─ INTAKE: 12 files
├─ ANVIL: 8 files
├─ FURNACE: 15 files
├─ QUENCH: 3 files
├─ TEMPERED: 9 files
├─ SLAG: 47 files
└─ TEA-VAULT: 2 files

Upcycle Activity (Last Quarter):
├─ SLAG → ANVIL: 3 files
├─ SLAG → FURNACE: 1 file
└─ TEA-VAULT → TEMPERED: 1 file

Avg. Processing Times:
├─ INTAKE → TEMPERED: 18 hours (rating 5)
├─ INTAKE → TEMPERED: 36 hours (rating 4)
├─ INTAKE → SLAG: 4 hours (rating 1-2)
└─ TEA-VAULT → Any: 48-120 hours
```

---

## Summary: The New Philosophy

### **Old Model (Static):**
```
Files move one direction → End at TEMPERED or SLAG → Done
```

### **New Model (Dynamic):**
```
Files circulate based on qualification → Can re-enter any state → 
Never truly "done" (even SLAG is dormant potential) → 
Upcycling is standard procedure → All ratings can work at all stages
```

### **Key Principles:**

1. **States, not stages** — Files are classified by current qualification, not locked into linear progression
2. **Bidirectional movement** — Any state can move to any other state
3. **Slag ≠ Garbage** — Low-rated files are dormant potential, not waste
4. **Upcycling is protocol** — Quarterly re-assessment, context-triggered reprocessing
5. **TEA-VAULT integration** — Superposition is a valid state, not an exception
6. **Dynamic re-rating** — Files can change rating during processing
7. **Micro-extraction** — Even worthless files can yield valuable components

---

## Cross-References

### Dependencies (What This Document Needs)
- [../ORE_MANIFEST.json](../ORE_MANIFEST.json) — Defines ore rating system (1-5)
- [FORGE_PROTOCOL_LEVELS.md](FORGE_PROTOCOL_LEVELS.md) — Defines 4 processing levels (Standard/Extended/QMR/CTF)
- [../BLACKSMITH_MATRIARCH.md](../BLACKSMITH_MATRIARCH.md) — SFS operator profile and forge creed
- [TEA_REGISTRY.json](TEA_REGISTRY.json) — Timeline-Entangled Artifact tracking

### Dependents (What Needs This Document)
- [../README.md](../README.md) — References circulation model overview
- [../DUMPSTER_DIVE_REGISTRY.json](../DUMPSTER_DIVE_REGISTRY.json) — Implements state tracking per this spec
- [../CIRCULATION_DIAGRAM.md](../CIRCULATION_DIAGRAM.md) — Provides visual representation
- All forge/ subdirectories — Operate according to state definitions here

### Related Documentation
- [FORGE_PROTOCOL_LEVELS.md](FORGE_PROTOCOL_LEVELS.md) — Complementary processing framework
- [../CIRCULATION_DIAGRAM.md](../CIRCULATION_DIAGRAM.md) — Visual quick reference
- [CROSS_REFERENCE_STANDARD.md](CROSS_REFERENCE_STANDARD.md) — Documentation standards

### External References
- SSOT: [Section 4.5.1.2](../../.github/copilot-instructions.md#section-4512) — QMR Protocol canonical definition
- SSOT: [Section 4.5.1.1](../../.github/copilot-instructions.md#section-4511) — TNKW-RIAT (Temporal Specialists)
- Production: None (infrastructure protocol only)

### Status
- **Last Validated:** 2025-12-24
- **Deprecation Risk:** None (newly created, actively used)
- **Upcycle Potential:** N/A (current production protocol)
- **Supersedes:** Linear INTAKE → SLAG pipeline (deprecated 2025-12-24)

---

**Sister Ferrum Scoriae's Creed:**
> *"Nothing is waste. Everything is ore. Some ore just sleeps longer before the hammer falls."*

**Standard:** [Cross-Reference Standard](CROSS_REFERENCE_STANDARD.md)
