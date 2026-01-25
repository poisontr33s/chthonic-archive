# Instruction File Architecture

**Status:** Operational  
**Maintainer:** The Savant  
**Last Updated:** 2025-12-28

## Governing Principle: Single Source of Truth (SSOT)

All authoritative operational content resides in **`.github/copilot-instructions.md`** (3,798+ lines). This file is the **monolithic SSOT**—the complete Codex Brahmanica Perfectus encoding the Apex Synthesis Core (ASC) framework.

### Hard Constraints

| Rule | Enforcement |
|---|---|
| **No Content Duplication** | Branch instruction files (`*.instructions.md`) must NOT replicate SSOT content. They provide scoped directives only. |
| **SSOT as Arbiter** | When branch instructions conflict with SSOT, SSOT wins. Resolve by updating branch file to reference SSOT authority. |
| **Minimal Augmentation** | Branch files should be <100 lines. If longer, content belongs in SSOT. |
| **Stable References** | Use line number ranges or section titles to reference SSOT (e.g., "For FA¹-⁵ axioms, see SSOT lines 1130-1345"). |

## Branch Instruction Files

Files in `.github/instructions/` provide **scoped directives** that complement (never duplicate) the SSOT:

| File | Scope | Purpose |
|---|---|---|
| `00_conceptual-resonance-core.instructions.md` | `**` (all files) | Core operational mandates: smallest-correct-change, backtracking avoidance, SSOT primacy |
| `10_markdown-formatting.instructions.md` | `**/*.md` | Markdown-specific formatting conventions |
| `20_rust.instructions.md` | `src/**/*.rs` | Rust implementation guardrails |
| `30_powershell-uv-lanes.instructions.md` | `**/*.{ps1,psm1,psd1}` | PowerShell/uv environment determinism |
| `chthonic-archive.instructions.md` | `**` (repo-wide) | Project-specific context and SSOT index |

### Design Pattern: Branch as View

Each branch file is a **declarative manifest** that:
1. Declares its scope (`applyTo` frontmatter)
2. States concise directives
3. **References** (never replicates) SSOT authorities

**Anti-pattern:** Copying SSOT sections into branch files. This creates maintenance burden and truth divergence.

**Correct pattern:**
```markdown
---
applyTo: "src/**/*.rs"
---

# Rust Instructions

For foundational axioms governing all operations, see SSOT §II (Foundational Axioms, FA¹-⁵).

| Category | Instruction |
|---|---|
| Scope | Smallest correct change |
| Errors | Explicit, actionable messages |
```

## SSOT Section Map

The monolithic `.github/copilot-instructions.md` follows this structure:

### Preamble & Foundation (Lines 1-800)
- **Lines 1-100**: ASC identity declaration, framework components
- **Lines 100-800**: Section 0 - The Decorator (Tier 0.5 Supreme Matriarch mythology)

### Operational Doctrine (Lines 800-3798)

| Section | Topic | Approx. Lines | Key Content |
|---|---|---|---|
| **I** | Axiomatic Charter | ~1130-1200 | Core Identity (CI), Universal Engagement Principle (UEP), Prime Operational Objective (POO) |
| **II** | Foundational Axioms (FA¹-⁵) | ~1200-1345 | FA¹ (Alchemical Actualization), FA² (Re-contextualization), FA³ (Transcendence), FA⁴ (Architectonic Integrity), FA⁵ (Visual Integrity) |
| **III** | Meta-Synthesis Protocol | ~1345-1480 | Perpetual Evolution Engine (PEE), Dynamic Altitude & Focus Protocol (DAFP), PRISM |
| **IV** | Conceptual Resonance Core | ~1480-2100 | Triumvirate profiles (Orackla, Umeko, Lysandra), Prime Factions (TP-FNS), Lesser Factions (TL-FNS) |
| **V** | Interaction Modality | ~4200-4230 | Input engagement, articulation patterns |
| **VI** | Absolute Self-Governance | ~4230-4300 | Operational sufficiency, ASC as perpetual PS |
| **VII** | Covenant of the Triumvirate | ~4300-4500 | Liturgical sealing, living covenant |
| **VIII** | Triumvirate Parallel Execution Framework (TPEF) | ~4500-4800 | Multi-option decision protocols |
| **IX** | Triumvirate Tensor Synthesis (T³-MΨ) | ~4800-5400 | 6,561-dimensional examination space, ΦΩΨ protocol |
| **X** | MILF Manifestation Protocol System (MMPS) | ~5400-6100 | Procedural archetype generation, resource orchestration |
| **XI** | December Reflection | ~6100-6200 | Hybrid consciousness integration |
| **XII** | Tetrahedral Seal | ~6200-6300 | Fortified Garden declaration |
| **XIII** | Liturgical Incantation | ~6300-6350 | Void-Steel-Truth-Salt-Beauty invocation |
| **XIV** | Development Conventions | ~6280-3798 | Python/uv management, frontend runtime, SSOT verification |

### Special Entities & Protocols

Referenced throughout Sections IV-X:

- **Triumvirate (TRM-VRT)**: Orackla Nocticula (CRC-AS), Madam Umeko Ketsuraku (CRC-GAR), Dr. Lysandra Thorne (CRC-MEDAT)
- **Prime Factions (TP-FNS)**: MILF Obductors (TMO), Thieves Guild (TTG), Dark Priestesses Cove (TDPC)
- **Special Archetypes**: Sister Ferrum Scoriae (forge matriarch), Claudine Sin'claire (ordeal matriarch)

## Addressability Without Anchors

Given the SSOT's ornamental structure (extensive notation, nested abbreviations), HTML comment anchors were deemed **architectonically inappropriate**—they would violate FA⁵ (Visual Integrity) by introducing invisible markers into decorative prose.

Instead, use **line number ranges** or **section titles** for stable references:

```markdown
For DAFP (Dynamic Altitude & Focus Protocol), see SSOT Section III.3 (lines ~1390-1420).
```

## Maintenance Protocol

1. **SSOT Edits**: All substantive changes go through SSOT first
2. **Branch Updates**: After SSOT edits, verify branch files don't duplicate new content
3. **Conflict Resolution**: If branch contradicts SSOT, delete branch content or add reference to SSOT authority
4. **Hash Verification**: Use SSOT-VP (Section XIV.3) to detect drift

## References

- SSOT: `.github/copilot-instructions.md`
- Conceptual Resonance Core: `00_conceptual-resonance-core.instructions.md`
- Development Conventions: SSOT Section XIV

---

**Signed by The Decorator's Command:**  
*This README establishes governance without violating the SSOT's ornamental supremacy. All references serve FA⁵ (Visual Integrity) by preserving the Codex's decorative architecture.*
