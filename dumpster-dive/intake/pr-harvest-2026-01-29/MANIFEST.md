# PR Harvest Manifest — 2026-01-29

## Source Material

| PR | Title | Status | Lines | Origin |
|----|-------|--------|-------|--------|
| #2 | ANKH semantic lineage framework | Draft | +1,227 | copilot-swe-agent |
| #5 | SSOT_Canon.md governance document | Open | +8,380 | GPT-5.2 posturing |

## Context

Both PRs encoded a fundamental misunderstanding: treating "ANKH" (intended as Egyptological ☥ symbol) as an acronym for a governance framework. Rather than discard, we transmute.

**Wet-Paper-to-Gold Principle:** Nothing is waste if you see the extractable value.

---

## Extraction Tiers

### Tier 1: Direct Use (Immediate Value)

| File | Source | Target | Notes |
|------|--------|--------|-------|
| `ssot_hash.py` | PR #2 | `scripts/ssot_hash.py` | SHA-256 hash verification for drift detection. Clean utility, no mythology. |

**Action:** Copy to `scripts/` and use directly.

### Tier 2: Schema Definitions (Structured Data)

| File | Source | Description |
|------|--------|-------------|
| `translation_matrix.json` | PR #2 ankh.md | What survives/decays/prohibited in translations. Useful for validation schemas. |
| `entity_template.json` | PR #2 entity files | Template structure for procedural entity generation. |
| `tier_hierarchy.json` | PR #5 SSOT_Canon.md | Hierarchical authority model. Maps to RBAC, microservice tiers, agent orchestration. |

**Action:** Use as schema templates, test fixtures, or procedural generation inputs.

### Tier 3: Conceptual Salvage (Repurposed Metaphors)

| File | Source | Repurpose |
|------|--------|-----------|
| `body_system_metaphor.md` | PR #5 body system mapping | Microservice architecture documentation metaphor. |
| `emoji_vocabulary.md` | PR #5 emoji semantic layer | Consistent status indicators for commits, logs, dashboards. |

**Action:** Reference for documentation patterns, not mythology.

### Raw (Unprocessed Source)

| File | Source | Notes |
|------|--------|-------|
| `pr2_patches.json` | All PR #2 file patches | Complete (42KB) |
| `pr5_patches.json` | PR #5 metadata | Patch null - file too large for API |

**Note:** Full SSOT_Canon.md (8,380 lines) available via `gh pr diff 5` or branch checkout.

**Action:** Mine for additional patterns as needed.

---

## PR Disposition

### PR #2 — Recommend: Close (Draft)
- Core concept (ANKH as framework) is mislabeled
- Useful pieces extracted (ssot_hash.py, entity templates)
- No merge value remaining

### PR #5 — Recommend: Close
- Massive redundancy with existing SSOT
- GPT-5.2 "posturing" without practical utility
- Useful structures extracted (tier hierarchy, emoji vocab)
- 8,380 lines is unmaintainable

---

## Transmutation Summary

```
Input:  ~9,600 lines of mislabeled mythology
Output:
  - 1 working utility script (182 lines)
  - 3 JSON schemas (~180 lines total)
  - 2 documentation patterns (~100 lines total)
  - Raw material for future mining

Compression ratio: ~20:1
Value extraction: High
Mythology residue: Sanitized
```

---

## Next Steps

1. [ ] Copy `ssot_hash.py` to `scripts/` if hash verification desired
2. [ ] Validate schemas against actual use cases
3. [ ] Close PR #2 and #5 with note pointing to this harvest
4. [ ] Consider renaming `ankh_atlas/` to reflect actual intent (Egyptological, not acronym)

---

**Harvested:** 2026-01-29
**Harvester:** Claude Opus 4.5 + The Savant
**Methodology:** Wet-paper-to-gold selective uptake
