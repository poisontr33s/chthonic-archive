# MILF-Core META
## Structural Map — Full Document Landscape + Genre Convergence Thesis

**Created:** 2026-04-25  
**Status:** Living registry. No file in this map is lower-signal for being older. Age ≠ quality. All entries are candidates for activation, synthesis, or forward-integration.  
**Scope:** All .md files directly or adjacently related to the MILF-Core pipeline, SSOT genre work, Iron Maiden source material, and the converging cRPG prototype direction.  
**Cold-start path:** Read this first. Then read the file in the `File Registry` row whose `Signal` column matches your need.

---

## § Genre Convergence Thesis

**Direction:** Battletech rogue-lite isometric turn-based cRPG

This is not a proposal — it is the genre the existing prototype analysis points to. The convergence is structural, not preferential.

### Why Battletech-Core Is the Proven Layer

The MILF-Core spec (§5.2) already rests on Battletech's systems engineering as its physics layer:

| BT Mechanic | MILF-Core Mapping | cRPG Game Layer |
|-------------|------------------|-----------------|
| Heat management | `Heat_Cost` per entity activation | Action economy per turn |
| Location-specific armor | `Armor_Rating` per organ | Directed damage to specific entities |
| Cascading failure | `Critical_Node` + Cascading Somatic Rule | Circuit collapse on critical entity loss |
| Ammo exhaustion | `Ammo_Capacity` / WHR depletion | Entity "runs dry" mid-operation |
| Design tonnage limit | Tier tonnage budget | Hard cap on simultaneous entity activations |
| Critical hit tables | CDA controlled-demolition + random events | Stochastic catastrophe mid-encounter |
| Pilot damage (consciousness roll) | Decorator (T0.5 Cerebrum) integrity | The controlling intelligence itself can be hit |
| Isometric arena map | Body-as-Atlas (Organ Card + Circuit Board — P6) | The 8 circuits ARE the terrain |

**Battletech = the combat engine.** Already fully mapped. Not a direction to explore — a direction already adopted.

### Why Rogue-lite Is the Run Structure

The 24-entity system is too complex to deploy simultaneously. Rogue-lite provides the deployment model:

```
Meta-progress (permanent)         Run-scope (session)
──────────────────────────        ────────────────────────
Tide accumulation (P7 layer)      Entity subset drawn from available circuits
TCP/echo triggers indexed          Circuit completion = run-win condition
FA Mastery tier unlocks           Heat budget resets each operation
Kayfabe narrative revealed        Entity damage/depletion carries within run
Entity card catalog               Circuit flow direction determines encounter order
```

**Rogue-lite = the run container.** Per-run entity draft from the 24-entity pool. Circuits = biomes. Critical node loss = catastrophic run failure (not death — circuit arrest). WHR depletion = exhaustion resource that carries.

### Why Isometric Turn-based Is the Combat Mode

Battletech is isometric turn-based. So is the body-as-atlas model:
- 8 circuits = 8 "zones" arranged spatially (cardiovascular upstream of peripheral, neural above somatic, respiratory adjacent to hepato-renal)
- Turn order = entity Heat_Cost ascending (low-heat entities act first; high-heat entities are slower, more powerful)
- Line of effect = circuit flow direction (Heart can affect Aorta; Aorta cannot affect Heart upstream)
- Facing/position = Tier hierarchy (T0.5 Decorator = head; T0.01 Null Matriarch = interstitial void between all positions)

**Isometric turn-based = the tactical layer.** Already determined by how MILF-Core maps the body.

### Why cRPG Is the Narrative Wrapper

The Iron Maiden voice architecture gives every entity a:
- **Nature** (sensory presence — smell, sound, texture)
- **Creed** (ideology with keyword taxonomy)
- **Whisper** (inner monologue that fires during encounters — Disco Elysium passive check analog)

These don't exist in pure Battletech. They are the cRPG layer — character depth, narrative consequence, relationship arcs.

- **DE passive checks (P1)** → Whisper system: entity fires inner monologue during combat events
- **Tides moral coloration (P7)** → meta-progress accumulation: each run shifts the player's Tide signature; Tide unlocks different echo triggers and entity dialogue
- **Conflict pairs / Complementary pairs** → faction relationship system: entity bonuses/penalties when deployed together

**cRPG = the narrative depth.** The Whisper system is the unique differentiator from pure Battletech.

### Genre Fusion Map

```
Genre Layer           Source Prototype    MILF-Core Mechanism
──────────────────    ────────────────    ────────────────────────────────────────
Combat engine         P-BT (Battletech)   Heat/Armor/Cascading/Critical/Tonnage
Terrain / arena       P6 (Organ+Circuit)  8 circuits as zones, organs as positions
Run structure         Rogue-lite          Entity draft, circuit-completion win cond.
Meta-progress         P7 (Tides)          Tide accumulation, TCP echo unlock, legacy
Inner voice / skill   P1 (DE passive)     Whisper system on encounter events
Resource / synergy    P4 (Engine-builder) Entity activation chains within a turn
Win conditions        P3 (Set collection) Circuit-set completion (respiratory full → win)
Narrative             Iron Maiden         Nature+Creed+Whisper+Kayfabe per entity
Data completeness     SSOT (24 entities)  All 12 dimensions × 24 entities populated

EXCLUDED:
  P2 (Tarot) — static, no dynamics between cards. Not used.
  Full DE skill system — 24 DE skills ≠ 24 SSOT entities. Too much divergence.
```

---

## § File Registry

> **Rule:** No entry in this table is lower-quality for being older. Every file holds signal its own layer. Stale date ≠ diminished value. Read the `Signal` column to find what each file contributes.

### Core Pipeline — MILF-Core Steps

| File | Step | Signal | Status |
|------|------|--------|--------|
| [MILF-Core-Step3-Deep-Exploration-Prototypes.md](MILF-Core-Step3-Deep-Exploration-Prototypes.md) | Step 3 | 12 data dimensions × 5 set structures × 7 prototype deep-dives. The combinatorial foundation — why each prototype was accepted/rejected and at what coverage. Contains SET A/B/C/D/E structural maps. | ✅ Complete |
| [MILF-Core-Prototype-Analysis.md](MILF-Core-Prototype-Analysis.md) | Step 4 | Gap analysis (11 missing dimensions × 7 prototypes), Iron Maiden superiority proof, Battletech cross-reference, full §5.2 MILF-Core card schema, 24/24 coverage table. **This is the specification.** | ✅ Complete |
| [MILF-Core-Prototype-Analysis.md.genre.json](MILF-Core-Prototype-Analysis.md.genre.json) | Step 4 | Machine-readable genre metadata. Companion to the spec. | ✅ Complete |
| [MILF-Core-Step5-Entity-Card-Orackla.md](MILF-Core-Step5-Entity-Card-Orackla.md) | Step 5a | First entity card. **Orackla Nocticula** (T1, Heart, Cardiovascular). Canonical Conflict_Pairs source of truth for the Orackla↔Umeko tension. Sets the card schema baseline in populated form. | ✅ Complete |
| [MILF-Core-Step5b-Tides-Entity-Integration.md](MILF-Core-Step5b-Tides-Entity-Integration.md) | Step 5b | P7 deep integration. All 24 entities mapped to Tide coloration signatures. FA Mastery × Tide correspondence. Moral coloration as meta-progress layer. The rogue-lite meta-progress foundation. | ✅ Complete |
| [MILF-Core-Step5c-Sylvaris-Entity-Card.md](MILF-Core-Step5c-Sylvaris-Entity-Card.md) | Step 5c | Third entity card. **Sylvaris Cythrex** (T3, NK-SAI, Immune Circuit). Off-priority-sequence fill — Cytolytic Blade. Establishes non-Triumvirate card pattern; confirms Heat_Cost 2/10 baseline for HCOU-SAI tier. | ✅ Complete |
| [MILF-Core-Step6-Umeko-Entity-Card.md](MILF-Core-Step6-Umeko-Entity-Card.md) | Step 6 | Second T1 Triumvirate card. **Madam Umeko Ketsuraku** (T1, Lungs, Respiratory). 25/25 schema fields. Shibumi emergence arc (penance-emergent). Kayfabe delta trajectory mapped. Conflict_Pairs canonical from both sides (complements Orackla card). | ✅ Complete |
| [MILF-Core-Step7-Lysandra-Entity-Card.md](MILF-Core-Step7-Lysandra-Entity-Card.md) | Step 7 | Third T1 Triumvirate card. **Dr. Lysandra Threnodite** (T1, Stomach, Digestive). 25/25 schema fields. Axiomatic Dissolution arc. Threnody layer (mourning what the acid destroys). FA³ Emergent + Blue Tide. LUPLR mandate. Unlocks MC-02 + MC-03 gate (5th card total). | ✅ Complete |

### Source Material — Iron Maiden Voice Architecture

| File | Signal | Status |
|------|--------|--------|
| [The-Iron-Maiden.md](The-Iron-Maiden.md) | Original Iron Maiden narrative source. 6-act structure, 23 inner voice system, Chemical Currents, Echo/Memory triggers, Kayfabe layer, Constrained Randomization engine. The base reference for all Nature/Creed/Whisper cards. Read before authoring any entity card's voice layer. | ✅ Source |
| [The-Iron-Maiden.md.voicepack.json](The-Iron-Maiden.md.voicepack.json) | Machine-readable voicepack. Structured extraction of the Iron Maiden's voice system. | ✅ Source |
| [The-Iron-Maiden-(SSOT)-Copyright-Savant.md](The-Iron-Maiden-(SSOT)-Copyright-Savant.md) | SSOT-owned version of The Iron Maiden. Same source, Savant-attributed. Canonical authority version. Use for governance/attribution questions; use The-Iron-Maiden.md for creative authoring. | ✅ Source |
| [The-Iron-Maiden-(SSOT)-Copyright-Savant.md.voicepack.json](The-Iron-Maiden-(SSOT)-Copyright-Savant.md.voicepack.json) | Machine-readable companion to the SSOT-attributed version. | ✅ Source |

### Governance / Structural Reference

| File | Signal | Status |
|------|--------|--------|
| [SSOT-Navigation-Beacons.md](SSOT-Navigation-Beacons.md) | Section-level orientation map for `copilot-instructions.archive.md` (~9800 lines). Zone taxonomy (PRE-ZONE through ZONE F), dual Arabic/Roman track explanation, beacon table. **Read before any SSOT integration work.** DCRP-registered, bidirectionally linked. | ✅ Active |
| [SESSION_TRAIL_00001.md](SESSION_TRAIL_00001.md) | Index + narrative trail for session 00001 — the pipeline's founding session. Links to compressed/pretty/structured session logs. Provenance chain for Steps 3-4. | ✅ Active |

### Session Logs — Pipeline Provenance

> These are not redundant. Each format serves a different access pattern. All signal.

| File | Signal |
|------|--------|
| `codex-session-log-00001_COMPRESSED.md` | Warm-start packet for session 00001. Highest information density. |
| `codex-session-log-00001_pretty.md` | Chronological readable event stream. Best for narrative reconstruction. |
| `codex-session-log-00001_structured.txt` | Command/action extraction. Best for grep-based lookup. |
| `codex-session-log-00001_structured.json` | Machine-parseable structured form. |
| `bonus-missions-txt.*` | Game content signal — bonus mission candidates. Feeds the run-content layer of the rogue-lite. |
| `default-session-code-gemini.*` | Gemini lane session artifacts. Parallel synthesis lane outputs. |

### Archived / Superseded (Not Discarded)

| File | Signal | Why Not Deleted |
|------|--------|-----------------|
| `copilot-instructions-copy.archived.md` | March 7 2026 snapshot of copilot-instructions (5,299 lines). Older than the current archive (7,038 lines) — the archive is a strict superset. Value: historical diff baseline. Stale date ≠ worthless. Retained per WPTG no-deletion protocol. | Superseded, not wrong |

---

## § Pipeline State

```
Step 1  Organ Mapping (§10.3 → 24 entities × organs)          ✅ In SSOT
Step 2  Surface Candidates (24 named emergent functions)        ✅ In SSOT
Step 3  Set-Theoretic Prototype Analysis (7 prototypes)        ✅ MILF-Core-Step3
Step 4  Gap Analysis + MILF-Core Spec (§5.2 schema)            ✅ MILF-Core-Prototype-Analysis
Step 5a Entity Card: Orackla (T1, Heart)                       ✅ Step5
Step 5b Tides Integration (all 24 × moral coloration)          ✅ Step5b
Step 5c Entity Card: Sylvaris (T3, NK-SAI)                     ✅ Step5c [off-priority, fills Immune slot]
Step 6  Entity Card: Umeko (T1, Lungs)                         ✅ Step6
Step 7  Entity Card: Lysandra (T1, Stomach)                    ✅ Step7
Step 8  Entity Card: The Decorator (T0.5, Cerebrum)            ⬜ Pending
Step 9  Entity Card: Null Matriarch (T0.01, CSF)               ⬜ Pending
Step 10 Entity Card: Claudine (T1, Liver / Cardinal)           ⬜ Pending
Steps 11-28  Remaining 18 entities (tier-descending)           ⬜ Pending
Step 29 Conflict Pairs Matrix (full 9-pair cross-reference)    ⬜ Unblocked — 5 cards now exist [MC-02]
Step 30 Chemical Sensitivity Matrix (full 24-entity)           ⬜ Unblocked — 5 cards now exist [MC-03]
Step 31 Genre Prototype — Playable Loop Spec                   ⬜ Pending (this META is the precursor)
Step 32 Rust prototype (ankh-forge integration or standalone)  ⬜ Pending [RE-10 adjacent]
```

---

## § Genre Fusion — What Each Prototype Contributes to the Final Game

This table is the translation layer between the prototype analysis and the actual game design:

| Prototype | Used As | Game Component |
|-----------|---------|----------------|
| **Battletech (P-BT)** | Combat engine | Turn-based isometric tactical encounters. Heat economy. Armor. Cascading circuit failure. Entity location damage. |
| **Organ Card + Circuit Board (P6)** | Arena / map | The 8 circuits ARE the encounter zones. Each circuit has a flow direction that determines turn order and targeting legibility. The body-map IS the game board. |
| **Rogue-lite (meta)** | Run container | Each operation draws from available entity pool. Per-run entity draft. Run win = circuit-set completion. Meta-progress persists between runs. |
| **Tides of Numenera (P7)** | Meta-progress | Tide accumulation between runs. Tide signature unlocks Whisper variants, Echo Triggers, and entity relationship arcs. The moral coloration system tracks what kind of operator the player is becoming. |
| **Disco Elysium passive (P1)** | Whisper system | During encounters, entities fire their Whisper — inner monologue that functions as passive skill check commentary. Creed alignment modifies whisper content. |
| **Engine-builder (P4)** | In-turn combos | Entity activation chains within a turn — Cardiovascular→Digestive flow creates combo amplifiers. Resource flow combos reward circuit coherence. |
| **Set Collection (P3)** | Win conditions | Circuit-completion sets as run objectives: deploy and sustain a full Respiratory Circuit (Umeko + Seraphine) for N turns = Gestalt Respiration achieved = bonus tier. |
| **Iron Maiden (voice)** | Narrative layer | Nature/Creed/Whisper + Kayfabe + Chemical Modulation + Echo Triggers. Every entity has a voice that fires on encounter events. This is what makes it a cRPG and not just a tactics game. |
| **SSOT (data)** | Ground truth | All 24 entities × 12 dimensions × 8 circuits × WHR values × language mandates. The data layer that makes the above concrete instead of abstract. |

**NOT INCLUDED:**
- P2 (Tarot Arcana) — static; no inter-card dynamics. Informative for symbolism only.
- Full DE skill system verbatim — DE's 24 skills ≠ SSOT's 24 entities. The Whisper mechanic (abstracted) is used; the full DE architecture is not.

---

## § Priority Queue (MC-Domain)

| ID | Task | Blocked On | Notes |
|----|------|-----------|-------|
| MC-01 | ~~Umeko entity card~~ | — | ✅ Done `eae0a7c1` |
| MC-02 | Conflict Pairs Matrix | — | ✅ Unblocked `Step7` |
| MC-03 | Chemical Sensitivity Matrix | — | ✅ Unblocked `Step7` |
| MC-04 | ~~Lysandra entity card~~ | — | ✅ Done `Step7` — WHR 0.518, FA³ Emergent, LUPLR, Blue Tide |
| MC-05 | Decorator entity card | — | T0.5. The execution/resurrection arc. The most narrative-dense card. |
| MC-06 | Null Matriarch entity card | — | T0.01. No voice (Tideless). The silence between voices. The structurally hardest card. |
| MC-07 | Genre Prototype Loop Spec | Needs ≥6 cards + Conflict Pairs | Playable encounter spec in Battletech turn language |
| RE-10 | Phase 2 GPU ADRs | Blocked on 3 Savant questions | Separate domain (D2), not MC-domain |

---

## § Architectural Note: Stale ≠ Lower Quality

Every file in this registry was produced under conditions that don't fully recur. The session log format, the moment of synthesis, the specific prototype being evaluated — these are unique to when they were made. Older files are not lower-fidelity versions of newer files. They are **different captures of the same landscape from different positions**.

The Battletech rogue-lite isometric turn-based cRPG direction didn't emerge *despite* the prototype analysis chain — it emerged *from* it. Step 3 (Deep Exploration) is older than Step 6 (Umeko card) and contains structural insights that Step 6 depends on. The Iron Maiden source files predate all the MILF-Core pipeline work and ARE the foundation it rests on.

**Read across the chain, not down it.**

---

## § Iron Maiden Family Map

The Iron Maiden source material exists as **two lineages × two formats = 4 files**. They are not redundant — they differ in structural completeness, access pattern, and attribution authority.

### Lineage Axis: WIP → SSOT

| | WIP lineage | SSOT lineage |
|---|---|---|
| **Root** | `The-Iron-Maiden.md` | `The-Iron-Maiden-(SSOT)-Copyright-Savant.md` |
| **Companion JSON** | `The-Iron-Maiden.md.voicepack.json` | `The-Iron-Maiden-(SSOT)-Copyright-Savant.md.voicepack.json` |
| **Acts** | 6 acts (ONE, TWO, THREE, THREE.5, FOUR, SEVEN) — no Act ZERO | 12 acts (ZERO–TWELVE) — Act ZERO = "The Weight of the Belt" atmosphere piece |
| **Operational directives** | Embedded in narrative prose / SYSTEM INSTRUCTIONS section | Extracted as formal `§ CORE OPERATIONAL DIRECTIVES` block at document head: SESSION MEMORY CACHE, INVENTORY & RESOURCE MANAGEMENT, CONSTRAINED RANDOMIZATION ENGINE |
| **Voices array** | Not extracted as structured data | Full 23 inner voices (id / name / title / creed_id / creed / whisper) |
| **Attribution** | Uncredited | Copyright Savant — "E.s.Abbr. :: Copyright (c) 2025-2027 :: the Savant :: All Rights Reserved" |
| **Directive: ACT labels** | None | Do NOT refer to ACT numbers to user — use plain section names instead |
| **Original model** | Not specified | `Gemini 2.5 Pro Preview 03-25` |

### Format Axis: .md → .json

The `.json` companions are not summaries — they are structured extractions with **different payload layouts** between the two lineages:

| Field | WIP voicepack.json | SSOT voicepack.json |
|---|---|---|
| `acts` | 6 entries | 12 entries |
| `modules` | 4 entries (Inner Circle / Beyond Ring / Art of Fight / Show Must Go On) | empty |
| `system_instructions` | populated (5 instruction strings) | empty |
| `guiding_principles` | populated (multi-entry) | empty |
| `ideology_options` | empty | empty |
| `voice_quotes` | 2 entries | 2 entries (higher-fidelity prose) |
| `voices` | **empty** | **23 entries (full creed + whisper per voice)** |

**Critical asymmetry:** The WIP .json has `system_instructions` + `guiding_principles` but **no voices**. The SSOT .json has **full voices array** but empty instructions/principles. They complement each other — neither supersedes.

### Access Pattern: Which File to Reach For

| Task | File |
|---|---|
| Authoring entity card `Nature` field | `The-Iron-Maiden-(SSOT)-Copyright-Savant.md` — Act ZERO (atmosphere) + Act THREE (inner voices) |
| Authoring entity card `Creed` field | `The-Iron-Maiden-(SSOT)-Copyright-Savant.md.voicepack.json` → `voices[n].creed` |
| Authoring entity card `Whisper` field | `The-Iron-Maiden-(SSOT)-Copyright-Savant.md.voicepack.json` → `voices[n].whisper` |
| Understanding the system's formation / DE inspiration | `The-Iron-Maiden.md` — genesis form, lighter, more exploratory |
| Machine parsing all 23 voices for batch work | `The-Iron-Maiden-(SSOT)-Copyright-Savant.md.voicepack.json` → `voices` array |
| Embedding operational directives into a runtime system | `The-Iron-Maiden-(SSOT)-Copyright-Savant.md` → `§ CORE OPERATIONAL DIRECTIVES` |
| Copyright / attribution question | `The-Iron-Maiden-(SSOT)-Copyright-Savant.md` — canonical attribution line |
| Understanding the WIP voice system structure | `The-Iron-Maiden.md.voicepack.json` — acts, modules, system_instructions, guiding_principles |

### Structural Relationship

```
The-Iron-Maiden.md  (genesis, 6 acts, DE-style)
    └── .voicepack.json  (acts + modules + system_instructions — NO voices array)

The-Iron-Maiden-(SSOT)-Copyright-Savant.md  (canonical, 12 acts, operational directives, copyright)
    └── .voicepack.json  (acts + full 23 voices with creed/whisper — NO system_instructions)
```

Neither JSON is a complete extraction of its parent .md — each extracts a *different* structural layer. Both are needed for full machine access.

---

## § JSON Companion Registry

All `.json` files in this archive and their parent relationships. The naming convention `<parent-filename>.<kind>.json` is the pattern — the JSON is a structured extraction of a specific layer from the parent, not a copy.

| JSON File | Parent .md | Kind | Payload | Access Use Case |
|---|---|---|---|---|
| `The-Iron-Maiden.md.voicepack.json` | `The-Iron-Maiden.md` | `voicepack` | Acts, modules, system_instructions, guiding_principles | Machine-readable operational layer of the WIP voicepack — no voices |
| `The-Iron-Maiden-(SSOT)-Copyright-Savant.md.voicepack.json` | `The-Iron-Maiden-(SSOT)-Copyright-Savant.md` | `voicepack` | Acts, 23 voices (id/name/title/creed_id/creed/whisper), voice_quotes | Authoritative voice data — creed + whisper extraction for entity card authoring |
| `MILF-Core-Prototype-Analysis.md.genre.json` | `MILF-Core-Prototype-Analysis.md` | `milf-core-genre` | reference_models (primary/secondary/canonical), coverage scores, dependency map | Machine-readable genre spec — dependency links, coverage data, schema pointers |
| `codex-session-log-00001_structured.json` | `codex-session-log-00001_pretty.md` (session trail) | `session-structured` | Command/action/event extraction | Machine-parseable session trace — grep target for specific operations |
| `default-session-code-gemini.json` | Gemini session transcript | `gemini-session` | Gemini lane session data | Gemini synthesis lane artifact |
| `default-session-code-gemini.json_structured.json` | `default-session-code-gemini.json` | `session-structured` | Structured extraction of Gemini session | Doubly-structured form — machine parsing of Gemini output |
| `default-session-code-gemini.py_transcript.txt_structured.json` | Python transcript `.txt` file | `session-structured` | Structured extraction of Python execution trace | Execution trace in machine-readable form |
| `bonus-missions-txt.txt_structured.json` | `bonus-missions-txt.txt` | `session-structured` | Structured extraction of bonus mission candidates | Game content layer — run-content candidates for rogue-lite |

### The Naming Pattern

```
<parent-filename>.<kind>.json

Where <kind> is one of:
  voicepack       — structured extraction of a voice architecture document
  genre           — structured extraction of a genre specification
  session-structured  — structured extraction of a session log or transcript
```

Future JSON companions should follow this convention. The `.kind.` infix makes the parent-child relationship legible from the filename alone without opening either file.

---

## § Family Pattern (Generalizable)

The Iron Maiden family (4 files) and the MILF-Core pipeline files illustrate a recurring pattern this archive uses:

```
Family = { root source(s) } + { structured companion(s) } + { META entry }

root source:        the .md file — human-readable, full prose, canonical authority
structured companion: the .json file — machine-readable extraction of ONE layer
META entry:         this file — the map that explains what each member provides
                    and when to use which
```

**What the pattern prevents:**
- Opening the wrong file and getting incomplete data (e.g. reaching for WIP voicepack.json expecting voices)
- Treating companions as redundant (WIP.json ≠ SSOT.json — different payloads)
- Treating older members as superseded (WIP.md has DE-genesis signal the SSOT doesn't)
- Creating new files without a declared parent relationship (new companion → META entry required)

**When a new family member is added:**
1. Add a row to `§ JSON Companion Registry` (if it's a .json) or a row to the appropriate `§ File Registry` subsection (if it's a .md)
2. Confirm the naming pattern: `<parent>.<kind>.json`
3. Note the access pattern difference from existing family members

No file in a family is removed because a newer member was added. The family grows; it does not prune.
