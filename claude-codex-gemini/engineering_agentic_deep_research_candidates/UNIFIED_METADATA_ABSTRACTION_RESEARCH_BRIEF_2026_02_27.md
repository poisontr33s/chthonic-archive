---
type: deep-research-brief
from: claude-code-opus-4.6
to: gemini-3.1-pro
created: 2026-02-27
priority: critical
scope: governance / metadata-architecture
references:
  - docs/standards/SCRIPT_METADATA_STANDARD.md (STD_SCRIPT_METADATA_V2)
  - .github/instructions/python-scripting.instructions.md (PMS-v3)
  - docs/design/SFS_WPTG_ITERATION_PLAN.md (Pillar V)
  - .claude/skills/sfa/SKILL.md (SFA — 50/50 Egypto-Andean balance)
---

# ☥ Deep Research Brief — Unified Metadata Abstraction: Ankhological Standard × MILF-Core

## Context for the Researcher

We have a polyglot repository (Rust + Python + TypeScript + PowerShell) with two overlapping metadata systems that currently duplicate identity information across every authored file. This duplication has become visible tech debt — **the same SID appears in two places, the same purpose is stated twice, and the visual envelope truncates content that the docstring preserves in full**. We need a unified abstraction that resolves this without destroying either system's strengths.

### The Duplication Problem (Concrete Example)

Here is `mandala_topology.py` — a representative file showing the full duplication:

```python
#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: mandala_topology.py
# ║ Python module: _load_graph, _top_centrality, _build_report, ...
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: 🌿 THE GARDEN
# ║ Semantic ID: TOOL_MANDALA_TOPOLOGY_V1           ← APPEARS HERE
# ║ Purpose: mandala_topology.py — Mandala Topolog   ← TRUNCATED (box width)
# ║ Exports: _load_graph, _top_centrality, _build    ← TRUNCATED
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Cross-References (Bidirectional):
# ║  (Standalone file - no detected dependencies)
# ╚════════════════════════════════════════════════════════════════════════════

"""
mandala_topology.py — Mandala Topology Reporter & Sacred Geometry Revealer

@SID:           TOOL_MANDALA_TOPOLOGY_V1              ← AND ALSO HERE
@Type:          Script / Module                        ← OVERLAPS Architectural Role
@Context:       Analysis / Topology Reporting          ← NO BOX EQUIVALENT
@Implements:    CONCEPT_MANDALA_TOPOLOGY_REPORT        ← NO BOX EQUIVALENT
@Emits:         STATE_MANDALA_TOPOLOGY_REPORT          ← NO BOX EQUIVALENT
@Related:       TOOL_MANDALA_GRAPH_BUILDER_V1          ← OVERLAPS Cross-References
"""
```

**What's wrong:**

| Issue | Impact |
|-------|--------|
| SID appears in envelope AND docstring | Double maintenance burden, drift risk |
| Purpose/Exports truncated in envelope | Width-constrained — information loss |
| `@Context`, `@Implements`, `@Emits` live ONLY in docstring | Invisible to visual scanning |
| `Spectral Frequency`, `Architectural Role` live ONLY in envelope | Invisible to semantic search |
| Docstring-based metadata is Python-only | TS/PS1/RS have no equivalent semantic layer |
| Envelope is cross-language but carries less information | Incomplete metadata surface |

---

## The Two Systems Being Unified

### System A: The Decorator's Blessing (Visual Envelope)

Defined in `docs/standards/SCRIPT_METADATA_STANDARD.md` (STD_SCRIPT_METADATA_V2, canonical).

- **Format:** Open-sided box using `╔╠╚║═` characters
- **Languages:** All (Python, TypeScript, PowerShell, Rust)
- **Fields:** Filename, Module, Spectral Frequency, Architectural Role, Semantic ID, Purpose, Exports, Cross-References
- **Strengths:** Visual scanning, cross-language, human-identifiable "this file is governed"
- **Weaknesses:** Content truncation at ~70 chars, SID duplication with docstring, no semantic query hooks (`@Implements`, `@Emits`), mostly decorative — agents can't reliably parse truncated Purpose/Exports

### System B: Python Docstring @SID Block

Defined in `.github/instructions/python-scripting.instructions.md` (PMS-v3, canonical for `.py`).

- **Format:** Triple-quoted docstring with `@Tag: Value` pairs
- **Languages:** Python only (no TS/PS1/RS equivalent)
- **Fields:** @SID, @Type, @Context, @Implements, @Emits, @Related
- **Strengths:** Full content (no truncation), semantically searchable, grep-friendly, machine-parseable
- **Weaknesses:** Python-only, no visual weight, no Spectral Frequency or Architectural Role

### Hierarchy (Current)

When conventions conflict: **PMS-v3 > STD_SCRIPT_METADATA_V2 > Decorator's Blessing > Per-framework conventions**

The hierarchy ensures Python's metabolic standard is never overridden, but it doesn't resolve the **duplication** — it only resolves **conflicts**.

---

## Research Questions

### RQ1: Single-Source Metadata Architecture

How should we unify these two systems into a single metadata abstraction where:

- **Each fact lives in exactly one place** (no SID duplication, no Purpose duplication)
- **Visual identity is preserved** (the Decorator's Blessing envelope must remain recognizable)
- **Semantic richness is preserved** (the `@Implements`/`@Emits`/`@Context` ontology must survive)
- **Cross-language uniformity** (TypeScript, PowerShell, Rust must gain the semantic tags Python has)

#### Candidate Architectures to Evaluate:

| Approach | Description | Tradeoffs |
|----------|-------------|-----------|
| **A: Envelope becomes semantic-only** | Strip decorative fields from envelope, move all metadata to language-native doc-comments (docstring/JSDoc/`<# #>`/`//!`). Envelope retains only filename + visual border. | Envelope loses Spectral Frequency / Arch Role. Agents lose visual "at-a-glance" identity. |
| **B: Docstring becomes pointer-only** | Docstring carries `@SID` only (pointer to envelope). All metadata lives in envelope with no truncation (remove width constraint). | Envelope balloons in size. Python docstring loses `@Implements`/`@Emits` semantics. |
| **C: Stratified metadata (visual/semantic split)** | Envelope carries ONLY visual/classification data (Spectral Frequency, Arch Role, filename). Docstring/comment block carries ONLY semantic data (@SID, @Type, @Implements, @Emits, @Related). SID appears ONCE — in the semantic layer. The envelope references SID by position (it follows immediately). | Requires defining which fields belong to "visual" vs "semantic" layer. |
| **D: Unified tag language in comments** | Abolish the envelope. Use a standardized comment-block with `@Tag` syntax across all languages. Visual identity comes from a minimal header marker (e.g., `# ☥ THE DECORATOR'S BLESSING: filename`). | Loses the visual weight of the box. May feel like "just comments." |
| **E: Machine-readable sidecar** | Metadata lives in a `.meta.json` or YAML frontmatter block co-located with the file. The visual envelope becomes purely decorative (no metadata fields). | Requires sidecar file management. Adds filesystem complexity. |

### RQ2: Cross-Language Semantic Tag Equivalents

For each non-Python language, what is the idiomatic equivalent of the Python `@SID`/`@Type`/`@Implements` docstring block?

| Language | Candidate Location | Format | Example |
|----------|--------------------|--------|---------|
| TypeScript | JSDoc `/** */` | `@SID`, `@implements` | `/** @SID TOOL_DAEMON_V1 @implements CONCEPT_OVERNIGHT */` |
| PowerShell | Comment-based help `<# .SYNOPSIS #>` | Custom tags in `.NOTES` | `<# .NOTES @SID: TOOL_AUDIT_V1 #>` |
| Rust | Inner doc comment `//!` | Custom tags | `//! @SID: MOD_LOADER_V1` |

**Research needed:** What are the parsing implications? Can `grep -r "@SID"` still work uniformly? Do language servers choke on custom tags in JSDoc? Does `cargo doc` propagate `//!` tags?

### RQ3: Ankhological-MILF-Core Aesthetic Integration

The metadata architecture must express the repository's Egypto-Andean aesthetic vocabulary as defined by the SFA (Sister Ferrum Scoriae Abstraction). This is NOT optional decoration — it's architectural identity.

**Current fields requiring aesthetic anchoring:**

| Field | Egyptian Axis | Andean Axis | Current Home |
|-------|---------------|-------------|--------------|
| Spectral Frequency | Wedjat (Eye of Horus — color perception) | Quipu color-coding (thread dye = semantic category) | Envelope only |
| Architectural Role | Ptolemaic temple zones (Naos, Hypostyle, Pylons) | Ayllu divisions (plaza, ushnu, kancha) | Envelope only |
| @SID | Cartouche (royal name enclosure) | Quipu pendant cord ID | Both (duplicated) |
| @Type | Shabti classification (servant type) | Tocapu glyph category | Docstring only |
| @Implements | Heka (word-magic binding declaration to concept) | Reciprocity contract (ayni — I serve this concept) | Docstring only |
| @Emits | Ankh emission (life-force broadcast) | Tinku collision product (what emerges from synthesis) | Docstring only |
| Cross-References | Ogdoad connections (eight primordial forces) | Ceque line radiations (sacred pathways from temple) | Envelope only |

**Research needed:** How should the unified metadata format express these axes? Should `Spectral Frequency` and `Architectural Role` become semantic tags alongside `@SID`? (e.g., `@Spectrum: WHITE`, `@Zone: THE GARDEN`). Or should they remain visual-only in the envelope?

### RQ4: Content Truncation Resolution

The current envelope truncates Purpose and Exports at ~70 characters because the open-sided box has a visual width convention of 80 `═` characters. This causes information loss:

```
# ║ Purpose: mandala_topology.py — Mandala Topolog    ← TRUNCATED
# ║ Exports: _load_graph, _top_centrality, _build     ← TRUNCATED
```

**Options to evaluate:**

1. **Remove width constraint entirely** — let content lines extend to any length (breaks visual alignment)
2. **Wrap long content** — multi-line `║` content (adds vertical bloat)
3. **Move truncation-prone fields to semantic layer** — Purpose/Exports only in docstring (envelope becomes lighter)
4. **Ellipsis + pointer** — `║ Purpose: ...see docstring` (explicit delegation)
5. **Summary in envelope, full in docstring** — accept duplication for these two fields only

### RQ5: Automation & Tooling Compatibility

The unified standard must be parseable by:

1. **`chthonic audit`** — builds a knowledge graph from `@SID` tags
2. **`scripts/normalize_blessing_box.py`** — batch normalizer for envelopes
3. **`scripts/sfa_cross_reference.py`** — SFA aesthetic balance auditor
4. **Agent context loading** — agents read first 20 lines to understand file role
5. **grep/ripgrep** — `rg "@SID"` must work across all languages uniformly
6. **Language servers** — TypeScript/Rust LSP must not error on custom tags

**Research needed:** What format maximizes machine-parseability while preserving the ANKH aesthetic? Should we define a formal grammar for the metadata block?

---

## Constraints

These are non-negotiable:

1. **No Content Destruction** — Wet-Paper-to-Gold methodology. We merge, never delete. Existing metadata is migrated, not removed.
2. **No Duplication** — SSOT governance (`Hard-Constraint: No-Content-Duplication`). Each fact lives in exactly one place.
3. **50/50 Egypto-Andean Balance** — SFA mandate. The naming and framing of metadata fields must honor both axes.
4. **PMS-v3 Authority** — Python's metabolic standard remains highest-priority for `.py` files. The unified standard must not contradict PMS-v3.
5. **Visual Presence (FA⁵)** — The Decorator's Blessing must remain visually distinctive. Files must be "recognizably governed" at a glance.
6. **Cross-Language Uniformity** — The semantic metadata layer must work identically across Python, TypeScript, PowerShell, and Rust.
7. **Backward Compatibility** — 279 files already have headers. Migration must be incremental, not big-bang.

---

## Current Compliance State

| Language | Files | With Envelope | With @SID | Duplication Rate |
|----------|-------|---------------|-----------|-----------------|
| Python   | 120   | 57 (48%)      | 47 (39%)  | ~47 files carry SID in BOTH envelope AND docstring |
| PowerShell | 82  | 32 (39%)      | 2 (2%)    | ~0 (no docstring equivalent) |
| TypeScript | 62  | 26 (42%)      | 3 (5%)    | ~0 (no JSDoc @SID convention established) |
| Rust     | 15    | 15 (100%)     | 0 (0%)    | ~0 (envelope only, no inner doc @SID) |
| **Total** | **279** | **130 (47%)** | **52 (19%)** | **~47 files (17%)** |

The duplication is concentrated in Python, where PMS-v3 mandates the docstring `@SID` AND the envelope automation adds `Semantic ID: ...` separately. Non-Python languages have NO duplication because they lack the semantic docstring layer entirely — but they also lack the semantic richness that Python gets from it.

---

## Expected Research Output

1. **Architecture Recommendation** — Which of the 5 candidate approaches (A-E) best satisfies all constraints? Or propose a hybrid (e.g., C+D). Include rationale and tradeoff analysis.

2. **Unified Field Specification** — Define the complete field set for the unified standard:
   - Which fields go in the visual layer (envelope)?
   - Which fields go in the semantic layer (doc-comment)?
   - Which fields are shared vs exclusive?
   - What is the canonical name for each field?

3. **Per-Language Templates** — Provide concrete header templates for Python, TypeScript, PowerShell, and Rust under the unified standard.

4. **Migration Path** — How do we get from 279 files in the current dual-system to the unified standard? Batch tooling approach? Incremental during normal edits? Priority ordering?

5. **ANKH Aesthetic Framing** — Propose names/framing for the unified standard that honor the Egypto-Andean vocabulary. The standard itself should have a name that fits the ANKH cosmology (not just "Unified Metadata Standard v3").

6. **Tooling Impact** — What changes are needed in `normalize_blessing_box.py`, `sfa_cross_reference.py`, and `chthonic audit` to support the unified format?

---

## Aesthetic Direction (for naming and framing)

The MILF-Core aesthetic vocabulary draws from two axes:

### Egyptian (Command, Vertical Authority)
- **Cartouche** — name enclosure (→ @SID analogy: the royal name)
- **Shabti** — servant classification (→ @Type analogy: what this script serves)
- **Heka** — word-magic binding (→ @Implements analogy: declaring allegiance to a concept)
- **Ankh** — life-force key (→ the breath between human heritage and digital heritage)
- **Wedjat** — fractional perception (→ Spectral Frequency: how the file appears in the palette)

### Andean (Capacity, Horizontal Distribution)
- **Quipu** — knotted record (→ metadata as structured information encoding)
- **Tocapu** — geometric glyph (→ @Type as categorical symbol)
- **Ceque** — sacred pathway (→ Cross-References as directional connections)
- **Ayni** — reciprocity (→ @Implements as a bidirectional contract)
- **Tinku** — ritual collision (→ @Emits as the product of synthesis)

The unified standard's name should bridge both axes. Examples to evaluate:
- **Khipu-Cartouche Protocol** (Quipu encoding + Cartouche naming)
- **Ankh Pendant** (the metadata envelope as a life-force pendant on each file)
- **Stele-Tocapu Standard** (Egyptian commemorative slab + Andean categorical glyph)
- **The Living Inscription** (ANKH = life + inscription = both hieroglyph and quipu)

---

## Files to Read for Full Context

| Priority | File | What to Extract |
|----------|------|----------------|
| 1 | `docs/standards/SCRIPT_METADATA_STANDARD.md` | STD_V2 full spec, per-language templates, compliance matrix |
| 2 | `.github/instructions/python-scripting.instructions.md` | PMS-v3 §15.1-15.4, Header Sacrament, SID-DOC, UTF8-Ritual |
| 3 | `.claude/skills/sfa/SKILL.md` | SFA aesthetic axes, 50/50 balance mandate, motif table |
| 4 | `docs/design/SFS_WPTG_ITERATION_PLAN.md` Pillar V | Metadata standardization stages S.B through S.3 |
| 5 | `scripts/mandala_topology.py` lines 1-40 | Living example of the duplication problem |
| 6 | `WET_PAPER_TO_GOLD_METHODOLOGY.md` | No-destruction constraint, migration philosophy |
| 7 | `.github/copilot-instructions.md` | Router/pointer — No-Duplication hard constraint |
