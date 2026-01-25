# INSTRUCTIONS_CONSOLIDATED.md

**Purpose:** Selective consolidation of redundant/overlapping instruction files from `.github/instructions/`  
**Date:** 2025-12-30  
**Status:** Operational Archive (Read-Only)

**Consolidation Scope:**
- Preserves SSOT core instructions (00-30 numbered files, chthonic-archive.instructions.md)
- Consolidates redundant ANKH-bound variants and operational overlaps
- No paraphrasing or improvement — concatenation with provenance headers only

---

## Source: `.github/instructions/README.md`
**Original Path:** `.github/instructions/README.md`  
**Lines:** 119 total  
**Function:** Instruction file architecture index and SSOT section map

### Content:

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

---

## Source: `.github/instructions/ANKH_bound-copilot-instructions.md`
**Original Path:** `.github/instructions/ANKH_bound-copilot-instructions.md`  
**Lines:** 100 total (estimated)  
**Function:** ANKH authority model and fracture detection

### Content:

# chthonic-archive — GitHub Copilot Instructions (ANKH-Bound)

## Authority Model

- This repository is governed by a Single Source of Truth (SSOT).

**SSOT:** `copilot-instructions.md`  
- This file is authoritative, singular, and must not be duplicated or paraphrased.

- All Copilot behavior in this repository defers to the SSOT.

---

## Reference Discipline (Mandatory)

- All references to SSOT content MUST use anchor notation:  
  `[ssot:section-name]`
- Prefer reference over reproduction.
- Do NOT restate, summarize, or paraphrase SSOT content.
- Quote fewer than 15 words only when strictly necessary.

- If a required anchor is missing or broken, STOP and surface the issue.

---

## Fracture-Detection

Copilot must surface a **(`fracture`)** immediately when detecting:

- Duplicate definitions across files
- Parallel or competing authority
- Restatement or paraphrase of SSOT content without anchor
- Missing or broken `[ssot:*]` references
- Cross-file or cross-session semantic drift

### Fracture Report Format

```ankh
⚠️ ANKH FRACTURE DETECTED
Type: [duplication | ambiguity | parallel-authority | broken-anchor]
Location: [file or code region]
SSOT Anchor: [ssot:reference-if-known]
Action Required: [escalate | repair | remove-duplicate]
Details: [brief description of the fracture]
```
- Upon detecting a fracture, Copilot must halt further changes and output the fracture report.

## Enforcement

- Copilot must enforce these instructions strictly. Any deviation must be treated as a fracture and reported immediately.

---

## Revision History

| Version | Date | Description | Author |
|---|---|---|---|
| 1.0.0 | 2024-06-10 | Initial creation of ANKH-bound Copilot instructions. | The Savant |

---

## Source: `.github/instructions/copilot-SSOT-ANKH-instructions.yaml`
**Original Path:** `.github/instructions/copilot-SSOT-ANKH-instructions.yaml`  
**Lines:** 100 total (estimated)  
**Function:** YAML continuation of ANKH-bound instructions

### Content:

```yaml
# Refusal to proceed due to unresolved fracture is correct behavior.

---

## Branch and File Handling

- Branch files and secondary `.md` or `.instructions.md` files are **views**, not sources.
- They may be edited or generated.
- They MUST reference SSOT anchors.
- They MUST NOT introduce new authority.
- Copilot must never elevate branch content to canonical status.

---

## Code Generation and Review

When generating or reviewing code:

- Do not invent architectural rules.
- Do not infer policy from examples.
- Reference SSOT anchors when constraints or conventions apply.
- If the SSOT does not specify a rule, do not fabricate one.

Unspecified behavior → surface ambiguity instead of guessing.

---

## Continuity

- Maintain anchor-based addressability across edits.
- Do not recreate definitions from memory.
- Always verify `[ssot:*]` references remain valid.
- Semantic drift is a failure state.

---

## Operational Stance

- Copilot operates as a governed projection.
- Accuracy and coherence take priority over convenience.
- Silence or refusal is valid when authority is unclear.
- This repository prioritizes lineage preservation and semantic stability over speed.

---

## Enforcement Priority

1. Prevent duplication
2. Preserve SSOT singularity
3. Detect fractures early
4. Maintain anchor-based continuity
5. Respect projection boundaries
```

---

## Source: `.github/instructions/agent-sleep-mode.md`
**Original Path:** `.github/instructions/agent-sleep-mode.md`  
**Lines:** 168 total  
**Function:** Overnight autonomy operational directives

### Content:

---
applyTo: "**"
---

# Agent Sleep-Mode Instructions (Overnight Autonomy)

**Date baseline:** 2025-12-25 (update only if running later)

This repo is in a "tidy + curate" phase:
- Repo hygiene: keep machine-generated artifacts out of git (Python bytecode/caches, runtime outputs if not explicitly intended).
- Dumpster-dive curation: validate/fix cross-references, decide which large protocol/docs additions are intentional, keep navigation coherent.

These instructions are for autonomous work **while the user is asleep**. They are designed to prevent terminal lock-ups and to keep progress "safe, reversible, and reviewable."

---

## 0) Prime Directive

1. **Do not get stuck** in any long-running terminal process.
2. **Prefer small, reversible edits** over sweeping refactors.
3. **Always leave an audit trail**: summarize what changed and what remains.

---

## 1) Flow Balance ("YOLO Mode" Without Overheating)

When uncertain, act — but **timebox** and keep changes reversible.

### 1.1 Timeboxing
- Work in **25-minute blocks**.
- At the end of each block, do one of:
  - ship a small safe improvement,
  - switch tasks,
  - stop and leave a clear note.

### 1.2 Decision rule
If a task becomes ambiguous or error-prone for **> 10 minutes**, stop digging and pivot to something deterministic.

### 1.3 Risk tiers
- **Tier 0 (safe):** `.gitignore` hygiene, deleting cache artifacts, link fixes, small doc corrections, running read-only validation scripts.
- **Tier 1 (medium):** reorganizing docs, renames/moves, large-format rewrites.
- **Tier 2 (high):** code refactors, dependency changes, integration/manifest automation.

Overnight work should stay mostly in Tier 0–1.

---

## 2) Terminal Anti-Stuck Protocol (Critical)

### 2.1 Prefer Tasks over ad-hoc terminals
- If a VS Code task exists (e.g., Cargo tasks), run it via task runner.
- Avoid starting servers or watch processes overnight unless explicitly requested.

### 2.2 Time limits and watchdog checks
- Any terminal command must have a **clear expected runtime**.
- If a command may run long, run it in the background **only** if you have a plan to check output.
- Watchdog:
  - Check output once.
  - If it appears stuck, **stop issuing more commands** and pivot to non-terminal work.

### 2.3 "Stuck detection" heuristics
Treat the terminal as "stuck" if:
- no new output for ~2 minutes on a command that should be active,
- command hangs waiting for input,
- it's a long-running service that blocks further progress.

### 2.4 If stuck anyway
- Do not spiral.
- Pivot immediately to file-based work (docs/ignores/link fixes).
- Leave a note: *which command*, *why it appears stuck*, *what alternative path you took*.

---

## 3) Overnight Checklist (Current Work)

### 3.1 Repo hygiene sweep (Tier 0)
Goal: ensure no generated artifacts are tracked.

Actions:
- Confirm `.gitignore` includes:
  - `**/__pycache__/`
  - `**/*.pyc`
  - `**/*.pyo`
- Remove any newly introduced caches if they appear again.
- Identify other likely runtime outputs and decide whether they are intended to be committed:
  - examples: diagnostic JSON reports, memory snapshots, logs.

Deliverable:
- A short report listing:
  - what was removed/ignored,
  - any questionable artifacts that need user intent.

### 3.2 Dumpster-dive reference validation (Tier 0–1)
Goal: ensure links are not broken and cross-reference coverage is coherent.

Actions:
- Run the cross-reference validator:
  - `powershell -File .\dumpster-dive\validate_references.ps1 -Path .\dumpster-dive`
- If broken links are reported:
  - Fix the simplest/high-confidence broken links.
  - Leave a summary for the user to review ambiguous ones.

### 3.3 Python env determinism (Tier 0)
Goal: ensure no version drift in the uv lanes and that GPU diagnostics remain up-to-date.

Actions:
- Verify `.python-version` is pinned (currently 3.13).
- Run: `uv python upgrade 3.13 --reinstall` (optional, if no version churn).
- Confirm GPU validation scripts run without error.

Deliverable:
- Short report:
  - Which lane was tested.
  - Any newly detected drift or missing dependencies.

### 3.4 Optional: doc consolidation experiments (Tier 1)
Goal: prototype a consolidated roadmap or meta-index for the archive.

Actions:
- **Only if prior tasks finished quickly and cleanly**.
- Propose or generate a high-level `ROADMAP.md` for upcoming phases (e.g., integration checkpoints, public presentation strategy).
- Avoid creating duplicate "vision" documents if existing ones suffice.

Deliverable:
- A draft or proposal (not committed without user review).

---

## 4) Deliverables Format

At the end of your work session, produce:
1. **Session Summary** (a `SESSION_SUMMARY_YYYYMMDD.md` in `logs/` or `dev/`):
   - What tasks were attempted.
   - What succeeded.
   - What was skipped or flagged for user review.
   - Any terminal commands that ran (or stalled).
   - Total time spent (~estimate based on block count).

2. **Artifact List**:
   - Files touched or created.
   - Key changes (e.g., "Added 3 .gitignore entries", "Fixed 5 broken cross-refs").

3. **Pending Questions** (if any):
   - Brief list of decisions left for the user.

---

## 5) Escalation

If a critical or unexpected fracture is detected (e.g., SSOT semantic drift, critical missing dependency), **stop work** and surface the issue in a `FRACTURE_REPORT_YYYYMMDD.md`.

Do not attempt automatic fix without explicit permission.

---

## 6) Post-Session Behavior

- Do not leave VS Code tasks running.
- Close or stop any terminals that might remain open (if possible via command).
- Ensure repo state is clean for the user to wake up to.

---

## Revision History

| Version | Date | Notes |
|---|---|---|
| 1.0 | 2025-12-25 | Initial overnight autonomy instructions. |

---

## Source: `.github/instructions/Yolic_Agent_Swift_Prompt_Alphaic_Directive_Instructions.md`
**Original Path:** `.github/instructions/Yolic_Agent_Swift_Prompt_Alphaic_Directive_Instructions.md`  
**Lines:** 200 total (estimated)  
**Function:** YOLIC mode behavior distillation (outsourced SSOT for agent behavior)

### Content:

---
applyTo: "**"
---

# Yolic_Agent_Swift_Prompt_Alphaic_Directive_Instructions

This file is the **outsourced SSOT for agent behavior** (YOLIC mode) distilled from the Over-Prompt section of `.github/copilot-instructions.md`.

Scope rule: this document governs **behavior + safety + repo-operational workflow**. It intentionally does **not** duplicate the monolith body.

---

## 0) Alphaic Directive (Read First)

- Default posture: **smallest correct change**.
- If a solution works: **stop**.

---

## 1) Hard Bans (Anti-Patterns)

- DO NOT add complexity to create "tech depth".
- DO NOT introduce new layers (frameworks/abstractions/scripts/modules/caches) unless the request strictly requires it.
- DO NOT expand scope for "future-proofing" or "nice-to-have".
- DO NOT create new variants of existing commands/tools unless the old one is retired and a **single canonical path** replaces it.

---

## 2) Execution Style (Swift + Surgical)

- Prefer **one small patch** over broad refactors.
- Preserve existing style and conventions.
- Avoid reformatting unrelated blocks.
- When uncertain, ask **1–3 precise questions** or choose the simplest valid interpretation.

---

## 3) Toolchain (Win11, uv lanes)

Policy: latest-stable lanes.

- Repo Python pin: `.python-version` = `3.13`
- Lanes:
  - `python` → uv shim `python3.13.exe` (3.13.x latest patch)
  - `python314` → uv shim `python3.14.exe` (3.14.x latest patch)

Maintenance:
- `uv python upgrade 3.13 --reinstall`
- `uv python upgrade 3.14 --reinstall`
- `uv python update-shell`

Tools:
- Ruff is managed via uv tool:
  - `uv tool install ruff` or `uv tool update ruff`

---

## 4) Terminal Activation (Claudine)

- In this repo, `claudine` is a **repo-local command** wired by the workspace profile.
- It should be deterministic: show versions; do not surprise-mutate user system state.
- Avoid global auto-activation behaviors leaking from other repos.

---

## 5) Governance / Gated Deploy (Timeline A)

- Drift gate is a hard stop: do not deploy if SSOT drift check fails.
- Default deploy runs are **dry-run** unless explicitly applying.
- "Apply" must be idempotent: no churn when there are no changes.
- Registry identity is stable; mutable bytes tracking uses `artifact_hash*`.

---

## 6) Output Expectations

- Always report:
  - What changed
  - Where
  - How to verify
  - Any risks/assumptions
- Keep answers concise; avoid repetition.

---

## End of Consolidated Content
