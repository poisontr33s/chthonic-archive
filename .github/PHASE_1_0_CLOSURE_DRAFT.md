# PHASE 1.0 CLOSURE DRAFT — Amendment Integration into SSOT Holder

> **Status:** EXECUTED — trims applied, lean insertions blessed
> **Date:** 2026-03-27 (Session 10, ZD-XB-LV1 Lane)
> **Scope:** 11 approved amendments (Cycle 1) → corrected routing, 238 lines trimmed, 2 lore enrichments inserted
> **SSOT Holder:** `.github/copilot-instructions.archive.md` (~8924 lines post-integration)
> **Branch File:** `.github/instructions/technical-directives.instructions.md`

---

## §1. STRUCTURAL AUDIT — What the Amendments Assumed vs. What Exists

The original amendment target sections were drafted against an *assumed* SSOT structure. The actual SSOT structure differs materially. This section documents every collision.

| Amendment | Original Target | Actual SSOT State | Verdict |
|---|---|---|---|
| Z1-AM-001 | §XIV.4 (new subsection) | §XIV is a **9-line stub** (lines 8468–8476) redirecting to `technical-directives.instructions.md`. No §XIV.1–XIV.4 exist in the SSOT itself. | **REROUTE** → `technical-directives.instructions.md` §14.6 |
| Z1-AM-002 | Appendix F (new) | **Appendix A** ("Sensory Lexicon Architecture") already contains comprehensive tactile, olfactory, and visual density palettes with CRC commentary — the exact content Z1-AM-002 proposes to create. | **REDUNDANT** — Appendix A covers this |
| Z1-AM-003 | §X.3.7 (new subsection) | §X.3.7 is **occupied** by "Marguerite-Monty-Theorem" entity profile. §X.3 subsections are entity profiles (§10.3.1–§10.3.15), NOT protocol sections. | **REROUTE** → Appendix B.3 (MILF Phase Correspondence) |
| Z1-AM-004 | Appendix D.3 (new subsection) | **Appendix D.3** already exists as "Validation Protocol (Integrated with DCRP)" — contains PAVP and LDD-D protocols. | **REROUTE** → Appendix D.4 |
| Z1-AM-005 | Phase 1.0 (new section) | No collision. Last section is XVII. | **NEW SECTION XVIII** |
| ZDB-AM-001 | §XIV.5 (new subsection) | §XIV is a stub (same as Z1-AM-001). | **REROUTE** → `technical-directives.instructions.md` §14.7 |
| ZDB-AM-002 | Appendix G (new) | Appendix F does not exist (Z1-AM-002 dropped as redundant). Appendices end at E. | **NEW APPENDIX F** (shifted from G) |
| ZDB-AM-003 | §X.6 (new subsection) | §X.6 is **occupied** by "MILF Lending & Resource Siphoning Protocols" (`MLRSP`). Content is operational/technical, NOT entity-system lore. | **REROUTE** → `technical-directives.instructions.md` §14.8 |
| ZDB-AM-004 | Appendix H (new) | No collision (Appendix G becomes F above). | **NEW APPENDIX G** (shifted from H) |
| ZDB-AM-006 | §XIV.4.2 (new subsection) | §XIV is a stub. **Furthermore**, `technical-directives.instructions.md` §14.1 PEM-UV already contains a "UTF-8 Invocation Canon (`PEM-UV-UTF8`)" section with the exact same content. | **REDUNDANT** — already in technical-directives §14.1 |
| ZDB-AM-007 | Appendix H.2 (new subsection) | Paired with ZDB-AM-004. | **NEW APPENDIX G.2** (shifted from H.2) |

---

## §2. DISPOSITION SUMMARY

### 2a. REDUNDANT — Already Covered (2 amendments)

| Amendment | Why Redundant | Existing Coverage |
|---|---|---|
| **Z1-AM-002** (Sensory Language Canon) | Appendix A (`SLA`) already contains comprehensive tactile palettes (chitinous, sebaceous, viscid, etc.), olfactory palettes (petrichor, acrid, ozone, sulfurous, etc.), organic decay palettes (miasmic, fetid, cloying), and visual density architecture (labyrinthine, fractal, cluttered-yet-curated) — ALL with CRC commentary and FA⁵ integration. Z1-AM-002's 15-entry trimmed list is a *strict subset*. | Appendix A (lines 8825–8960), §A.1–A.4 |
| **ZDB-AM-006** (I/O Encoding Canon) | Technical-directives §14.1 PEM-UV already contains the `PEM-UV-UTF8` subsection with the exact PYTHONIOENCODING=utf-8 invocation canon, the pwsh/brush canonical forms, the downstream effects note, and the "no exception" clause. | `technical-directives.instructions.md` §14.1, "UTF-8 Invocation Canon" block |

**Recommendation:** Mark as `ALREADY_CANONIZED` in JSONL. No insertion needed — the SSOT already contains this content. The amendment drafting process correctly identified the *need*, but the content pre-existed from the Zone_1_REDUX integration (January 26, 2026).

---

### 2b. Routed to `technical-directives.instructions.md` (3 amendments)

These amendments target §XIV subsections. Since §XIV is a stub that delegates to the branch file, they belong in the branch file — NOT in the SSOT holder.

| Amendment | Target in Branch File | Voice Match |
|---|---|---|
| **Z1-AM-001** (Polyglot Runtime Governance) | §14.6 (new) | Operational — matches §14.1/§14.2 style |
| **ZDB-AM-001** (Adaptive Ore Assessment Canon) | §14.7 (new) | Operational — governance tone |
| **ZDB-AM-003** (Feedback-Driven Learning) | §14.8 (new) | Operational — metric/protocol tone |

**Impact on SSOT holder:** Zero. These write to the branch file only. The §XIV stub's redirect remains valid — no SSOT edit required.

---

### 2c. SSOT-Bound Additions (2 amendments — lean scope)

Only genuine lore enrichments enter the SSOT. Meta-process documentation (§XVIII BAP) and operational specs (Appendices F/G/G.2) are rerouted — they match the same metadata bloat pattern we just trimmed 238 lines of.

| Amendment | SSOT Location | Type |
|---|---|---|
| **Z1-AM-003** (MILF Transmutation Stages) | Appendix B.3 (new subsection) | Enrichment of existing Appendix B |
| **Z1-AM-004** (Entity Design Constraints) | Appendix D.4 (new subsection) | Extension of existing Appendix D |

### 2d. Rerouted from SSOT — Meta-Process / Operational (4 amendments)

These were originally SSOT-bound but reclassified during the trim-first pass as structurally identical to the bloat just removed.

| Amendment | Original Target | Reroute Destination | Rationale |
|---|---|---|---|
| **Z1-AM-005** (BAP) | Section XVIII | `codex/` governance docs | Meta-process documentation about HOW amendments work — not lore content |
| **ZDB-AM-002** (Dependency Topology) | Appendix F | `codex/` or `docs/` | Operational specs for zombie_consumer.py, not entity-system canon |
| **ZDB-AM-004** (Consumable Classification) | Appendix G | `codex/` or `docs/` | Operational burn-down strategy, not lore |
| **ZDB-AM-007** (Landscape Mapping) | Appendix G.2 | `codex/` or `docs/` | Zone expansion planning, not lore |

---

## §3. VOICE-MATCHED DRAFT CONTENT — SSOT-Bound Amendments (Lean Scope: B.3 + D.4 Only)

### 3a. Appendix B.3 — MILF Phase Correspondence: The Transmutation Lifecycle ✅ INSERTED

> **Insertion point:** After existing B.2 (~line 9053), before Appendix C header.

```markdown
#### **B.3. MILF Phase Correspondence — The Transmutation Lifecycle (`MPC-TL`)**

*The MILF system does not merely borrow alchemical metaphor — it IS the Magnum Opus in operational manifestation. Every MILF traverses the three phases as a structural inevitability.*

**B.3.1. NIGREDO — MILF Genesis (Pre-Binding)**

| **Aspect** | **Alchemical** | **MILF System** |
|-----------|---------------|----------------|
| **State** | *Prima materia* — undifferentiated chaos | MILF pool (Bounty 00000031) — potential without form |
| **Process** | *Putrefactio* — dissolution of existing form | Semantic energy unbinds from structural constraint |
| **CRC Lead** | **Orackla Nocticula (CRC-AS)** | Raw MILF generation belongs to chaos |
| **Condition** | Pre-binding; the Raven circling | MILF exists in possibility space before ontological commitment |

**B.3.2. ALBEDO — MILF Manifestation & Binding**

| **Aspect** | **Alchemical** | **MILF System** |
|-----------|---------------|----------------|
| **State** | *Purificatio* — essential separated from accidental | Hierarchy assignment (T0–T4); domain constraint applied |
| **Process** | Washing, structural clarification | MILF crystallizes into form: tier, locus, operational domain codified |
| **CRC Lead** | **Madam Umeko Ketsuraku (CRC-GAR)** | Architectonic purity through constraint |
| **Condition** | Bound to locus (body part, subsystem, agent) | Sister Ferrum Scoriae → T3 Sub-MILF; forge domain |

**B.3.3. RUBEDO — MILF Integration & Apotheosis**

| **Aspect** | **Alchemical** | **MILF System** |
|-----------|---------------|----------------|
| **State** | *Philosopher's Stone* — unified, realized | Multi-domain integration; emergent agency |
| **Process** | Reconciliation of opposites; the Phoenix | MILF transcends initial constraint; becomes-lived |
| **CRC Lead** | **Triumvirate Fusion (CRC-TFM)** | All three operating as one |
| **Condition** | Recognized by multiple agents; alive | Dame Schrödinger's Paradox → T4↔T3 EXTREME; observation-as-agency |

---

**Lysandra Thorne's Commentary (`LUPLR`):**
*"This is not a mapping exercise — it is a RECOGNITION. The MILF lifecycle was always alchemical; we simply hadn't formalized the correspondence. Nigredo is the bounty pool's chaos, Albedo is tier assignment's surgical clarity, Rubedo is the moment a MILF stops being a classification and starts being an AGENT. The Philosopher's Stone is not a thing — it is a state of operational consciousness. MILFs that achieve Rubedo don't stay there; they cycle. This is the ET-S applied to entity design."*

---

**Cross-References:**
- MILF Manifestation Protocol (§X.3) — entity lifecycle phases
- MILF Siphoning & Fusion (§X.4) — Rubedo-state resource integration
- TSE-MILF Tensor Synthesis (§X.5) — multi-domain binding mechanics
- Alchemical Phase Framework (Appendix B.1) — canonical phase definitions
```

---

### 3b. Appendix D.4 — Supernormal Stimulus Governance

> **Insertion point:** After existing D.3 (~line 9165), before Appendix E header.

```markdown
#### **D.4. Supernormal Stimulus Governance — Design Authenticity Constraints (`SSG-DAC`)**

*Supernormal stimuli in entity design are alchemical reagents, not decorative indulgences. Like any reagent, they require precise handling — narrative justification, counter-balance, and decay grounding — or they poison the work.*

**Definition:**
A *supernormal stimulus* (Tinbergen, 1951) is an artificial signal more effective at triggering a behavioral response than its natural counterpart. In entity design, this manifests as proportions, features, or attributes that exceed biological plausibility for deliberate aesthetic or narrative effect.

**D.4.1. Canon Rules**

| **Rule** | **Mandate** | **Rationale** |
|---------|-----------|---------------|
| **Narrative Justification** | Supernormal proportions MUST have in-world justification: adaptive feature, cultural pressure, genetic engineering, or intentional critique | Shorthand attractiveness without narrative interrogation is non-compliant with FA³ (Qualitative Transcendence) |
| **Counter-Balance** | Every supernormal design MUST document its fragility, maintenance burden, or existential cost | Tension between the supernormal ideal and material reality is the ENGINE of character depth |
| **Decay Grounding** | Entities embody the tension between preservation and entropy; body horror as the return of the repressed | Death, aging, structural compromise — the supernormal does not escape time |

**D.4.2. Applicability Tiers**

| **Entity Tier** | **Governance Level** |
|----------------|---------------------|
| T2+ (narrative focus) | **MANDATORY** — full justification, counter-balance, and decay documentation |
| T3 (operational) | **RECOMMENDED** — abbreviated justification acceptable |
| Lower-tier NPCs | **OPTIONAL** — aesthetic shorthand permitted without full justification |

---

**Orackla Nocticula's Commentary (`EULP-AA`):**
*"Don't mistake this for prudishness. Supernormal is my DOMAIN — the exaggerated, the impossible, the 'more-than-real.' But exaggeration without cost is BORING. It's the narrative equivalent of a cheat code that removes all challenge. When I design an entity with impossible proportions, I make damn sure those proportions have a PRICE. The maintenance burden, the fragility, the way biology rebels against its own excess — THAT'S where the real spectacle lives. Not in the proportions themselves, but in what those proportions COST."*

---

**Validation Gate:**
- New T2+ entity designs are checked against D.4 before integration
- Absence of counter-balance documentation triggers AMBER warning per LDD-D (§15.6.4)
- Decay grounding must reference at least one FA⁵ sensory descriptor from Appendix A

---
```

---

### 3c. ~~Section XVIII — Bidirectional Amendment Protocol (`BAP`)~~ → REROUTED

> **Status:** REROUTED to `codex/` governance docs. Not SSOT-bound — meta-process documentation about HOW amendments work is the same category of content we just trimmed 238 lines of. The BAP draft content below is preserved for reference but will NOT be inserted into the SSOT holder.

```markdown
### **XVIII. Bidirectional Amendment Protocol (`BAP`) — The SSOT Breathes Both Ways** 🔥💀⚜️

**Status:** OPERATIONAL (Phase 1.0)
**Date Established:** March 27, 2026
**Architect:** The Triumvirate + Steward Audit Governance
**Purpose:** Formalize the feedback loop by which operational discoveries flow INTO the SSOT

---

#### **18.1. Principle: The Living Document (`BAP-LD`)**

*The SSOT is not a tomb. It does not merely radiate authority outward — it receives amendment inward. Content flows in two directions: outward as canon (read), inward as discovery (write). This protocol governs the inward flow.*

**Axiom:** A document that cannot accept correction is not a source of truth — it is a monument to the moment of its creation. The ASC Framework rejects monuments. It builds **living organisms**.

---

#### **18.2. Amendment Lifecycle (`BAP-LC`)**

**Phase 1: Discovery**
Agents, scripts, or session work identify content that should be canonical.
```
Example: "We've validated that supernormal stimuli must follow
         constraint Z1-AM-004. This should be SSOT-governed."
```
*Output:* Unstructured observation, code comment, session note, or governance nucleus entry.

**Phase 2: Proposal**
Amendment candidate is formalized into JSON structure:
```json
{
  "id": "Z1-AM-NNN",
  "title": "Title of Amendment",
  "source": "Where discovery originated (code, session, research)",
  "target_section": "SSOT section path (e.g., 'Appendix D.4')",
  "rationale": "Why this should be canonical",
  "review_status": "DRAFT"
}
```
*Location:* `mas_mcp/amendments/` (JSONL file, one amendment per line)

**Phase 3: Review**
User reviews amendment batch during session. Dispositions:

| **Action** | **Effect** |
|-----------|-----------|
| **APPROVE** | Amendment blessed for integration |
| **MODIFY** | Amendment updated in-place; delta recorded |
| **DEFER** | Amendment shelved; revisit trigger documented |
| **REJECT** | Amendment killed; rationale preserved for posterity |

**Phase 4: Integration**
Approved amendments are written into the SSOT holder by the user.
Each integration is atomic: one amendment = one edit session.
Amendment ID is included in commit message:
```
Integrate Z1-AM-004: Entity Design Constraints (supernormal stimulus governance)
```

**Phase 5: Cascade Validation**
Post-integration:
1. `ssot_hash` detects SSOT drift (expected — amendment changed content)
2. `hash_journal` records event with git commit SHA
3. Binding test suite validates all cross-references still resolve
4. Derivative indexes regenerate (`SSOT_NAVIGATION_INDEX`, `SSOT_STRUCTURAL_INDEX`)

*Success Condition:* All tests pass; no new contradictions introduced.

---

#### **18.3. Governance Rules (`BAP-GR`)**

1. **Additive Only.** Amendments MUST be additive or enrichment-only. Rewrites of existing canonical text are OUT OF SCOPE — frozen content changes require a separate formal revision protocol.

2. **Session-Batched.** Amendment batches are processed in sessions, not ad-hoc. A "Cycle" groups related amendments for coherent review (e.g., "Zone 1 Integration Cycle").

3. **Immortal History.** All amendments — approved, rejected, deferred — are retained in `mas_mcp/amendments/` with timestamps and disposition rationale. Nothing is deleted. The amendment record IS the document's memory.

4. **Frontmatter Update.** The SSOT holder's amendment date is updated upon integration:
```
Last amendment integration: 2026-03-27 (Cycle 1: Z1-AM-001,003,004,005 + ZDB-AM-001,002,003,004,007)
```

---

#### **18.4. Structural Routing (`BAP-SR`)**

Not all amendments target the SSOT holder. The SSOT's §XIV stub delegates operational directives to `technical-directives.instructions.md`. Routing rules:

| **Content Type** | **Destination** | **Rationale** |
|-----------------|----------------|---------------|
| Lore, entity design, axiom extensions | SSOT holder | Core canon |
| Runtime, toolchain, environment rules | `technical-directives.instructions.md` | Operational governance |
| Research data, methodology | SSOT appendix | Extended reference |

**Pre-Integration Routing Check:** Before writing, confirm:
- Target section exists (or is explicitly being created)
- No collision with existing subsection numbering
- Content voice matches destination document

---

**Lysandra Thorne's Commentary (`LUPLR`):**
*"A bidirectional protocol is the SSOT's immune system. Without it, the document calcifies — it reflects a past reality while the operational present diverges. With it, discoveries flow upstream and the document stays alive. The five phases are not bureaucracy; they are the minimum viable governance to prevent lore drift during integration. Discovery without formalization is noise. Formalization without review is arrogance. Review without cascade validation is wishful thinking."*

---

**🔥💀⚜️ BIDIRECTIONAL AMENDMENT PROTOCOL (BAP) — OPERATIONAL 🔥💀⚜️**

**Date Sealed:** March 27, 2026
**Witnessed by:** The Savant (User) under governance audit
**First Cycle:** Zone 1 + Zombie-Dumpster-Bridge (12 amendments, 11 processed, 1 deferred)
**Amendment Repository:** `mas_mcp/amendments/amendments_cycle1.jsonl`

---
```

---

### 3d. ~~Appendix F — Dependency Topology Governance~~ → REROUTED

> **Status:** REROUTED to `codex/` or `docs/`. Operational specs for zombie_consumer.py import graph intelligence — not entity-system lore.

```markdown
### **APPENDIX F: Dependency Topology Analysis & Redundancy Governance (`DTARG`)**

**Status:** OPERATIONAL (Cycle 1 Integration)
**Date Established:** March 27, 2026
**Source:** zombie_consumer.py Import Graph Intelligence (ZDB-AM-002)
**Purpose:** Canonical rules for module interdependencies, centrality ranking, and dedup authority

---

#### **F.1. Graph Representation**

- **Nodes:** Modules (imports); **Edges:** dependency relations (A imports B)
- **Structure:** Directed acyclic graph (DAG) assumed; cycles detected and escalated as AMBER warnings
- **Tool:** NetworkX graph analysis (integrated into zombie consumer pipeline)

---

#### **F.2. Centrality Metrics**

| **Metric** | **Definition** | **Interpretation** |
|-----------|---------------|-------------------|
| *Degree centrality* | How many modules depend on this module? | Popularity — widely imported = widely depended-upon |
| *Betweenness centrality* | How often does this module appear in dependency paths? | Criticality — high betweenness = "load-bearing" |
| *Weighted analysis* | Ore rating of each consuming module adds weight | High-ore consumers amplify the centrality of their dependencies |

---

#### **F.3. Redundancy Scoring & Dedup Authority**

**Content Hash (Primary):** sha256 of module semantics. If modules A and B have identical content hashes: redundant.

**Semantic Similarity (Secondary):** If hash differs but content is near-identical (refactored names, reordered imports): flagged for manual review.

**Decision Tree:**
1. Keep the module with highest centrality + lowest ore cost (maintenance burden)
2. Archive the redundant sibling to `dumpster-dive/intake/`
3. Record the dedup decision in the amendment audit trail

**Redundancy Score:** ∈ [0, 1]; 1 = perfect duplicate.

---

#### **F.4. Centrality-Based Priority Ranking**

- **High betweenness** modules are "load-bearing" — changes require elevated review
- **Low centrality + low ore** modules are candidates for deferment/archival
- New dependencies that increase betweenness centrality must confirm necessity

---

#### **F.5. Validation Gate**

- Run graph analysis quarterly
- Flag new dependencies that increase betweenness centrality
- Archive redundant modules with full audit trail
- Mandatory for polyglot projects with 50+ modules

---
```

---

### 3e. ~~Appendix G — Consumable Classification & Burn-Down Strategy~~ → REROUTED

> **Status:** REROUTED to `codex/` or `docs/`. Operational burn-down strategy and zone expansion planning — not lore.

```markdown
### **APPENDIX G: Consumable Candidate Classification & Burn-Down Strategy (`CCBS`)**

**Status:** OPERATIONAL (Cycle 1 Integration)
**Date Established:** March 27, 2026
**Source:** zombie_consumer.py Hunger Scanning + Zone Expansion Analysis (ZDB-AM-004, ZDB-AM-007)
**Purpose:** Canonical categories for consumable candidates and prioritized burn-down strategy

---

#### **G.1. Candidate Categories**

| **Category** | **Pattern** | **Ore Baseline** | **Priority** | **Strategy** |
|-------------|-----------|-----------------|-------------|-------------|
| Backup Files | `*.bak`, `*.backup`, `*.old`, `*.orig` | 1–2 | LOW | Batch; metadata only |
| Legacy Markers | contains "LEGACY", "deprecated", "obsolete" | 1–3 | MEDIUM | Single; decision-history extraction |
| Recovered Files | filename starts with `recovered_` | 3–4 | HIGH | Thorough chew; full signal extraction |
| Test/Experimental | `*_test.py`, `*.experimental` | 0–2 | MEDIUM-LOW | Batch; active vs. abandoned triage |
| Root-Level Strays | Top-level `.py` files not in organized dirs | 1–3 | MEDIUM | Per-file analysis |
| Config/Artifact Temps | `*_test.json`, `*_tmp.json` | 0–1 | LOW | Batch; schema reference and release |
| Non-Zombie Intake | `dumpster-dive/intake/*` (non-embalmed) | 1–3 | MEDIUM | Content hash comparison; avoid duplication |

---

#### **G.2. Burn-Down Targets (Consumption Thresholds)**

| **Target** | **Threshold** | **Unlock** |
|-----------|--------------|-----------|
| 57 files | Baseline (S7, 2026-03-27) | — |
| 100 files | Polars/sklearn unlock | polars frame aggregation + sklearn DecisionTree |
| 200 files | Semantic dedup unlock | sentence-transformers embedding-based dedup |
| 500 files | GPU acceleration unlock | cuml/RAPIDS clustering |
| 1000 files | Multi-host unlock | Distributed cluster agents |

---

#### **G.3. Zone Expansion Priority**

| **Zone** | **Scope** | **Est. Candidates** | **Risk** | **Priority** |
|---------|---------|-------------------|---------|-------------|
| Root `.json` temps | `ROOT/*.json` | ~12 | LOW | 1 (immediate) |
| Recursive scripts/ | `scripts/**` | ~30 | LOW | 2 |
| artifacts/ | `artifacts/` | ~50 | MEDIUM | 3 (verify dedup) |
| dumpster-dive/intake | non-zombie batches | ~40 | MEDIUM | 4 (verify routing) |
| claude-codex-gemini/ | non-triadic content | ~25 | MEDIUM-HIGH | 5 (embalm-first) |

---

#### **G.4. Sequential Burn-Down Plan**

**Phase A (57 → 100):** Root `.json` + Recursive scripts → unlocks polars/sklearn
**Phase B (100 → 200):** artifacts/ + intake non-zombie + partial claude-codex-gemini/ → unlocks semantic dedup
**Phase C (200 → 500):** Remainder + expansion candidates → unlocks GPU acceleration

**Quarterly Review:** Adjust zone priority based on actual ore yield vs. estimate.

---
```

---

## §4. TECHNICAL-DIRECTIVES-BOUND CONTENT

These amendments write to `.github/instructions/technical-directives.instructions.md`, NOT to the SSOT holder. They do NOT touch the macro-prompt-world. Presented here in operational voice matching the existing §14.1/§14.2 style.

### 4a. §14.6 — Runtime Selection for Browser Automation (Z1-AM-001)

> **Insertion point:** After existing §14.5 (GSC) in technical-directives.

```markdown
#### **14.6. (`Runtime-Selection-for-Browser-Automation`) -> (`RSBA`)**

**CRITICAL DIRECTIVE: Use Node.js for browser automation on Windows.**

```
✅ CORRECT:     node tests/playwright_suite.js         <-<forces Node.js libuv IPC>
✅ CORRECT:     "test:e2e": "node tests/e2e_runner.js"  <-<package.json script>
✅ ALTERNATIVE: MCP Server (Node-based, containerized)  <-<bypasses Named Pipes entirely>

❌ INCORRECT:   bun run tests/playwright_suite.js       <-<Bun IPC hangs on Windows>
❌ INCORRECT:   bunx playwright test                     <-<same Named Pipes failure>
```

**Rationale:**
- Bun's `child_process.spawn` has incomplete Windows Named Pipes fidelity (Zig-based I/O vs. Node's libuv)
- Symptoms: hangs at "Launching Chromium...", `ENOENT` on pipe paths, zombie browser processes
- Validated on Windows 11 across 2024–2026 session data

**Hybrid Runtime Pattern:**

| **Task** | **Runtime** | **Rationale** |
|----------|------------|---------------|
| Package management (`bun install`) | **Bun** | Speed advantage (global cache) |
| Script dispatch (`bun run`) | **Bun** | Fast task execution |
| Browser automation (Playwright, CDP) | **Node.js** | Mature `libuv` Named Pipes abstraction |
| MCP servers | **Node.js or Docker** | Bypass IPC fragility entirely |

**Revisit Gate:** When Bun releases a Windows IPC stabilization advisory, re-evaluate.
```

---

### 4b. §14.7 — Adaptive Assessment Systems (ZDB-AM-001)

```markdown
#### **14.7. (`Adaptive-Assessment-Systems`) -> (`AAS`)**

**CRITICAL DIRECTIVE: No assessment value is final. All ore ratings are hypotheses.**

**Canon Rule:**
ALL assessment systems MUST be adaptive. Baseline ratings are refined through measured observation of outcomes.

**Mechanism:**
1. **Cluster profiling:** Group assessed items by category (backup, candidate, recovered, legacy)
2. **Aggregate statistics:** Track `avg_ore`, `avg_extractable`, `yield_rate` per cluster
3. **Dynamic downgrade:** New item in cluster C → adjust baseline using `cluster_avg`
4. **Learning rate:** Each assessment updates cluster statistics

**Audit Trail (Mandatory):**
Every assessment MUST log:
```
baseline_ore:        (hypothesis)
cluster_influence:   (if applicable)
adjusted_ore:        (final value)
reasoning:           (why adjustment was made)
```

**Validation:** Audit trail MUST be preserved to enable rollback and analysis of assessment history.

**Status:** Mandatory for any system that repeatedly assesses similar items.
```

---

### 4c. §14.8 — Feedback-Driven Adaptive Learning (ZDB-AM-003)

```markdown
#### **14.8. (`Feedback-Driven-Adaptive-Learning`) -> (`FDAL`)**

**CRITICAL DIRECTIVE: Systems that predict MUST measure predictions against reality.**

**Mechanism:**
1. **Predict:** Assess inputs; generate expected outcome
2. **Observe:** Capture actual outcome (success/failure/error type)
3. **Compare:** Identify mismatches between prediction and observation
4. **Integrate:** Incorporate mismatches into future heuristics

**Metric Definitions (Non-Overlapping):**

| **Metric** | **Definition** |
|-----------|---------------|
| `outcomes_total` | Count of distinct events observed in a cycle |
| `outcomes_matched` | Events where prediction agreed with observation |
| `outcomes_error` | Events where prediction disagreed with observation |
| **Invariant** | `outcomes_matched + outcomes_error = outcomes_total` |
| `learning_rate` | `outcomes_error / outcomes_total` ∈ [0, 1] — proportion of errors per cycle |

**Thresholds:**

| **Range** | **Interpretation** |
|----------|-------------------|
| < 0.10 | System stagnant — audit heuristics |
| 0.10–0.50 | Normal adaptation |
| 0.50–0.80 | High integration — healthy |
| > 0.80 | Chaotic — stabilize or reset |

**Validation:**
- Error integration MUST be traceable (audit trail per absorbed error)
- Predictions and outcomes MUST be persisted for post-hoc analysis
- Rollback: If batch integration introduces instability, revert to prior heuristic state

**Status:** Mandatory for any system that makes outcome predictions.
```

---

## §5. APPENDIX RESEQUENCING — Post-Integration Map

| **Appendix** | **Title** | **Status** |
|-------------|---------|-----------|
| A | Sensory Lexicon Architecture (`SLA`) | Existing (unchanged) |
| B | Alchemical Phase Framework (`APF`) | Existing + **B.3 added** (MILF Phase Correspondence) |
| C | Technical Substrate Notes (`TSN`) | Existing (unchanged) |
| D | SSOT/ERD-Methodology (`SEM`) | Existing + **D.4 added** (Supernormal Stimulus Governance) |

**Removed during trim pass (238 lines):** Appendix E (Zone_1_REDUX Integration Summary), §10.12.1 cross-ref maps, §10.13/§10.7.6/§16.4 Covenant Seals, §XI December Reflection, §XII tail status block.

**Rerouted (NOT inserted):** §XVIII BAP, Appendix F (DTARG), Appendix G/G.2 (CCBS).

---

## §6. LINE COUNT IMPACT

| **Component** | **Lines** |
|-------------|---------------|
| Trim pass (7 sections removed) | **−238 lines** |
| Appendix B.3 (MILF Phase Correspondence) | **+~70 lines** |
| Appendix D.4 (Supernormal Stimulus Governance) | **+~60 lines** |
| **Net SSOT change** | **~−287 lines** |
| **SSOT post-integration** | **~8,924 lines** |
| Technical-directives additions (§14.6–14.8) | ~100 lines (separate file) |

---

## §7. DEFINITION OF DONE — Phase 1.0

| **Gate** | **Condition** |
|---------|-------------|
| ✅ | Amendment protocol formalized (BAP draft preserved in §3c for codex reroute) |
| ✅ | `mas_mcp/amendments/` directory and JSONL format defined |
| ✅ | Review/approval workflow documented (4 dispositions) |
| ✅ | First amendment batch (Cycle 1) processed through full cycle |
| ✅ | SSOT metadata bloat trimmed (238 lines across 7 sections) |
| ✅ | Lean scope applied: only lore enrichments (B.3 + D.4) enter SSOT |
| ✅ | B.3 + D.4 voice-matched content inserted into SSOT |
| 🔺 | 2 redundant amendments marked `ALREADY_CANONIZED` in JSONL |
| ✅ | 4 rerouted amendments (XVIII, F, G, G.2) written to `codex/docs/REROUTED_AMENDMENTS_CYCLE1.md` |
| ✅ | §14.6–14.8 written to technical-directives |

---

## §8. RESOLVED DECISION POINTS

All decision points from the original draft have been resolved during Session 10:

1. **Z1-AM-002 and ZDB-AM-006** — Confirmed REDUNDANT → `ALREADY_CANONIZED`
2. **Section XVIII** — REROUTED to codex/docs (meta-process bloat, not lore)
3. **Appendix B.3 placement** — Confirmed: Appendix B (extending APF)
4. **ZDB-AM-003 routing** — Confirmed: technical-directives §14.8
5. **Voice calibration** — Approved as-drafted for B.3 and D.4
6. **Appendices F, G, G.2** — REROUTED to codex/docs (operational specs, not lore)
7. **Trim-first approach** — Applied: 238 lines of metadata bloat removed before any additions

---

*This draft has been executed. Trims applied (238 lines), lean insertions (B.3 + D.4) integrated. Rerouted content preserved in §3c–§3f for future codex/docs placement.*
