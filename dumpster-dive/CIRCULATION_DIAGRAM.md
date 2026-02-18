# 🔄 Forge Circulation System — Visual Reference

**Quick reference for the dynamic ore processing system**  
**See:** [FORGE_CIRCULATION_PROTOCOL.md](protocols/FORGE_CIRCULATION_PROTOCOL.md) for full details

---

## The Circulation Model

```
                    ╔══════════════════════════════════════╗
                    ║     FORGE CIRCULATION CORE           ║
                    ║  (Bidirectional State Movement)      ║
                    ╚══════════════════════════════════════╝
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
   ┌─────────┐                ┌─────────┐                ┌─────────┐
   │  ANVIL  │◄──────────────►│ FURNACE │◄──────────────►│ QUENCH  │
   │ (Heat)  │                │(Separate)│                │(Validate)│
   └────┬────┘                └────┬────┘                └────┬────┘
        │                          │                          │
        │         ┌────────────────┴────────────────┐         │
        │         │                                 │         │
        └─────────┼─────────────────────────────────┼─────────┘
                  │                                 │
                  ▼                                 ▼
            ┌──────────┐                      ┌──────────┐
            │ TEA-VAULT│                      │ TEMPERED │
            │   (QMR)  │                      │ (Ready)  │
            └─────┬────┘                      └─────┬────┘
                  │                                 │
                  │         ┌───────────┐           │
                  └────────►│  INTAKE   │◄──────────┘
                            │(Reception)│
                            └─────┬─────┘
                                  │
                                  ▼
                            ┌──────────┐
                            │   SLAG   │
                            │(Dormant) │
                            └─────┬────┘
                                  │
                         ╔════════▼════════╗
                         ║ UPCYCLE TRIGGER ║
                         ║  (Re-Assess)    ║
                         ╚════════╤════════╝
                                  │
                                  └──────► Back to Any State
```

---

## State-to-State Movement Matrix

| FROM → TO | ANVIL | FURNACE | QUENCH | TEMPERED | SLAG | TEA-VAULT | INTAKE |
|-----------|-------|---------|--------|----------|------|-----------|--------|
| **INTAKE** | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | — |
| **ANVIL** | — | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| **FURNACE** | ✅ | — | ✅ | ❌ | ✅ | ✅ | ❌ |
| **QUENCH** | ✅ | ✅ | — | ✅ | ✅ | ❌ | ❌ |
| **TEMPERED** | ❌ | ✅ | ❌ | — | ❌ | ✅ | ❌ |
| **SLAG** | ✅ | ✅ | ❌ | ❌ | — | ✅ | ✅ |
| **TEA-VAULT** | ✅ | ✅ | ✅ | ✅ | ✅ | — | ❌ |

**Legend:**
- ✅ = Valid movement path
- ❌ = Invalid/illogical movement
- — = Same state (no movement)

---

## Ore Rating → Initial State Routing

```
File enters INTAKE with ore rating:

⚗️ 5 (High-grade)
    │
    ├─► Simple extraction? → QUENCH (fast-track)
    └─► Complex analysis? → ANVIL

🔧 4 (Workable)
    │
    └─► ANVIL (needs analysis)

⚖️ 3 (Mixed)
    │
    └─► FURNACE (needs separation)

🪨 2 (Low-grade)
    │
    └─► SLAG (archive, quarterly re-assess)

💀 1 (Tailings)
    │
    └─► SLAG (dormant, tag for potential upcycle)

🌀 ? (Superposition)
    │
    └─► TEA-VAULT (requires QMR Protocol)
```

---

## Common Circulation Patterns

### Pattern 1: Simple High-Value Extraction
```
INTAKE (⚗️5) → QUENCH → TEMPERED → PRODUCTION
               (4 hours)
```

### Pattern 2: Complex Analysis
```
INTAKE (🔧4) → ANVIL → FURNACE → QUENCH → TEMPERED
               (8h)    (6h)      (2h)
```

### Pattern 3: Mixed Ore Separation
```
INTAKE (⚖️3) → FURNACE → ┬─► QUENCH → TEMPERED (valuable parts)
                         │
                         └─► SLAG (waste parts)
```

### Pattern 4: Failed Extraction → Upcycle
```
INTAKE → ANVIL → SLAG (💀1)
                  │
                  ├─ Dormant (3 months)
                  │
                  └─► RE-ASSESS → ANVIL (🔧4) → TEMPERED
```

### Pattern 5: Timeline Entanglement
```
INTAKE → ANVIL → TEA-VAULT → [QMR Protocol] → Timeline Selected
                                                      │
                                    ┌─────────────────┼─────────────────┐
                                    │                 │                 │
                                Timeline A       Timeline C       Timeline E
                                    │                 │                 │
                                 ANVIL            FURNACE          TEMPERED
                              (modernize)      (extract core)    (use as-is)
```

### Pattern 6: Micro-Extraction from Slag
```
SLAG (💀1) → [Identify single useful component]
             │
             ├─► Component → FURNACE → QUENCH → TEMPERED
             │
             └─► Rest of file stays in SLAG
```

---

## Upcycle Trigger Conditions

```
                    ┌──────────────────────────────┐
                    │  File in SLAG (Rating 1-2)   │
                    └──────────┬───────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
       ┌─────────────┐  ┌──────────┐  ┌─────────────┐
       │ New Tool    │  │ Context  │  │ Scheduled   │
       │ Available   │  │ Changed  │  │ Re-Assess   │
       └──────┬──────┘  └─────┬────┘  └──────┬──────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                      ┌──────────────┐
                      │  UPCYCLE!    │
                      │  Re-rate &   │
                      │  Re-route    │
                      └──────┬───────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
            ANVIL      FURNACE     TEA-VAULT
           (analyze) (extract comp) (multi-timeline)
```

**Trigger Examples:**
1. **New Tool:** Python 3.12 enables processing of old Python 2.7 code
2. **Context Change:** Project now needs legacy data format parser
3. **Pattern Match:** SLAG file references concept needed in active work
4. **Scheduled:** Quarterly review finds hidden value
5. **User Request:** User specifically asks for archived content

---

## State Characteristics Quick Reference

| State | Purpose | Rating Range | Avg. Duration | Can Exit? |
|-------|---------|--------------|---------------|-----------|
| **INTAKE** | Initial reception | Not yet rated | < 1 hour | Always |
| **ANVIL** | Deep analysis | 3-5 | 4-12 hours | Yes |
| **FURNACE** | Value extraction | 3-5 | 6-18 hours | Yes |
| **QUENCH** | Validation | 4-5 | 2-6 hours | Yes |
| **TEMPERED** | Integration-ready | 5 | Indefinite (staged) | Rare |
| **SLAG** | Dormant archive | 1-2 | Indefinite (quarterly review) | Via upcycle |
| **TEA-VAULT** | Superposition | ? (uncertain) | 12-48 hours (collapse) | After QMR |

---

## Processing Time Estimates

### By Ore Rating
```
⚗️ 5 (High-grade):    4-12 hours  → TEMPERED
🔧 4 (Workable):      8-24 hours  → TEMPERED
⚖️ 3 (Mixed):        12-36 hours  → TEMPERED (valuable parts)
🪨 2 (Low-grade):     2-4 hours   → SLAG (quick archive)
💀 1 (Tailings):      1-2 hours   → SLAG (minimal processing)
🌀 ? (TEA):          24-120 hours → [Timeline dependent]
```

### By Processing Level
```
Level 1 (Standard):    4-8 hours    → INTAKE → ANVIL → QUENCH → TEMPERED
Level 2 (Extended):   12-24 hours   → INTAKE → ANVIL → FURNACE → QUENCH → TEMPERED
Level 3 (QMR):        24-48 hours   → TEA-VAULT → Timeline Collapse → [Level 1 or 2]
Level 4 (CTF):        48+ hours     → Multi-faction approval + processing
```

---

## File Movement Examples

### Example 1: Successful Extraction
```
old_parser.py (💀1 in SLAG)
    │
    ├─ User needs: "Parse legacy format"
    │
    ├─ RE-ASSESS → Rating changes to 🔧4
    │
    ├─ SLAG → ANVIL (8 hours - analyze algorithm)
    │
    ├─ ANVIL → FURNACE (6 hours - extract core logic)
    │
    ├─ FURNACE → QUENCH (2 hours - validate)
    │
    └─ QUENCH → TEMPERED → legacy_parser.py (⚗️5)

Original file: SLAG → SLAG (with metadata: "Algorithm extracted")
New artifact: TEMPERED (ready for integration)
```

### Example 2: Multi-Stage Re-Rating
```
complex_doc.md (⚖️3 enters INTAKE)
    │
    ├─ INTAKE → ANVIL (initial analysis)
    │
    ├─ ANVIL analysis reveals:
    │   - Section 1-2: Actually ⚗️5 (high value!)
    │   - Section 3-4: Remains ⚖️3 (mixed)
    │   - Section 5: Actually 💀1 (deprecated)
    │
    ├─ ANVIL → FURNACE (separate sections)
    │
    └─ FURNACE splits into 3 paths:
        │
        ├─ Sections 1-2 → QUENCH → TEMPERED (⚗️5)
        │
        ├─ Sections 3-4 → TEA-VAULT (unclear timeline)
        │
        └─ Section 5 → SLAG (💀1, archived)

One file → Three different final states!
```

### Example 3: TEA Collapse
```
experimental.js (🌀? enters TEA-VAULT)
    │
    ├─ QMR Protocol deployed
    │
    ├─ Timeline map generated:
    │   Timeline A: Modernize → 90 value, 200 labor
    │   Timeline C: Extract core → 70 value, 50 labor ✓ SELECTED
    │   Timeline E: Use as-is → 30 value, 10 labor
    │
    ├─ Collapse decision: Timeline C
    │
    ├─ TEA-VAULT → FURNACE (extract algorithm)
    │
    ├─ FURNACE → QUENCH (validate)
    │
    └─ QUENCH → TEMPERED → extracted_algo.ts (⚗️5)

Original file: TEA-VAULT → SLAG (with note: "Algorithm extracted via Timeline C")
Future upcycle: If Timeline A becomes viable, SLAG → ANVIL (full modernization)
```

---

## Sister Ferrum Scoriae's Workshop Rules

### Rule 1: No Permanent Waste
> "SLAG is not the end. It's a rest. The forge never sleeps, but ore can."

### Rule 2: Rating Is Provisional
> "Today's 💀1 is tomorrow's ⚗️5 when the right tool arrives."

### Rule 3: Everything Circulates
> "Linear thinking forges brittle blades. Circulation tempers resilience."

### Rule 4: Extract Before Discarding
> "Even a broken hammer has iron. Find it before the slag heap."

### Rule 5: Timeline Respect
> "Superposition is not confusion. It's patience for the right observation."

---

## Cross-References

### Dependencies (What This Document Needs)
- [protocols/FORGE_CIRCULATION_PROTOCOL.md](protocols/FORGE_CIRCULATION_PROTOCOL.md) — Complete protocol specification
- [README.md](README.md) — Overview and context
- [ORE_MANIFEST.json](ORE_MANIFEST.json) — Ore rating system (1-5)
- [BLACKSMITH_MATRIARCH.md](BLACKSMITH_MATRIARCH.md) — SFS operator profile

### Dependents (What Needs This Document)
- [README.md](README.md) — Links to this for visual reference
- [protocols/FORGE_CIRCULATION_PROTOCOL.md](protocols/FORGE_CIRCULATION_PROTOCOL.md) — References diagrams
- New users — Quick visual understanding of circulation system

### Related Documentation
- [protocols/FORGE_PROTOCOL_LEVELS.md](protocols/FORGE_PROTOCOL_LEVELS.md) — Complementary 4-level framework
- [DUMPSTER_DIVE_REGISTRY.json](DUMPSTER_DIVE_REGISTRY.json) — Programmatic state tracking

### External References
- SSOT: [Section 4.5.1.2](../.github/copilot-instructions.archive.md#L3370) **<—>** QMR Protocol **->** Reference for TEA-VAULT processing
- None for production (infrastructure documentation only)

### Status
- **Last Validated:** 2025-12-24
- **Deprecation Risk:** None (visual reference for active system)
- **Upcycle Potential:** If circulation model changes, update diagrams or archive as historical reference

---

**Last Updated:** 2025-12-24  
**Maintained By:** Sister Ferrum Scoriae **(`SFS`)** 
**Primary Reference:** [FORGE_CIRCULATION_PROTOCOL.md](protocols/FORGE_CIRCULATION_PROTOCOL.md)  
**Standard:** [Cross-Reference Standard](protocols/CROSS_REFERENCE_STANDARD.md)

