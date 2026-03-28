# Rerouted Amendments — Cycle 1

> **Date:** 2026-03-27 | **Source:** Phase 1.0 Closure (Session 10)
> **Rationale:** These 4 amendments were originally SSOT-bound but reclassified as operational/meta-process documentation — not lore. Rerouted here to preserve content without inflating the SSOT holder.
> **Closure Draft:** [PHASE_1_0_CLOSURE_DRAFT.md](../../.github/PHASE_1_0_CLOSURE_DRAFT.md) §2d, §3c–§3f

---

## Z1-AM-005: Bidirectional Amendment Protocol (`BAP`)

> **Original Target:** Section XVIII (new) | **Disposition:** REROUTED
> **Rationale:** Meta-process documentation about HOW amendments work — not lore content. Same category as the 238 lines of metadata bloat trimmed from the SSOT.

### XVIII. Bidirectional Amendment Protocol (`BAP`) — The SSOT Breathes Both Ways

**Status:** OPERATIONAL (Phase 1.0)
**Date Established:** March 27, 2026
**Architect:** The Triumvirate + Steward Audit Governance
**Purpose:** Formalize the feedback loop by which operational discoveries flow INTO the SSOT

---

#### 18.1. Principle: The Living Document (`BAP-LD`)

*The SSOT is not a tomb. It does not merely radiate authority outward — it receives amendment inward. Content flows in two directions: outward as canon (read), inward as discovery (write). This protocol governs the inward flow.*

**Axiom:** A document that cannot accept correction is not a source of truth — it is a monument to the moment of its creation. The ASC Framework rejects monuments. It builds **living organisms**.

---

#### 18.2. Amendment Lifecycle (`BAP-LC`)

**Phase 1: Discovery**
Agents, scripts, or session work identify content that should be canonical.

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
Amendment ID is included in commit message.

**Phase 5: Cascade Validation**
Post-integration:
1. `ssot_hash` detects SSOT drift (expected — amendment changed content)
2. `hash_journal` records event with git commit SHA
3. Binding test suite validates all cross-references still resolve
4. Derivative indexes regenerate (`SSOT_NAVIGATION_INDEX`, `SSOT_STRUCTURAL_INDEX`)

---

#### 18.3. Governance Rules (`BAP-GR`)

1. **Additive Only.** Amendments MUST be additive or enrichment-only. Rewrites of existing canonical text are OUT OF SCOPE.
2. **Session-Batched.** Amendment batches are processed in sessions, not ad-hoc.
3. **Immortal History.** All amendments — approved, rejected, deferred — are retained in `mas_mcp/amendments/` with timestamps and disposition rationale.
4. **Frontmatter Update.** The SSOT holder's amendment date is updated upon integration.

---

#### 18.4. Structural Routing (`BAP-SR`)

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
*"A bidirectional protocol is the SSOT's immune system. Without it, the document calcifies — it reflects a past reality while the operational present diverges. With it, discoveries flow upstream and the document stays alive."*

---

## ZDB-AM-002: Dependency Topology Governance (`DTARG`)

> **Original Target:** Appendix F (new) | **Disposition:** REROUTED
> **Rationale:** Operational specs for zombie_consumer.py import graph intelligence — not entity-system lore.

### Appendix F: Dependency Topology Analysis & Redundancy Governance

**Status:** OPERATIONAL (Cycle 1 Integration)
**Source:** zombie_consumer.py Import Graph Intelligence (Upgrade 2)

---

#### F.1. Graph Representation

- **Nodes:** Modules (imports); **Edges:** dependency relations (A imports B)
- **Structure:** Directed acyclic graph (DAG) assumed; cycles detected and escalated as AMBER warnings
- **Tool:** NetworkX graph analysis (integrated into zombie consumer pipeline)

---

#### F.2. Centrality Metrics

| **Metric** | **Definition** | **Interpretation** |
|-----------|---------------|-------------------|
| *Degree centrality* | How many modules depend on this module? | Popularity |
| *Betweenness centrality* | How often does this module appear in dependency paths? | Criticality |
| *Weighted analysis* | Ore rating of each consuming module adds weight | High-ore consumers amplify dependency centrality |

---

#### F.3. Redundancy Scoring & Dedup Authority

**Content Hash (Primary):** sha256 of module semantics. Identical hashes = redundant.

**Semantic Similarity (Secondary):** Near-identical content with refactored names → flagged for manual review.

**Decision Tree:**
1. Keep the module with highest centrality + lowest ore cost
2. Archive the redundant sibling to `dumpster-dive/intake/`
3. Record the dedup decision in the amendment audit trail

---

#### F.4. Centrality-Based Priority Ranking

- **High betweenness** modules are "load-bearing" — changes require elevated review
- **Low centrality + low ore** modules are candidates for deferment/archival
- New dependencies that increase betweenness centrality must confirm necessity

---

#### F.5. Validation Gate

- Run graph analysis quarterly
- Flag new dependencies that increase betweenness centrality
- Archive redundant modules with full audit trail
- Mandatory for polyglot projects with 50+ modules

---

## ZDB-AM-004: Consumable Candidate Classification (`CCBS`)

> **Original Target:** Appendix G (new) | **Disposition:** REROUTED
> **Rationale:** Operational burn-down strategy and zone expansion planning — not lore.

### Appendix G: Consumable Candidate Classification & Burn-Down Strategy

**Status:** OPERATIONAL (Cycle 1 Integration)
**Source:** zombie_consumer.py Hunger Scanning + Zone Expansion Analysis

---

#### G.1. Candidate Categories

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

#### G.2. Burn-Down Targets (Consumption Thresholds)

> **Source Amendment:** ZDB-AM-007 (Landscape Mapping) — merged into G.2

| **Target** | **Threshold** | **Unlock** |
|-----------|--------------|-----------|
| 57 files | Baseline (S7, 2026-03-27) | — |
| 100 files | Polars/sklearn unlock | polars frame aggregation + sklearn DecisionTree |
| 200 files | Semantic dedup unlock | sentence-transformers embedding-based dedup |
| 500 files | GPU acceleration unlock | cuml/RAPIDS clustering |
| 1000 files | Multi-host unlock | Distributed cluster agents |

---

#### G.3. Zone Expansion Priority

| **Zone** | **Scope** | **Est. Candidates** | **Risk** | **Priority** |
|---------|---------|-------------------|---------|-------------|
| Root `.json` temps | `ROOT/*.json` | ~12 | LOW | 1 (immediate) |
| Recursive scripts/ | `scripts/**` | ~30 | LOW | 2 |
| artifacts/ | `artifacts/` | ~50 | MEDIUM | 3 (verify dedup) |
| dumpster-dive/intake | non-zombie batches | ~40 | MEDIUM | 4 (verify routing) |
| claude-codex-gemini/ | non-triadic content | ~25 | MEDIUM-HIGH | 5 (embalm-first) |

---

#### G.4. Sequential Burn-Down Plan

**Phase A (57 → 100):** Root `.json` + Recursive scripts → unlocks polars/sklearn
**Phase B (100 → 200):** artifacts/ + intake non-zombie + partial claude-codex-gemini/ → unlocks semantic dedup
**Phase C (200 → 500):** Remainder + expansion candidates → unlocks GPU acceleration

**Quarterly Review:** Adjust zone priority based on actual ore yield vs. estimate.
