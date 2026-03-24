---
sid: HIERARCHICAL_WORK_PLAN_2026_03_18
title: Hierarchical Work Plan — Desktop Parity, Rust Lane, Skill Architecture
type: strategic-plan
status: ACTIVE
created: 2026-03-18
scope: infrastructure · rust-lane · skill-architecture · SSOT-gap
machine: desktop (eldno) — RTX 4090 24GB · Win11 · VS 2026 Insiders 18.5
---

# Hierarchical Work Plan — 2026-03-18

> Structured by dependency chain. What VS 2026 enables → what's immediately actionable → what needs approval.

---

## Tier 0 — Toolchain Foundation (VS 2026 Unlocks)

**Status:** VS 2026 Community Insiders 18.5 11605.296 INSTALLED. 17 workloads. MSVC 14.50.35717 confirmed.
VS 2026 Build Tools Insiders 18.5 11605.296 INSTALLED at BuildTools/Microsoft Visual Studio/18/BuildTools).
SSMS 22.3 11527.330 INSTALLED at [Microsoft SQL Server Management Studio 22\Release](C:\Program Files\Microsoft SQL Server Management Studio 22\Release).
Bicep CLI: NOT INSTALLED (az CLI also absent — install via `winget install Microsoft.Bicep` if needed).

| Component | Status | Path |
|-----------|--------|------|
| MSVC cl.exe (x64) | ✅ PRESENT | `C:\Program Files\Microsoft Visual Studio\18\Insiders\VC\Tools\MSVC\14.50.35717\bin\Hostx64\x64\cl.exe` |
| Windows SDK 26100 | ✅ PRESENT | Installed via NativeDesktop workload |
| CMake (VS-integrated) | ✅ PRESENT | Component.Linux.CMake + VC.CMake.Project |
| .NET SDK 10.0 | ✅ PRESENT | `dotnet --version` → `10.0.201` |
| CUDA 13.2 + 12.8 | ✅ PRESENT | `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\` |
| Rust 1.94.0 (stable) | ✅ PRESENT | `rustup show` → stable-x86_64-pc-windows-msvc |
| Clang/LLVM (VS) | ✅ PRESENT | Add `Microsoft.VisualStudio.Component.VC.Llvm.Clang` via .vsconfig |
| ATL/MFC | ✅ PRESENT | Needed for some native builds — check .vsconfig |
| VS 2026 Build Tools | ✅ PRESENT | `C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools` (18.5.11605.296) |
| SSMS 22 | ✅ PRESENT | `C:\Program Files\Microsoft SQL Server Management Studio 22\Release` (22.3.11527.330) |
| Bicep CLI | ✅ PRESENT | `winget install Microsoft.Bicep` — needed for Azure IaC |
| Azure CLI | ✅ PRESENT | `winget install Microsoft.AzureCLI` — needed for `az bicep` |
| mistralrs-server | ❌ NOT INSTALLED | No binary in `~/.cargo/bin/` — BLOCKS Track A |
| GGUF model file | ❌ NOT PRESENT | No model in `dev/models/` — BLOCKS Track A |

**What VS 2026 unlocked:** MSVC toolchain required for `cargo install mistralrs-server --features cuda` (links against cl.exe + CUDA). Previously impossible without Build Tools.

### Immediate Action: Install mistralrs-server

```powershell
# Per RUSTIFICATION.md — canonical inference engine
# Requires: MSVC (✅), CUDA toolkit (✅ v13.2), Rust (✅ 1.94.0)
cargo install mistralrs-server --features cuda
```

This is the **single highest-leverage action** — it unblocks Track A items U3, C6, C7, U5, and eventually the LoRA pipeline (LF1–LF2).

---

## Tier 1 — Immediate Work (No Blockers)

### 1A. Rust Lane — mistralrs Compilation + Validation

| Step | Action | Agent | Depends On |
|------|--------|-------|------------|
| 1 | `cargo install mistralrs-server --features cuda` | User | VS 2026 ✅ |
| 2 | Verify `mistralrs-server --help` resolves | User | Step 1 |
| 3 | Download GGUF model to `dev/models/` (Task U1) | User | None |
| 4 | Create `scripts/start_mistralrs.ps1` (Task C2) | Claude/Codex | None |
| 5 | Start server, verify `localhost:8080/health` (Task U3) | User | Steps 2–4 |

### 1B. ~~Dead Code Fix (procedural.rs)~~ — ALREADY RESOLVED

**Source:** [codex/mailbox/FIX_DEAD_CODE_WARNINGS.md](../../codex/mailbox/FIX_DEAD_CODE_WARNINGS.md)
- ✅ `generate_sub_milf`, `generate_agent` — already have `#[allow(dead_code)]` + TODO comments
- ✅ `FactionCode` — already uses `impl fmt::Display`
- ✅ `cargo check` returns ZERO warnings as of 2026-03-18
- **Action:** Close this handoff. No work needed.

### 1C. CHORE Phase 3 — Script Variant Triage

**Source:** CHORE_CODEBASE_HYGIENE Phase 3
- 6+ variant families: `decorator_cross_ref` (3×172KB), `hf_` (6×), `claude_` (8×)
- Identify canonical variant per family, redirect rest
- **Effort:** 1 session. **Impact:** ~50% reduction in scripts/ noise.

### 1D. ANKH Gap Closure (Tasks CA1–CA5)

Per TASK_SCHEDULE — all unblocked, all Claude work:
- **CA1:** `docs/frameworks/ankh/ANKH_FOUNDATIONAL_AXIOMS.md` — FA¹–FA⁵ standalone specs (HIGH)
- **CA2:** ANKH Invocation Protocol (after CA1)
- **CA3:** MSP-RSG Generative Engine (after CA1)
- **CA4:** DAFP context modulation (after CA1)
- **CA5:** ANKH Anti-Patterns / Horse-Market (after CA1+CA2)

---

## Tier 2 — Requires Approval or Dependencies

### 2A. Skill Consolidation (27 → ≤15)

**Source:** [codex/mailbox/SKILL_CONSOLIDATION_PROPOSAL.md](../../codex/mailbox/SKILL_CONSOLIDATION_PROPOSAL.md)
- 8 archive candidates identified (REDIRECT/STASHED/PROTOCOL)
- 4 more merges needed to hit target
- **BLOCKED ON:** User approval of the proposal
- **Why it matters:** AGENTS.md cap is 15. Currently 12 over.

### 2B. Log Archaeology Untrack (218 files)

**Source:** [codex/mailbox/LOG_ARCHAEOLOGY_TRIAGE.md](../../codex/mailbox/LOG_ARCHAEOLOGY_TRIAGE.md)
- 340 logs triaged: 118 preserve, 218 untrack-after-extraction, 4 extract-then-archive
- Includes VS2026_ELEVATED_VALIDATE logs, MISTRALRS_CUDA_BUILD logs, VSCODE_INSIDERS_MATRIX logs
- **BLOCKED ON:** User approval of the untrack list

### 2C. OxidizedIndex Spec + Implementation (Track B)

Per TASK_SCHEDULE:
- B1–B3 (Claude spec work) — unblocked
- B4–B6 (Codex implementation) — after B1–B3
- B7–B8 (daemon integration) — after B4 + Track A complete

### 2D. .vsconfig Component Additions

Generated [claude/mailbox/VS2026_DESKTOP.vsconfig](VS2026_DESKTOP.vsconfig):
- Adds Clang/LLVM, ATL/MFC, diagnostic tools, .NET 4.8.1 SDK
- Import via: `Tools → Get Tools and Features → Import .vsconfig`
- Also update VS to 11612.153 (pending update shown in installer)

---

## Tier 3 — Strategic / Convergence Work

### 3A. LoRA Fine-Tune Pipeline (Tasks L1, LF1, LF2)

Converges Tracks A + C:
- Requires: mistralrs running (Tier 1A), ANKH gaps closed (Tier 1D), character extraction (L3, L5)
- Claude drafts DR brief → Gemini executes SSOT corpus extraction → User runs Unsloth → Deploy to TabbyAPI
- **This is the endgame** — local model serving LUPLR voice natively.

### 3B. CHORE Phase 6 — Forge Dedup Audit

- Furnace ↔ tempered 1:1 mirror after perfect 18/18 graduation
- Depends on script variant triage (Tier 1C) being clean first

### 3C. CHORE Phase 7 — Migration Plan

- Stale `.ankhrc` references in MIGRATION_PLAN_STATUS.md
- Depends on ANKH gap closure (Tier 1D) to have canonical paths

---

## Skill Depth Gap: SSOT vs Skills

| Dimension | SSOT Archive (956KB) | Skills (27 @ avg 5KB) | Gap |
|-----------|---------------------|----------------------|-----|
| Entity Architecture | 17 tiers, 15+ entity profiles, full genealogy | Zero entity awareness | **TOTAL** |
| Protocol Systems | ANKH, MSP-RSG, CRC, TCP, SAP, ASP, DCRP, APCR | None implemented | **TOTAL** |
| Mathematical Engines | TPEF, T³-MΨ, WHR Power Law, tensor synthesis | None | **TOTAL** |
| Game Mechanics | MILF procedural gen, SBS interactive scenarios, SLA | procedural.rs (dead code) | **CRITICAL** |
| Linguistic Framework | DULSS, LUPLR, ESL (emoji semantics) | None | **TOTAL** |
| Development Conventions | §XIV full convention set | python-header-canon (1.5KB) | **SEVERE** |
| Cross-Reference | DCRP self-awareness system, §XV | None | **TOTAL** |
| Agent Governance | APCR priority/conflict, §XVI | Partial (postman, mailbox-handoff) | **HIGH** |

**Verdict:** Skills are procedural shells. The SSOT contains deep architectural blueprints — entity ontologies, protocol grammars, mathematical foundations — that skills don't reference, implement, or even acknowledge. The gap isn't about quantity; it's about *structural depth*. Skills tell Codex *what to do*. The SSOT tells any agent *what things are and why they exist*.

### Bridging Strategy

1. **ANKH gap closure (CA1–CA5)** extracts the architectural core into standalone docs that skills can reference
2. **OxidizedIndex (B1–B6)** proves the model: SSOT knowledge → spec → implementation → verified tool
3. **LoRA fine-tune (LF1–LF2)** encodes the depth directly into model weights, bypassing the skill layer entirely

---

## Priority Execution Order

```
NOW     → Install mistralrs-server (Tier 1A step 1)
NOW     → Fix dead code warnings (Tier 1B)
NOW     → Start ANKH FA¹–FA⁵ (Tier 1D / CA1)
NEXT    → Download GGUF model (Tier 1A step 3)
NEXT    → Script variant triage (Tier 1C)
PENDING → Skill consolidation (Tier 2A — needs approval)
PENDING → Log untrack (Tier 2B — needs approval)
QUEUED  → OxidizedIndex spec (Tier 2C / B1)
FUTURE  → LoRA pipeline (Tier 3A — after A+C converge)
```
