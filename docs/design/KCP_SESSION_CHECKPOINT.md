# ╔════════════════════════════════════════════════════════════════════════════
# ║ KCP SESSION CHECKPOINT — Crash-Resilient Continuation State
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Temple-Ayllu Zone: 🏛️ THE HYPOSTYLE
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ docs/design/SFS_WPTG_ITERATION_PLAN.md
# ║   └─◄ claude-codex-gemini/ANKH_EGYPTOLOGY_SOUTH_AMERICAN/ANKH_UNIFYING_REPOSITORY_METADATA_STANDARDS.md
# ╚════════════════════════════════════════════════════════════════════════════

<!--
@SID:           DOC_KCP_SESSION_CHECKPOINT_V1
@Type:          Checkpoint / Handoff
@Context:       Khipu-Cartouche Protocol Implementation Tracker
@Purpose:       Single file that any new session reads FIRST to know exactly
                where to pick up. Designed for VS Code Insiders crash recovery.
                Every completed phase updates this file atomically — one commit
                per phase, one checkpoint update per commit.
-->

# Khipu-Cartouche Protocol — Session Checkpoint

> **Read this file first.** It tells you exactly where we are, what just
> finished, what's next, and how to validate. If the session crashed, this is
> your recovery point.

---

## Current State

| Field | Value |
|-------|-------|
| **HEAD** | (pending commit) |
| **Branch** | `main` |
| **Last Completed Phase** | Stage S.0 — Python Header Canon |
| **Active Phase** | KCP Phase 0.0 — Protocol Ontology Specification |
| **Blockers** | None |
| **Working Tree** | Clean (pending directory rename commit) |

---

## Recovery Protocol

If you are a new session picking up from a crash:

1. Run `git log --oneline -3` to verify HEAD matches the checkpoint above
2. Run `git status --short` to verify working tree state
3. Read the **Active Phase** section below for exact instructions
4. Mark the phase complete in this file when done
5. Commit this file atomically with the phase work

---

## Gemini Research Verdict

**Source:** `claude-codex-gemini/ANKH_EGYPTOLOGY_SOUTH_AMERICAN/ANKH_UNIFYING_REPOSITORY_METADATA_STANDARDS.md`

**Decision:** Approach C — Stratified Metadata (Visual/Semantic Split)

**Protocol Name:** Khipu-Cartouche Protocol (KCP)

### Architecture Summary

| Layer | Name | Content | Constraint |
|-------|------|---------|------------|
| **Stratum 1** | Cartouche (Envelope) | Artifact Name, Wedjat-Quipu Spectrum, Temple-Ayllu Zone, Ogdoad-Ceque Radiance | 80-char width, enumeration only, NO unbounded text |
| **Stratum 2** | Khipu (Docstring) | @SID, @Shabti, @Heka-Ayni, @Ankh-Tinku, @Purpose | Language-native doc-comment, unbounded width |

### Field Mapping (Legacy → KCP)

| KCP Field | Legacy Field | Layer |
|-----------|-------------|-------|
| Artifact Name | Filename | Cartouche |
| Wedjat-Quipu Spectrum | Spectral Frequency | Cartouche |
| Temple-Ayllu Zone | Architectural Role | Cartouche |
| Ogdoad-Ceque Radiance | Cross-References | Cartouche |
| @SID | Semantic ID | Khipu ONLY (never in Cartouche) |
| @Shabti | @Type | Khipu |
| @Heka-Ayni | @Implements | Khipu |
| @Ankh-Tinku | @Emits | Khipu |
| @Purpose | Purpose | Khipu ONLY (never truncated in Cartouche) |

### Per-Language Khipu Encapsulation

| Language | Khipu Syntax | Constraint |
|----------|-------------|------------|
| Python | `"""..."""` triple-quoted docstring | PMS-v3 shebang + `#-*-` precede Cartouche |
| TypeScript | `/**..*/` JSDoc block | Custom @tags gracefully ignored by tsc |
| PowerShell | `<#.SYNOPSIS...NOTES...#>` | Khipu tags INSIDE `.NOTES` block (parser brittleness) |
| Rust | `//!` inner doc comments | cargo doc renders @tags as Markdown text |

---

## Phase Tracker

### Completed

| Phase | Name | Commit | Validation |
|-------|------|--------|------------|
| S.B | Box Normalization | `51062d30`→`5ed27d93` | 0 closed boxes, 145 files |
| STD_V2 | Metadata Standard Ratification | `aa3d6e84` | Canonical status |
| 2.1 | Icon Collision Resolution | `7a544db0` | 24→11 pairs, 76/76 audits pass |
| S.0 | Python Header Canon | (this commit) | 143 files: spaced→tight `#-*-` |

### Active — KCP Integration Phases

| Phase | Name | Description | Status | Gate |
|-------|------|-------------|--------|------|
| **KCP-0.0** | Protocol Ontology Spec | Finalize field mappings, write canonical schema to `docs/standards/` | ⬜ NEXT | 100% legacy fields mapped, 0 data loss |
| **KCP-1.0** | Architecture Ratification | Lock Approach C into WPTG plan, document rejections | ⬜ | Decision doc merged |
| **KCP-2.0** | Template Canonization | Character-perfect boilerplate for Python/TS/PS1/Rust | ⬜ | All 4 templates pass native parser |
| **KCP-3.0** | Python Consolidation | Batch: eliminate dual @SID, populate Khipu layer in 120 .py files | ⬜ | 0 duplicate @SIDs in Python |
| **KCP-4.0** | TypeScript Injection | Embed Khipu in JSDoc for 62 .ts/.tsx files | ⬜ | `bun run compile` clean |
| **KCP-5.0** | PowerShell Encapsulation | Khipu in `.NOTES` block for 82 .ps1 files | ⬜ | `Get-Help` returns synopsis |
| **KCP-6.0** | Rust Alignment | `//!` Khipu for 15 .rs files | ⬜ | `cargo doc --no-deps` clean |
| **KCP-7.0** | Tooling Refactor | Update `chthonic audit`, SFA engine, normalize script | ⬜ | Knowledge graph indexes all @SIDs |
| **KCP-8.0** | SFA Equilibrium Audit | Overhaul `sfa_cross_reference.py` for KCP fields | ⬜ | 50/50 balance on new ontology |
| **KCP-9.0** | Legacy Purge Verification | Regex sweep: 0 instances of `║ Purpose:` in envelopes | ⬜ | Zero legacy truncated fields |
| **KCP-10.0** | Protocol Ascension | Full integration test: all parsers, all audits, 0% duplication | ⬜ | GOLD |

### Parallel Work (Independent of KCP)

| Stage | Name | Status | Notes |
|-------|------|--------|-------|
| S.0 | Python `#-*-` tight format | ✅ | 143 files fixed, 0 spaced remaining |
| S.3 | Rust @SID tags | ⬜ | 15 files, feeds into KCP-6.0 |
| 4.0 | Token scope coverage | ⬜ | Create `theme_token_coverage.py` |
| 6.0 | Product icon census | ⬜ | Discovery-only |
| 2.1+ | Remaining 11 collision pairs | ⬜ | Need motif redesign (Stage 3.0) |

---

## Priority Stack (Ordered)

1. **S.0** — Python `#-*-` tight format (92 scripts, quickest win, prerequisite for KCP-3.0)
2. **KCP-0.0** — Protocol Ontology Specification (canonical schema doc)
3. **KCP-1.0** — Architecture Ratification (lock Approach C)
4. **KCP-2.0** — Template Canonization (4 language templates)
5. **D.0** — Daemon-Forge Bridge (SFS forge × overnight daemon convergence)
6. **4.0** — Token scope coverage audit
7. **S.3** — Rust @SID tags
8. **6.0** — Product icon census

---

## Validation Commands

```bash
# Icon pipeline gates
uv run python scripts/icon_svg_audit.py          # 76/76 structural+WCAG+palette
uv run python scripts/icon_distinctiveness_audit.py  # collision pairs report

# Build gates
cargo build                                       # Rust compilation
bun run --cwd extensions/chthonic-archive compile # Extension build

# SFA balance
uv run python scripts/sfa_cross_reference.py balance-audit

# Python header compliance (after S.0)
grep -rn "# -*- coding" scripts/ --include="*.py" | wc -l  # should be 0
grep -rn "#-*- coding" scripts/ --include="*.py" | wc -l   # should be 120
```

---

## Key Files

| File | Role |
|------|------|
| `docs/design/SFS_WPTG_ITERATION_PLAN.md` | Master WPTG plan |
| `docs/design/KCP_SESSION_CHECKPOINT.md` | THIS FILE — crash recovery point |
| `docs/standards/SCRIPT_METADATA_STANDARD.md` | Current metadata standard (to be superseded by KCP) |
| `claude-codex-gemini/ANKH_EGYPTOLOGY_SOUTH_AMERICAN/ANKH_UNIFYING_REPOSITORY_METADATA_STANDARDS.md` | Gemini research report |
| `scripts/normalize_blessing_box.py` | Cartouche structural validator |
| `scripts/sfa_cross_reference.py` | SFA 50/50 balance engine |

---

## Disruption Recovery Notes

> "Then the disruptions are predictable if they occur, you then know exactly
> the error that is the same to pick up from. Make it safe and predictable
> while annoying. Cannot be helped."

- VS Code Insiders token budget causes session crashes
- This checkpoint file is the recovery contract
- Each phase completion = 1 atomic commit updating this file
- New sessions: read this file → verify HEAD → resume Active Phase
- Never start a phase without marking it active here first
