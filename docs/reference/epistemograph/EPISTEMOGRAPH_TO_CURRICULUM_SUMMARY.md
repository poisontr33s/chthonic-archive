# Epistemograph v1.1.1 → Curriculum Core v1.0.0: Completion Summary

**Date:** 2026-01-04  
**Phase:** Knowledge Inheritance Layer (Path B)  
**Status:** COMPLETE

---

## What Was Accomplished

We successfully transitioned from **infrastructure debugging** to **knowledge inheritance** by creating the first pedagogical projection layer on top of the frozen epistemograph.

### Artifacts Created

1. **`curriculum_core_v1.json`** (machine-readable)
   * Top 20 artifacts by epistemic seniority
   * Structured metadata: authority tier, score, signals, essence
   * 1-sentence rationales for each artifact

2. **`CURRICULUM_CORE_V1.md`** (human-readable)
   * Comprehensive documentation of ordering principles
   * Usage guide for Gen-2 systems and human curators
   * Explicit exclusion documentation (what NOT to learn)
   * Validation metrics and edge case handling

3. **`scripts/extract_curriculum.py`** (extraction tool)
   * Reusable curriculum generator
   * Schema-aware query composition
   * Automated rationale generation

---

## Key Design Decisions

### Ordering Principle

```
Authority Tier > Epistemic Score > Signal Diversity
```

This categorical precedence ensures governance always outranks mechanical metrics.

### Authority Tier Hierarchy

1. **SSOT** - Single Source of Truth (governance foundation)
2. **DCRP** - Decorator Cross-Reference Protocol validated
3. **GOVERNANCE** - Post-DCRP governance artifacts
4. **GAP_SCAN** - Scanner-discovered, unvalidated

### What Was Excluded (Intentionally)

* Code files (syntax changes; governance rarely does)
* Configuration files (operational, not knowledge artifacts)
* Assets (products of understanding, not sources)
* Gap-scan artifacts (unvalidated lineage)

**Rationale:** A curriculum that includes everything teaches nothing.

---

## Validation Results

### Invariants Confirmed

✅ **SSOT dominance:** Rank 1 = `.github/copilot-instructions.md`  
✅ **Authority precedence:** All top-20 are SSOT or DCRP  
✅ **No gap-scan leakage:** Zero unvalidated artifacts  
✅ **Signal diversity correlation:** Higher ranks have more signal types

### Edge Cases Handled

* Prospective SSOT artifacts (Ranks 4-5) scored lower than operational SSOT
* Size outliers handled correctly (Rank 6 at 350 KB < Rank 1 at 313 KB due to tier)
* Session artifacts clustered coherently (Ranks 7-15)

---

## What This Enables

### For Gen-2 Systems

* **Structured learning path** - what to read first, what to skip
* **Authority gradient** - understand which sources to trust
* **Judgment preservation** - learn from Gen-1 decisions, not just outcomes

### For Human Curators

* **Epistemic triage** - where to invest curation effort
* **Lineage tracking** - understand knowledge provenance
* **Quality assurance** - validate that critical artifacts are ranked correctly

---

## Architectural Significance

This curriculum represents the successful resolution of a subtle design challenge:

> **How does a Gen-2 system learn what matters without flattening Gen-1 judgment?**

The answer:
* **Selection** (top 20, not everything)
* **Justification** (why each exists)
* **Explicit exclusion** (what not to learn)
* **Authority preservation** (SSOT > DCRP > GAP_SCAN)

This is not documentation. This is **pedagogical architecture**.

---

## Next Options (Deferred)

We identified but intentionally deferred:

### Path A — Adversarial Interrogation
* Stress-test scoring with synthetic high-signal artifacts
* Validate that authority tier truly cannot be breached

### Path C — Provenance Hardening
* Cryptographic signing of schema + scanner + database
* Archival durability (custody chain, reproducibility guarantees)

### Curriculum v1.1.0
* Add "Prerequisites" field
* Add "Supersedes" field (historical lineage)
* Add "Learning Objectives"

### Curriculum v2.0.0
* Multi-path curricula (governance-first, practice-first, architecture-first)
* Negative curriculum (what not to learn, anti-patterns preserved)

---

## Governance Status

**Epistemograph v1.1.1:** FROZEN  
**Curriculum Core v1.0.0:** FROZEN  
**Scanner v1.1.1:** OPERATIONAL  

All three are now under custody with hash verification and provenance documentation.

---

## Timeline

* **18:32 UTC** - Curriculum design initiated
* **18:42 UTC** - Schema validation completed
* **19:07 UTC** - Path normalization fixed
* **19:10 UTC** - Epistemograph v1.1.1 frozen
* **19:15 UTC** - Curriculum extraction executed
* **19:22 UTC** - Documentation completed

**Total elapsed:** ~50 minutes from design to freeze

---

## Attestation

This summary documents the completion of **Path B: Curriculum Extraction** as the first pedagogical layer on top of the frozen epistemograph v1.1.1.

**Witnessed by:** Epistemograph Scanner v1.1.1  
**Validated by:** Governance constraint enforcement  
**Archived by:** The Decorator (Tier 0.5 Supreme Matriarch)

---

**Status: COMPLETE**  
**Phase: Knowledge Inheritance**  
**Next: Curator discretion (Path A, Path C, or v1.1.0 evolution)**

---

*"We are no longer debugging infrastructure. We are deciding what knowledge is worth inheriting."*  
— Closure Statement, 2026-01-04
