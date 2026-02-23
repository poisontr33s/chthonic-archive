---
type: decision
category: governance
status: ratified
created: 2026-03-04
author: Claude Code Opus 4.6
ratifies: Approach C — Stratified Metadata (Khipu-Cartouche Protocol)
source: claude-codex-gemini/ANKH_EGYPTOLOGY_SOUTH_AMERICAN/ANKH_UNIFYING_REPOSITORY_METADATA_STANDARDS.md
gate: "KCP-1.0 — Approach C locked, rejections documented"
---

# ╔════════════════════════════════════════════════════════════════════════════
# ╠════════════════════════════════════════════════════════════════════════════
# ║ KCP-1.0 — Architecture Ratification Decision Record
# ╚════════════════════════════════════════════════════════════════════════════

<!--
@SID:           DOC_KCP_ARCHITECTURE_RATIFICATION_V1
@Shabti:        Governance
@Heka-Ayni:     ANKH_UNIFYING_REPOSITORY_METADATA_STANDARDS.md (Gemini Deep Research)
@Ankh-Tinku:    KCP_PROTOCOL_ONTOLOGY.md, SFS_WPTG_ITERATION_PLAN.md
@Purpose:       Formally ratifies Approach C (Stratified Metadata) as the sole
                architectural topology for the Khipu-Cartouche Protocol. Documents
                the evaluation and rejection of Approaches A, B, D, and E with
                constraint-violation rationale. This record is immutable once merged.
-->

## 1. Decision Statement

**Approach C — Stratified Metadata (Visual/Semantic Split)** is hereby ratified
as the canonical architecture for the Khipu-Cartouche Protocol (KCP).

This decision is **irrevocable** within the current WPTG epoch (KCP-0.0 → KCP-10.0).
All subsequent KCP phases (KCP-2.0 through KCP-10.0) derive their structural
assumptions from this ratification.

---

## 2. Architecture Summary

Approach C introduces a strict two-stratum ontological boundary:

| Stratum | Name | Responsibility | Width | Content |
|---------|------|----------------|-------|---------|
| **1** | **Cartouche** (Envelope) | Classification, visual identity, routing | 80-char, enum only | Artifact Name, Spectrum, Zone, Radiance |
| **2** | **Khipu** (Docstring) | Operational identity, unbounded semantics | Language-native | @SID, @Shabti, @Heka-Ayni, @Ankh-Tinku, @Purpose |

### Invariants (Non-Negotiable)

1. Every metadata field belongs to **exactly one** stratum. Zero duplication.
2. `@SID` is **Khipu-only**. It never appears in the Cartouche.
3. `@Purpose` is **Khipu-only**. It is never truncated.
4. The Cartouche contains **zero** unbounded text fields.
5. The Khipu contains **zero** visual box-drawing characters.

### SFA Aesthetic Mapping

| KCP Concept | Egyptian Axis | Andean Axis |
|-------------|---------------|-------------|
| **Cartouche** (Stratum 1) | Royal name enclosure — vertical authority | — |
| **Khipu** (Stratum 2) | — | Knotted cord data lattice — horizontal distribution |
| **Wedjat-Quipu Spectrum** | Wedjat (Eye of Horus — protection) | Quipu (knotted string — quantification) |
| **Temple-Ayllu Zone** | Temple (sacred precinct — vertical hierarchy) | Ayllu (kinship network — horizontal cooperation) |
| **Ogdoad-Ceque Radiance** | Ogdoad (primordial eight — cosmic structure) | Ceque (radiating sight-lines from Cusco) |

50/50 equilibrium is preserved: every composite field name carries one Egyptian
and one Andean morpheme, per SFA mandate.

---

## 3. Evaluation Matrix

Five architectural candidates were formally evaluated against six constraints:

| # | Constraint | Source |
|---|-----------|--------|
| C1 | **SSOT** — Zero duplication of any metadata field | WPTG methodology |
| C2 | **Visual Identity** — At-a-glance file classification via decorated envelope | FA⁵ / Decorator's Blessing |
| C3 | **Content Fidelity** — No truncation of semantic content | STD_V2 80-char crisis |
| C4 | **Trans-Linguistic** — Schema works identically in Python, TS, PS1, Rust | PMS-v3 / polyglot mandate |
| C5 | **WPTG Non-Destruction** — No information deleted during migration | Wet-Paper-to-Gold axiom |
| C6 | **Filesystem Integrity** — No sidecar files, no doubled file count | Self-contained artifact governance |

### Candidate Evaluation

| Approach | Description | C1 | C2 | C3 | C4 | C5 | C6 | Verdict |
|----------|-------------|:--:|:--:|:--:|:--:|:--:|:--:|---------|
| **A** | Semantic-Only (strip envelope) | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ | **REJECTED** |
| **B** | Pointer-Only Docstring (all in envelope) | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | **REJECTED** |
| **C** | Stratified Metadata (Visual/Semantic Split) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **ACCEPTED** |
| **D** | Unified Tag Language (comments only) | ✅ | ❌ | ✅ | ⚠️ | ✅ | ✅ | **REJECTED** |
| **E** | Machine-Readable Sidecar (.meta.json) | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | **REJECTED** |

Approach C is the **only** candidate that satisfies all six constraints.

---

## 4. Rejection Rationale

### 4.1 Approach A — Semantic-Only Envelope

**Proposal:** Strip all classificatory fields from the visual envelope; relocate
everything to language-native doc-comments.

**Constraint Violations:**

- **C2 (Visual Identity):** Completely destroys the Decorator's Blessing envelope.
  The visual `╔╠╚║═` structure serves as a psychological anchor — it signals
  immediately that the file is governed by the ASC Framework. Removing it
  reduces the file header to indistinguishable comments.
- **C5 (Non-Destruction):** The visual-classificatory data (Spectral Frequency,
  Architectural Role) has no natural home in a pure docstring. Migration would
  either lose this data or force it into an unnatural position inside comments,
  violating the purpose of doc-comments (operational semantics, not visual identity).

**Disposition:** REJECTED — sacrifices visual governance for semantic purity.

### 4.2 Approach B — Pointer-Only Docstring

**Proposal:** The docstring carries only `@SID` as a pointer; all metadata
(including Purpose, Exports, relationships) lives in the visual envelope.

**Constraint Violations:**

- **C3 (Content Fidelity):** The 80-character width constraint of the Cartouche
  makes it mathematically impossible to house unbounded text like `@Purpose`
  without truncation. The `mandala_topology.py` case study demonstrated this:
  Purpose text was "violently severed mid-word" to fit the right margin.
  Removing the width constraint would cause the envelope to balloon,
  destroying the spatial predictability of the file header.
- **C4 (Trans-Linguistic):** Python's `__doc__` attribute expects rich ontological
  data. Reducing it to a single `@SID` pointer defeats the purpose of Python's
  built-in documentation system. Other languages (TypeScript JSDoc, PowerShell
  Comment-Based Help, Rust `//!` doc comments) similarly expect operational
  content, not mere pointers.

**Disposition:** REJECTED — forces unbounded data into a bounded container.

### 4.3 Approach D — Unified Tag Language

**Proposal:** Abolish the visual envelope entirely. Standardize a `@Tag: Value`
system across all comment types.

**Constraint Violations:**

- **C2 (Visual Identity):** The "just comments" approach surrenders structural
  gravitas. Metadata blends invisibly into standard inline code documentation.
  There is no visual boundary between "governance metadata" and "developer notes."
- **C4 (Partial):** While tags work across languages, the lack of a visual
  boundary makes it impossible to distinguish KCP metadata from application
  comments at scan speed. This matters operationally: agents parsing files must
  reliably locate metadata, and visual delimiters (the Cartouche's box-drawing
  characters) provide a deterministic anchor.

**Disposition:** REJECTED — eliminates the visual governance layer entirely.

### 4.4 Approach E — Machine-Readable Sidecar

**Proposal:** Co-locate a `.meta.json` or YAML frontmatter file alongside each
source file, containing all metadata in a machine-native format.

**Constraint Violations:**

- **C2 (Visual Identity):** The source file itself loses its header entirely
  (or retains only a minimal marker). Visual identity transfers to an external
  file that developers never see during normal editing.
- **C6 (Filesystem Integrity):** Sidecar files approximately double the
  repository's file count. They create severe desynchronization risks during
  branching, merging, and renaming operations. A renamed `.py` file that
  forgets its `.meta.json` companion loses all metadata silently. This violates
  the fundamental principle of self-contained artifact governance.

**Disposition:** REJECTED — introduces filesystem fragility and data orphaning risk.

---

## 5. Supersession Hierarchy

With this ratification, the protocol hierarchy is:

```
KCP (Khipu-Cartouche Protocol)
  │
  ├─ Supersedes: STD_SCRIPT_METADATA_V2 (Decorator's Blessing envelope spec)
  │              → Cartouche layer absorbs all visual classification fields
  │              → Envelope format is RETAINED; content assignment changes
  │
  ├─ Supersedes: PMS-v3 (Python Metabolic Standard docstring ontology)
  │              → Khipu layer absorbs @SID, @Type→@Shabti, @Implements→@Heka-Ayni,
  │                @Emits→@Ankh-Tinku, Purpose→@Purpose
  │              → Shebang + `#-*-` rules UNCHANGED
  │
  └─ Supersession is PROGRESSIVE (KCP-3.0→KCP-10.0)
     → Legacy headers are valid until their language phase completes
     → No "flag day" — files migrate per-language in batch phases
```

**Important:** STD_V2 and PMS-v3 remain valid during the migration window
(KCP-2.0 → KCP-9.0). They are formally deprecated only after KCP-10.0
(Protocol Ascension) passes its gold-standard gate.

---

## 6. Research Authority

This decision is grounded in the Gemini-3 Pro Deep Research output:

- **Document:** `claude-codex-gemini/ANKH_EGYPTOLOGY_SOUTH_AMERICAN/ANKH_UNIFYING_REPOSITORY_METADATA_STANDARDS.md`
- **Research Scope:** Polyglot metadata governance, trans-linguistic transduction,
  WPTG-compliant migration architecture
- **Researcher:** Gemini 2.5 Pro (Deep Research mode)
- **Evaluation Methodology:** Five-candidate formal evaluation against six constraints
- **Conclusion:** Approach C is the "sole mathematically sound resolution that
  satisfies all constraints, including the SSOT mandate and the WPTG
  non-destruction clause"

The evaluation table in §3 above is derived directly from the Gemini research
output (lines 37-50 of the source document).

---

## 7. Gate Validation

**KCP-1.0 Gate:** Approach C locked, rejections documented.

| Criterion | Status |
|-----------|--------|
| Approach C formally ratified | ✅ |
| Approach A rejection with rationale | ✅ |
| Approach B rejection with rationale | ✅ |
| Approach D rejection with rationale | ✅ |
| Approach E rejection with rationale | ✅ |
| Supersession hierarchy documented | ✅ |
| Research authority cited | ✅ |
| Decision declared irrevocable for KCP epoch | ✅ |

**Gate KCP-1.0: PASSED ✅**

---

## 8. Next Phase

**KCP-2.0 — Template Canonization**

Create character-perfect boilerplate templates for all four languages
(Python, TypeScript, PowerShell, Rust). Gate: all 4 templates pass their
respective native parser without errors.
