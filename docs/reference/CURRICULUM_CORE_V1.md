# Curriculum Core v1.0.0 - Epistemic Seniority Ordering

**Status:** OPERATIONAL  
**Source Database:** `chthonic_epistemograph_v1.1.1.sqlite`  
**Extraction Date:** 2026-01-04  
**Architect:** Epistemograph Scanner v1.1.1

---

## Purpose

This curriculum represents the **first 20 artifacts** a Gen-2 system should study when inheriting knowledge from this repository, ordered by **epistemic seniority** rather than mechanical score.

The ordering principle:
```
Authority Tier > Epistemic Score > Signal Diversity
```

Where authority tier hierarchy is:
1. **SSOT** (Single Source of Truth - governance foundation)
2. **DCRP** (Decorator Cross-Reference Protocol validated)
3. **GOVERNANCE** (Post-DCRP governance artifacts)
4. **GAP_SCAN** (Scanner-discovered, unvalidated)

---

## Design Principles

### What This Is

* **Selection with justification** - not comprehensive indexing
* **Ordering by epistemic seniority** - what matters most, not what's biggest
* **Negative space documentation** - explicitly states what to skip

### What This Is NOT

* A replacement for the epistemograph database
* A comprehensive tutorial
* A flattened summary that loses judgment gradients

---

## Top 20 Artifacts (Epistemic Seniority Order)

### Rank 1-5: SSOT Foundation

**1. `.github/copilot-instructions.md`** (GOLD/DOCUMENTATION)
* **Why:** Single Source of Truth - governance foundation
* **Score:** 1.0 (maximum epistemic weight)
* **Signals:** 6 distinct categories detected
* **Size:** 313 KB
* **Essence:** "Single Source of Truth - Codex Brahmanica Perfectus"

**Read this first.** All other artifacts derive authority from this document.

**2. `.github/instructions/project-workflow.instructions.md`** (GOLD/DOCUMENTATION)
* **Why:** Single Source of Truth - governance foundation
* **Score:** 0.447
* **Essence:** Workflow procedural guidance

**3. `.github/SESSION_RESUME.md`** (GOLD/DOCUMENTATION)
* **Why:** Single Source of Truth - governance foundation
* **Score:** 0.354
* **Essence:** Session continuity protocol

**4-5. Macro-Prompt-World Documentation** (GOLD/DOCUMENTATION)
* Located in: `.github/macro-prompt-world/even-more-disparate-extranerrous-md-documentation/`
* **Why:** SSOT-adjacent future planning artifacts
* **Note:** Lower scores (~0.266-0.271) due to prospective rather than operational status

### Rank 6-10: DCRP-Validated Core

**6. `CROSS_REFERENCE_TRIPTYCH.md`** (GOLD/DOCUMENTATION)
* **Why:** DCRP-validated documentation (GOLD frequency)
* **Score:** 0.947
* **Signals:** 5 distinct categories
* **Size:** 350 KB
* **Essence:** Tri-modal architecture (Fortress/Garden/Observatory) canonical projection

**Second most important artifact.** This is the epistemograph's predecessor—Gen-1 hand-crafted topology.

**7. `AUTONOMOUS_SESSION_3_MISSION_COMPLETE.md`** (GOLD/DOCUMENTATION)
* **Why:** DCRP-validated documentation (GOLD frequency)
* **Score:** 0.879
* **Signals:** 4 categories
* **Essence:** Autonomous session synthesis artifact

**8. `AUTONOMOUS_SESSION_5_COMPLETE.md`** (GOLD/DOCUMENTATION)
* **Score:** 0.857
* **Essence:** Later autonomous session record

**9. `DEVELOPMENT_STATE.md`** (GOLD/DOCUMENTATION)
* **Score:** 0.847
* **Essence:** Repository operational status snapshot

**10. `AUTONOMOUS_SESSION_4_COMPLETE.md`** (GOLD/DOCUMENTATION)
* **Score:** 0.842
* **Essence:** Intermediate autonomous session

### Rank 11-15: Secondary DCRP Artifacts

**11-15:** Additional autonomous session completions and mission reports
* All GOLD/DOCUMENTATION frequency
* All DCRP-validated
* Scores range 0.776-0.833
* **Pattern:** These represent Gen-1 judgment crystallized in session artifacts

### Rank 16-20: Tertiary Documentation

**16. `ANKH_README.md`** (GOLD/DOCUMENTATION)
* **Score:** 0.723
* **Essence:** ANKH evaluation framework documentation

**17-20:** DCRP status artifacts and lineage documentation
* Scores range 0.658-0.712
* All DCRP-validated GOLD documentation

---

## Usage Guide

### For Gen-2 Systems

1. **Start with Rank 1** (`.github/copilot-instructions.md`)
   * This defines the ASC framework, axioms, and governance
   * Do not proceed until you understand FA¹⁻⁵ (Foundational Axioms)

2. **Study Rank 6** (`CROSS_REFERENCE_TRIPTYCH.md`)
   * This shows Gen-1's hand-crafted topology understanding
   * Compare this to the epistemograph's computed topology
   * Divergences are learning opportunities

3. **Sample Ranks 7-10** (Autonomous sessions)
   * These show Gen-1 *in action*, not just theory
   * Look for judgment patterns, not just solutions

4. **Skip Ranks 4-5** initially
   * These are prospective, not operational
   * Return after understanding core governance

### For Human Curators

* **High-signal invariant:** SSOT artifacts (Ranks 1-5) form governance foundation
* **Authority gradient:** DCRP validation correlates with epistemic weight
* **Signal diversity:** Rank 1 has 6 signal types; most others have 0-5
  * This suggests SSOT documents are densest in epistemic markers
* **Size-score decoupling:** Rank 1 (313 KB) outranks Rank 6 (350 KB) due to authority tier
  * Size is not destiny; lineage is

---

## What This Curriculum Excludes (Intentionally)

### Not Included in Top 20

* **Code files** (even highly connected ones)
  * Rationale: Code changes frequently; governance rarely does
  * Learning Python/Rust syntax from curriculum would be pedagogical waste

* **Configuration files** (`.toml`, `.json`, `.yaml`)
  * Rationale: These are operational artifacts, not knowledge artifacts
  * They implement decisions; curriculum teaches *why* decisions were made

* **Assets** (shaders, images, binaries)
  * Rationale: These are products of understanding, not sources of it

* **Gap-scan artifacts** (even with high signal density)
  * Rationale: Unvalidated by DCRP; may contain noise
  * Gen-2 should learn from validated lineage first

### Why These Exclusions Matter

A curriculum that includes *everything* teaches *nothing*.

The exclusions above preserve the **signal-to-noise ratio** that makes this curriculum pedagogically useful.

---

## Validation Metrics

### Invariants Confirmed

✅ **SSOT dominance:** Rank 1 is `.github/copilot-instructions.md`  
✅ **Authority precedence:** All top-20 are either SSOT or DCRP  
✅ **No gap-scan leakage:** Zero unvalidated artifacts in top-20  
✅ **Signal diversity correlation:** Higher-ranked artifacts have more signal types

### Edge Cases Handled

* **Prospective SSOT artifacts** (Ranks 4-5): Included but scored lower than operational SSOT
* **Size outliers:** Rank 6 (350 KB) scored below Rank 1 (313 KB) correctly due to tier
* **Session artifacts:** Clustered together (Ranks 7-15) showing coherent lineage

---

## Next Steps (Curriculum Evolution)

### v1.1.0 (Proposed)

* Add **"Prerequisites"** field (which artifacts must be read first)
* Add **"Supersedes"** field (historical lineage tracking)
* Add **"Learning Objectives"** (what each artifact teaches)

### v2.0.0 (Future)

* **Pedagogical Projections:** Multi-path curricula for different learner types
  * Path A: Governance-first (start with SSOT)
  * Path B: Practice-first (start with session artifacts)
  * Path C: Architecture-first (start with technical documents)

* **Negative Curriculum:** Explicit "what not to learn" documentation
  * Anti-patterns preserved for teaching purposes
  * Historical failures documented for context

---

## Custody

**Artifact:** `curriculum_core_v1.json`  
**Schema Version:** 1.0.0  
**Extraction Script:** `scripts/extract_curriculum.py`  
**Source Database:** `chthonic_epistemograph_v1.1.1.sqlite` (SHA256: d55ac9ce1d5cf2c1a40dddb1f933ea7c4e88f6b1bf90f5ce6859c3cf82a3f1b0)

**Immutability Contract:**
* This curriculum is **read-only**
* Updates require version bump and new artifact
* Original v1.0.0 preserved for lineage tracking

---

## Attestation

This curriculum was extracted via:
```bash
cd C:\Users\erdno\chthonic-archive
uv run python scripts\extract_curriculum.py
```

**Validation Date:** 2026-01-04  
**Validator:** Epistemograph Scanner v1.1.1  
**Witnessed by:** The Decorator (Tier 0.5 Supreme Matriarch)

---

**Status: FROZEN**  
**Date: 2026-01-04**  
**Architect: Epistemic Seniority Ordering Protocol**

---

*"Authority precedes topology, but never follows it."*  
— Scanner Approval Document, Section 2.2
