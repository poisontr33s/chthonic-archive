---
type: standard
category: governance
status: canonical
created: 2026-03-04
author: Claude Code Opus 4.6
supersedes: STD_SCRIPT_METADATA_V2 (partially — see §9)
ratified-from: ANKH_UNIFYING_REPOSITORY_METADATA_STANDARDS.md (Gemini-3 Pro Deep Research)
---

# Khipu-Cartouche Protocol — Ontology Specification

**@SID:** STD_KCP_ONTOLOGY_V1
**@Context:** Metadata Governance / SSOT Architecture
**@Purpose:** Canonical schema defining every field, stratum, enumeration value,
              and per-language encapsulation rule for the Khipu-Cartouche Protocol.
              This document is the single source of truth for all KCP regex patterns,
              field assignments, and migration tooling.

> **Gate KCP-0.0:** 100% legacy fields mapped, 0 data loss.

---

## 1. Protocol Summary

The Khipu-Cartouche Protocol (KCP) resolves the metadata duplication crisis
caused by the coexistence of two overlapping standards:

- **STD_SCRIPT_METADATA_V2** — the visual "Decorator's Blessing" envelope
- **PMS-v3** — the Python Metabolic Standard docstring `@Tag` ontology

KCP introduces a **strict two-stratum architecture** (Approach C — Stratified
Metadata) that binds every unit of metadata to exactly one spatial coordinate:

| Stratum | Name | Responsibility | Width Constraint |
|---------|------|----------------|------------------|
| **1** | **Cartouche** (Envelope) | Classification, visual identity, routing | 80-char, enumeration only |
| **2** | **Khipu** (Docstring) | Operational identity, unbounded semantics | Language-native, no width limit |

**Invariants:**

1. Every field belongs to exactly one stratum. No field may appear in both.
2. `@SID` is **Khipu-only**. It never appears in the Cartouche.
3. `@Purpose` is **Khipu-only**. It is never truncated in the Cartouche.
4. The Cartouche contains **zero** unbounded text fields.
5. The Khipu contains **zero** visual box-drawing characters.

---

## 2. Stratum 1 — The Visual Cartouche

The Cartouche is the topmost boundary of the source file (after shebang/encoding
where applicable). It uses the open-sided `╔╠╚║═` formatting structure, bounded
to exactly 80 `═` characters per border line.

### 2.1 Field Inventory

| # | KCP Field | Legacy Equivalent | Type | Required |
|---|-----------|-------------------|------|----------|
| C1 | **Artifact Name** | `Filename` | String (filesystem name) | Yes |
| C2 | **Wedjat-Quipu Spectrum** | `Spectral Frequency` | Enum (see §4.1) | Yes |
| C3 | **Temple-Ayllu Zone** | `Architectural Role` | Enum (see §4.2) | Yes |
| C4 | **Ogdoad-Ceque Radiance** | `Cross-References` | Path list | Optional |

### 2.2 Cartouche Template (Universal)

```
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: <artifact_name>
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: <SPECTRUM_ENUM>
# ║ Temple-Ayllu Zone: <ZONE_ENUM>
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ <relative/path/to/dependency>
# ╚════════════════════════════════════════════════════════════════════════════
```

### 2.3 Prohibited Content

The following are **permanently banned** from the Cartouche:

| Banned Field | Reason | Destination |
|--------------|--------|-------------|
| `Semantic ID` / `@SID` | Duplication crisis origin | Khipu `@SID` |
| `Purpose:` | Truncation at 80-char boundary | Khipu `@Purpose` |
| `Module:` / `Exports:` | Unbounded text, truncation-prone | Khipu `@Purpose` body |
| `@Type` / `@Shabti` | Operational identity = Khipu domain | Khipu `@Shabti` |
| Any freeform description | Violates enumeration-only constraint | Khipu `@Purpose` |

### 2.4 Structural Rules

1. Top border: `╔` + 80× `═` (total 81 chars after comment prefix).
2. Divider: `╠` + 80× `═`.
3. Bottom border: `╚` + 80× `═`.
4. Content lines: `║` + single space + field content.
5. **No right border.** The open-sided design eliminates width calculation.
6. Comment prefix is language-specific: `#` (Python/PS1/Bash), `//` (TS/Rust).

---

## 3. Stratum 2 — The Semantic Khipu

The Khipu resides entirely within the language's native documentation syntax.
It follows immediately after the Cartouche closure (`╚═════`). It is
unconstrained by visual width and assumes total responsibility for
machine-parseable ontological mapping.

### 3.1 Field Inventory

| # | KCP Field | Legacy Equivalent | Type | Required |
|---|-----------|-------------------|------|----------|
| K1 | **@SID** | `Semantic ID` | Identifier (UPPER_SNAKE) | Yes |
| K2 | **@Shabti** | `@Type` | Enum (see §4.3) | Yes |
| K3 | **@Heka-Ayni** | `@Implements` | Concept ID | Optional |
| K4 | **@Ankh-Tinku** | `@Emits` | State ID | Optional |
| K5 | **@Purpose** | `Purpose` + `Module`/`Exports` | Free text (unbounded) | Yes |

### 3.2 Khipu Tag Format

All Khipu tags use the `@Tag:` format with consistent alignment:

```
@SID:           TOOL_EXAMPLE_V1
@Shabti:        CLI Script
@Heka-Ayni:     CONCEPT_SSOT
@Ankh-Tinku:    STATE_AUDIT_COMPLETE
@Purpose:       Full, unbounded description of the artifact's operational
                intent, including former Module/Exports content.
```

**Alignment:** The colon is flush to the tag name. The value begins at column 17
(0-indexed) within the Khipu block, padded with spaces. Multi-line values use
matching indentation on continuation lines.

### 3.3 Prohibited Content

| Banned Element | Reason |
|----------------|--------|
| Box-drawing characters (`╔╠╚║═`) | Visual identity = Cartouche domain |
| `Spectral Frequency` / `Wedjat-Quipu Spectrum` | Classification = Cartouche domain |
| `Architectural Role` / `Temple-Ayllu Zone` | Classification = Cartouche domain |
| `Cross-References` / `Ogdoad-Ceque Radiance` | Routing = Cartouche domain |

---

## 4. Enumeration Registries

### 4.1 Wedjat-Quipu Spectrum (formerly Spectral Frequency)

The Spectrum classifies the artifact's execution logic and operational domain.
Values are **single uppercase tokens**. The legacy freeform values
(e.g., `orchestration/bootstrap`, `integration/mcp`) are mapped to the
nearest canonical enum.

| Enum Value | Semantic Domain | Legacy Values Absorbed |
|------------|-----------------|----------------------|
| `WHITE` | General-purpose utility, hygiene, compliance | `WHITE`, `tooling/scanner` |
| `ORANGE` | Extension/IDE integration, TypeScript modules | `ORANGE`, `integration/copilot`, `integration/mcp` |
| `RED` | Security, permissions, emergency | — |
| `BLUE` | Orchestration, daemon, async oversight | `orchestration/automation`, `orchestration/bootstrap` |
| `BLACK` | Systems programming, low-level allocation | — |
| `GOLD` | Transcendence, meta-governance, completed evolution | `GOLD` |
| `GREEN` | Configuration, environment, probe | `configuration/environment`, `diagnostic/passive` |

**Migration rule:** Any freeform `Spectral Frequency` value that does not match
a canonical enum is mapped to the closest semantic match. If ambiguous, default
to `WHITE`.

### 4.2 Temple-Ayllu Zone (formerly Architectural Role)

The Zone classifies the artifact's position in the architectural hierarchy.
Values use the **emoji + UPPER_CASE NAME** format. The legacy freeform
descriptions (e.g., `CLI profile shim (non-destructive)`) are stripped from
the Cartouche and relocated to `@Purpose`.

| Enum Value | Semantic Domain | Legacy Values Absorbed |
|------------|-----------------|----------------------|
| `🌿 THE GARDEN` | Utilities, scripts, batch tools | `UTILITY`, `HARVEST`, `SSOT`, `COMPLIANCE` |
| `🔭 THE OBSERVATORY` | Monitoring, daemons, oversight | `DIAGNOSTIC`, `PROBE` |
| `🏛️ THE HYPOSTYLE` | Core infrastructure, design docs | `INFRASTRUCTURE`, `GOVERNANCE` |
| `⚔️ THE PYLONS` | Security, validation, gates | `VALIDATION`, `EMERGENCY` |
| `🕳️ THE NAOS` | Systems core, memory, allocation | — |
| `🔥 THE FOUNDRY` | Build, compilation, forge | `🛠️ THE FOUNDRY` |
| `📜 THE SCRIPTORIUM` | Documentation, standards, specs | — |

**Migration rule:** Any freeform `Architectural Role` description is stripped
and relocated to `@Purpose`. Only the canonical enum remains in the Cartouche.

### 4.3 @Shabti Values (formerly @Type)

The Shabti classifies the artifact's execution archetype.

| Enum Value | Description |
|------------|-------------|
| `CLI Script` | Command-line tool invoked directly |
| `Library Module` | Importable module providing functions/classes |
| `Daemon` | Long-running background process |
| `Config` | Configuration or settings file |
| `Router` | Request dispatcher or protocol bridge |
| `Standard` | Governance document or specification |
| `Checkpoint` | Session state / crash-recovery document |
| `Script / Module` | Dual-purpose: both importable and directly executable |
| `Automation Script` | CI/CD, batch, or pipeline automation |
| `Extension Module` | VS Code extension source component |

---

## 5. Legacy Field Mapping — Complete Inventory

This table demonstrates **zero data loss** by mapping every field from both
legacy systems to a KCP destination.

### 5.1 STD_SCRIPT_METADATA_V2 (Envelope Fields)

| Legacy Field | Location | KCP Destination | Stratum | Data Loss |
|-------------|----------|-----------------|---------|-----------|
| `Filename` (THE DECORATOR'S BLESSING: ...) | Envelope line 2 | **Artifact Name** | Cartouche | None |
| `Module: <description>` | Envelope line 3 | **@Purpose** body | Khipu | None — was truncated, now unbounded |
| `Spectral Frequency: <COLOR>` | Envelope | **Wedjat-Quipu Spectrum** | Cartouche | None — enum preserved |
| `Architectural Role: <ROLE>` | Envelope | **Temple-Ayllu Zone** | Cartouche | None — enum preserved; freeform text → @Purpose |
| `Semantic ID: <SID>` | Envelope | **@SID** | Khipu | None — **removed from Cartouche** to end duplication |
| `Purpose: <text>` | Envelope | **@Purpose** | Khipu | None — was truncated, now unbounded |
| `Exports: <list>` | Envelope | **@Purpose** body | Khipu | None — was truncated, now unbounded |
| `Cross-References` | Envelope | **Ogdoad-Ceque Radiance** | Cartouche | None — structural rename only |

### 5.2 PMS-v3 (Docstring Tags)

| Legacy Tag | Location | KCP Destination | Stratum | Data Loss |
|-----------|----------|-----------------|---------|-----------|
| `@SID` | Docstring | **@SID** | Khipu | None — single-source enforced |
| `@Type` | Docstring | **@Shabti** | Khipu | None — aesthetic rename |
| `@Context` | Docstring | **@Purpose** body or **Temple-Ayllu Zone** | See §5.3 | None — see resolution |
| `@SessionOrigin` | Docstring | **@SessionOrigin** (retained) | Khipu (optional) | None — see §5.4 |
| `@Implements` | Docstring | **@Heka-Ayni** | Khipu | None — aesthetic rename |
| `@Emits` | Docstring | **@Ankh-Tinku** | Khipu | None — aesthetic rename |
| `@Related` | Docstring | **Ogdoad-Ceque Radiance** | Cartouche | None — see §5.5 |

### 5.3 @Context Disposition

`@Context` was a freeform domain classifier (e.g., `Hygiene`, `Infrastructure / Identity Resolution`). Under KCP:

- **When it maps to a canonical zone** (e.g., `Infrastructure` → `🏛️ THE HYPOSTYLE`): absorbed into `Temple-Ayllu Zone`.
- **When it is a freeform descriptor** (e.g., `Local Refinement / L1→L2 Pipeline`): relocated to the opening line of `@Purpose`.
- **The `@Context` tag is abolished.** It does not survive as a KCP field.

### 5.4 @SessionOrigin Disposition

`@SessionOrigin` is provenance metadata (e.g., `SESSION_2026_01_28_IDE_FIX`).
It is **retained as an optional Khipu field** without aesthetic rename:

```
@SessionOrigin: SESSION_2026_01_28_IDE_FIX
```

It is NOT renamed because:
1. It has no cosmological equivalent — it is purely operational provenance.
2. It is used in < 5 files and will naturally decay as sessions age.
3. Renaming it would add aesthetic complexity with no structural benefit.

### 5.5 @Related Disposition

`@Related` was a docstring-level cross-reference pointing to other `@SID` values.
Under KCP:

- **File-level dependencies** (paths): absorbed into **Ogdoad-Ceque Radiance** (Cartouche).
- **Concept-level links** (SID references): absorbed into **@Heka-Ayni** (Khipu).
- **The `@Related` tag is abolished.** It does not survive as a KCP field.

---

## 6. Per-Language Encapsulation

### 6.1 Python (`.py`)

**Ordering:**

| Line | Content | Required |
|------|---------|----------|
| 1 | `#!/usr/bin/env python3` | Yes — shebang |
| 2 | `#-*- coding: utf-8 -*-` | Yes — tight, NO space (PMS-v3) |
| 3 | (blank) | Yes |
| 4–N | Cartouche (`# ╔...# ╚...`) | Recommended |
| N+1 | (blank) | Yes (if Cartouche present) |
| N+2–M | `"""` Khipu docstring `"""` | Yes |
| M+1 | (blank) | Yes |
| M+2 | `import` statements | — |

**Khipu syntax:** Triple-quoted module docstring `"""..."""`. The `__doc__`
attribute captures the entire Khipu for runtime reflection.

**Example:**

```python
#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: mandala_topology.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone — no detected dependencies)
# ╚════════════════════════════════════════════════════════════════════════════

"""
mandala_topology.py — Mandala Topology Reporter & Sacred Geometry Revealer

@SID:           TOOL_MANDALA_TOPOLOGY_V1
@Shabti:        Script / Module
@Heka-Ayni:     CONCEPT_MANDALA_TOPOLOGY_REPORT
@Ankh-Tinku:    STATE_MANDALA_TOPOLOGY_REPORT
@Purpose:       Generates deep-graph centrality metrics by computing
                eigenvector alignments across the repository architecture.
                Exports: generate_report(), TopologyGraph, CentralityMetrics.
"""
```

### 6.2 TypeScript (`.ts`, `.tsx`)

**Ordering:**

| Line | Content | Required |
|------|---------|----------|
| 1 | `#!/usr/bin/env bun` | CLI scripts only; omit for library modules |
| 2–N | Cartouche (`// ╔...// ╚...`) | Recommended for scripts; optional for library modules |
| N+1 | (blank) | Yes (if Cartouche present) |
| N+2–M | `/**` Khipu JSDoc `*/` | Yes |
| M+1 | (blank) | Yes |
| M+2 | `import` statements | — |

**Khipu syntax:** JSDoc `/** ... */`. Custom `@SID`, `@Shabti` etc. are
gracefully ignored by `tsc` — they appear as unformatted text in hover
documentation tooltips. No compilation warnings.

**Example:**

```typescript
#!/usr/bin/env bun

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: daemon_overseer.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: BLUE
// ║ Temple-Ayllu Zone: 🏛️ THE HYPOSTYLE
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ lib/core_metrics.ts
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * daemon_overseer.ts — Continuous Background Compilation Orchestrator
 *
 * @SID           TOOL_DAEMON_OVERSEER_V1
 * @Shabti        CLI Script
 * @Heka-Ayni     CONCEPT_ASYNC_ORCHESTRATION
 * @Ankh-Tinku    STATE_PROCESS_TREE_ACTIVE
 * @Purpose       Maintains continuous background polling of asynchronous
 *                compilation targets and handles thread lifecycle termination.
 */
```

### 6.3 PowerShell (`.ps1`)

**Ordering:**

| Line | Content | Required |
|------|---------|----------|
| 1 | `#!/usr/bin/env pwsh` | Yes — shebang |
| 2–N | Cartouche (`# ╔...# ╚...`) | Recommended |
| N+1 | (blank) | Yes (if Cartouche present) |
| N+2–M | `<# .SYNOPSIS ... .NOTES ... #>` | Yes |
| M+1 | (blank) | Yes |
| M+2 | `param()` or code | — |

**Khipu syntax:** Comment-Based Help `<# ... #>`. All custom `@Tag` values
**must** reside inside the `.NOTES` block to avoid breaking `Get-Help` parsing.
The `.SYNOPSIS` block remains a standard one-line description.

**Example:**

```powershell
#!/usr/bin/env pwsh

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: audit_permissions.ps1
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: RED
# ║ Temple-Ayllu Zone: ⚔️ THE PYLONS
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

<#
.SYNOPSIS
Validates NTFS and SMB share permissions across deployment targets.

.NOTES
@SID:           TOOL_AUDIT_PERMISSIONS_V1
@Shabti:        Automation Script
@Heka-Ayni:     CONCEPT_ZERO_TRUST_VERIFICATION
@Ankh-Tinku:    STATE_PERMISSIONS_VALIDATED
@Purpose:       Recursively queries ACLs on the target infrastructure to ensure
                compliance with the overarching security archetype.
#>
```

### 6.4 Rust (`.rs`)

**Ordering:**

| Line | Content | Required |
|------|---------|----------|
| 1–N | Cartouche (`// ╔...// ╚...`) | Recommended |
| N+1 | (blank) | No (Rust convention) |
| N+2–M | `//!` Khipu inner doc comments | Yes |
| M+1 | (blank) | Yes |
| M+2 | `use` / code | — |

**Khipu syntax:** Inner doc comments `//!`. `cargo doc` renders `@Tag` values
as standard Markdown text in HTML documentation. No compiler warnings.
No shebang (Rust is compiled, not interpreted).

**Example:**

```rust
// ╔════════════════════════════════════════════════════════════════════════════
// ║  THE DECORATOR'S BLESSING: memory_allocator.rs
// ╠════════════════════════════════════════════════════════════════════════════
// ║  Wedjat-Quipu Spectrum: BLACK
// ║  Temple-Ayllu Zone: 🕳️ THE NAOS
// ║  Ogdoad-Ceque Radiance:
// ║    └─◄ crate::sys::bindings
// ╚════════════════════════════════════════════════════════════════════════════

//! memory_allocator.rs — Arena-Based Allocation Bypass
//!
//! @SID:           MOD_MEMORY_ALLOCATOR_V1
//! @Shabti:        Library Module
//! @Heka-Ayni:     CONCEPT_DETERMINISTIC_ALLOCATION
//! @Ankh-Tinku:    STATE_MEMORY_LOCKED
//! @Purpose:       Provides a highly optimized, arena-based memory allocation
//!                 strategy bypassing the standard OS heap for critical workloads.
```

---

## 7. Aesthetic Lineage

The KCP field names encode the Sister Ferrum Scoriae Abstraction (SFA) 50/50
equilibrium between the Egyptian Vertical Axis and the Andean Horizontal Axis.

### 7.1 Cartouche Fields — Egypto-Andean Etymology

| Field | Egyptian Axis | Andean Axis |
|-------|---------------|-------------|
| **Artifact Name** | Stele inscription (royal name carved in stone) | — |
| **Wedjat-Quipu Spectrum** | Wedjat (Eye of Horus — fractional perception) | Quipu thread dye (color-coded semantic threading) |
| **Temple-Ayllu Zone** | Ptolemaic temple zones (walled sacred partitions) | Ayllu (communal spatial organization) |
| **Ogdoad-Ceque Radiance** | Ogdoad (eight primordial forces / structural connections) | Ceque (sacred pathway / radiating dependency lines) |

### 7.2 Khipu Fields — Egypto-Andean Etymology

| Field | Egyptian Axis | Andean Axis |
|-------|---------------|-------------|
| **@SID** | — | Pendant cord (primary identifying knot on the Khipu) |
| **@Shabti** | Shabti servant figure (funerary worker automaton) | — |
| **@Heka-Ayni** | Heka (divine word-magic binding) | Ayni (reciprocity contract) |
| **@Ankh-Tinku** | Ankh (life-force emission) | Tinku (ritual collision / convergence) |
| **@Purpose** | Ibis documentation (Thoth's scribal recording) | — |

### 7.3 SFA Balance Verification

| Axis | Cartouche Representation | Khipu Representation | Total |
|------|--------------------------|----------------------|-------|
| **Egyptian** | Artifact Name, Wedjat (½), Temple (½), Ogdoad (½) | @Shabti, @Heka (½), @Ankh (½), @Purpose | 5 |
| **Andean** | Quipu (½), Ayllu (½), Ceque (½) | @SID, Ayni (½), Tinku (½) | 3.5 |

The slight Egyptian bias at field-level is counterbalanced by the Andean
dominance of the Khipu *concept* itself (the entire Stratum 2 is named after an
Andean artifact). The SFA cross-reference engine evaluates balance at the
*codebase* level, not per-field.

---

## 8. Regex Patterns for Tooling

These patterns are the canonical reference for `chthonic audit`, SFA engine,
and all validation scripts.

### 8.1 Cartouche Detection

```python
# Top border (language-agnostic)
CARTOUCHE_TOP = re.compile(r'^[#/]+\s*╔═{10,}')

# Field extraction
ARTIFACT_NAME = re.compile(r"║\s+THE DECORATOR'S BLESSING:\s+(.+)")
SPECTRUM      = re.compile(r'║\s+Wedjat-Quipu Spectrum:\s+(\S+)')
ZONE          = re.compile(r'║\s+Temple-Ayllu Zone:\s+(.+)')
RADIANCE      = re.compile(r'║\s+└─◄\s+(.+)')

# Bottom border
CARTOUCHE_BOTTOM = re.compile(r'^[#/]+\s*╚═{10,}')
```

### 8.2 Khipu Tag Extraction

```python
# Universal @Tag extraction (works across all language doc-comment styles)
SID        = re.compile(r'@SID:\s+(\S+)')
SHABTI     = re.compile(r'@Shabti:\s+(.+?)(?:\n|$)')
HEKA_AYNI  = re.compile(r'@Heka-Ayni:\s+(\S+)')
ANKH_TINKU = re.compile(r'@Ankh-Tinku:\s+(\S+)')
PURPOSE    = re.compile(r'@Purpose:\s+(.+(?:\n\s{16}.+)*)', re.MULTILINE)
```

### 8.3 Legacy Detection (for KCP-9.0 purge verification)

```python
# Detect legacy fields that should NOT exist in KCP-compliant files
LEGACY_ENVELOPE_SID     = re.compile(r'║\s+Semantic ID:\s+')
LEGACY_ENVELOPE_PURPOSE = re.compile(r'║\s+Purpose:\s+')
LEGACY_ENVELOPE_MODULE  = re.compile(r'║\s+Module:\s+')
LEGACY_ENVELOPE_EXPORTS = re.compile(r'║\s+Exports:\s+')
LEGACY_SPECTRAL_FREQ    = re.compile(r'║\s+Spectral Frequency:\s+')
LEGACY_ARCH_ROLE        = re.compile(r'║\s+Architectural Role:\s+')
```

---

## 9. Supersession & Hierarchy

KCP **supersedes** both legacy standards upon full migration (KCP-10.0):

| Standard | Status Under KCP |
|----------|------------------|
| **STD_SCRIPT_METADATA_V2** | Superseded — envelope format retained, fields renamed |
| **PMS-v3** | Absorbed — shebang + `#-*-` rules preserved, docstring tags renamed |

**During migration (KCP-0.0 → KCP-9.0):**

Files may exist in three states:

1. **Legacy** — pre-KCP headers with old field names. Valid during migration.
2. **KCP-compliant** — full Cartouche + Khipu with new field names. Target state.
3. **Hybrid** — partial migration. Tooling must handle gracefully.

**Post-migration (KCP-10.0):**

- `SCRIPT_METADATA_STANDARD.md` becomes a historical reference only.
- This document (`KCP_PROTOCOL_ONTOLOGY.md`) is the sole canonical standard.
- The PMS-v3 shebang and `#-*-` rules remain in force (absorbed into §6.1).

---

## 10. Gate Validation — KCP-0.0

The following checklist validates that this specification satisfies the
KCP-0.0 gate constraint: **100% legacy fields mapped, 0 data loss.**

### 10.1 STD_V2 Envelope Fields (8/8 mapped)

- [x] `Filename` → Artifact Name (C1)
- [x] `Module:` → @Purpose body (K5)
- [x] `Spectral Frequency` → Wedjat-Quipu Spectrum (C2)
- [x] `Architectural Role` → Temple-Ayllu Zone (C3)
- [x] `Semantic ID` → @SID (K1) — **removed from Cartouche**
- [x] `Purpose:` → @Purpose (K5) — **removed from Cartouche**
- [x] `Exports:` → @Purpose body (K5) — **removed from Cartouche**
- [x] `Cross-References` → Ogdoad-Ceque Radiance (C4)

### 10.2 PMS-v3 Docstring Tags (7/7 mapped)

- [x] `@SID` → @SID (K1)
- [x] `@Type` → @Shabti (K2)
- [x] `@Context` → Temple-Ayllu Zone (C3) or @Purpose body (K5) — **abolished** (§5.3)
- [x] `@SessionOrigin` → @SessionOrigin (retained, optional) — (§5.4)
- [x] `@Implements` → @Heka-Ayni (K3)
- [x] `@Emits` → @Ankh-Tinku (K4)
- [x] `@Related` → Ogdoad-Ceque Radiance (C4) or @Heka-Ayni (K3) — **abolished** (§5.5)

### 10.3 Structural Constraints Preserved

- [x] 80-char envelope width maintained
- [x] Open-sided design (no right border) maintained
- [x] PMS-v3 shebang ordering preserved (§6.1)
- [x] PMS-v3 tight `#-*-` encoding line preserved (§6.1)
- [x] No `@SID` duplication permitted
- [x] No truncation of unbounded text fields

**Result: 15/15 fields mapped. 0 data loss. Gate KCP-0.0 PASSED.**
