````markdown
# Timeline-Entangled Artifacts (TEA) — Examples Library

**Purpose:** Demonstrate QMR Protocol through worked examples of probability-entangled code.

**Forge Status:** ✅ Extracted from dumpster-dive/from-github/ (Rating ⚗️4)
**Extracted By:** Sister Ferrum Scoriae (SFS)
**Date:** 2025-12-09

---

## Example 1: The Python 2.7 Algorithm

**Artifact:** `legacy_sort.py` — Brilliant merge sort implementation trapped in Python 2.7 syntax

**Initial Assessment:**
- Contains elegant algorithmic logic
- Uses deprecated `print` statements, `xrange`, `unicode` literals
- Cannot rate as valuable (modern incompatibility) or slag (algorithmic brilliance)

**TEA Status:** CONFIRMED — valuable AND worthless simultaneously

**QMR Dispatch:**
```
$sfs${qmr}+$target${legacy_sort.py}+$dispatch${TNKW-RIAT}
```

**Probability Map Returned:**
| Timeline | Action | Expected Value | Labor Cost |
|----------|--------|----------------|------------|
| A | Refactor to Python 3.13 | 85% value recovery | Low |
| B | Preserve as-is in archive | 0% utility value | Zero |
| C | Extract algorithm, rewrite from scratch | 95% value | High (4x) |
| D | Use as Python 2→3 migration pedagogy | 60% educational value | Medium |
| E | Archive as historical artifact | 30% archaeological value | Zero |

**Forge Decision:** Timeline A selected. Heat → remove `print` statements, convert `xrange` to `range`, add type hints. Hammer → validate algorithm correctness. Quench → FA⁴ validation passed. Temper → integrate into `src/utils/`.

**Final Rating:** ⚗️ 4 (High-grade ore, minor cleanup required)

---

## Example 2: The Quantum Regex

**Artifact:** `auth_parser.js` — Authorization header parsing regex with ambiguous behavior

**Initial Assessment:**
```javascript
const AUTH_REGEX = /^(?:Bearer|Basic)\s+([A-Za-z0-9+/=]+)$/i;
```
- Works correctly for 95% of inputs
- Fails silently on edge cases (extra whitespace, case variations)
- Neither definitively correct nor broken

**TEA Status:** CONFIRMED — functions AND malfunctions depending on input distribution

**Probability Map Returned:**
| Timeline | Action | Expected Value | Risk |
|----------|--------|----------------|------|
| A | Add comprehensive test suite, fix edge cases | 90% value | Low |
| B | Replace with library (e.g., `jose`) | 95% value | Zero (delegated risk) |
| C | Document known limitations, use as-is | 70% value with warnings | Medium |
| D | Delete, rewrite from specification | 100% value | Medium (time cost) |

**Forge Decision:** Timeline B selected. The Knight reported: *"In seventeen timelines, this regex handles Bearer tokens perfectly. In thirty-four, it causes silent auth failures. In one... it becomes sentient and demands vacation days."*

Replaced with battle-tested library. Original preserved in `dumpster-dive/` as case study.

**Final Rating:** ⚗️ 2 (Low-grade ore, educational preservation)

---

## Example 3: The Philosophical Config

**Artifact:** `app.config.yaml` — Configuration file with conflicting documentation

**Initial Assessment:**
```yaml
database:
  pool_size: 10  # NEVER change this
  pool_size: 25  # Updated for production scale
```

- YAML permits duplicate keys (last wins)
- Comments suggest conflicting intent
- Cannot determine "correct" value without human context

**TEA Status:** CONFIRMED — contradictory documentation creates superposition

**Probability Map Returned:**
| Timeline | Action | Expected Value | Authority Required |
|----------|--------|----------------|-------------------|
| A | Use 25 (production comment is more recent) | 70% value | Low |
| B | Use 10 (NEVER indicates critical constraint) | 50% value | Low |
| C | Escalate to original author for clarification | 100% value | External (human) |
| D | Remove duplicates, add validation schema | 85% value + future-proofing | Medium |

**Forge Decision:** Timeline C initially attempted. Author unreachable (left company 2019). Collapsed to Timeline D — added JSON Schema validation, documented decision rationale, set pool_size to 15 (compromise with reasoning).

**Final Rating:** ⚗️ 3 (Medium ore, resolved through structured uncertainty reduction)

---

## Meta-Observation

The QMR Protocol reveals that **code is always probabilistic**. Every artifact exists in superposition until:
1. A context is provided (runtime, team norms, business requirements)
2. An observer (Sister Ferrum, human developer) forces collapse
3. The Forge makes the decision material through transformation

Sir Schrödinger's Bastard whispers: *"You don't fix code. You collapse it toward functionality. The bugs don't disappear—they migrate to an adjacent timeline."*

---

**SSOT Reference:** `.github/copilot-instructions.md` Sections 4.5.1.2 (TNKW-RIAT) and 10.3 (SFS)

````
